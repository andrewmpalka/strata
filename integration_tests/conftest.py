from __future__ import annotations

import os

import pytest

from strata.config import ConfigError, load_config


@pytest.fixture(scope="session")
def db_config():
    """Configuration sourced from the real process environment.

    Integration tests skip when no database environment is present, so the unit
    suite stays runnable on a bare checkout. CI sets STRATA_REQUIRE_DB=1, which
    turns that skip into a hard failure — otherwise "all tests passed" could
    quietly mean "the tests that matter never ran".
    """
    try:
        config = load_config()
    except ConfigError as exc:
        if os.environ.get("STRATA_REQUIRE_DB") == "1":
            pytest.fail(
                f"STRATA_REQUIRE_DB=1 but the database environment is incomplete: {exc}"
            )
        pytest.skip(f"no database environment available: {exc}")
    return config.database
