"""Day 1 skeleton entrypoint: connect to Postgres, log "connected", idle.

There is deliberately no schema work here. Migrations arrive as ordered
plain-SQL files in a later increment.
"""

from __future__ import annotations

import logging
import signal
import sys
import threading

from .config import ConfigError, load_config
from .db import ConnectionTimeout, FatalConnectionError, connect_with_backoff

logger = logging.getLogger("strata")

_shutdown = threading.Event()


def _handle_signal(signum, _frame) -> None:
    logger.info("received %s, shutting down", signal.Signals(signum).name)
    _shutdown.set()


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
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user, version()")
            dbname, user, version = cur.fetchone()
        # The process keeps this connection open while it idles. End the
        # handshake transaction first so it never sits "idle in transaction".
        conn.commit()

        logger.info("connected")
        logger.info(
            "postgres handshake ok: database=%s user=%s server=%s",
            dbname,
            user,
            version.split(" on ")[0],
        )

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

        logger.info("idling; no ingestion or analytics exists in this increment")
        _shutdown.wait()

    logger.info("shutdown complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
