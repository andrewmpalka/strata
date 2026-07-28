# C4 Deployment — TARGET MVP demo and live environments

This view separates the deterministic disposable demo/CI deployment from the
persistent live deployment and makes the live-resource safety boundary visible.
It also identifies which baseline elements exist now and which services remain
target MVP.

> **TARGET MVP — NOT FULLY IMPLEMENTED**

**Audience:** platform, operations, security, and reliability engineers.

## How to read this diagram

Read each environment independently from its operator entry point toward its
database and services. Solid `CURRENT` nodes exist in the baseline; dashed
`TARGET` nodes are specified but incomplete. The central prohibition is a
boundary, not a data flow: no demo, test, verification, or cleanup action may
cross it.

```mermaid
flowchart TB
    reviewer["EXTERNAL PERSON<br/>Developer or reviewer<br/>Runs deterministic verification"]
    operator["EXTERNAL PERSON<br/>Live operator<br/>Supplies secrets and observes health"]
    eth["EXTERNAL SYSTEM<br/>Ethereum providers<br/>Finalized live evidence"]
    aptos["EXTERNAL SYSTEM<br/>Aptos providers<br/>Committed live evidence"]

    subgraph demo["DEMO AND CI DEPLOYMENT — Compose project strata_ci"]
        demo_env[("CURRENT DATA STORE<br/>Checked-in .env.demo<br/>Non-secret disposable configuration")]
        ci["CURRENT COMMAND<br/>scripts/ci.sh<br/>Guarded clean build, verification, and test lifecycle"]
        demo_app["CURRENT CONTAINER<br/>Strata application<br/>Migration-safe Python service"]
        demo_db[("CURRENT DATA STORE<br/>PostgreSQL demo or test database<br/>Disposable project-prefixed volume")]
        fixtures[("TARGET DATA STORE<br/>Checked-in deterministic provider fixtures<br/>Zero external provider calls")]
        no_network["TARGET CONTROL<br/>Demo network isolation<br/>Provider requests are prohibited"]
        demo_services["TARGET CONTAINER<br/>Ingestion and analytics services<br/>Populate deterministic target state"]
        demo_dashboard["TARGET CONTAINER<br/>Streamlit dashboard<br/>Serve populated run-labeled demo state"]

        demo_env -->|"supplies pinned demo configuration"| ci
        ci -->|"builds, starts, verifies, tests, and guarded-cleans"| demo_app
        ci -->|"verifies populated migration sentinel state"| demo_db
        demo_app -->|"runs migrations and stores sentinel state"| demo_db
        fixtures -->|"supplies deterministic provider-shaped evidence"| demo_services
        fixtures -.->|"requires zero provider requests"| no_network
        demo_services -->|"writes populated lineage and analytics state"| demo_db
        demo_db -->|"returns labeled demo results and coverage"| demo_dashboard
    end

    subgraph live["LIVE DEPLOYMENT — Compose project strata_live"]
        secrets["TARGET RUNTIME INPUT<br/>Runtime-supplied secrets<br/>Never baked into code, images, fixtures, or logs"]
        live_services["TARGET CONTAINER<br/>Ingestion and analytics workers<br/>Acquire, derive, and gate live runs when implemented"]
        live_db[("TARGET DATA STORE<br/>PostgreSQL live persistent state<br/>Evidence, coverage, manifests, and published runs")]
        live_dashboard["TARGET CONTAINER<br/>Dashboard and readiness<br/>Expose run labels, coverage, freshness, and health"]
        health["TARGET CONTROL<br/>Honest health and stale-state behavior<br/>Required stream failures are unhealthy; stale analytics are labeled"]

        secrets -->|"supplies live credentials at runtime"| live_services
        live_services -->|"writes durable evidence and run state"| live_db
        live_db -->|"returns published run, coverage, and freshness"| live_dashboard
        live_services -->|"reports dependency and stream health"| health
        health -->|"gates readiness and labels stale state"| live_dashboard
    end

    reviewer -->|"invokes supported demo and CI commands"| ci
    demo_dashboard -->|"presents deterministic non-empirical output"| reviewer
    operator -->|"starts and monitors live services"| live_services
    live_dashboard -->|"presents readiness, coverage, freshness, or unhealthy state"| operator
    eth -->|"live finalized evidence only"| live_services
    aptos -->|"live committed evidence only"| live_services

    prohibited["PROHIBITED BOUNDARY<br/>Demo, tests, verification, and cleanup never name, mount, reset, or delete live resources"]
    ci -.->|"cleanup guard refuses crossing"| prohibited
    prohibited -.->|"protects persistent live state"| live_db
    classDef current fill:#eef6ff,stroke:#245a8d,stroke-width:2px,color:#111;
    classDef target fill:#f7f3ff,stroke:#604080,stroke-width:2px,stroke-dasharray:6 4,color:#111;
    classDef currentStore fill:#f5f5f5,stroke:#333,stroke-width:2px,color:#111;
    classDef targetStore fill:#f5f5f5,stroke:#604080,stroke-width:2px,stroke-dasharray:6 4,color:#111;
    classDef external fill:#fff8dc,stroke:#6b5b00,stroke-width:2px,color:#111;
    classDef prohibited fill:#fff0f0,stroke:#8b1a1a,stroke-width:3px,color:#111;
    class ci,demo_app current;
    class demo_env,demo_db currentStore;
    class fixtures,no_network,demo_services,demo_dashboard,secrets,live_services,live_dashboard,health target;
    class live_db targetStore;
    class reviewer,operator,eth,aptos external;
    class prohibited prohibited;
    style live stroke:#604080,stroke-width:2px,stroke-dasharray:8 5,fill:none
```

