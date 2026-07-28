# Demo and live operation

This document covers only behavior supported by the current repository.

## Demo

The disposable demo identity is Compose project `strata_ci` with `.env.demo`.
The root Makefile is the public command interface:

```bash
make green
make up
make verify
make down
make fg
```

Make delegates protected Compose lifecycle and destructive operations to
`scripts/ci.sh`. The clean green command removes only guarded disposable state,
builds and starts PostgreSQL plus the application, verifies health, requires
migration version `001` and the populated `migration engine ready` sentinel,
then runs the complete suite. `make up` and `make fg` are non-destructive
starts. `make down` preserves volumes.

Demo mode uses checked-in deterministic state and zero external API calls. A
running but empty, unstable, skipped, or silently degraded service is not
success.

## Live boundary

Live resources use project `strata_live` and runtime-supplied secrets. The
repository currently provides no complete live ingestion operator procedure, so
none is implied here. Implemented live components must fail visibly when a
required dependency or stream fails, and stale results must be labeled.

Never aim demo, test, verification, or cleanup commands at live resources.
