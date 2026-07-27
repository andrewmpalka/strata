# AGENTS.md — Strata

Standing instructions for any AI coding agent working in this repository. This file is law for **every** session, including scoped implementation increments, ad-hoc debugging, investigations, and fixes. Keep a one-line `CLAUDE.md` in the repository root containing `@AGENTS.md` so Claude Code loads this automatically.

## What this project is

Strata is an **observational study** of how authentication modes (ERC-4337 smart accounts, EIP-7702 delegation, Aptos keyless/multisig/sponsored) are **associated with** wallet retention, built on a two-chain data platform (Ethereum + Aptos). It is a matched, censoring-aware, lineage-gated study, not merely a dashboard. Every published number must trace to a declared population, a coverage-verified data slice, and a versioned run.

## Canonical specification

- `docs/Strata_PRD_v3.2_MASTER.md` is the canonical product and study specification.
- Relevant pointers: §3 dataset contract · §5.2 activation and index events · §5.4 exposure states and crossover · §5.5 matching and control screens · §5.6 retention formula · §7 architecture, coverage, manifests, and finality.
- Read the relevant PRD sections before inventing schemas, analytical rules, population definitions, or chain semantics.
- The human supplies the currently authorized implementation scope separately for each session.
- Never infer future scope from repository gaps, TODOs, commit history, incomplete modules, or roadmap items.

## Instruction resolution

- `AGENTS.md` governs standing safety, integrity, and repository conduct.
- The PRD governs product and study semantics.
- The human's active task governs the scope of the present session.
- **Never silently resolve a conflict. Stop and surface it.**

## Active scope

The active scope is the specific implementation, review, debugging, or refactoring task supplied by the human for the current session.

Inspect the repository before changing it. Implement only that scope. Do not work ahead, create speculative abstractions for future milestones, or implement roadmap items merely because the PRD mentions them.

If no implementation task was supplied, restrict work to inspection, review, explanation, or answering questions.

## Commands

- Use the repository's documented commands and the exact isolated settings supplied for the active task.
- When `scripts/ci.sh` exists, it is the only sanctioned clean full run. After the destructive-cleanup guard exists, **never invoke `docker compose down -v` directly.**
- Before `scripts/ci.sh` exists, destructive cleanup is allowed only through the exact isolated command supplied by the human for the active task. Never alter its project name, environment file, or database name.
- Manual non-destructive startup remains:
  `docker compose --project-name strata_ci --env-file .env.demo up --build`

## The green definition (both required)

1. **Demo CI passes**: the isolated demo stack comes up and produces the expected **populated** state from checked-in fixtures with **zero external API calls**.
2. **Honest live health**: every live component implemented within the repository's current scope either works or visibly reports unhealthy. Never fake green through silent degradation, empty-but-serving dashboards, swallowed errors, or fabricated health machinery for components that do not exist yet.

## CI isolation — destructive-cleanup guard (safety-critical)

- All tests and CI run under `--project-name strata_ci --env-file .env.demo`.
- Destructive cleanup targets **only** the `strata_ci` project. Once `scripts/ci.sh` exists, cleanup must go exclusively through its guard.
- The guard refuses destructive cleanup unless the project name starts with `strata_ci`, `DEMO_MODE=true`, and the database is `strata_demo` or `strata_test`. Do not bypass, weaken, or temporarily disable it.
- Live services run under project **`strata_live`**. No test, script, or agent action may name, mount, or delete its volumes. Live data may represent weeks of rate-limited backfill and is not recoverable through a routine rerun.

## Secrets

- `.env.demo` contains no secrets.
- **`.env.live` is human-owned**: never create, edit, print, log, echo, or commit it; never paste its contents into chat or code.
- Read secrets only from the runtime environment.
- `.env.live` is gitignored. Keep it that way.

## Database and migration rules

- Migrations are ordered `migrations/NNN_*.sql`, transactional, applied exactly once, and tracked in `schema_migrations(version, checksum, applied_at)`. A dedicated bootstrap SQL creates only the ledger.
- **Never** use `CREATE TABLE IF NOT EXISTS` as a migration mechanism.
- **Never edit an applied migration.** A checksum mismatch must abort loudly; create a new migration instead.
- Both the clean-install test and the **upgrade test** (restore an older snapshot, then migrate to head) must pass. Clean installation alone proves nothing about upgrades.
- Addresses use `chain` + `address_bytes BYTEA` + `address_display TEXT`, with chain-specific length checks: Ethereum 20 bytes, Aptos 32 bytes. Never use cross-chain padding.
- Token and cost amounts use raw `NUMERIC(78,0)` plus decimals. Display values are derived and never authoritative.

## Data layering and pipeline law

