"""Unit tests. No database required."""

from __future__ import annotations

import psycopg
import pytest

from strata.config import ConfigError, DatabaseConfig, load_config
from strata.db import ConnectionTimeout, FatalConnectionError, connect_with_backoff

BASE_ENV = {
    "DEMO_MODE": "true",
    "POSTGRES_DB": "strata_demo",
    "POSTGRES_USER": "strata",
    "POSTGRES_PASSWORD": "pw",
}


def _config(**overrides) -> DatabaseConfig:
    fields = {
        "host": "postgres",
        "port": 5432,
        "dbname": "strata_demo",
        "user": "strata",
        "password": "pw",
        "connect_timeout_seconds": 10.0,
    }
    fields.update(overrides)
    return DatabaseConfig(**fields)


def _operational_error(sqlstate: str | None) -> psycopg.OperationalError:
    exc = psycopg.OperationalError("simulated")
    # psycopg derives sqlstate from an attached diagnostic; for a synthetic
    # error we set the attribute the classifier reads.
    exc.sqlstate = sqlstate  # type: ignore[attr-defined]
    return exc


@pytest.mark.parametrize("missing", sorted(BASE_ENV))
def test_missing_required_env_var_raises(monkeypatch, missing):
    for key, value in BASE_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv(missing)

    with pytest.raises(ConfigError) as excinfo:
        load_config()
    assert missing in str(excinfo.value)


def test_no_password_default_exists(monkeypatch):
    """There must be no fallback password anywhere in the config path."""
    for key, value in BASE_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("POSTGRES_PASSWORD", "")

    with pytest.raises(ConfigError):
        load_config()


def test_bad_demo_mode_value_raises(monkeypatch):
    for key, value in BASE_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("DEMO_MODE", "yes")

    with pytest.raises(ConfigError):
        load_config()


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "-inf"])
def test_connect_timeout_must_be_finite_and_positive(monkeypatch, value):
    for key, env_value in BASE_ENV.items():
        monkeypatch.setenv(key, env_value)
    monkeypatch.setenv("DB_CONNECT_TIMEOUT_SECONDS", value)

    with pytest.raises(ConfigError):
        load_config()


@pytest.mark.parametrize("value", ["0", "-1", "65536", "not-a-port"])
def test_postgres_port_must_be_valid(monkeypatch, value):
    for key, env_value in BASE_ENV.items():
        monkeypatch.setenv(key, env_value)
    monkeypatch.setenv("POSTGRES_PORT", value)

    with pytest.raises(ConfigError):
        load_config()


def test_redacted_target_excludes_password():
    assert "pw" not in _config(password="pw").redacted()


@pytest.mark.parametrize("sqlstate", ["28P01", "28000", "3D000", "42501"])
def test_server_rejections_are_fatal(monkeypatch, sqlstate):
    attempts = []

    def fake_connect(_conninfo):
        attempts.append(1)
        raise _operational_error(sqlstate)

    monkeypatch.setattr(psycopg, "connect", fake_connect)

    with pytest.raises(FatalConnectionError):
        connect_with_backoff(_config(), timeout_seconds=30, sleep=lambda _s: None)

    assert len(attempts) == 1, "a server rejection must not be retried at all"


def test_unknown_sqlstate_is_fatal_not_looped(monkeypatch):
    """An unanticipated server answer surfaces instead of becoming a quiet loop."""
    monkeypatch.setattr(
        psycopg, "connect", lambda _c: (_ for _ in ()).throw(_operational_error("XX000"))
    )
    with pytest.raises(FatalConnectionError):
        connect_with_backoff(_config(), timeout_seconds=30, sleep=lambda _s: None)


