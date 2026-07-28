"""Integration tests: these require the compose Postgres to be reachable."""

from __future__ import annotations

import time

import pytest

from strata.db import ConnectionTimeout, FatalConnectionError, connect_with_backoff


def test_connects_using_environment_credentials(db_config):
    """Env-sourced smoke test: the configured credentials actually work."""
    with connect_with_backoff(db_config, timeout_seconds=60) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user")
            dbname, user = cur.fetchone()

    assert dbname == db_config.dbname
    assert user == db_config.user


def test_demo_database_is_the_expected_one(db_config):
    """CI must never be pointed at anything but a disposable demo/test database."""
    assert db_config.dbname in {"strata_demo", "strata_test"}


def test_bad_password_fails_loudly_and_immediately(db_config):
    """A wrong password must raise at once, not be absorbed by the retry loop.

    The generous timeout budget is the point: if the loop were retrying auth
    failures, this test would sit here burning the whole budget instead of
    failing in well under a second.
    """
    started = time.monotonic()

    with pytest.raises(FatalConnectionError) as excinfo:
        connect_with_backoff(
            db_config,
            password="definitely-not-the-password",
            timeout_seconds=30,
        )

    elapsed = time.monotonic() - started
    assert elapsed < 5, f"bad password was retried for {elapsed:.1f}s instead of failing fast"

    message = str(excinfo.value)
    assert "28P01" in message or "password" in message.lower()
    # The failure must not leak the credential it was handed.
    assert "definitely-not-the-password" not in message


def test_bad_password_is_not_reported_as_a_timeout(db_config):
    """Rejection and unreachability are different diagnoses; keep them apart."""
    with pytest.raises(FatalConnectionError):
        connect_with_backoff(
            db_config, password="definitely-not-the-password", timeout_seconds=30
        )


def test_missing_database_fails_loudly(db_config):
    """Pointing at a nonexistent database is a misconfiguration, not a wait."""
    bogus = type(db_config)(
        host=db_config.host,
        port=db_config.port,
        dbname="strata_does_not_exist",
        user=db_config.user,
        password=db_config.password,
        connect_timeout_seconds=db_config.connect_timeout_seconds,
    )
    with pytest.raises(FatalConnectionError):
        connect_with_backoff(bogus, timeout_seconds=30)


def test_unreachable_host_times_out_within_budget(db_config):
    """The retry loop is bounded: unreachable means ConnectionTimeout, not a hang."""
    unreachable = type(db_config)(
        host="postgres-that-does-not-resolve",
        port=db_config.port,
        dbname=db_config.dbname,
        user=db_config.user,
        password=db_config.password,
        connect_timeout_seconds=db_config.connect_timeout_seconds,
    )

    started = time.monotonic()
    with pytest.raises(ConnectionTimeout):
        connect_with_backoff(unreachable, timeout_seconds=3)
    elapsed = time.monotonic() - started

    assert elapsed < 20, f"retry loop overran its 3s budget by too much ({elapsed:.1f}s)"
