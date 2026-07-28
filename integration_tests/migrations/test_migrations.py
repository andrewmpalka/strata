"""Migration engine integration and adversarial tests against PostgreSQL."""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

import pytest

from strata.db import connect_with_backoff
from strata.migrations import (
    ChecksumMismatch,
    MigrationExecutionError,
    MigrationLayoutError,
    LedgerCorruptionError,
    bootstrap_ledger,
    discover_migrations,
    run_migrations,
)

REPOSITORY_MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"


@pytest.fixture
def migration_db(db_config):
    """Give each test an isolated schema inside the disposable CI database."""
    schema = f"migration_test_{uuid.uuid4().hex}"
    conn = connect_with_backoff(db_config, timeout_seconds=60)
    conn.autocommit = True
    with conn.cursor() as cursor:
        cursor.execute(f'CREATE SCHEMA "{schema}"')
        cursor.execute(f'SET search_path TO "{schema}"')
    conn.autocommit = False
    try:
        yield conn, schema
    finally:
        conn.rollback()
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute("SET search_path TO public")
            cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        conn.close()


def _copy_migrations(destination: Path) -> Path:
    target = destination / "migrations"
    shutil.copytree(REPOSITORY_MIGRATIONS, target)
    return target


def _relation_names(conn) -> list[str]:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = current_schema()
            ORDER BY tablename
            """
        )
        return [row[0] for row in cursor.fetchall()]


def test_first_run_bootstraps_and_applies_001(migration_db):
    conn, _schema = migration_db

    assert run_migrations(conn, REPOSITORY_MIGRATIONS) == [1]

    with conn.cursor() as cursor:
        cursor.execute("SELECT version, length(checksum) FROM schema_migrations")
        assert cursor.fetchall() == [(1, 64)]
        cursor.execute("SELECT singleton, message FROM strata_migration_sentinel")
        assert cursor.fetchall() == [(True, "migration engine ready")]


def test_double_apply_is_logged_no_op(migration_db, caplog):
    conn, _schema = migration_db
    run_migrations(conn, REPOSITORY_MIGRATIONS)

    with caplog.at_level(logging.INFO):
        assert run_migrations(conn, REPOSITORY_MIGRATIONS) == []

    assert "no pending migrations; schema is current at version 001" in caplog.text
    with conn.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM schema_migrations")
        assert cursor.fetchone() == (1,)


def test_tampered_applied_migration_aborts_loudly(migration_db, tmp_path):
    conn, _schema = migration_db
    migrations = _copy_migrations(tmp_path)
    run_migrations(conn, migrations)
    migration = migrations / "001_migration_sentinel.sql"
    migration.write_text(
        migration.read_text(encoding="utf-8") + "\n-- unauthorized edit\n",
        encoding="utf-8",
    )

    with pytest.raises(ChecksumMismatch, match="checksum mismatch.*001"):
        run_migrations(conn, migrations)

    with conn.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM schema_migrations")
        assert cursor.fetchone() == (1,)


def test_failing_migration_and_ledger_insert_roll_back_atomically(
    migration_db, tmp_path
):
    conn, _schema = migration_db
    migrations = _copy_migrations(tmp_path)
    (migrations / "002_forced_failure.sql").write_text(
        """
        CREATE TABLE must_rollback (id INTEGER PRIMARY KEY);
        INSERT INTO must_rollback (id) VALUES (1), (1);
        """,
        encoding="utf-8",
    )

    with pytest.raises(MigrationExecutionError, match="002.*rolled back"):
        run_migrations(conn, migrations)

    assert "must_rollback" not in _relation_names(conn)
    with conn.cursor() as cursor:
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        assert cursor.fetchall() == [(1,)]


def test_nontransactional_ddl_is_rejected_without_partial_state(
    migration_db, tmp_path
):
    conn, _schema = migration_db
    migrations = _copy_migrations(tmp_path)
    (migrations / "002_concurrent_index.sql").write_text(
        """
        CREATE TABLE index_target (id INTEGER PRIMARY KEY);
        CREATE INDEX CONCURRENTLY index_target_id ON index_target (id);
        """,
        encoding="utf-8",
    )

    with pytest.raises(MigrationExecutionError, match="002.*rolled back"):
        run_migrations(conn, migrations)

    assert "index_target" not in _relation_names(conn)
    with conn.cursor() as cursor:
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        assert cursor.fetchall() == [(1,)]


def test_migration_cannot_escape_runner_transaction_with_commit(
    migration_db, tmp_path
):
    conn, _schema = migration_db
    migrations = _copy_migrations(tmp_path)
    (migrations / "002_forbidden_commit.sql").write_text(
        """
        CREATE TABLE must_not_commit (id INTEGER PRIMARY KEY);
        COMMIT;
        """,
        encoding="utf-8",
    )

    with pytest.raises(MigrationLayoutError, match="transaction control.*COMMIT"):
        run_migrations(conn, migrations)

    assert "must_not_commit" not in _relation_names(conn)


def test_transaction_words_inside_comments_and_function_bodies_are_allowed(tmp_path):
    migrations = _copy_migrations(tmp_path)
    (migrations / "002_function.sql").write_text(
        """
        -- COMMIT is documentation here, not transaction control.
        CREATE FUNCTION harmless() RETURNS void AS $body$
        BEGIN
            PERFORM 'ROLLBACK';
        END;
        $body$ LANGUAGE plpgsql;
        """,
        encoding="utf-8",
    )

    assert [item.version for item in discover_migrations(migrations)] == [1, 2]


def test_applied_version_without_checked_in_file_is_ledger_corruption(migration_db):
    conn, _schema = migration_db
    bootstrap_ledger(conn, REPOSITORY_MIGRATIONS / "bootstrap.sql")
    with conn.transaction():
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO schema_migrations (version, checksum)
                VALUES (002, %s)
                """,
                ("a" * 64,),
            )

    with pytest.raises(LedgerCorruptionError, match="files are missing.*002"):
        run_migrations(conn, REPOSITORY_MIGRATIONS)

    assert _relation_names(conn) == ["schema_migrations"]


def test_bootstrap_is_safe_to_repeat_and_creates_only_the_ledger(migration_db):
    conn, _schema = migration_db
    bootstrap = REPOSITORY_MIGRATIONS / "bootstrap.sql"

    bootstrap_ledger(conn, bootstrap)
    bootstrap_ledger(conn, bootstrap)

    assert _relation_names(conn) == ["schema_migrations"]


def test_upgrade_from_bootstrap_only_database_applies_001(migration_db):
    conn, _schema = migration_db
    bootstrap_ledger(conn, REPOSITORY_MIGRATIONS / "bootstrap.sql")

    assert run_migrations(conn, REPOSITORY_MIGRATIONS) == [1]
    assert _relation_names(conn) == [
        "schema_migrations",
        "strata_migration_sentinel",
    ]


def test_migrations_are_sorted_numerically(tmp_path):
    migrations = _copy_migrations(tmp_path)
    (migrations / "010_tenth.sql").write_text("SELECT 10;\n", encoding="utf-8")
    (migrations / "002_second.sql").write_text("SELECT 2;\n", encoding="utf-8")

    assert [item.version for item in discover_migrations(migrations)] == [1, 2, 10]
