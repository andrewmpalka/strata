# Provider integration

Provider work must preserve evidence, source roles, and honest health. The
canonical PRD determines chain semantics and required streams.

- A canonical source establishes analytical truth for its declared universe.
  Adapters and bulk sources may validate or accelerate work, but they are
  different universes and never silently substitute for the canonical source.
- Source disagreements retain both raw artifacts, record provenance and content
  hashes, flag the conflict, and follow the declared precedence.
- Unwired capabilities, exhausted lookups, and failed required streams surface
  as censored, refused, or unhealthy according to the contract. Never fabricate
  provider data, coverage, health, or success.
- Demo mode uses checked-in deterministic artifacts and makes zero external API
  calls, including registry-verification and other on-demand paths.
- Live integrations retain replayable raw responses before typed derivation and
  advance watermarks only after durable writes.
- When source capabilities vary, detect and record implemented capabilities
  explicitly. Do not infer success from an endpoint name or silently downgrade.
- Bound concurrency, respect rate limits, retry only transient failures within a
  finite budget, and make every retry visible. Authentication, permission,
  malformed-data, and other non-transient failures stop loudly.

Do not document or simulate provider implementations that do not yet exist in
the repository.
