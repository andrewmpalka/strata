# PRD v3.2 — Strata: An Observational Study of Authentication Modes and Wallet Retention Across Two Chains

**Working title:** Strata
**Type:** Product Requirements Document (personal build / portfolio)
**Author:** Andy
**Status:** **v3.2 — Approved for build.** Final adversarial review passed; this document merges PRD v3, amendment v3.1 (A1–A9), and the closing amendments (A10–A11, E1–E4) into the single canonical specification. All prior documents are superseded. *Roadmap addendum (July 25, 2026): Robinhood Chain RWA extension pinned as gated post-MVP future work (§9).*
**Last updated:** July 25, 2026
**One-line:** A reproducible two-chain data platform (Ethereum + Aptos) that measures how observed authentication mode is *associated with* wallet retention — modeled correctly on each chain's own terms, with one study clock, structurally attributable exposure arms, and every published number bound to a declared population, a coverage-verified data slice, and a versioned run.

---

## 1. Summary

Most on-chain analytics tooling is EVM-shaped and population-naive: it assumes account-model semantics, treats transaction counts as engagement, and computes retention over whatever addresses happen to appear. Strata takes the opposite position twice. It models two structurally different chains on their own terms — Ethereum's account model with probabilistic finality, and Aptos's Move resource model with deterministic finality — and it models its own *study* on honest terms: a committed dataset contract, one index clock, mutually exclusive and structurally attributable exposure arms, matched comparisons, censoring rules, and analytics runs that refuse to publish over incomplete data.

The study: newer authentication modes now exist alongside plain keys — ERC-4337 smart accounts and EIP-7702 delegation on Ethereum (post-Pectra, May 2025; EntryPoint v0.8+ supports the native 7702-via-4337 path); keyless, multisig, and sponsored transactions on Aptos. Strata measures whether addresses using these modes retain differently than matched plain-key addresses, reports the **association** with limitations stated, adds a descriptive **delegation-adoption view** for the direct-7702 population whose actor attribution MVP evidence cannot support, and documents an on-thesis finding about what each chain's data model lets an analyst honestly observe.

Deliverables: a reproducible pipeline (one-command demo mode as the CI target; honest live mode), a dashboard whose every chart carries its run manifest, and a written analysis with at least two non-obvious findings.

## 2. Thesis and timing

**The technical gap.** Three recurring failures: activity is overcounted (failures, approvals, bots, and mechanical housekeeping inflate counts on both chains, differently); balances are not fields (Ethereum balances replay from events; Aptos balances are typed resources); and cross-chain behavioral comparison is unsupported because account semantics differ per chain and tools don't model them. Correctness requires modeling each chain — and each study population — on its own terms.

**Why now, publicly.** EIP-7702 shipped in Pectra (May 2025); ERC-4337 is in production through a registry of EntryPoint versions (v0.6 → v0.9, the latter released November 2025); Aptos ships keyless accounts, native multisig, and fee-payer transactions. "Does authentication mode relate to whether users stick?" is newly measurable from entirely public data.

**Why this builder.** Data-platform architecture, entity resolution, and lifecycle analytics transfer directly: indexers are CDC/ETL; matched-cohort comparison is standard observational method from marketing analytics; wallet analysis is entity-level work without PII. Strata is the inspectable proof of transfer.

## 3. The Dataset Contract (v1.0)

A committed repository artifact; analytics code reads its constants; every run manifest records its version.

**Networks and window.** Ethereum mainnet and Aptos mainnet. Observation window: **90 consecutive days**, dates pinned at build time (90 days so cohorts from the first 60 days reach D30 maturity in-window).

