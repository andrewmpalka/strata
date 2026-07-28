"""Postgres connection with a bounded, non-silent retry loop.

Two failure classes are deliberately kept apart:

* **Transient** — the server is not accepting connections yet (TCP refused,
  DNS not resolvable, "the database system is starting up"). These are worth
  retrying while the container comes up.
* **Fatal** — the server answered and rejected us: wrong password, wrong role,
  missing database. Retrying these is pure noise, and a retry loop that
  swallows them is exactly how a broken stack learns to look healthy. They
  raise immediately.
"""

from __future__ import annotations

import logging
import math
import time

import psycopg

from .config import DatabaseConfig

logger = logging.getLogger(__name__)

# SQLSTATEs where the server responded and refused. No amount of waiting fixes
# these, so they must not be absorbed by the retry loop.
FATAL_SQLSTATES = {
    "28P01",  # invalid_password
    "28000",  # invalid_authorization_specification
    "3D000",  # invalid_catalog_name (database does not exist)
    "42501",  # insufficient_privilege
}

# The server is up but explicitly not ready. Retryable.
TRANSIENT_SQLSTATES = {
    "57P03",  # cannot_connect_now
}

# libpq can lose the SQLSTATE when PostgreSQL rejects a connection during the
# startup handshake. Keep the deliberately small set of server-generated FATAL
# messages that mean waiting cannot help. These are the stock messages emitted
# by the official PostgreSQL image used by this project.
FATAL_STARTUP_MESSAGES = {
    "password authentication failed",
    "no password supplied",
    "does not exist",
    "no pg_hba.conf entry",
    "pg_hba.conf rejects connection",
}


class FatalConnectionError(RuntimeError):
    """The database rejected us outright; waiting cannot help."""


class ConnectionTimeout(RuntimeError):
    """The database never became reachable inside the configured budget."""


def _classify(exc: psycopg.OperationalError) -> str:
    sqlstate = getattr(exc, "sqlstate", None)
    if sqlstate in FATAL_SQLSTATES:
        return "fatal"
    message = str(exc).lower()
    if any(marker in message for marker in FATAL_STARTUP_MESSAGES):
        return "fatal"
    if sqlstate is None or sqlstate in TRANSIENT_SQLSTATES:
        # No SQLSTATE means we never got a protocol-level answer: refused
        # socket, unresolvable host, timeout — except for the known startup
        # rejection messages handled above.
        return "transient"
    # An unrecognised SQLSTATE means the server answered with something we did
    # not anticipate. Surface it rather than looping on a guess.
    return "fatal"


def connect_with_backoff(
    config: DatabaseConfig,
    *,
    password: str | None = None,
    timeout_seconds: float | None = None,
    initial_delay: float = 0.25,
    max_delay: float = 4.0,
    sleep=time.sleep,
    monotonic=time.monotonic,
) -> psycopg.Connection:
    """Connect to Postgres, retrying only transient failures.

    Raises FatalConnectionError on an outright rejection and ConnectionTimeout
    when the budget is exhausted. Never returns None, never loops forever, and
    never retries silently.
    """
    budget = (
        config.connect_timeout_seconds if timeout_seconds is None else timeout_seconds
    )
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError(f"connection timeout must be finite and positive, got {budget!r}")
    deadline = monotonic() + budget
    delay = initial_delay
    attempt = 0
    supplied_password = config.password if password is None else password

    while True:
        attempt += 1
        try:
            return psycopg.connect(config.conninfo(password=password))
        except psycopg.OperationalError as exc:
            kind = _classify(exc)
            if kind == "fatal":
                detail = str(exc).replace(supplied_password, "[REDACTED]")
                raise FatalConnectionError(
                    f"database rejected the connection to {config.redacted()} "
                    f"(sqlstate={getattr(exc, 'sqlstate', None)}): {detail}"
                ) from exc

            remaining = deadline - monotonic()
            if remaining <= 0:
                detail = str(exc).replace(supplied_password, "[REDACTED]")
                raise ConnectionTimeout(
                    f"could not reach {config.redacted()} after {attempt} attempts "
                    f"within {budget:g}s: {detail}"
                ) from exc

            # Every retry is visible. A quiet loop is indistinguishable from a
            # hang, and a hang here is indistinguishable from working.
            detail = str(exc).replace(supplied_password, "[REDACTED]")
            logger.warning(
                "postgres not ready at %s (attempt %d, %.1fs of budget left): %s",
                config.redacted(),
                attempt,
                remaining,
                detail,
            )
            sleep(min(delay, max_delay, remaining))
            delay = min(delay * 2, max_delay)
