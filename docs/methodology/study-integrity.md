# Study integrity

Strata estimates descriptive associations among matchable addresses. It does
not estimate a causal effect.

- The validated dataset-contract object is the only source of study windows,
  scopes, exclusions, populations, and version pins. Do not add ad hoc scope or
  window arguments outside explicitly labeled diagnostics, and do not copy
  magic study constants into other code.
- Matching is 1:1 without replacement under the declared exact and coarsened
  fields. Every matching variable is available by the end of index day 0.
- Published matched cells must satisfy the contract-owned pair floor and balance
  rule. A balance failure, sub-floor cell, or immature cell is absent with an
  explanation, never zeroed.
- Unmatched treated addresses remain counted and disclosed; they are not silently
  folded into the matched estimand.
- Fixture data never produces empirical findings.
- Findings eligibility is derived from `analytics_runs`, never asserted by hand.
  Every empirical number is tied to a qualifying live run ID and its manifest.
- Address is not person. Perform no identity resolution, make no ownership
  claims, and make no person-level behavioral or experience claim.
- Post-MVP and roadmap items are outside active scope until the human explicitly
  authorizes them after their stated gates. Repository gaps are not authority to
  build ahead.

Self-selection, censoring, coverage boundaries, matchability, crossover, and
source limitations remain visible wherever results are interpreted.
