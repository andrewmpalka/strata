# Strata

An **observational study** of how authentication modes — ERC-4337 smart
accounts, EIP-7702 delegation, and Aptos keyless / multisig / sponsored
transactions — are **associated with** wallet retention, built on a two-chain
(Ethereum + Aptos) data platform.

Strata is a matched, censoring-aware, lineage-gated study, not a dashboard.
Every published number traces to a declared population, a coverage-verified
data slice, and a versioned run.

## Canonical documents

- **[PRD v3.2 (canonical spec)](docs/Strata_PRD_v3.2_MASTER.md)** — dataset
  contract (§3), index events (§5.2), exposure states (§5.4), matching (§5.5),
  retention (§5.6), architecture and coverage (§7).
- **[AGENTS.md](AGENTS.md)** — standing instructions for AI coding agents.

Read the PRD before inventing schemas, population definitions, or chain
semantics.

## Status

**Day 2 of 37 — migration engine.** Postgres plus a Python service that
connects, runs an explicit ledger-only bootstrap, applies ordered checksummed
SQL migrations transactionally, logs `connected`, and idles. Migration 001
populates a sentinel proving the mechanism. There is no ingestion or analytics
yet.

No empirical study findings are published because no qualifying live analytics
run exists yet.

## Quick start

```bash
make green     # guarded clean teardown, build, verify populated state, run tests
```

The Makefile is the public verification interface:

- `make green` runs the canonical isolated clean verification.
- `make verify` verifies the running stack's populated state.
- `make test` runs the complete test suite in the Compose application image.
- `make test-unit` runs the fast checkout-local test suite.
- `make test-integration` starts the disposable stack and runs the PostgreSQL
  integration suite.
- `make test-e2e` aliases the full guarded green path.
- `make test-docs` runs the public-guidance graph tests.

The checkout-local targets require a local test environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
```

This setup is required only for `make test-unit` and `make test-docs`;
`make green` remains Docker-based.

Operational convenience targets are `make up`, `make down`, `make clean`,
`make logs`, `make psql`, and `make fg`; run `make help` for their descriptions.

For manual foreground startup only, the following non-verification convenience
is also supported:

```bash
docker compose --project-name strata_ci --env-file .env.demo up --build
```

Expected: Postgres reports healthy, migration 001 populates its sentinel, then
the app logs `connected` and idles.

## Modes

| | Demo | Live |
|---|---|---|
| Compose project | `strata_ci` | `strata_live` |
| Env file | `.env.demo` (checked in, no secrets) | `.env.live` (human-owned, gitignored) |
| Data | checked-in deterministic fixtures | provider APIs, keys required |
| External APIs | **zero** | required |

**"Green" means both:** demo CI passes — the isolated demo stack comes up and
produces the expected *populated* state from checked-in fixtures with zero
external API calls — **and** live health is honest: every live component either
works or visibly reports unhealthy. Never a silently degraded stack, an
empty-but-serving dashboard, or a swallowed error.

## Safety conventions

- All container-backed tests and CI use Compose project names beginning with
  `strata_ci` and the checked-in `.env.demo`. Checkout-local unit and
  documentation checks do not start Compose and must never read live
  configuration or access live resources.
- `scripts/ci.sh` is the only sanctioned path for destructive cleanup. Its guard
  refuses to delete volumes unless the project name starts with `strata_ci`,
  `DEMO_MODE=true`, and the database is `strata_demo` or `strata_test`.
  **Never run `docker compose down -v` by hand** — live volumes may hold weeks
  of rate-limited backfill that no rerun can reproduce.
- `.env.live` is human-owned. Agents must never create, edit, print, or commit
  it. Secrets are read only from the runtime environment, never from code.

## Layout

```
src/strata/           Python package implementation
tests/                fast checkout-local tests
integration_tests/    PostgreSQL-backed integration tests
migrations/           ledger-only bootstrap + ordered numbered SQL migrations
docs/                 canonical PRD and focused guidance
Makefile              public task and verification interface
scripts/ci.sh:        guarded Compose lifecycle and container-backed suites
Dockerfile            application image
docker-compose.yml    PostgreSQL and application services
.env.demo             demo configuration (no secrets)
```
