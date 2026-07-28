# Logical Responsibility Map — TARGET MVP platform, not fully implemented

This logical component view presents the approved MVP responsibilities for a
reproducible Ethereum and Aptos data platform and its observational
authentication-mode retention study.

> **TARGET MVP — NOT FULLY IMPLEMENTED**

**Audience:** data-platform engineers, methodology reviewers, and technical
interviewers evaluating the intended platform boundaries.

## How to read this diagram

Read live evidence from the external systems at the top and deterministic demo
evidence from the fixture store at the left. Both paths enter the same
lineage-preserving platform, but the live provider adapters remain
source-specific and are never silently interchangeable. Dashed borders and
`TARGET` labels identify capabilities that are not fully implemented.

```mermaid
flowchart TB
    ethereum["EXTERNAL SYSTEM<br/>Ethereum network and provider APIs<br/>Finalized blocks, transactions, receipts, logs, code, and history"]
    aptos["EXTERNAL SYSTEM<br/>Aptos fullnode and provider APIs<br/>Committed versions, transactions, events, and write sets"]
    canonical["EXTERNAL SYSTEM<br/>Canonical history and registry sources<br/>Authoritative activation, EntryPoint, and account evidence"]
    fixtures[("TARGET DATA STORE<br/>Checked-in deterministic fixtures<br/>Demo evidence with zero network access")]

    subgraph target_platform["TARGET MVP — Strata platform responsibilities, not fully implemented"]
        contract["TARGET RESPONSIBILITY<br/>Dataset contract<br/>Governs networks, windows, scopes, lists, and version pins"]
        eth_adapter["TARGET RESPONSIBILITY<br/>Ethereum provider adapters<br/>Acquire finalized, source-specific evidence"]
        apt_adapter["TARGET RESPONSIBILITY<br/>Aptos provider adapters<br/>Acquire committed, source-specific evidence"]
        raw["TARGET RESPONSIBILITY<br/>Raw evidence ingestion<br/>Retain provider-shaped payloads, provenance, and hashes"]
        staging["TARGET RESPONSIBILITY<br/>Typed staging and parsers<br/>Decode evidence under parser versions"]
        facts["TARGET RESPONSIBILITY<br/>Activity-fact builder<br/>Preserve actor, role, success, meaning, exclusions, and pins"]
        control["TARGET RESPONSIBILITY<br/>Coverage and watermark control<br/>Record intervals and advance only after durable writes"]
        features["TARGET RESPONSIBILITY<br/>Feature and cohort builder<br/>Apply index, temporal, attribution, and maturity rules"]
        analytics["TARGET RESPONSIBILITY<br/>Matching and retention analytics<br/>Estimate descriptive associations for eligible populations"]
        gate["TARGET RESPONSIBILITY<br/>Run manifest and publication gate<br/>Bind lineage and refuse incomplete publication"]
        postgres[("TARGET DATA STORE<br/>PostgreSQL<br/>Persist evidence, derived layers, coverage, runs, and results")]
        dashboard["TARGET RESPONSIBILITY<br/>Streamlit dashboard<br/>Serve run-labeled results, coverage, and freshness"]
    end

    ethereum -->|"live finalized Ethereum evidence"| eth_adapter
    aptos -->|"live committed Aptos evidence"| apt_adapter
    canonical -->|"authoritative history and registry evidence"| eth_adapter
    canonical -->|"authoritative account-history evidence"| apt_adapter
    eth_adapter -->|"provider-specific raw responses and provenance"| raw
    apt_adapter -->|"provider-specific raw responses and provenance"| raw
    fixtures -->|"demo artifacts with network disabled"| raw

    contract -->|"validated scopes, windows, lists, and versions"| eth_adapter
    contract -->|"validated scopes, windows, lists, and versions"| apt_adapter
    contract -->|"validated derivation and study rules"| features
    contract -->|"required streams and publication parameters"| gate
    raw -->|"retained payloads and content hashes"| staging
    staging -->|"typed parser-versioned records"| facts
    facts -->|"actor-safe qualifying activity"| features
    features -->|"eligible features, cohorts, and controls"| analytics
    analytics -->|"run outputs, balance, intervals, and suppression state"| gate
    control -->|"gap-free coverage intersection and watermarks"| gate
    raw -->|"durable raw evidence writes"| postgres
    staging -->|"typed staging writes"| postgres
    facts -->|"activity-fact writes"| postgres
    control -->|"coverage and watermark writes"| postgres
    features -->|"feature and cohort writes"| postgres
    analytics -->|"analytical run writes"| postgres
    gate -->|"atomic published or auditable refused run"| postgres
    postgres -->|"single labeled published run plus coverage and freshness"| dashboard

    classDef target fill:#f7f3ff,stroke:#604080,stroke-width:2px,stroke-dasharray:6 4,color:#111;
    classDef external fill:#fff8dc,stroke:#6b5b00,stroke-width:2px,color:#111;
    classDef targetStore fill:#f5f5f5,stroke:#604080,stroke-width:2px,stroke-dasharray:6 4,color:#111;
    class contract,eth_adapter,apt_adapter,raw,staging,facts,control,features,analytics,gate,dashboard target;
    class ethereum,aptos,canonical external;
    class fixtures,postgres targetStore;
    style target_platform stroke:#604080,stroke-width:2px,stroke-dasharray:8 5,fill:none
```

