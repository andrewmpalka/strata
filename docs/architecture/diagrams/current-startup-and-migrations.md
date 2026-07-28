# UML Sequence — current startup and migration protocol

This sequence explains the implemented application startup path, including
bounded database retries, explicit migration bootstrap, checksum verification,
transactional migration execution, sentinel creation, and visible failures.

**Audience:** application, database, operations, and reliability engineers who
need to understand startup ordering and failure semantics.

## How to read this diagram

Time moves from top to bottom. Solid arrows are calls or writes; dashed arrows
are returns or reported outcomes. `loop` marks bounded retry behavior and `alt`
marks mutually exclusive success and failure paths.

```mermaid
sequenceDiagram
    actor Operator as EXTERNAL Operator
    participant Compose as CURRENT Docker Compose
    participant App as CURRENT Strata application
    participant Config as CURRENT Environment configuration
    participant DB as CURRENT PostgreSQL
    participant Resolver as CURRENT Migration path resolver
    participant Runner as CURRENT Migration runner
    participant Files as CURRENT Migration files

    Operator->>Compose: Start strata_ci PostgreSQL and application
    Compose->>DB: Start PostgreSQL container and wait for health
    Compose->>App: Start python -m strata.main
    App->>Config: Load required environment configuration

    alt Configuration is valid
        Config-->>App: Return redacted application and database settings
        loop Bounded retry budget for transient failures
            App->>DB: Attempt PostgreSQL connection
            alt Database is reachable
                DB-->>App: Return open connection
            else Transient connection failure
                DB-->>App: Return retryable connection error
                App->>App: Log attempt and wait with bounded backoff
            else Fatal database rejection
                DB-->>App: Return fatal rejection
                App-->>Operator: Report fatal database connection failure and exit 3
            end
        end
        alt Retry budget expires
            App-->>Operator: Report connection timeout and exit 4
        else Connection succeeds within budget
            App->>Resolver: Resolve explicit container override or source-checkout-relative migration path
            Resolver-->>App: Return /srv/migrations or repository migration directory
            App->>Runner: Run migrations on the startup database connection
            Runner->>Files: Discover bootstrap and numbered SQL in version order
            Files-->>Runner: Return UTF-8 SQL and SHA-256 checksums
            Runner->>DB: Acquire session advisory lock

            alt Migration ledger is absent
                Runner->>DB: Bootstrap schema_migrations only
                DB-->>Runner: Commit ledger creation
            else Migration ledger exists
                DB-->>Runner: Return existing version and checksum rows
            end

            Runner->>DB: Read applied migration ledger
            DB-->>Runner: Return applied versions and checksums
            Runner->>Runner: Verify every applied file checksum and layout

            alt Checksum, ledger, or layout validation fails
                Runner-->>App: Return migration failure
                App-->>Operator: Report migration failure and exit 5
            else History is valid
                loop Each pending numbered migration
                    Runner->>DB: Execute SQL and ledger insert in runner-owned transaction
                    alt Migration executes successfully
                        DB-->>Runner: Commit migration and checksum atomically
                    else Migration execution fails
                        DB-->>Runner: Roll back migration and ledger insert
                        Runner-->>App: Return migration execution failure
                        App-->>Operator: Report migration failure and exit 5
                    end
                end
                Note over Runner,DB: Migration 001 creates and populates the migration-engine sentinel
                Runner->>DB: Release advisory lock
                DB-->>Runner: Confirm lock release
                Runner-->>App: Return applied versions or no-op at head
                App->>DB: Verify database handshake
                DB-->>App: Return database, user, and server version
                App-->>Operator: Report connected and remain healthy until shutdown
            end
        end
    else Configuration is invalid
        Config-->>App: Return configuration error
        App-->>Operator: Report configuration error and exit 2
    end
```

## Legend and notation

- `CURRENT` participants are implemented.
- `EXTERNAL` identifies the operator outside the application boundary.
- `alt` is a conditional branch; `loop` repeats only within its named bound.
- SHA-256 is the Secure Hash Algorithm used to bind applied ledger rows to
  migration file bytes.
- A dashed return arrow communicates a result or failure; text, not color,
  identifies the outcome.

## Current versus target

The entire sequence is current. It ends at a healthy, idle migration baseline;
it does not continue into provider ingestion, parsing, analytics, publication,
or dashboard serving.

## Limitations and non-goals

This sequence compresses advisory-lock cleanup and SQL discovery validation for
readability. It is not a substitute for the exact exit handling, exception
types, or migration tests, and it does not address the documented wheel-runtime
migration-discovery limitation.

## Source traceability

| Diagram claim | Status | Source |
|---|---|---|
| Compose starts PostgreSQL before the application | Current | `docker-compose.yml` |
| Configuration errors exit visibly | Current | `src/strata/config.py`, `src/strata/main.py`, `tests/unit/test_config_and_retry.py` |
| Transient connections retry within a budget; fatal rejection and timeout differ | Current | `src/strata/db.py`, `integration_tests/postgres/test_connection.py` |
| Migration path uses an explicit container override or source-checkout-relative resolution | Current | `Dockerfile`, `src/strata/main.py`, [migration contract](../migrations.md) |
| Bootstrap creates only the ledger when absent | Current | `migrations/bootstrap.sql`, `src/strata/migrations.py`, `integration_tests/migrations/test_migrations.py` |
| Applied migrations are checksum-verified and pending migrations are transactional | Current | `src/strata/migrations.py`, [migration contract](../migrations.md) |
| Migration 001 creates and populates the sentinel | Current | `migrations/001_migration_sentinel.sql`, `scripts/ci.sh` |
| Startup reports connected and remains running | Current | `src/strata/main.py`, `scripts/ci.sh` |