**Study population (by arm; index events in §5.2).**
- *Ethereum treated:* addresses whose in-window observations place them in a primary exposure state — `contract_account_4337` or `eoa_7702_via_4337` (§5.4). The `eoa_7702_direct` population enters the **descriptive adoption view** (§5.7), not the matched analysis.
- *Ethereum control:* plain-key EOAs with ≥1 qualifying in-window transaction, screened **through the candidate index boundary only** (§5.5): no prior 4337 (EntryPoint sender history, v0.6 boundary stated), no prior 7702 authority observation (Pectra-bounded authorization index), undelegated at the pseudo-index block, not infrastructure, not a contract.
- *Aptos:* accounts observed in-window as user-transaction senders, classified by decomposed authentication fields (§7.4); keyless-at-index treated vs. matched single-key controls; multisig and sponsored contrasts as descriptive stratifications where the pair floor is unmet.
- *Passive participants:* addresses that only receive are recorded with `participant_role = passive` and are **never** activated, indexed, cohorted, or counted active by receipt.

**Exclusions.** Bundlers, EntryPoints, exchanges/bridges (curated, versioned list), contracts on the control side, Aptos system/bookkeeping transaction types.

**Finality policy.** Ethereum: finalized blocks only (MVP). Aptos: committed versions (deterministically final).

**Claim ceiling — the evidence ladder.** (1) First observed authentication mode in-window; (2) first observed chain activity (activation); (3) account-creation / authenticator-registration evidence; (4) product onboarding. **Claims live on rungs 1–2.** Activation age is a censoring-correction covariate only. Rung 3 is reported only where the chain supplies direct evidence (Aptos account creation; F8), with coverage stated. The word "onboarding" appears nowhere but the limitations section explaining its absence.

**Language rule.** Association, never causation: "associated with retention," never "improves retention." This is an observational study and says so in its own header.

**Pinned versions.** `dataset_contract_version`, `filter_version`, `matching_protocol_version`, `entrypoint_registry_version`, and per-stream `parser_version` are recorded on derived rows and in every manifest.

**Cohort maturity.** A cohort contributes to a D*n* cell only at age ≥ *n* days in-window; immature cells are suppressed; the dashboard shows cohort age.

## 4. Users

A growth/lifecycle analyst who needs auth-mode comparisons that survive methodological questioning; an ecosystem researcher who needs inflation-filtered activity with the filter auditable; and, candidly, a technical interviewer for whom every design choice is evidence.

## 5. Study design

### 5.1 Research questions
**RQ1 (primary, matched).** Among matched Ethereum addresses, is exposure state at index — `plain_eoa` vs. `contract_account_4337` vs. `eoa_7702_via_4337` — associated with D1/D7/D30 retention?
**RQ2 (primary, matched, parallel).** On Aptos, is keyless-at-index vs. matched single-key associated with retention, with sponsorship as a separate within-arm stratification axis? Multisig/sponsored contrasts report as descriptive stratifications where the 200-pair floor is unmet. Cross-chain claims are directional only.
**RQ3 (on-thesis finding).** What does each data model let an analyst honestly observe? Aptos exposes rung-3 evidence (explicit account creation; observable key rotation); Ethereum EOAs have no creation event by construction. Reported as a result about observability.
**RQ4 (secondary, descriptive).** The delegation-adoption view: following an observed in-window authorization, what is the authority's subsequent **sent** activity — including never-sent-after-adoption as an outcome category?

### 5.2 Three clocks and the index events

- **`activation_date`** — canonical earliest chain activity per actor class (§5.3). Covariate only.
- **`index_date`** — timestamp of the study index event. Study entry.
- **Outcome clock** — retention measured from `index_date`, never from activation. `activation_age = index_date − activation_date`.

| Arm | Index event |
|---|---|
| `contract_account_4337` / `eoa_7702_via_4337` | First qualifying in-window UserOperation as `sender` |
| Plain-EOA control | One qualifying in-window transaction, sampled **deterministically** (uniform under the manifest seed) from the control's transactions in the treated partner's index ISO week |
| Aptos mode | First qualifying in-window user transaction sent under the observed mode |
| Adoption view (`eoa_7702_direct` population) | The in-window **authorization event** (§5.7) |

