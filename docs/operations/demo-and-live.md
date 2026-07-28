# Demo and live operation

This document covers only behavior supported by the current repository.

## Demo

The disposable demo identity is Compose project `strata_ci` with `.env.demo`.
The supported commands are:

```bash
./scripts/ci.sh green
./scripts/ci.sh up
./scripts/ci.sh verify
./scripts/ci.sh down
docker compose --project-name strata_ci --env-file .env.demo up --build
```

The clean green command removes only guarded disposable state, builds and starts
PostgreSQL plus the application, verifies health, requires migration version
`001` and the populated `migration engine ready` sentinel, then runs the complete
suite. `up` and the direct Compose command are non-destructive starts. `down`
preserves volumes.

Demo mode uses checked-in deterministic state and zero external API calls. A
running but empty, unstable, skipped, or silently degraded service is not
success.

## Live boundary

Live resources use project `strata_live` and runtime-supplied secrets. The
repository currently provides no complete live ingestion operator procedure, so
none is implied here. Implemented live components must fail visibly when a
required dependency or stream fails, and stale results must be labeled.

Never aim demo, test, verification, or cleanup commands at live resources.
