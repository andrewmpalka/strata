# Strata — convenience targets.
#
# Every CI target delegates to scripts/ci.sh, which pins
# `--project-name strata_ci --env-file .env.demo` and owns the destructive-
# cleanup guard. Do not add a target that calls `docker compose down -v`
# directly, and do not add a target that can name a strata_live volume.

.PHONY: help green up down clean verify test logs psql fg

help:
	@echo "green   - clean isolated state, build, verify populated, run tests"
	@echo "up      - build and start the strata_ci stack (detached)"
	@echo "fg      - build and start the strata_ci stack in the foreground"
	@echo "verify  - assert postgres healthy and app logged 'connected'"
	@echo "test    - run the test suite inside the app image"
	@echo "down    - stop the strata_ci stack, preserving volumes"
	@echo "clean   - guarded teardown of strata_ci containers AND volumes"
	@echo "logs    - show strata_ci logs"
	@echo "psql    - open psql against the demo database"

green:
	./scripts/ci.sh green

up:
	./scripts/ci.sh up

verify:
	./scripts/ci.sh verify

test:
	./scripts/ci.sh test

down:
	./scripts/ci.sh down

clean:
	./scripts/ci.sh clean

logs:
	./scripts/ci.sh logs

psql:
	./scripts/ci.sh psql

# The documented manual, non-destructive foreground startup.
fg:
	docker compose --project-name strata_ci --env-file .env.demo up --build
