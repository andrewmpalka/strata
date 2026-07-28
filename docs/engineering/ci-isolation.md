# Docker and CI isolation

This file is the canonical destructive-cleanup safety contract.

- All container-backed tests and CI use
  Compose project names beginning with `strata_ci`, the checked-in `.env.demo`,
  and only the disposable databases `strata_demo` or `strata_test`.
  Checkout-local unit and documentation checks do not start Compose and must
  never read live configuration or access live resources.
- `scripts/ci.sh` is the only sanctioned path for destructive cleanup. Never
  invoke `docker compose down -v` directly.
- The cleanup guard must require all three conditions: the project starts with
  `strata_ci`, `DEMO_MODE=true`, and the database is `strata_demo` or
  `strata_test`.
- The guard must also refuse suspicious live-named volumes. Never bypass,
  weaken, parameterize away, or temporarily disable any guard condition.
- Live services use project `strata_live`. No test, script, or agent action may
  name, mount, reset, or delete its volumes.

Guard tests must prove refusal for a non-CI project, false demo mode, a
non-disposable database, and live-looking volumes, as those paths become
testable. A required database suite must fail when its database environment is
missing; it must not quietly pass by skipping.

The supported manual startup is non-destructive:

```bash
docker compose --project-name strata_ci --env-file .env.demo up --build
```

Stopping while preserving volumes is distinct from guarded destructive cleanup.
Live data may represent weeks of rate-limited backfill and is not assumed
recoverable through a routine rerun.
