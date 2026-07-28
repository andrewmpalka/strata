# Testing and the green definition

Repository work is complete only when both parts of green are honest:

1. Demo CI starts the isolated stack, verifies the expected populated state from
   checked-in deterministic fixtures, makes zero external API calls, and passes
   all required tests.
2. Every implemented live component either works or visibly reports unhealthy.
   Silent degradation, swallowed errors, fabricated health, skipped required
   suites, and empty-but-serving output are failures.

## Verification layers

- `./scripts/harness unit` runs the fast, database-free suite.
- `./scripts/harness integration` starts the disposable stack and runs the
  PostgreSQL integration suite.
- `./scripts/ci.sh green` is the sanctioned guarded clean build, populated-state
  verification, and complete test run.
- `make test` runs the complete suite in the current Compose application image.

Fixture-first development decodes recorded artifacts before live source wiring.
Demo verification must remain deterministic and network-isolated, including
on-demand registry checks.

Migration work requires clean-install coverage and a genuine upgrade test that
restores an older supported snapshot and migrates it to head. A green clean
installation alone does not prove upgrades.

After implementation, review adversarially: exercise named risks, failure paths,
boundary conditions, and honest-health behavior. Never weaken an assertion,
guard, required suite, or publication gate to obtain green. Do not declare
completion until focused tests and the required isolated green check pass, and
leave the repository green.
