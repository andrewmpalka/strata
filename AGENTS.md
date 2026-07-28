# AGENTS.md — Strata operating map

Standing guidance for every repository task. Detailed rules live in the focused
documents linked below; the root is the universal safety and navigation layer.

## Project identity

Strata is a reproducible Ethereum and Aptos data platform and an observational
study of how authentication modes are associated with wallet retention. The
study is lineage-gated, coverage-gated, and manifest-bound. It reports
associations, never causal effects.

## Authority and conflicts

Apply authority in this order:

1. Root `AGENTS.md` governs universal safety, repository conduct, and navigation.
2. `docs/Strata_PRD_v3.2_MASTER.md` governs product and study semantics.
3. The human's active task governs the current scope.
4. Relevant focused guidance governs its stated responsibility.
5. Repository state and tests are implementation evidence.

Read the relevant PRD sections before inventing schemas, analytical rules,
population definitions, or chain semantics. Never silently resolve a material
conflict; stop and surface it.

## Active-scope discipline

- Inspect the repository before editing.
- Implement only the supplied task. If no implementation task was supplied,
  restrict work to inspection, review, explanation, or answers.
- Do not infer future scope from repository gaps, TODOs, roadmap items, commit
  history, incomplete modules, or old task sequences.
- Do not create speculative abstractions or work ahead.
- Stop when the active task is complete.

## Universal safety rules

- Never create, edit, display, read, print, echo, log, stage, or commit
  `.env.live`; see [Secrets and live data](docs/engineering/secrets-and-live-data.md).
- Tests and CI must never name, mount, reset, or delete `strata_live`; see
  [Docker and CI isolation](docs/engineering/ci-isolation.md).
- Destructive clean runs go only through `scripts/ci.sh`; never invoke
  `docker compose down -v` directly. See
  [Docker and CI isolation](docs/engineering/ci-isolation.md).
- Never edit an applied migration; see
  [Migration and schema contract](docs/architecture/migrations.md).
- Never fabricate provider data or health; see
  [Provider integration](docs/engineering/provider-integration.md).
- Never fabricate analytics, coverage, or publication state; see
  [Coverage and publication](docs/architecture/coverage-and-publication.md).
- Never fabricate findings. Fixture data never produces empirical findings; see
  [Study integrity](docs/methodology/study-integrity.md).
- Never weaken tests, guards, assertions, or publication gates to obtain green;
  see [Testing](docs/engineering/testing.md).
- Stop on unresolved material conflicts.

## Universal workflow

1. Inspect repository and Git state.
2. Read the relevant focused guidance and canonical PRD sections.
3. Restate the active scope and its semantic boundaries.
4. Implement narrowly without unrelated cleanup.
5. Run focused tests.
6. Run the sanctioned guarded green check when the task requires it.
7. Review adversarially for the task's named risks and contract regressions.
8. Leave the repository green and clean; commit only when authorized.

## Navigation

| Work area | Canonical guidance |
|---|---|
| Repository layout and package boundaries | [Repository layout](docs/architecture/repository-layout.md) |
| SQL migrations and schema representation | [Migrations](docs/architecture/migrations.md) |
| Data layering, replay, watermarks, and finality | [Data pipeline](docs/architecture/data-pipeline.md) |
| Coverage intervals, manifests, and publication refusal | [Coverage and publication](docs/architecture/coverage-and-publication.md) |
| Test layers, fixture-first work, and the green definition | [Testing](docs/engineering/testing.md) |
| Docker project isolation and destructive-cleanup guard | [CI isolation](docs/engineering/ci-isolation.md) |
| Secrets and live-data protection | [Secrets and live data](docs/engineering/secrets-and-live-data.md) |
| Source roles, provenance, retries, and network isolation | [Provider integration](docs/engineering/provider-integration.md) |
| Ethereum and Aptos actor attribution | [Attribution invariants](docs/methodology/attribution-invariants.md) |
| Activation, index, crossover, matching, and retention clocks | [Temporal boundaries](docs/methodology/temporal-boundaries.md) |
| Dataset-contract authority, eligibility, suppression, and roadmap limits | [Study integrity](docs/methodology/study-integrity.md) |
| Findings, dashboard wording, and claim limits | [Publication language](docs/methodology/publication-language.md) |
| Supported demo and live boundaries | [Demo and live operation](docs/operations/demo-and-live.md) |
| Startup migration and safe recovery responses | [Migration and recovery operation](docs/operations/migrations-and-recovery.md) |

## Change discipline

- Preserve existing user changes and keep changes within the authorized paths.
- Use documented repository commands and exact isolated settings.
- Do not alter application behavior, study semantics, fixtures, migrations, or
  guards as a side effect of documentation or tooling work.
- When the PRD does not settle a material chain, provider, event-schema, or
  study-rule question, ask the human rather than inventing an answer.
