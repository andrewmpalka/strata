# C4 System Context — current implemented Strata baseline

This view explains the implemented Strata system as a migration-safe application
skeleton and local verification environment. It deliberately excludes the
target ingestion platform, analytics, and dashboard.

**Audience:** new engineers, reviewers, and technical interviewers who need a
fast, accurate boundary around what exists today.

## How to read this diagram

Read left to right from the external developer or reviewer to Strata as one
system. C4 System Context deliberately hides the application, PostgreSQL,
migrations, tests, and Compose runtime; the following deployment and sequence
views explain those internal details.

```mermaid
flowchart LR
    person["EXTERNAL PERSON<br/>Developer or reviewer<br/>Runs and evaluates the local baseline"]
    strata["CURRENT SYSTEM<br/>Strata migration-safe baseline<br/>Loads configuration, connects, migrates, verifies, and idles"]

    person -->|"runs documented startup and verification commands"| strata
    strata -->|"reports connected state or a visible startup failure"| person

    classDef current fill:#eef6ff,stroke:#245a8d,stroke-width:2px,color:#111;
    classDef external fill:#fff8dc,stroke:#6b5b00,stroke-width:2px,color:#111;
    class strata current;
    class person external;
```

## Legend and notation

- `CURRENT` means tracked implementation or configuration supports the element.
- `EXTERNAL PERSON` is outside the Strata system boundary.
- C4 System Context collapses Strata into one system and omits its internal
  containers, data stores, and verification artifacts.
- Solid borders denote implemented elements. Status text remains authoritative
  in light and dark themes.

## Current versus target

The Strata system shown here is current. Ethereum and Aptos providers,
raw and staging layers, activity facts, analytics, publication gating, and a
dashboard are target MVP capabilities and therefore do not appear in this
current view.

## Limitations and non-goals

This diagram does not show function-level code, every test command, or every
failure mode. It is not a live deployment guide and makes no claim that provider
ingestion or empirical analysis exists.

## Source traceability

| Diagram claim | Status | Source |
|---|---|---|
| The application loads configuration, connects, migrates, reports connected, and idles | Current | `src/strata/main.py`, `src/strata/config.py`, `src/strata/db.py` |
| Compose starts PostgreSQL and the application | Current | `docker-compose.yml`, `Dockerfile` |
| Migrations are repository-owned, ordered, checksummed, and transactional | Current | `src/strata/migrations.py`, `migrations/`, [migration contract](../migrations.md) |
| Verification is repository-owned and guarded | Current | `scripts/harness`, `scripts/ci.sh`, [testing guidance](../../engineering/testing.md) |
| Ingestion, analytics, and dashboard are absent from current implementation | Current boundary | `src/strata/`, `migrations/`, [canonical PRD §7](../../Strata_PRD_v3.2_MASTER.md#7-architecture) |
