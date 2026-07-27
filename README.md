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

Or the documented manual, non-destructive foreground startup:

```bash
docker compose --project-name strata_ci --env-file .env.demo up --build
```

Expected: Postgres reports healthy, migration 001 populates its sentinel, then
the app logs `connected` and idles.

Other targets: `make up`, `make verify`, `make test`, `make down`, `make clean`,
`make logs`, `make psql`.

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

- All tests and CI run under `--project-name strata_ci --env-file .env.demo`.
- `scripts/ci.sh` is the only sanctioned path for destructive cleanup. Its guard
  refuses to delete volumes unless the project name starts with `strata_ci`,
  `DEMO_MODE=true`, and the database is `strata_demo` or `strata_test`.
  **Never run `docker compose down -v` by hand** — live volumes may hold weeks
  of rate-limited backfill that no rerun can reproduce.
- `.env.live` is human-owned. Agents must never create, edit, print, or commit
  it. Secrets are read only from the runtime environment, never from code.

## Layout

```
app/                  minimal Python service (Dockerfile, strata/, tests/)
migrations/           ledger-only bootstrap + ordered numbered SQL migrations
docs/                 canonical PRD
scripts/ci.sh         pinned CI entrypoint + destructive-cleanup guard
docker-compose.yml    postgres + app
.env.demo             demo configuration (no secrets)
```
