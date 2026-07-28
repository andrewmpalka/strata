"""Restore a preserved PostgreSQL snapshot and exercise real upgrade paths."""

from __future__ import annotations

import shutil
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import pytest
from psycopg import sql

from strata.db import connect_with_backoff
from strata.migrations import (
    MigrationExecutionError,
    discover_migrations,
    run_migrations,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_MIGRATIONS = REPOSITORY_ROOT / "migrations"
PRIOR_SCHEMA_SNAPSHOT = (
    REPOSITORY_ROOT / "fixtures" / "postgres" / "migration_engine_v1.sql"
)
TEST_DATABASE = "strata_test"
SNAPSHOT_APPLIED_AT = datetime(2026, 7, 27, 23, 30, tzinfo=timezone.utc)


@pytest.fixture
def isolated_database(db_config):
    """Provide a fresh permitted test database in the disposable CI server."""
    admin = connect_with_backoff(db_config, timeout_seconds=60)
    admin.autocommit = True
    with admin.cursor() as cursor:
        _drop_test_database(cursor)
        cursor.execute(
            sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8'").format(
                sql.Identifier(TEST_DATABASE)
            )
        )

    test_config = replace(db_config, dbname=TEST_DATABASE)
    connection = connect_with_backoff(test_config, timeout_seconds=60)
    try:
        yield connection
    finally:
        connection.close()
        with admin.cursor() as cursor:
            _drop_test_database(cursor)
        admin.close()


def _drop_test_database(cursor: psycopg.Cursor) -> None:
    """Remove only the fixed disposable database after ending its sessions."""
    cursor.execute(
        """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = %s
          AND pid <> pg_backend_pid()
        """,
        (TEST_DATABASE,),
    )
    cursor.execute(
        sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(TEST_DATABASE))
    )


def _migration_set(destination: Path, migration_sql: str) -> Path:
    """Copy repository migrations and append one temporary migration at head."""
    target = destination / "migrations"
    shutil.copytree(REPOSITORY_MIGRATIONS, target)
    (target / "002_upgrade_probe.sql").write_text(
        migration_sql.strip() + "\n",
        encoding="utf-8",
    )
    return target


def _reset_public_schema(connection: psycopg.Connection) -> None:
    """Return the disposable database to an empty clean-install state."""
    connection.rollback()
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA public CASCADE")
            cursor.execute("CREATE SCHEMA public")
    connection.commit()


def _restore_snapshot(connection: psycopg.Connection) -> None:
    """Restore the checked-in pg_dump without invoking the migration runner."""
    snapshot = PRIOR_SCHEMA_SNAPSHOT.read_text(encoding="utf-8")
    assert "-- PostgreSQL database dump" in snapshot
    assert "CREATE TABLE public.schema_migrations" in snapshot
    assert "INSERT INTO public.schema_migrations VALUES (1," in snapshot

    connection.rollback()
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA public CASCADE")
            cursor.execute(snapshot)
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO public")
    connection.commit()


def _ledger(connection: psycopg.Connection) -> list[tuple[int, str, datetime]]:
    """Read ordered ledger evidence for checksum and history assertions."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT version, checksum, applied_at
            FROM schema_migrations
            ORDER BY version
            """
        )
        return cursor.fetchall()


def _fail_if_bootstrap_runs(
    _connection: psycopg.Connection, _bootstrap_path: Path
) -> None:
    """Reject an upgrade test that silently replaces restore with bootstrap."""
    raise AssertionError("restored upgrade path must not invoke bootstrap")


def test_clean_install_applies_temporary_head(isolated_database, tmp_path):
    """A clean database reaches the temporary migration head with valid checksums."""
    migrations = _migration_set(
        tmp_path,
        """
        -- Temporary probe proving clean and upgrade paths reach the same head.
        CREATE TABLE upgrade_probe (
            singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
            source TEXT NOT NULL
        );
        INSERT INTO upgrade_probe (source) VALUES ('temporary migration');
        """,
    )

    assert run_migrations(isolated_database, migrations) == [1, 2]
    expected = {
        migration.version: migration.checksum
        for migration in discover_migrations(migrations)
    }
    assert [(version, checksum) for version, checksum, _ in _ledger(isolated_database)] == [
        (1, expected[1]),
        (2, expected[2]),
    ]


def test_snapshot_restores_and_migrates_to_temporary_head(
    isolated_database, tmp_path, monkeypatch
):
    """A real prior-schema dump upgrades in place without reinstalling version 001."""
    migrations = _migration_set(
        tmp_path,
        """
        -- Temporary probe proving clean and upgrade paths reach the same head.
        CREATE TABLE upgrade_probe (
            singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
            source TEXT NOT NULL
        );
        INSERT INTO upgrade_probe (source) VALUES ('temporary migration');
        """,
    )
    _restore_snapshot(isolated_database)

    before = _ledger(isolated_database)
    assert before == [
        (
            1,
            "3110ca52ef12fea7826b33d5ccc580cdbc1d46559770b5a51b20396ad60b51e8",
            SNAPSHOT_APPLIED_AT,
        )
    ]
    assert before[0][1] == discover_migrations(REPOSITORY_MIGRATIONS)[0].checksum
    with isolated_database.cursor() as cursor:
        cursor.execute("SELECT message FROM strata_migration_sentinel")
        assert cursor.fetchone() == ("migration engine ready",)

    monkeypatch.setattr(
        "strata.migrations.bootstrap_ledger",
        _fail_if_bootstrap_runs,
    )
    assert run_migrations(isolated_database, migrations) == [2]

    expected = {
        migration.version: migration.checksum
        for migration in discover_migrations(migrations)
    }
    after = _ledger(isolated_database)
    assert [(version, checksum) for version, checksum, _ in after] == [
        (1, expected[1]),
        (2, expected[2]),
    ]
    assert after[0][2] == SNAPSHOT_APPLIED_AT
    with isolated_database.cursor() as cursor:
        cursor.execute("SELECT singleton, source FROM upgrade_probe")
        assert cursor.fetchall() == [(True, "temporary migration")]
    assert run_migrations(isolated_database, migrations) == []


def test_upgrade_rejects_historical_breakage_that_clean_install_misses(
    isolated_database, tmp_path
):
    """Historical ledger data exposes a migration a clean install cannot catch."""
    migrations = _migration_set(
        tmp_path,
        """
        -- Deliberately unsafe: historical ledger rows predate this cutoff.
        ALTER TABLE schema_migrations
        ADD CONSTRAINT schema_migrations_recent_only
        CHECK (applied_at >= TIMESTAMPTZ '2026-07-28 00:00:00+00');
        """,
    )

    assert run_migrations(isolated_database, migrations) == [1, 2]

    _reset_public_schema(isolated_database)
    _restore_snapshot(isolated_database)
    with pytest.raises(MigrationExecutionError, match="002.*rolled back"):
        run_migrations(isolated_database, migrations)

    assert _ledger(isolated_database) == [
        (
            1,
            "3110ca52ef12fea7826b33d5ccc580cdbc1d46559770b5a51b20396ad60b51e8",
            SNAPSHOT_APPLIED_AT,
        )
    ]
    with isolated_database.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(*)
            FROM pg_constraint
            WHERE conname = 'schema_migrations_recent_only'
            """
        )
        assert cursor.fetchone() == (0,)
