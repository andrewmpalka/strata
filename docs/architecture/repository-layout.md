# Repository layout and package boundaries

This document governs where repository code and verification support belong. The
canonical PRD governs product and study semantics.

## Current structure

- `src/strata/` is the only Python package implementation. Runtime configuration,
  database connectivity, startup, and migration execution live there.
- `tests/` contains fast tests that require no database. The current fast suite is
  under `tests/unit/`.
- `integration_tests/` contains PostgreSQL-backed tests. Migration upgrade and
  connection behavior belong here because they require the disposable database.
- `migrations/` is top-level and contains the ledger-only bootstrap plus ordered
  numbered SQL migrations.
- The root `Dockerfile` installs the package from `src/`, then copies migrations
  and verification suites into the image. `docker-compose.yml` defines the
  current PostgreSQL and application services.
- The root `Makefile` is the public task and verification interface.
  `scripts/ci.sh` owns the guarded Compose lifecycle, destructive cleanup,
  populated-state verification, and container-backed full runs.

Do not create a second package implementation under a script, test, application,
or compatibility directory. Runtime validation belongs in `src/strata/`;
test-only helpers belong with the suite that uses them. Imports must work through
the installed package—never mutate `sys.path` arbitrarily to conceal a packaging
or layout error.

## Thresholds for adding new top-level support

The following are placement thresholds, not claims that these directories exist:

- Add `fixtures/` only when checked-in deterministic artifacts need a shared,
  reviewable home beyond one test module.
- Add `tools/` only for maintained operator or developer programs that are too
  substantial for a thin script.
- Add `benchmarks/` only with a real performance trigger, a reproducible
  comparison, and an owned success criterion.
- Add a distinct end-to-end suite only when behavior crosses boundaries not
  honestly covered by the fast and PostgreSQL integration suites.

Do not create speculative directories, duplicate implementations, or placeholder
architecture for future roadmap work.
