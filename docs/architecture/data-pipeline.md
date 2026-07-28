# Data pipeline, replay, and finality

The canonical data flow is:

`raw_*` → `staging_*` → `activity_fact` → features and cohorts → `analytics_runs`

The canonical PRD defines the product semantics of each layer. This document
governs evidence preservation and replay behavior.

## Layer contracts

- Raw records retain source-shaped payloads, provider provenance, and content
  hashes.
- Staging records are typed and carry `parser_version`.
- Activity facts preserve actor, role, classification, success, meaningfulness,
  exclusions, and the relevant version pins before downstream derivation.
- Features, cohorts, and analytics runs derive only from validated upstream
  layers and the validated dataset-contract object.

Every replayable ingestion or derivation write is idempotent on a documented
natural key. Append-only evidence, history, coverage, and audit data—including
authorization attempts, delegation observations, manifests, coverage intervals,
and retained artifacts—use immutable unique keys or explicit versioning. Never
obtain idempotency by destructively overwriting historical evidence.

Decoder fixes replay staging from retained raw artifacts under a new
`parser_version`; they do not re-fetch a provider merely to replace evidence.
Per-stream watermarks advance only after all corresponding writes are durable.

Ethereum ingestion uses finalized blocks only. Aptos committed versions have
deterministic finality; the absence of Ethereum-style reorganization machinery
for Aptos is an explicit chain-semantic decision, not silent degradation.
