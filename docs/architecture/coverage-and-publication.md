# Coverage, manifests, and publication

Coverage and lineage are publication prerequisites. The canonical PRD supplies
the required streams, scopes, version pins, and analytical semantics.

## Interval coverage

`stream_coverage` records scanned intervals by chain, stream, scope, and parser
version. Status has evidence-bearing meaning:

- `completed` means the interval was scanned and produced the recorded rows.
- `completed-empty` means the interval was scanned successfully and produced
  zero events; it is valid coverage.
- `failed` means the attempted interval did not complete and records its error.
- Unscanned space is not inferred to be complete. Gaps are explicit rows or
  mechanically identified interval gaps, never treated as harmless absence.

## Run and publish boundary

An analytics run may publish only over the recorded intersection of gap-free
completed intervals for every required stream. If that intersection is missing
or insufficient, the run records `status=refused` with a reason and leaves no
partial published state. Refused runs remain auditable.

Every published result is bound to a versioned run manifest containing the
validated contract and filter versions, matching and registry versions,
per-stream parser versions, source boundaries and completeness, row and
censoring counts, source conflicts, code revision, model parameters, random
seed, and timestamp as applicable.

Dashboards and result documents never combine run boundaries. Every chart shows
its run label; coverage and freshness are visible. Stale analytics are labeled,
and incomplete coverage cannot be presented as current or green.