## Legend and notation

- `TARGET` and dashed borders mean specified by the canonical PRD but not fully
  implemented.
- `EXTERNAL SYSTEM` is outside Strata and may have a different evidence
  universe.
- `DATA STORE` is persistent fixture or PostgreSQL state.
- This is a logical responsibility/component view, not a C4 Container diagram.
  A responsibility may later share a runnable worker with other
  responsibilities.
- MVP means minimum viable product. API means application programming
  interface.

## Current versus target

The complete diagram is a target view. The repository currently implements only
the configuration, PostgreSQL connection, migration runner, migration ledger,
sentinel, and verification baseline. The provider, lineage, analytics,
publication, and dashboard responsibilities shown here are not fully
implemented.

## Limitations and non-goals

This diagram does not prescribe process topology, queue technology, scaling, or
independent deployment for each responsibility. It excludes post-MVP chains,
alternative analytical stores, trace-backed application attribution, and other
roadmap capabilities. It reports an observational association architecture, not
a causal inference system.

## Source traceability

| Diagram claim | Status | Source |
|---|---|---|
| Dataset contract governs networks, windows, scopes, populations, and versions | Target | [canonical PRD §3](../../Strata_PRD_v3.2_MASTER.md#3-the-dataset-contract-v10), [study integrity](../../methodology/study-integrity.md) |
| Ethereum uses finalized evidence and Aptos uses committed versions | Target | [canonical PRD §7.1–§7.2](../../Strata_PRD_v3.2_MASTER.md#7-architecture), [data pipeline](../data-pipeline.md) |
| Provider adapters preserve source roles rather than silently substitute | Target | [provider integration](../../engineering/provider-integration.md), canonical PRD §5.3 |
| Raw, staging, fact, feature, and analytics layers preserve replay and lineage | Target | [canonical PRD §7](../../Strata_PRD_v3.2_MASTER.md#7-architecture), [data pipeline](../data-pipeline.md) |
| Coverage and manifests gate publication | Target | [canonical PRD §7.5–§7.6](../../Strata_PRD_v3.2_MASTER.md#75-coverage-as-intervals-mvp), [coverage and publication](../coverage-and-publication.md) |
| Demo fixtures make zero network calls; live dependencies report health honestly | Target | [canonical PRD §7.7](../../Strata_PRD_v3.2_MASTER.md#77-demo-and-live-modes-mvp), [demo and live operations](../../operations/demo-and-live.md) |
| PostgreSQL and Streamlit are the MVP storage and serving choices | Target | canonical PRD §6 F7 and §7.8 |