Index events include failed attempts (the attempt is the adoption act; success flag retained; a sensitivity view excluding failed-index addresses is available). Outcomes use meaningful, successful activity only (§5.6).

### 5.3 Activation: canonical definition by actor class

| Actor class | Canonical activation event | Canonical MVP source and procedure |
|---|---|---|
| Plain Ethereum EOA / 7702 authority | Earliest top-level transaction **sent** | `txlist`-family, **ascending pages, filter `from == address`, paginate until the first sent transaction is found**; the endpoint returns transactions *involving* the address, so early pages can be all-incoming. Provider limits exhausted with no sent tx ⇒ **unresolved** ⇒ window-censored, manifest-counted |
| ERC-4337 account | Earliest decoded UserOperation attributed to its `sender` | Full-history `eth_getLogs` on registered EntryPoints filtered by the indexed `sender` topic, chunked; **coverage boundary: v0.6 deployment onward**, stated as a disclosed limitation (pre-v0.6 EntryPoints exist and are outside the screen) |
| Aptos account | Earliest user transaction **sent** | Fullnode account-transactions endpoint, ascending, first user transaction |
| Passive recipient | **Never** activated by receipt | — |

Policies: source precedence (canonical authoritative; adapters — Alchemy transfers, Dune export, Aptos indexer GraphQL — validation/bulk only, documented as different universes, never silently substituted); disagreement (flag `source_conflict`, retain both raw artifacts, use canonical, manifest-count conflicts); provenance (raw provider response retained with content hash; `first_activity` rows point to the artifact); golden fixtures per actor class asserted against canonical and adapters; hard fallback (unwired or failed lookup ⇒ window-censored; manifest records backfilled vs. censored counts).

### 5.4 Exposure states, assignment, and crossover

Mutually exclusive states, determined at index by index-event type crossed with sender code inspection at the index block: `plain_eoa` · `contract_account_4337` · `eoa_7702_via_4337` (UserOp sender bearing the 7702 designator — the v0.8+ native path) · `eoa_7702_direct` (**Descriptive/Target for matched purposes**; returns to primary only given supported delegate decoders, trace-backed attribution with authority-signature validation, or an equivalent documented method) · `mixed_or_transitioning` (rare; reported, excluded from primary cells).

**Assignment policy: index-state assignment.** Exposure assigned at index and retained for the primary analysis. Any post-index inconsistent observation — a control's first UserOp, a new delegation or revocation, an Aptos scheme change or key rotation — is **crossover**: retained in the primary index-assigned arm, flagged, and censored only in the **crossover sensitivity table** (primary = index assignment; sensitivity = censor-at-crossover). Time-varying analysis is beyond MVP.

### 5.5 Matching protocol (complete)

- **Estimand:** descriptive association, among matchable treated addresses, between exposure state at index and D1/D7/D30 retention vs. matched plain-key controls (ATT-style, observational).
- **Design:** 1:1, without replacement, same window.
- **Exact:** chain; index ISO week; **index weekday** (exact UTC calendar date preferred where cell sizes permit; contract-owned toggle, manifest-recorded).
- **Coarsened:** activation-age band `{window_censored, 0–30d, 31–90d, 91–365d, >365d}` at index; day-0 qualifying-activity count band `{1, 2–3, 4–10, >10}`; **`day_0_network_cost_attributed`** band (per-chain quartiles per run, manifest-recorded) — the network cost attributable to the address's day-0 qualifying activity **regardless of who paid** (sender fee for EOAs; `actualGasCost` for UserOps; sponsored cost attributed to the actor on Aptos).
- **Sponsorship is not a matching field** (near-collinear with treatment); it is a within-treated stratification axis, reported.
- **Baseline rule:** every matching variable measured at or before end of index day 0, strictly before outcomes open at D1.
- **Control admission (time-bounded at the candidate index):** eligible when no treated-mode observation **before or at** index; plain/undelegated **at** index; not infrastructure. Screens: `prior_4337` (EntryPoint sender history through index, v0.6 boundary); `prior_7702` (authorization-authority observation through index, via a one-time **Pectra-bounded authorization-authority index** built from a designated bulk source over all type-0x04 tuples, Pectra activation → window end, raw export retained and hashed); `delegated_at_index` (`eth_getCode` designator at the index block). Post-index treated-mode observation is crossover, never an admission failure. Aptos mirrors: authentication history inspected only through the candidate index version.
- **Balance:** standardized mean difference < 0.1 on all matched covariates; failing cells flagged and suppressed; covariate-balance table ships with findings.
- **Unmatched treated:** counted, characterized, excluded, disclosed (the estimand covers the matchable population).
- **Floor:** ≥ 200 matched pairs per published comparison cell (contract-owned knob).
- **Inference:** descriptive rates with bootstrap percentile intervals over matched pairs; no causal or hypothesis-test language. Propensity matching is Stretch, sensitivity-only.