## Legend and notation

- `CURRENT` with a solid border is supported by tracked implementation or
  configuration.
- `TARGET` with a dashed border is required by the MVP but incomplete.
- `EXTERNAL` identifies people and provider systems outside Strata.
- `DATA STORE` is configuration, fixture, or PostgreSQL state.
- The dotted demo-isolation arrow marks a prohibited interaction, not a
  provider request.
- CI means continuous integration. MVP means minimum viable product.

## Current versus target

The `strata_ci` Compose identity, checked-in demo configuration, PostgreSQL
service, application skeleton, and guarded lifecycle are current. Deterministic
provider fixtures, a populated data platform, analytics, and dashboard are
target. The live deployment is a target boundary with established safety and
health contracts; a complete live operator procedure does not currently exist.

## Limitations and non-goals

This diagram does not authorize live operations, specify secret-distribution
technology, or claim that ingestion workers and dashboard are deployable today.
It omits container counts, scaling, and networking detail. Demo fixture output
is deterministic verification material, never empirical findings.

## Source traceability

| Diagram claim | Status | Source |
|---|---|---|
| Demo uses Compose project `strata_ci` and checked-in non-secret configuration | Current | `scripts/ci.sh`, `docker-compose.yml`, [demo and live operations](../../operations/demo-and-live.md) |
| Demo PostgreSQL state is disposable only behind the cleanup guard | Current | `scripts/ci.sh`, [CI isolation](../../engineering/ci-isolation.md) |
| Current application connects, migrates, verifies, and idles | Current | `src/strata/main.py`, `migrations/`, `scripts/ci.sh` |
| Target demo uses deterministic fixtures with zero external calls and populated output | Target | [canonical PRD §7.7](../../Strata_PRD_v3.2_MASTER.md#77-demo-and-live-modes-mvp), [testing guidance](../../engineering/testing.md) |
| Live credentials are runtime-supplied and failures surface as unhealthy | Target contract | [provider integration](../../engineering/provider-integration.md), [secrets and live data](../../engineering/secrets-and-live-data.md) |
| Live readiness depends on minimum coverage and stale analytics are labeled | Target | canonical PRD §7.7, [coverage and publication](../coverage-and-publication.md) |
| Demo and test cleanup never access `strata_live` resources | Current safety contract | [CI isolation](../../engineering/ci-isolation.md) |
| No complete live operator procedure exists today | Current boundary | [demo and live operations](../../operations/demo-and-live.md) |
