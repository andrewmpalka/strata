"""Strata entrypoint: connect, migrate, report healthy, and idle."""

from __future__ import annotations

import logging
import os
import signal
import sys
import threading
from pathlib import Path

from .config import ConfigError, load_config
from .db import ConnectionTimeout, FatalConnectionError, connect_with_backoff
from .migrations import MigrationError, run_migrations

logger = logging.getLogger("strata")

_shutdown = threading.Event()


def _handle_signal(signum, _frame) -> None:
    logger.info("received %s, shutting down", signal.Signals(signum).name)
    _shutdown.set()


def _migrations_dir() -> Path:
    override = os.environ.get("STRATA_MIGRATIONS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "migrations"


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        config = load_config()
    except ConfigError as exc:
        logging.getLogger("strata").error("configuration error: %s", exc)
        return 2

    logging.getLogger().setLevel(config.log_level)
    logger.info(
        "strata app starting (demo_mode=%s, target=%s)",
        config.demo_mode,
        config.database.redacted(),
    )

    try:
        conn = connect_with_backoff(config.database)
    except FatalConnectionError as exc:
        # Wrong password / missing role / missing database. Exit non-zero so the
        # stack is visibly broken instead of quietly degraded.
        logger.error("fatal database connection failure: %s", exc)
        return 3
    except ConnectionTimeout as exc:
        logger.error("database never became reachable: %s", exc)
        return 4

    with conn:
        try:
            applied = run_migrations(conn, _migrations_dir())
        except MigrationError as exc:
            logger.error("migration failure: %s", exc)
            return 5

        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user, version()")
            dbname, user, version = cur.fetchone()
        # The process keeps this connection open while it idles. End the
        # handshake transaction first so it never sits "idle in transaction".
        conn.commit()

        logger.info("connected")
        logger.info(
            "migration check complete: applied=%s",
            ",".join(f"{item:03d}" for item in applied) or "none",
        )
        logger.info(
            "postgres handshake ok: database=%s user=%s server=%s",
            dbname,
            user,
            version.split(" on ")[0],
        )

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

        logger.info("idling; migration sentinel is populated")
        _shutdown.wait()

    logger.info("shutdown complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
