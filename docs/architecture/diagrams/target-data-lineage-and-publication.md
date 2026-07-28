# Data Flow and Sequence — TARGET MVP lineage and publication

This file explains how target MVP evidence moves from external providers through
versioned layers into run-bound publication, and how incomplete coverage causes
an auditable refusal instead of partial results.

> **TARGET MVP — NOT FULLY IMPLEMENTED**

**Audience:** data-platform engineers, analytics engineers, methodology
reviewers, and reliability reviewers.

## How to read these diagrams

In the data-flow view, read the main evidence pipeline left to right and the
control inputs from top to bottom. The replay arrow returns retained raw
artifacts to parsing under a new parser version. In the sequence view, time
moves downward and the `alt` block separates publishable coverage from refusal.

## A. Target data-flow diagram

```mermaid
flowchart TB
    evidence["EXTERNAL ENTITY<br/>Chain and provider evidence<br/>Finalized Ethereum and committed Aptos observations"]
    raw[("TARGET DATA STORE<br/>Raw artifacts and hashes<br/>Provider-shaped payloads, provenance, immutable evidence")]
    staging[("TARGET DATA STORE<br/>Typed staging<br/>Decoded records with parser versions")]
    facts[("TARGET DATA STORE<br/>Actor-safe activity facts<br/>Actor, role, class, success, meaning, exclusions, pins")]
    features[("TARGET DATA STORE<br/>Features and cohorts<br/>Index-safe covariates, exposure, maturity, and eligibility")]
    runs[("TARGET DATA STORE<br/>Analytics runs<br/>Matching, retention, balance, intervals, and status")]
    published[("TARGET DATA STORE<br/>Published dashboard and findings state<br/>Atomic, labeled outputs only")]

    contract["TARGET CONTROL<br/>Validated dataset contract<br/>Windows, scopes, populations, lists, and version pins"]
    coverage["TARGET CONTROL<br/>Stream coverage<br/>completed, completed-empty, failed, and explicit gaps"]
    watermarks["TARGET CONTROL<br/>Watermarks<br/>Durable progress by required stream"]
    manifest["TARGET CONTROL<br/>Run manifest<br/>Versions, boundaries, completeness, counts, code, parameters, seed"]
    gate["TARGET PROCESS<br/>Publication gate<br/>Compute gap-free intersection and publish or refuse"]

    evidence -->|"provider responses and source provenance"| raw
    raw -->|"payloads plus content hashes"| staging
    staging -->|"typed parser-versioned observations"| facts
    facts -->|"successful actor-role activity and declared exclusions"| features
    features -->|"eligible cohorts, controls, covariates, and outcomes"| runs
    runs -->|"candidate run outputs and status"| gate
    gate -->|"atomic run-labeled results when eligible"| published

    contract -->|"validated scope and version controls"| staging
    contract -->|"study population, index, matching, and retention rules"| features
    contract -->|"required streams and publication requirements"| gate
    coverage -->|"interval statuses and gap evidence"| gate
    watermarks -->|"durable stream boundaries"| coverage
    manifest -->|"complete lineage binding"| gate
    runs -->|"run identity, counts, parameters, and code revision"| manifest
    raw -.->|"replay retained evidence under a new parser version"| staging
    gate -.->|"auditable refused status and reason; no partial published state"| runs

    classDef target fill:#f7f3ff,stroke:#604080,stroke-width:2px,stroke-dasharray:6 4,color:#111;
    classDef targetStore fill:#f5f5f5,stroke:#604080,stroke-width:2px,stroke-dasharray:6 4,color:#111;
    classDef external fill:#fff8dc,stroke:#6b5b00,stroke-width:2px,color:#111;
    class contract,coverage,watermarks,manifest,gate target;
    class raw,staging,facts,features,runs,published targetStore;
    class evidence external;
```

The main pipeline never credits a bundler, fee payer, sponsor, or passive
recipient as the actor. Authorization attempts and proven delegation
observations remain distinct evidence states. Exposure is assigned at the index
boundary, and analytical language remains associative rather than causal.

## B. Target publication sequence