@pytest.mark.parametrize(
    "message",
    [
        'connection failed: FATAL: password authentication failed for user "strata"',
        'connection failed: FATAL: database "missing" does not exist',
        'connection failed: FATAL: role "missing" does not exist',
        "connection failed: no pg_hba.conf entry for host",
    ],
)
def test_startup_rejections_without_sqlstate_are_fatal(monkeypatch, message):
    attempts = []

    def fake_connect(_conninfo):
        attempts.append(1)
        raise psycopg.OperationalError(message)

    monkeypatch.setattr(psycopg, "connect", fake_connect)

    with pytest.raises(FatalConnectionError):
        connect_with_backoff(_config(), timeout_seconds=30, sleep=lambda _s: None)

    assert len(attempts) == 1


def test_transient_failure_is_retried_then_succeeds(monkeypatch):
    calls = {"n": 0}
    sentinel = object()

    def fake_connect(_conninfo):
        calls["n"] += 1
        if calls["n"] < 4:
            raise _operational_error(None)  # socket refused: no sqlstate
        return sentinel

    monkeypatch.setattr(psycopg, "connect", fake_connect)

    result = connect_with_backoff(
        _config(), timeout_seconds=30, sleep=lambda _s: None
    )
    assert result is sentinel
    assert calls["n"] == 4


def test_starting_up_sqlstate_is_transient(monkeypatch):
    calls = {"n": 0}

    def fake_connect(_conninfo):
        calls["n"] += 1
        if calls["n"] < 2:
            raise _operational_error("57P03")  # cannot_connect_now
        return object()

    monkeypatch.setattr(psycopg, "connect", fake_connect)
    connect_with_backoff(_config(), timeout_seconds=30, sleep=lambda _s: None)
    assert calls["n"] == 2


def test_retry_loop_is_bounded_by_a_virtual_clock(monkeypatch):
    """Prove the budget is enforced without waiting in real time."""
    clock = {"t": 0.0}

    monkeypatch.setattr(
        psycopg, "connect", lambda _c: (_ for _ in ()).throw(_operational_error(None))
    )

    def fake_sleep(seconds):
        clock["t"] += seconds

    with pytest.raises(ConnectionTimeout):
        connect_with_backoff(
            _config(),
            timeout_seconds=10,
            sleep=fake_sleep,
            monotonic=lambda: clock["t"],
        )

    assert clock["t"] >= 10


@pytest.mark.parametrize("budget", [0, -1, float("nan"), float("inf")])
def test_retry_budget_must_be_finite_and_positive(budget):
    with pytest.raises(ValueError):
        connect_with_backoff(_config(), timeout_seconds=budget)


def test_retry_loop_logs_every_attempt(monkeypatch, caplog):
    """A silent retry loop is indistinguishable from a hang."""
    monkeypatch.setattr(
        psycopg, "connect", lambda _c: (_ for _ in ()).throw(_operational_error(None))
    )
    clock = {"t": 0.0}

    with caplog.at_level("WARNING"):
        with pytest.raises(ConnectionTimeout):
            connect_with_backoff(
                _config(),
                timeout_seconds=5,
                sleep=lambda s: clock.__setitem__("t", clock["t"] + s),
                monotonic=lambda: clock["t"],
            )

    assert [r for r in caplog.records if "postgres not ready" in r.message]


def test_conninfo_password_override_does_not_mutate_config():
    config = _config(password="real")
    assert "wrong" in config.conninfo(password="wrong")
    assert config.password == "real"


def test_conninfo_escapes_password_metacharacters():
    conninfo = _config(password=r"spaces ' quotes \ slashes").conninfo()
    # If the generated string is syntactically invalid, conninfo_to_dict raises.
    assert psycopg.conninfo.conninfo_to_dict(conninfo)["password"] == (
        r"spaces ' quotes \ slashes"
    )


def test_connection_failure_redacts_password(monkeypatch):
    secret = "do-not-print-this"
    monkeypatch.setattr(
        psycopg,
        "connect",
        lambda _c: (_ for _ in ()).throw(
            psycopg.OperationalError(
                f"FATAL: password authentication failed: {secret}"
            )
        ),
    )

    with pytest.raises(FatalConnectionError) as excinfo:
        connect_with_backoff(_config(password=secret), timeout_seconds=30)

    assert secret not in str(excinfo.value)
