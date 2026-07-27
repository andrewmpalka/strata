"""Runtime configuration, read exclusively from the process environment.

Nothing here carries a default for a credential. A missing credential is a
loud startup failure, never a fallback to a guessable value.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass

from psycopg.conninfo import make_conninfo


class ConfigError(RuntimeError):
    """Raised when the environment does not describe a usable configuration."""


def _required(name: str) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        raise ConfigError(
            f"required environment variable {name} is unset or empty; "
            "expected it to be supplied via --env-file (e.g. .env.demo)"
        )
    return value


def _positive_number(name: str, default: str) -> float:
    raw = os.environ.get(name, default)
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from exc
    if not math.isfinite(value) or value <= 0:
        raise ConfigError(f"{name} must be a finite positive number, got {raw!r}")
    return value


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str
    connect_timeout_seconds: float

    def conninfo(self, *, password: str | None = None) -> str:
        """Build a libpq conninfo string.

        `password` overrides the configured credential; tests use it to prove
        that a wrong password fails loudly rather than being retried.
        """
        secret = self.password if password is None else password
        return make_conninfo(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=secret,
            # Per-attempt socket timeout. Distinct from the overall budget in
            # connect_timeout_seconds, which bounds the whole retry loop.
            connect_timeout=5,
        )

    def redacted(self) -> str:
        return f"{self.user}@{self.host}:{self.port}/{self.dbname}"


@dataclass(frozen=True)
class AppConfig:
    demo_mode: bool
    log_level: str
    database: DatabaseConfig


def load_config() -> AppConfig:
    demo_mode_raw = _required("DEMO_MODE").strip().lower()
    if demo_mode_raw not in {"true", "false"}:
        raise ConfigError(f"DEMO_MODE must be 'true' or 'false', got {demo_mode_raw!r}")

    port_raw = os.environ.get("POSTGRES_PORT", "5432")
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ConfigError(f"POSTGRES_PORT must be an integer, got {port_raw!r}") from exc
    if not 1 <= port <= 65535:
        raise ConfigError(f"POSTGRES_PORT must be between 1 and 65535, got {port}")

    return AppConfig(
        demo_mode=demo_mode_raw == "true",
        log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        database=DatabaseConfig(
            host=os.environ.get("POSTGRES_HOST", "postgres"),
            port=port,
            dbname=_required("POSTGRES_DB"),
            user=_required("POSTGRES_USER"),
            password=_required("POSTGRES_PASSWORD"),
            connect_timeout_seconds=_positive_number(
                "DB_CONNECT_TIMEOUT_SECONDS", "60"
            ),
        ),
    )