### 5.6 Retention, mathematically

UTC. `day_0` = calendar date of the index event. **Exact-day retention:** D*n* = ≥1 meaningful actor activity (successful, actor-role, non-excluded, per `filter_version`) on `day_0 + n`, n ∈ {1, 7, 30}. The index activity never counts toward outcomes; outcomes begin `day_0 + 1`. Failed activity never qualifies as an outcome. Rolling retention is a Target variant, named *rolling* wherever shipped. Maturity suppression applies.

### 5.7 The delegation-adoption view (secondary, descriptive)

For authorities with an in-window authorization: index at the **authorization event**; measure subsequent **authority-sent** activity (top-level transactions with the authority as sender — structurally attributable), labeled "retention following observed delegation adoption" — a different question from RQ1 and presented as such. **Delegated-but-inactive is an outcome category, not an exclusion.** No matching; manifest-labeled; no causal-adjacent language. Rationale: delegated code executes whenever anything targets the authority, so delegated *executions* cannot be attributed to the authority without implementation-specific decoding — the same evidence bar that moved app attribution to Target.

### 5.8 Limitations (stated up front)

Left-censoring corrected only to rung 2; self-selection mitigated by matching, not eliminated; 7702 delegation is time-varying and reversible (modeled as observations); direct-7702 actor attribution is beyond MVP evidence (hence §5.7); Aptos sponsorship is its own axis, never collapsed into scheme; pre-v0.6 EntryPoint activity is outside the historical screen; address ≠ person, everywhere, always.

## 6. Product scope (MVP / Target / Stretch)

**F1 — Address profile (MVP).** Per (chain, address): activation (§5.3), first observed activity and auth mode, index/exposure fields where applicable, meaningful-activity counts, fees, counterparties, participant roles. *Holdings: Target.*
**F2 — Activity facts (MVP).** Actor, role, activity class, app, success, meaningfulness, exclusion reason, filter version; raw and filtered co-reported.
**F3 — Cohort retention (MVP).** Exact-day D1/D7/D30 with maturity suppression.
**F4 — Matched auth-mode comparison (MVP).** RQ1/RQ2 per §5, with balance table, intervals, crossover sensitivity.
**F5 — Segmentation (Target).** Demoted: no longer serves the matched study; the observational design carries the data-science signal.
**F6 — Coordination similarity (Stretch).** Blocking, suppression lists, per-signal scores, reason codes, a strictness threshold (not "precision").
**F7 — Serving (MVP: Streamlit with manifest labels + coverage/freshness panel; Target: FastAPI read API).**
**F8 — Observability asymmetry report (MVP, descriptive).** Aptos creation evidence (write-set-created core resources; creator ≠ owner recorded; coverage stated) vs. Ethereum EOAs' constructed absence of creation events.
**F9 — Delegation-adoption view (MVP, descriptive).** §5.7.
**F10 — Trace-backed app attribution (Target).** EntryPoint bundle traces → per-UserOp execution subtree → first external app call with confidence and reason; `multi_app` for ambiguous; on delivery, matching upgrades under a new `matching_protocol_version`.

