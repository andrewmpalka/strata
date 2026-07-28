# Deployment and Verification Topology — current verification environment

This view maps the implemented repository entry points, runtime containers,
installed package, migration files, and test suites. It also shows the guarded
`strata_ci` deployment boundary and the explicit separation from live resources.

**Audience:** application, platform, database, and CI engineers reviewing how
the current baseline is built and verified.

## How to read this diagram

Read from the two command entry points on the left into the Compose boundary.
Tests are verification artifacts outside the product-runtime boundary; arrows
show when they are executed against or inside the disposable environment.

```mermaid
flowchart LR
    harness["CURRENT COMMAND<br/>scripts/harness<br/>Dispatches documentation, fast, and database-backed checks"]
    ci["CURRENT COMMAND<br/>scripts/ci.sh<br/>Guards the Compose lifecycle and destructive cleanup"]
    migrations[("CURRENT DATA STORE<br/>Top-level migration files<br/>Bootstrap plus ordered numbered SQL")]
    fast["CURRENT VERIFICATION ARTIFACT<br/>Fast test suite<br/>tests/unit, no database required"]
    integration["CURRENT VERIFICATION ARTIFACT<br/>PostgreSQL integration suite<br/>integration_tests"]
    provider_free["CURRENT CONTROL<br/>Current provider-free baseline<br/>No provider client exists in the implemented source tree"]

    subgraph ci_boundary["CURRENT DEPLOYMENT — Compose project strata_ci only"]
        compose["CURRENT EXECUTION ENVIRONMENT<br/>Docker Compose<br/>Builds, starts, waits, and runs checks"]
        app["CURRENT CONTAINER<br/>Application<br/>Python 3.12; python -m strata.main"]
        package["CURRENT CONTAINER CONTENT<br/>Installed strata package<br/>Configuration, connection, startup, migrations"]
        postgres["CURRENT CONTAINER<br/>PostgreSQL 16.4<br/>Disposable demo or test database"]
        volume[("CURRENT DATA STORE<br/>Disposable pgdata volume<br/>Project-prefixed and cleanup-guarded")]

        compose -->|"starts application process"| app
        app -->|"imports installed package"| package
        package -->|"connects and runs migration protocol"| postgres
        postgres -->|"persists database files"| volume
    end

    harness -->|"runs fast suite directly"| fast
    harness -->|"delegates database-backed lifecycle"| ci
    ci -->|"invokes pinned strata_ci Compose commands"| compose
    app -->|"contains no provider client calls"| provider_free
    migrations -->|"copied to /srv/migrations"| app
    package -->|"resolves STRATA_MIGRATIONS_DIR=/srv/migrations"| migrations
    fast -->|"verifies package behavior without a database"| package
    integration -->|"runs against disposable PostgreSQL"| postgres
    ci -->|"executes complete suite in the application image"| integration

    excluded["PROHIBITED EXTERNAL BOUNDARY<br/>strata_live resources<br/>Never named, mounted, reset, or deleted by demo, tests, or cleanup"]
    ci -.->|"guard refuses access"| excluded

    classDef current fill:#eef6ff,stroke:#245a8d,stroke-width:2px,color:#111;
    classDef store fill:#f5f5f5,stroke:#333,stroke-width:2px,color:#111;
    classDef verify fill:#f8f4ff,stroke:#604080,stroke-width:2px,color:#111;
    classDef prohibited fill:#fff0f0,stroke:#8b1a1a,stroke-width:3px,color:#111;
    class harness,ci,compose,app,package,postgres,provider_free current;
    class migrations,volume store;
    class fast,integration verify;
    class excluded prohibited;
```

## Legend and notation

- `CURRENT CONTAINER` is a runnable container instance in the Compose
  deployment.
- `CURRENT CONTAINER CONTENT` is installed inside a container, not a separate
  deployable service.
- `VERIFICATION ARTIFACT` is test code, never a product runtime container.
- `CURRENT CONTROL` states a verified execution constraint rather than a
  deployable product container.
- `Current provider-free baseline` describes the implemented source tree; it
  does not claim a firewall or network-namespace control.
- `DATA STORE` identifies repository SQL or persistent database state.
- The dotted refusal arrow is a prohibited interaction, reinforced by text.

## Current versus target

All solid elements are current. Checked-in deterministic provider fixtures, data
ingestion, analytics workers, and the dashboard remain target MVP and are not
shown as current container instances. The `strata_live` label is only a safety
boundary; it is not a claim that a complete live deployment exists.

## Limitations and non-goals

This view omits Docker networking detail and individual test cases. It does not
model test code as a service, authorize direct volume deletion, or provide a
live operator procedure.

## Source traceability

| Diagram claim | Status | Source |
|---|---|---|
| `scripts/harness` is a thin test dispatcher | Current | `scripts/harness`, [repository layout](../repository-layout.md) |
| `scripts/ci.sh` owns guarded Compose lifecycle and cleanup | Current | `scripts/ci.sh`, [CI isolation](../../engineering/ci-isolation.md) |
| The image runs Python 3.12 and `python -m strata.main` | Current | `Dockerfile` |
| The container sets `STRATA_MIGRATIONS_DIR=/srv/migrations` | Current | `Dockerfile`, `src/strata/main.py` |
| Compose contains application and PostgreSQL services with project-prefixed storage | Current | `docker-compose.yml` |
| Fast tests and PostgreSQL integration tests are separate suites | Current | `tests/unit/`, `integration_tests/`, [testing guidance](../../engineering/testing.md) |
| Demo verification makes no external provider calls | Current boundary | [demo and live operations](../../operations/demo-and-live.md), current source tree |
| Demo and test cleanup must not access live resources | Current safety contract | [CI isolation](../../engineering/ci-isolation.md) |
