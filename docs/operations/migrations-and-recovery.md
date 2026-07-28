# Migration and recovery operation

This document describes the current startup and safe response paths. The
architectural migration and evidence-replay contracts remain authoritative for
their respective responsibilities.

At application startup, Strata connects with a bounded visible retry policy,
acquires the migration lock, creates the ledger only when absent, validates
every applied checksum, applies pending numbered migrations transactionally,
and then reports `connected`. A rerun at head is a logged no-op.

Treat these conditions as hard stops:

- A checksum mismatch means an applied migration's bytes changed. Restore the
  accepted bytes and express the correction in a new numbered migration.
- A ledger version without its checked-in file is corruption, not a reason to
  rewrite the ledger.
- A migration execution error rolls back that migration and its ledger insert.
  Diagnose the new migration; do not mark it applied by hand.
- A fatal database rejection is configuration failure and must not become an
  unbounded readiness wait.

Disposable demo or test state may be reset only through `./scripts/ci.sh clean`
or the clean phase of `./scripts/ci.sh green`, after the isolation guard passes.
Routine destructive recovery is prohibited for live data.

When retained provider evidence needs reinterpretation, replay staging from raw
artifacts under a new parser version. Do not destroy history or re-fetch merely
to overwrite the evidence.
