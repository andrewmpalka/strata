# Strata architecture diagram index

This pack gives engineers, reviewers, and technical interviewers a compact set
of explanatory views of Strata. It uses GitHub-rendered Mermaid source so that
the diagrams remain reviewable beside the code and canonical product
specification.

> **Architecture status:** the current diagrams describe only the implemented
> migration-safe Python service, PostgreSQL database, and verification
> environment. The target diagrams describe the approved MVP architecture and
> are **not evidence that those capabilities are implemented**.

## How to read this pack

Start with the current system context to understand what exists today, then use
the target container and lineage views to understand the intended MVP. Read
status words and line styles before following arrows: `CURRENT` elements have
tracked implementation support, while `TARGET` elements come from the canonical
PRD and may not exist yet.

## Diagram index

| Diagram | Intended audience | Standard | Canonical source of truth |
|---|---|---|---|
| [Current system context](current-system-context.md) | New engineers and reviewers | C4 System Context semantics | Tracked source, Compose, migrations, and tests |
| [Current containers and deployment](current-container-and-deployment.md) | Application and platform engineers | C4 Container and Deployment semantics | Dockerfile, Compose, scripts, package, and tests |
| [Current startup and migrations](current-startup-and-migrations.md) | Application, database, and operations engineers | UML-style sequence | Startup, connection, and migration source plus integration tests |
| [Target platform containers](target-platform-containers.md) | Data-platform engineers and technical interviewers | C4 Container semantics | PRD §3 and §7 |
| [Target data lineage and publication](target-data-lineage-and-publication.md) | Data-platform and methodology reviewers | Data-flow diagram and UML-style sequence | PRD §7; coverage and pipeline guidance |
| [Target demo and live deployment](target-demo-and-live-deployment.md) | Platform, operations, and security reviewers | C4 Deployment semantics | PRD §7.7; demo/live and CI-isolation guidance |
| [Target core data model](target-core-data-model.md) | Data engineers and methodology reviewers | Logical entity-relationship model with crow's-foot cardinality | PRD §3, §5, and §7 |

## Legend and notation

| Notation | Meaning |
|---|---|
| `CURRENT` | Directly supported by tracked implementation or configuration |
| `TARGET` | Required by the canonical MVP specification but not fully implemented |
| `EXTERNAL` | A person, network, provider, or source outside Strata |
| `DATA STORE` | Persistent repository or runtime state |
| Solid border | Implemented element |
| Dashed border | Target-only element |
| Arrow label | The data, command, result, or control transferred |
| Database cylinder | Persistent data store |
| C4 | Context, Container, Component, and Code architecture model; this pack uses Context, Container, and Deployment semantics only |
| UML | Unified Modeling Language; sequence views use its participant and message conventions |
| DFD | Data-flow diagram; processes, stores, external entities, and labeled flows are distinguished textually |

Status is always stated in text; color is supplementary and never carries
meaning by itself. External systems remain explicitly labeled, and target
boundaries use dashed lines.

## Current versus target maintenance rule

- Current diagrams change when tracked implementation, configuration,
  migrations, or tests change.
- Target diagrams change only when the canonical PRD changes.
- A target capability moves into a current view only after tracked
  implementation and verification support it.

## Source traceability matrix

| Diagram | Code and configuration | Guidance | Canonical PRD |
|---|---|---|---|
| Current system context | `src/strata/`, `Dockerfile`, `docker-compose.yml`, `migrations/`, `scripts/` | [Repository layout](../repository-layout.md), [Migration contract](../migrations.md) | §7.3 |
| Current containers and deployment | `Dockerfile`, `docker-compose.yml`, `scripts/harness`, `scripts/ci.sh`, `tests/`, `integration_tests/` | [Testing](../../engineering/testing.md), [CI isolation](../../engineering/ci-isolation.md) | §7.3 and §7.7 |
| Current startup and migrations | `src/strata/main.py`, `src/strata/config.py`, `src/strata/db.py`, `src/strata/migrations.py`, `migrations/` | [Migration contract](../migrations.md), [Migration operations](../../operations/migrations-and-recovery.md) | §7.3 |
| Target platform containers | No complete implementation yet | [Data pipeline](../data-pipeline.md), [Provider integration](../../engineering/provider-integration.md) | §3 and §7.1–§7.8 |
| Target data lineage and publication | No complete implementation yet | [Data pipeline](../data-pipeline.md), [Coverage and publication](../coverage-and-publication.md) | §7, especially §7.5–§7.6 |
| Target demo and live deployment | Current baseline in `Dockerfile`, `docker-compose.yml`, and `scripts/ci.sh`; target services are not complete | [Demo and live](../../operations/demo-and-live.md), [CI isolation](../../engineering/ci-isolation.md) | §7.7 |
| Target core data model | Only the migration ledger and sentinel are currently implemented | [Attribution invariants](../../methodology/attribution-invariants.md), [Temporal boundaries](../../methodology/temporal-boundaries.md), [Study integrity](../../methodology/study-integrity.md) | §3, §5, and §7 |

## Limitations and authority

These diagrams are selective explanatory views, not schemas, operator
procedures, or substitutes for tests. Tracked code, configuration, migrations,
and tests are authoritative for implemented behavior. The
[canonical PRD](../../Strata_PRD_v3.2_MASTER.md) is authoritative for product
and study semantics. When a diagram and an authoritative source disagree, fix
the diagram.
