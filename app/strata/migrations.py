"""Ordered, checksummed, transactional PostgreSQL migrations.

The ledger has an explicit bootstrap because a migration runner cannot record
numbered migrations before its ledger exists. The bootstrap creates only that
ledger and is safe to repeat. Numbered migrations and their ledger inserts
commit in the same transaction.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import psycopg

logger = logging.getLogger(__name__)

BOOTSTRAP_FILENAME = "bootstrap.sql"
MIGRATION_FILENAME = re.compile(r"^(?P<version>[0-9]{3})_[a-z0-9][a-z0-9_]*\.sql$")
# A session lock serializes bootstrap and migration planning across app starts.
MIGRATION_ADVISORY_LOCK_ID = 0x535452415441


class MigrationError(RuntimeError):
    """Base class for migration failures that must stop startup."""


class MigrationLayoutError(MigrationError):
    """Migration files are missing, ambiguous, or incorrectly named."""


class ChecksumMismatch(MigrationError):
    """An already-applied migration no longer matches its recorded bytes."""


class LedgerCorruptionError(MigrationError):
    """The ledger cannot be reconciled with the checked-in migration set."""


class MigrationExecutionError(MigrationError):
    """A numbered migration failed and was rolled back."""


@dataclass(frozen=True)
class Migration:
    version: int
    path: Path
    sql: str
    checksum: str


def _statement_starts(sql: str) -> list[str]:
    """Return normalized statement prefixes outside comments and quoted text.

    This is intentionally a small lexer rather than a SQL parser. It only needs
    to find statement boundaries and leading keywords so the runner can forbid
    transaction control while leaving function bodies and string contents
    untouched.
    """
    visible: list[str] = []
    index = 0
    block_depth = 0
    while index < len(sql):
        pair = sql[index : index + 2]
        if block_depth:
            if pair == "/*":
                block_depth += 1
                index += 2
            elif pair == "*/":
                block_depth -= 1
                index += 2
            else:
                index += 1
            continue
        if pair == "--":
            newline = sql.find("\n", index + 2)
            index = len(sql) if newline < 0 else newline + 1
            visible.append(" ")
            continue
        if pair == "/*":
            block_depth = 1
            index += 2
            visible.append(" ")
            continue
        if sql[index] in {"'", '"'}:
            quote = sql[index]
            index += 1
            while index < len(sql):
                if sql[index] == quote:
                    if index + 1 < len(sql) and sql[index + 1] == quote:
                        index += 2
                        continue
                    index += 1
                    break
                index += 1
            visible.append(" ")
            continue
        if sql[index] == "$":
            tag_match = re.match(r"\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$", sql[index:])
            if tag_match is not None:
                tag = tag_match.group(0)
                closing = sql.find(tag, index + len(tag))
                index = len(sql) if closing < 0 else closing + len(tag)
                visible.append(" ")
                continue
        visible.append(sql[index])
        index += 1

    return [
        " ".join(statement.strip().upper().split()[:2])
        for statement in "".join(visible).split(";")
        if statement.strip()
    ]


def _assert_runner_owns_transactions(sql: str, path: Path) -> None:
    forbidden_first_words = {
        "ABORT",
        "BEGIN",
        "COMMIT",
        "END",
        "RELEASE",
        "ROLLBACK",
        "SAVEPOINT",
    }
    for prefix in _statement_starts(sql):
        words = prefix.split()
        if (
            words[0] in forbidden_first_words
            or prefix == "START TRANSACTION"
            or prefix == "PREPARE TRANSACTION"
        ):
            raise MigrationLayoutError(
                f"{path.name} contains transaction control ({prefix}); "
                "the migration runner owns transaction boundaries"
            )


def _read_sql(path: Path) -> tuple[str, str]:
    try:
        raw = path.read_bytes()
        sql = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise MigrationLayoutError(f"cannot read UTF-8 migration file {path}: {exc}") from exc
    if not sql.strip():
        raise MigrationLayoutError(f"migration file is empty: {path}")
    return sql, hashlib.sha256(raw).hexdigest()


def discover_migrations(migrations_dir: Path) -> list[Migration]:
    """Validate and return numbered migrations in numeric version order."""
    directory = Path(migrations_dir)
    if not directory.is_dir():
        raise MigrationLayoutError(f"migration directory does not exist: {directory}")

    bootstrap = directory / BOOTSTRAP_FILENAME
    if not bootstrap.is_file():
        raise MigrationLayoutError(f"bootstrap file does not exist: {bootstrap}")

    migrations: list[Migration] = []
    by_version: dict[int, Path] = {}
    for path in directory.glob("*.sql"):
        if path.name == BOOTSTRAP_FILENAME:
            continue
        match = MIGRATION_FILENAME.fullmatch(path.name)
        if match is None:
            raise MigrationLayoutError(
                f"invalid migration filename {path.name!r}; expected NNN_name.sql"
            )
        version = int(match.group("version"))
        if version < 1:
            raise MigrationLayoutError(f"migration versions begin at 001: {path.name}")
        if version in by_version:
            raise MigrationLayoutError(
                f"duplicate migration version {version:03d}: "
                f"{by_version[version].name} and {path.name}"
            )
        sql, checksum = _read_sql(path)
        _assert_runner_owns_transactions(sql, path)
        by_version[version] = path
        migrations.append(Migration(version, path, sql, checksum))

    if not migrations or 1 not in by_version:
        raise MigrationLayoutError("numbered migrations must begin with 001")
    return sorted(migrations, key=lambda migration: migration.version)


def _ledger_exists(cursor: psycopg.Cursor) -> bool:
    cursor.execute("SELECT to_regclass('schema_migrations') IS NOT NULL")
    row = cursor.fetchone()
    return bool(row and row[0])


def bootstrap_ledger(conn: psycopg.Connection, bootstrap_path: Path) -> None:
    """Execute the idempotent, ledger-only bootstrap in its own transaction."""
    sql, _checksum = _read_sql(Path(bootstrap_path))
    try:
        with conn.transaction():
            with conn.cursor() as cursor:
                cursor.execute(sql)
    except psycopg.Error as exc:
        raise MigrationExecutionError(
            f"bootstrap migration failed and was rolled back: {exc}"
        ) from exc


def _read_ledger(conn: psycopg.Connection) -> dict[int, str]:
    try:
        with conn.transaction():
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT version, checksum FROM schema_migrations ORDER BY version"
                )
                rows = cursor.fetchall()
    except psycopg.Error as exc:
        raise LedgerCorruptionError(f"cannot read schema_migrations ledger: {exc}") from exc

    applied: dict[int, str] = {}
    for version, checksum in rows:
        if version in applied:
            raise LedgerCorruptionError(
                f"schema_migrations contains duplicate version {version}"
            )
        if not isinstance(version, int) or version < 1:
            raise LedgerCorruptionError(
                f"schema_migrations contains invalid version {version!r}"
            )
        if not isinstance(checksum, str) or re.fullmatch(r"[0-9a-f]{64}", checksum) is None:
            raise LedgerCorruptionError(
                f"schema_migrations version {version:03d} has invalid checksum"
            )
        applied[version] = checksum
    return applied


def _acquire_migration_lock(conn: psycopg.Connection) -> None:
    with conn.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_lock(%s)", (MIGRATION_ADVISORY_LOCK_ID,))
    conn.commit()


def _release_migration_lock(conn: psycopg.Connection) -> None:
    # A failed statement can leave a transaction aborted. Clear it before the
    # unlock query; closing the session remains the final lock-release fallback.
    conn.rollback()
    with conn.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_ADVISORY_LOCK_ID,))
        row = cursor.fetchone()
    conn.commit()
    if not row or row[0] is not True:
        raise MigrationError("database did not release the migration advisory lock")


def run_migrations(conn: psycopg.Connection, migrations_dir: Path) -> list[int]:
    """Bootstrap if needed, validate history, and apply each pending migration.

    Returns the versions applied by this invocation. An empty list is a logged
    no-op. The connection is dedicated to startup migration work; any open
    transaction is committed before the session-level advisory lock is taken.
    """
    migrations = discover_migrations(Path(migrations_dir))
    bootstrap_path = Path(migrations_dir) / BOOTSTRAP_FILENAME
    conn.commit()
    _acquire_migration_lock(conn)
    try:
        with conn.transaction():
            with conn.cursor() as cursor:
                ledger_exists = _ledger_exists(cursor)
        if not ledger_exists:
            logger.info("schema_migrations ledger absent; running explicit bootstrap")
            bootstrap_ledger(conn, bootstrap_path)
        else:
            logger.info("schema_migrations ledger already present; bootstrap skipped")

        applied = _read_ledger(conn)
        files_by_version = {migration.version: migration for migration in migrations}
        missing_files = sorted(set(applied) - set(files_by_version))
        if missing_files:
            formatted = ", ".join(f"{version:03d}" for version in missing_files)
            raise LedgerCorruptionError(
                f"applied migration files are missing for ledger versions: {formatted}"
            )

        for version, recorded_checksum in applied.items():
            actual_checksum = files_by_version[version].checksum
            if recorded_checksum != actual_checksum:
                raise ChecksumMismatch(
                    f"checksum mismatch for applied migration {version:03d}: "
                    f"ledger={recorded_checksum}, file={actual_checksum}"
                )

        pending = [
            migration for migration in migrations if migration.version not in applied
        ]
        if not pending:
            current = max(applied, default=0)
            logger.info(
                "no pending migrations; schema is current at version %03d", current
            )
            return []

        completed: list[int] = []
        for migration in pending:
            logger.info(
                "applying migration %03d from %s",
                migration.version,
                migration.path.name,
            )
            try:
                with conn.transaction():
                    with conn.cursor() as cursor:
                        cursor.execute(migration.sql)
                        cursor.execute(
                            """
                            INSERT INTO schema_migrations (version, checksum)
                            VALUES (%s, %s)
                            """,
                            (migration.version, migration.checksum),
                        )
            except psycopg.Error as exc:
                raise MigrationExecutionError(
                    f"migration {migration.version:03d} "
                    f"({migration.path.name}) failed and was rolled back: {exc}"
                ) from exc
            completed.append(migration.version)
            logger.info("migration %03d applied", migration.version)
        return completed
    finally:
        _release_migration_lock(conn)
