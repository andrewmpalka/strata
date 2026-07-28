-- Day 2 sentinel: a populated relation proves migration 001 committed.
CREATE TABLE strata_migration_sentinel (
    singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
    message TEXT NOT NULL
);

INSERT INTO strata_migration_sentinel (message)
VALUES ('migration engine ready');