```mermaid
sequenceDiagram
    participant Runner as TARGET Analytics runner
    participant Contract as TARGET Validated dataset contract
    participant Coverage as TARGET Stream coverage store
    participant Data as TARGET Validated upstream layers
    participant Runs as TARGET Analytics run and manifest store
    participant Gate as TARGET Publication gate
    participant Published as TARGET Published result store
    participant Dashboard as TARGET Streamlit dashboard

    Runner->>Contract: Load validated windows, scopes, required streams, and version pins
    Contract-->>Runner: Return validated dataset contract
    Runner->>Coverage: Read required interval coverage by stream, scope, and parser version
    Coverage-->>Runner: Return completed, completed-empty, failed, and gap evidence
    Runner->>Runner: Compute intersection of gap-free completed intervals
    Note over Runner,Coverage: completed-empty is valid coverage, while failed intervals and gaps block publication

    alt Sufficient gap-free intersection for every required stream
        Runner->>Data: Read validated facts, features, cohorts, and eligible matched data
        Data-->>Runner: Return run-bound analytical inputs
        Runner->>Runner: Derive features, matching diagnostics, retention, and suppression state
        Runner->>Runs: Write complete run and manifest with covered intersection
        Runs-->>Runner: Confirm durable run and lineage record
        Runner->>Gate: Request atomic publication for the complete run
        Gate->>Published: Commit labeled results as one published state
        Published-->>Gate: Confirm atomic publication
        Gate-->>Runner: Return published status
        Dashboard->>Published: Read one labeled published run
        Published-->>Dashboard: Return results with coverage and freshness
    else Insufficient coverage because a stream failed or a gap remains
        Runner->>Runs: Write status=refused with coverage evidence and reason
        Runs-->>Runner: Confirm auditable refused run
        Runner->>Gate: Request refusal finalization with no result payload
        Gate-->>Runner: Confirm no partial published state was written
        Dashboard->>Runs: Read refusal, coverage, and freshness status
        Runs-->>Dashboard: Return refusal reason instead of analytical results
    end
```

## Legend and notation

- Every process and store in both diagrams is `TARGET`; dashed borders reinforce
  that it is not fully implemented.
- `EXTERNAL ENTITY` originates evidence outside Strata.
- `DATA STORE`, `CONTROL`, and `PROCESS` distinguish DFD roles.
- A dotted arrow denotes replay or a refusal feedback path, not weaker
  correctness.
- `completed-empty` means a successfully scanned interval with zero events.
- A run manifest binds outputs to declared data, code, versions, parameters,
  and coverage.

## Current versus target

Both diagrams are entirely target MVP. The current database contains only the
migration ledger and sentinel; none of the depicted evidence, fact, coverage,
analytics-run, manifest, or published-result stores is implemented.

## Limitations and non-goals

The DFD is logical rather than a physical table map and does not prescribe job
scheduling or message transport. The sequence compresses matching and
suppression calculations. Fixture evidence may verify this path but can never
produce empirical findings.

## Source traceability

| Diagram claim | Status | Source |
|---|---|---|
| Canonical lineage is raw to staging to facts to features/cohorts to analytics runs | Target | [canonical PRD §7](../../Strata_PRD_v3.2_MASTER.md#7-architecture), [data pipeline](../data-pipeline.md) |
| Raw evidence retains provenance and hashes; staging is parser-versioned | Target | canonical PRD §7, [data pipeline](../data-pipeline.md) |
| Decoder corrections replay retained raw artifacts under a new parser version | Target | [data pipeline](../data-pipeline.md) |
| Watermarks advance only after durable writes | Target | [data pipeline](../data-pipeline.md), canonical PRD §7.1–§7.2 |
| `completed-empty` is valid while failed intervals and gaps block publication | Target | [coverage and publication](../coverage-and-publication.md), canonical PRD §7.5 |
| Publication requires the gap-free intersection for every required stream | Target | [coverage and publication](../coverage-and-publication.md), canonical PRD §7.6 |
| Insufficient coverage records `status=refused` and no partial published state | Target | [coverage and publication](../coverage-and-publication.md) |
| Published charts are run-labeled and expose coverage and freshness | Target | canonical PRD §7.6–§7.7, [publication language](../../methodology/publication-language.md) |
| Actor and delegation evidence remain structurally separated | Target | [attribution invariants](../../methodology/attribution-invariants.md) |
