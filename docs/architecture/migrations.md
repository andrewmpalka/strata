# Migration and schema contract

This is the canonical repository contract for PostgreSQL migrations. Product and
study semantics remain governed by the canonical PRD.

## File and ledger rules

- A dedicated `migrations/bootstrap.sql` creates only
  `schema_migrations(version, checksum, applied_at)`. Its repeatable ledger
  creation is the sole bootstrap mechanism; never use
  `CREATE TABLE IF NOT EXISTS` as a numbered-migration mechanism.
- Numbered migrations are UTF-8 plain SQL named `NNN_name.sql`, begin at `001`,
  and are discovered and applied in numeric version order.
- The runner owns transaction boundaries. A numbered migration and its ledger
  insert commit atomically, exactly once; migration SQL must not issue transaction
  control.
- The ledger records the SHA-256 checksum of each applied file. A missing applied
  file, invalid ledger row, or checksum mismatch aborts loudly.
- Never edit an applied migration. Create a new numbered migration for every
  correction.
- Clean-install coverage is necessary but insufficient. A real upgrade test must
  restore an older supported snapshot and migrate it to head.

The current source checkout resolves migrations from the installed module
location, independent of the current working directory. The container sets the
explicit `STRATA_MIGRATIONS_DIR=/srv/migrations` override. Those are the
supported resolution paths; do not silently search arbitrary working
directories.

## Schema representations

- Addresses use `chain`, `address_bytes BYTEA`, and `address_display TEXT`, with
  chain-specific byte-length checks: Ethereum is 20 bytes and Aptos is 32 bytes.
  Never cross-chain-pad addresses.
- Token and cost quantities use authoritative raw `NUMERIC(78,0)` values plus
  decimals. Display values are derived and never authoritative.

Migration review must protect existing bytes, checksums, ordering, transaction
ownership, and upgrade behavior.
