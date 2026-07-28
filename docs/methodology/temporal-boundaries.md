# Temporal boundaries, matching, and retention

The validated dataset contract and canonical PRD define the actual windows and
knobs. No ad hoc boundary may replace them.

## Three clocks

- `activation_date` is canonical earliest chain activity for the actor class and
  is a censoring-correction covariate.
- `index_date` is the declared study-entry event.
- Outcomes are measured from `index_date`, never from activation.

Canonical Ethereum EOA activation walks ascending account history, filters
`from == address`, and continues until the first sent transaction. Exhausted
provider limits without a sent transaction yield `window_censored`, not an
incoming-transfer activation.

## Screening and crossover

Control screens evaluate history only through the candidate index, including
treated-mode history and state at that boundary. Post-index adoption or mode
change is crossover, not an admission failure. Primary analysis retains the
index-assigned arm; only the declared crossover sensitivity censors at crossover.

Every matching variable is measured at or before the end of index day 0.
Nothing observed after that cutoff may enter matching.

## Outcomes and maturity

Retention is exact-day UTC: D*n* requires qualifying activity on
`day_0 + n`. The index event never counts toward an outcome, and failed activity
never qualifies. Outcomes begin on day 1.

A cohort cell exists only after it reaches the required age in the observation
window. Immature cells are absent with their maturity explanation, never
reported as zero.
