# Strata — convenience targets.
#
# All Compose lifecycle and destructive operations delegate to scripts/ci.sh,
# which pins `--project-name strata_ci --env-file .env.demo` and owns the
# destructive-cleanup guard. Checkout-local unit and documentation checks may
# invoke pytest directly. No target may call `docker compose down -v` directly.
# No target may reference strata_live or live volumes.

.PHONY: help green up down clean verify test test-unit test-integration test-e2e test-docs logs psql fg

help:
	@echo "help             - show available targets"
	@echo "green            - clean isolated state, build, verify populated, run tests"
	@echo "up               - build and start the strata_ci stack (detached)"
	@echo "fg               - build and start the strata_ci stack in the foreground"
	@echo "verify           - assert postgres healthy and app logged 'connected'"
	@echo "test             - run the complete test suite inside the app image"
	@echo "test-unit        - run the fast checkout-local test suite"
	@echo "test-integration - start the disposable stack and run PostgreSQL tests"
	@echo "test-e2e         - run the full guarded green path"
	@echo "test-docs        - run the public-guidance graph tests"
	@echo "down             - stop the strata_ci stack, preserving volumes"
	@echo "clean            - guarded teardown of strata_ci containers AND volumes"
	@echo "logs             - show strata_ci logs"
	@echo "psql             - open psql against the demo database"

green:
	./scripts/ci.sh green

up:
	./scripts/ci.sh up

verify:
	./scripts/ci.sh verify

test:
	./scripts/ci.sh test

test-unit:
	python -m pytest tests

test-integration:
	./scripts/ci.sh up
	./scripts/ci.sh test-integration

test-e2e:
	./scripts/ci.sh green

test-docs:
	python -m pytest tests/unit/test_guidance_graph.py

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