## 7. Architecture

**Layering (MVP):** `raw_*` (provider-shaped payloads + provenance + content hashes) → `staging_*` (typed, parser-versioned) → `activity_fact` → features/cohorts → `analytics_runs`. Decoder bugs are repaired by replaying staging from raw under a new parser version — never by re-fetching a provider.

**7.1 Ethereum ingestion (MVP; finalized-tag only — optimistic-plus-reconcile is Target, documented).** Streams, each with its own watermark and interval coverage: blocks; transactions; block receipts (`effective_gas_price`, `blob_gas_used`, `blob_gas_price`; fees always derived); ERC-20 transfer logs for contract scopes (amounts as raw `NUMERIC(78,0)` + decimals; display derived); **EntryPoint stream** — registry-driven (below), staging as three tables joined on `user_op_hash`: `user_operation(hash, sender, paymaster, nonce, success, actual_gas_cost, actual_gas_used)` from `UserOperationEvent`; `account_deployment(hash, sender, factory)` from `AccountDeployed`; `ignored_init_code(hash, sender, unused_factory)` from `IgnoredInitCode`; plus `EIP7702AccountInitialized` (v0.9-emitting) in the version-aware model — factory is never manufactured from the wrong event; **7702 stream** — type-0x04 transactions, each authorization tuple parsed and its authority recovered by signature, stored as time-varying **delegation observations**; the **Pectra-bounded authorization-authority index** (§5.5) as a one-time bulk build with retained provenance; **first-activity lookups** per §5.3; `eth_getCode` snapshots at index blocks for state determination and screening.

**EntryPoint registry.** `entrypoint_registry(chain_id, version, address, deployment_block, abi_hash, code_hash, active_from, active_to, source)` — a **pinned, checked-in snapshot** (demo CI depends only on the snapshot; a separate explicit update-and-verify command compares it to the official release source; deterministic demo mode never touches a live feed). The dataset contract pins a **registry version**, never a version list; at the current pin the registry spans v0.6–v0.9.

**7.2 Aptos ingestion (MVP: fullnode REST; Target: Rust Indexer SDK on the gRPC Transaction Stream).** User transactions by version with events and write-set provenance into raw; staging extracts sender, success, gas, entry function, and the decomposed auth fields; per-stream watermark; idempotent by construction (deterministic finality — a headline design contrast, not an omission).

**7.3 Migrations (MVP).** Ordered, numbered, transactional plain-SQL migrations with `schema_migrations(version, checksum, applied_at)`, plus an **upgrade test** migrating a preserved early-stage volume to head. Clean-install testing is necessary, not sufficient.

**7.4 Authentication decomposition (MVP, Aptos).** `sender_auth_scheme`, `transaction_authenticator_kind`, `is_sponsored`, `fee_payer_address`, `secondary_signer_count`, `key_rotation_observed` — sponsorship and scheme never one enum. Ethereum attribution rules are structural: the UserOperation `sender` is the actor (never the bundler); the authorization `authority` is the delegating party (never assumed to be the outer sender); fee payers recorded, not credited.

**7.5 Coverage as intervals (MVP).** `stream_coverage(chain, stream_name, scope_key, parser_version, start_position, end_position, status, row_count, completed_at, error)`; **completed-empty** (scanned, zero events) is distinct from unscanned or failed; gaps are rows, not absences.

**7.6 Run manifests and the publish gate (MVP).** Manifest fields: run id, dataset-contract / filter / matching-protocol / registry versions, parser versions, per-chain boundaries, source completeness and row counts, backfilled-vs-censored activation counts, source-conflict counts, screen-disclosure counts, code revision, model parameters, random seed, timestamp. **A run publishes only over the intersection of gap-free completed intervals across all required streams**, records that intersection, and refuses otherwise. Every chart carries its run label.