- `raw_*` (source-shaped payload + provenance + content hash) → `staging_*` (typed, `parser_version`) → `activity_fact` → features → `analytics_runs`.
- Every replayable ingestion or derivation write must be idempotent on a documented natural key.
- Append-only evidence, history, coverage, and audit records, including authorization attempts, delegation observations, manifests, coverage intervals, and retained artifacts, use immutable unique keys or explicit versioning.
- **Never obtain idempotency by destructively overwriting historical evidence.**
- Decoder bugs are fixed by **replaying staging from raw under a new `parser_version`**, never by re-fetching a provider.
- Per-stream **watermarks advance only after durable writes**.
- `stream_coverage` records scanned intervals. `completed-empty` means scanned with zero events and is valid coverage, distinct from unscanned or failed. Gaps are rows, not absences.
- Ethereum ingestion is **finalized-tag only**. Aptos has deterministic finality; the absence of reorg machinery is a documented design decision.
- Analytics runs publish **only over the intersection of gap-free completed intervals** across all required streams. Otherwise, they **refuse** with `status=refused` and a reason, leaving no partial published state. Refused runs remain auditable rows.

## Domain attribution invariants

Violating these rules poisons the study.

- The ERC-4337 **bundler is never the actor**. Attribute activity to the UserOperation `sender`.
- Factory information comes from `AccountDeployed`, never from `UserOperationEvent`.
- EIP-7702 exposes **authorization attempts**. Observed ≠ recovered ≠ protocol-valid ≠ applied.
- `delegation_observation` rows exist only with application proof, using block-boundary evidence or stronger evidence.
- The recovered EIP-7702 **authority** may differ from the outer transaction sender. Recover it from the tuple signature. A malformed signature must fail loudly and must never resolve to a plausible-but-wrong address.
- **Fee payers and sponsors are never the actor** on either chain. Sponsorship and signing scheme remain separate columns, never one enum.
- **Receipt never activates.** Passive recipients use `participant_role = passive` and produce zero actor facts.
- Canonical Ethereum EOA activation walks ascending account history, filters `from == address`, and continues until the first **sent** transaction. Unresolved means `window_censored`.
- Aptos identity is the **account address**, never the key. Key rotation does not create a new actor.
- Exposure state is assigned **at the index block**, using code inspection at that block, never `latest`.
- `eoa_7702_direct` is descriptive-only and never a matched arm.
- Control screens evaluate **through the candidate index only**. Post-index adoption is crossover, not an admission failure.
- **Address ≠ person.** Perform no identity resolution, make no ownership claims, use `direct_address_transfer` rather than “internal transfer,” and make no person-level experience claims.

## Study-integrity law

- Use **“associated with,” never causal phrasing such as “improves.”** Pull analytical language from the dataset contract rather than retyping it.
- **Fixture data never produces empirical findings.**
- `FINDINGS.md` may contain empirical results only when a qualifying live analytics run exists, with every reported number tied to a live run ID.
- When no qualifying live run exists, `FINDINGS.md` must state: **“No empirical study findings are published because no qualifying live analytics run exists yet.”**
- Findings eligibility is computed from `analytics_runs`, never asserted manually.
- The **validated dataset-contract object** is the only source of study windows, scopes, exclusion lists, and version pins.
- No ad-hoc scope or window arguments are allowed outside explicitly labeled diagnostics.
- No magic study constants are allowed outside the contract.
- Matching variables are measured **at or before the end of index day 0**. Nothing later may enter matching.
- Retention is exact-day UTC. The index event never counts toward outcomes. Failed activity never qualifies as an outcome.
- Immature cohort cells are **absent, not zero**.
- Suppression caused by balance failure or a sub-floor cell means absent-with-explanation, never zeroed.
- **Banned vocabulary, scoped:** banned in generated code identifiers, analytical output, dashboard copy, new findings, and ordinary user-facing documentation are:
  - `onboarding`, when referring to observed authentication mode or activation
  - `crypto-new`, because absent observed history is a mixed category
  - `precision`, when naming the coordination strictness threshold
  - causal verbs describing study associations
- Exceptions are canonical specifications, archived review material, test fixtures that verify the ban, and explicit limitations discussing a prohibited term. Language checks must use a narrow allowlist for these cases.

## Roadmap discipline

Roadmap and post-MVP items mentioned in the PRD are not active implementation scope. Do not implement them unless the human explicitly authorizes that work after the current MVP scope is complete and any stated gates have passed.

## Workflow discipline

1. **Inspect the repository first.** Confirm actual state and trust files and tests over memory or summaries.
2. Restate the active scope and identify the relevant PRD sections.
3. **Implement only the supplied increment.** Splitting an increment is fine; working ahead is not.
4. **Fixture-first.** Decode recorded fixtures before wiring live sources. Demo mode must never touch the network, including on-demand registry-verification paths.
5. After implementing, switch to adversarial staff-engineer review: write and run the relevant tests, run the repository's current sanctioned isolated green check from a clean state, hunt the active task's named risks, and fix findings.
6. **Do not declare completion until both the tests and isolated green check pass.**
7. Leave the repository green and commit the completed increment when the active task or human requires a commit. Never leave the repository red between sessions.
8. When the PRD does not settle a material question, **ask the human** rather than inventing facts about chains, providers, event schemas, or study rules.