**7.7 Demo and live modes (MVP).** *Demo:* checked-in deterministic fixtures (including the registry snapshot and bulk-index fixture), zero external APIs, one command yields a **populated** dashboard — the CI target and reviewer path. *Live:* keys required; a failing stream makes the ingester unhealthy; readiness gates on minimum completed ranges; stale analytics are labeled. "Green" = demo CI passes **and** live health is honest.

**7.8 Storage.** PostgreSQL throughout MVP. ClickHouse (self-hosted/embedded, zero cost) is Stretch on a real aggregate-scan trigger, with a same-query before/after benchmark as the deliverable.

## 8. Adversarial battlefield (v3.2)

**"Your population is whoever showed up"** — the contract defines arms, screens, and roles; receipt never activates. **"First-seen is not onboarding"** — the word is gone; claims sit on rungs 1–2; activation is a covariate with canonical per-class definitions and a censored fallback. **"Your clocks disagree"** — one index clock; activation demoted; matching on index week+weekday. **"Your arms overlap"** — mutually exclusive states; index-state assignment; crossover sensitivity; the native 7702-via-4337 path modeled explicitly. **"You can't attribute direct-7702 actions"** — agreed; demoted to the descriptive adoption view with authority-sent outcomes and inactivity as an outcome. **"Your control screen deletes your crossover"** — admission bounded at index; three screens through the boundary including the Pectra-bounded prior-7702 index. **"Your matching variables aren't observable for treatment"** — app category removed; all fields observable for every arm at day 0; trace attribution is a versioned Target upgrade. **"Your streams are misaligned or gapped"** — interval coverage plus the intersection gate makes misalignment a refused publish. **"Your sources disagree or rot"** — canonical precedence, retained raw artifacts, conflict flags; registry as pinned snapshot with an explicit verify command. **"Activity metrics are inflated"** — filter-versioned facts, raw and filtered co-reported. **"This is surveillance"** — address-level, aggregate, no identity resolution; coordination is Stretch and labeled similarity. **"This exists already"** — a matched, censoring-aware, lineage-gated, cross-model auth-mode study with open methodology does not meaningfully exist; the open methodology is the differentiator.

## 9. Roadmap

Phases P1–P4 (deterministic vertical slice; Ethereum correctly scoped; Aptos correctly scoped; study assembly and analytics) decompose into the companion build plan — fixture-first (decode recorded fixtures, then wire live), one green step per day, 37 steps per the v2.1 prompt amendment. P5 Stretch: trace attribution (F10), Rust processor swap, ClickHouse benchmark, coordination, segmentation, holdings, propensity sensitivity. Future work, in order: (1) **Robinhood Chain RWA extension (pinned July 25, 2026)** — a gated post-MVP study of tokenized-equity holder behavior on Robinhood's Arbitrum-Orbit L2, specified in `Strata_Extension_Robinhood_Chain_RWA.md`; it likely pulls the ClickHouse item forward with it. (2) Extend the account→resource→object spectrum to a fully object-centric chain (Sui), where the indexer pattern and the study design travel intact.

## 10. Open questions (genuinely open)

Window placement (pinned at build start); the 200-pair floor against observed AA volumes (contract-owned); bulk-vs-RPC for the large historical scans (interface-stable either way); the exact-date matching toggle default.

## Appendix — Terms with contract force

**Activation** (canonical earliest event per class) · **Index event / `index_date`** (study entry; the outcome clock's origin) · **Exposure state** (mutually exclusive, assigned at index) · **Crossover** (post-index inconsistent observation; sensitivity-censored only) · **Adoption view** (authorization-indexed descriptive analysis; inactivity is an outcome) · **Actor / passive participant** (receipt never activates) · **Meaningful activity** (filter-versioned; failures excluded) · **`day_0_network_cost_attributed`** (payer-independent day-0 cost) · **Window-censored** (activation unresolved; claims restricted; banded) · **Completed-empty** (scanned interval, zero events — valid) · **Registry snapshot** (pinned, checked-in; verified by explicit command) · **Run manifest** (the binding between every published number and the exact data, code, and parameters that produced it).
