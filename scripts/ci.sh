#!/usr/bin/env bash
#
# Strata CI entrypoint — the ONLY sanctioned path for a clean full run, and the
# only sanctioned path for destructive cleanup.
#
# Every command here is pinned to:
#     docker compose --project-name strata_ci --env-file .env.demo
#
# Do not invoke `docker compose down -v` by hand. Live services run under the
# project name strata_live, and their volumes may hold weeks of rate-limited
# backfill that no rerun can reproduce. The guard below is the safety interlock;
# bypassing, weakening, or temporarily disabling it is prohibited.
#
# Usage: scripts/ci.sh {green|clean|up|down|test|test-integration|logs|verify|psql}

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# --- Pinned CI identity. Never parameterise these. -------------------------
readonly CI_PROJECT_NAME="strata_ci"
readonly CI_ENV_FILE=".env.demo"
readonly ALLOWED_DATABASES=("strata_demo" "strata_test")
readonly VERIFY_TIMEOUT_SECONDS=30

log()  { printf '\033[1;34m[ci]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[ci]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[ci] FATAL:\033[0m %s\n' "$*" >&2; exit 1; }

[[ -f "$CI_ENV_FILE" ]] || die "$CI_ENV_FILE not found in $REPO_ROOT"

# Read a single key from the env file without sourcing it, so a malformed or
# hostile line cannot execute.
env_file_value() {
  local key="$1"
  sed -n "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*//p" "$CI_ENV_FILE" \
    | tail -n 1 \
    | sed -e 's/[[:space:]]*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'\$/\1/"
}

DEMO_MODE_VALUE="$(env_file_value DEMO_MODE)"
POSTGRES_DB_VALUE="$(env_file_value POSTGRES_DB)"

compose() {
  docker compose --project-name "$CI_PROJECT_NAME" --env-file "$CI_ENV_FILE" "$@"
}

# --- Destructive-cleanup guard (safety-critical) ---------------------------
#
# Refuses to delete volumes unless all three conditions hold:
#   1. the compose project name starts with strata_ci
#   2. DEMO_MODE=true
#   3. the database is strata_demo or strata_test
assert_destruction_is_safe() {
  local project="$CI_PROJECT_NAME"

  # Honour an externally exported project name if one is set, precisely so that
  # an operator who exported strata_live cannot have it silently ignored here.
  if [[ -n "${COMPOSE_PROJECT_NAME:-}" ]]; then
    project="$COMPOSE_PROJECT_NAME"
  fi

  [[ "$project" == strata_ci* ]] || die \
    "refusing destructive cleanup: project name '$project' does not start with 'strata_ci'."

  [[ "$DEMO_MODE_VALUE" == "true" ]] || die \
    "refusing destructive cleanup: DEMO_MODE in $CI_ENV_FILE is '$DEMO_MODE_VALUE', not 'true'."

  local allowed=0
  for db in "${ALLOWED_DATABASES[@]}"; do
    [[ "$POSTGRES_DB_VALUE" == "$db" ]] && allowed=1
  done
  (( allowed == 1 )) || die \
    "refusing destructive cleanup: database '$POSTGRES_DB_VALUE' is not one of: ${ALLOWED_DATABASES[*]}."

  # Belt and braces: never touch a volume whose name suggests live data.
  if compose config --volumes 2>/dev/null | grep -qi 'live'; then
    die "refusing destructive cleanup: a project volume name contains 'live'."
  fi

  log "destruction guard passed (project=$project demo_mode=$DEMO_MODE_VALUE db=$POSTGRES_DB_VALUE)"
}

cmd_clean() {
  assert_destruction_is_safe
  log "removing $CI_PROJECT_NAME containers and volumes"
  compose down -v --remove-orphans
}

cmd_down() {
  log "stopping $CI_PROJECT_NAME (volumes preserved)"
  compose down --remove-orphans
}

cmd_up() {
  log "building and starting $CI_PROJECT_NAME"
  compose up --build -d --wait --wait-timeout 180
}

# Assert the stack reached the expected POPULATED-for-this-increment state.
# At Day 2 that includes a checksummed 001 ledger row and sentinel data.
cmd_verify() {
  local pg_container app_container
  pg_container="$(compose ps -q postgres)"
  app_container="$(compose ps -q app)"
  [[ -n "$pg_container" ]] || die "postgres container is not running"
  [[ -n "$app_container" ]] || die "app container is not running"

  local health
  health="$(docker inspect -f '{{.State.Health.Status}}' "$pg_container")"
  [[ "$health" == "healthy" ]] || die "postgres health is '$health', expected 'healthy'"
  log "postgres is healthy"

  # Match a whole log line so a message like "not connected" can never pass.
  # Capture first: with pipefail, grep -q may close its input after a match and
  # turn Compose's resulting SIGPIPE into a false verification failure.
  # Compose considers a service with no healthcheck ready as soon as its
  # process is running, which can precede this log by a few milliseconds.
  local app_logs state deadline
  deadline=$((SECONDS + VERIFY_TIMEOUT_SECONDS))
  while true; do
    state="$(docker inspect -f '{{.State.Status}}' "$app_container")"
    [[ "$state" == "running" ]] || die "app state is '$state', expected 'running'"

    app_logs="$(compose logs --no-color app)"
    if grep -Eq '(^|[[:space:]])connected$' <<<"$app_logs"; then
      break
    fi
    if (( SECONDS >= deadline )); then
      warn "app logs did not contain the expected 'connected' line:"
      printf '%s\n' "$app_logs" >&2
      die "app never reported a successful database connection within ${VERIFY_TIMEOUT_SECONDS}s"
    fi
    sleep 1
  done
  log "app logged 'connected'"

  local migration_state
  migration_state="$(
    compose exec -T postgres sh -c \
      'PGPASSWORD="$POSTGRES_PASSWORD" exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "$1"' \
      sh \
      "SELECT count(*) || ':' || min(version) || ':' || min(length(checksum))
       FROM schema_migrations"
  )"
  [[ "$migration_state" == "1:1:64" ]] || die \
    "migration ledger state is '$migration_state', expected '1:1:64'"
  log "migration ledger contains checksummed version 001"

  local sentinel
  sentinel="$(
    compose exec -T postgres sh -c \
      'PGPASSWORD="$POSTGRES_PASSWORD" exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "$1"' \
      sh \
      "SELECT message FROM strata_migration_sentinel WHERE singleton"
  )"
  [[ "$sentinel" == "migration engine ready" ]] || die \
    "migration sentinel is '$sentinel', expected 'migration engine ready'"
  log "migration sentinel is populated"

  # An app that logged 'connected' and then crashed is not green.
  local restarts
  restarts="$(docker inspect -f '{{.RestartCount}}' "$app_container")"
  [[ "$restarts" == "0" ]] || die "app restarted $restarts time(s); startup is not stable"

  log "verify passed"
}

run_pytest() {
  # STRATA_REQUIRE_DB=1 turns a skipped integration test into a failure, so a
  # green suite cannot mean "the database tests never ran".
  compose run --rm --no-deps \
    -e STRATA_REQUIRE_DB=1 \
    app python -m pytest "$@" -v
}

cmd_test() {
  log "running the complete test suite inside the app image"
  run_pytest tests integration_tests
}

cmd_test_integration() {
  log "running the integration test suite inside the app image"
  run_pytest integration_tests
}

cmd_logs() { compose logs "$@"; }

cmd_psql() {
  # POSTGRES_INITDB_ARGS enforces SCRAM even for local connections. Reuse the
  # credential already present inside the container without expanding or
  # printing it in this host-side process.
  compose exec postgres sh -c \
    'PGPASSWORD="$POSTGRES_PASSWORD" exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"' \
    sh "$@"
}

# The full green check from an isolated clean state.
cmd_green() {
  cmd_clean
  cmd_up
  cmd_verify
  cmd_test
  log "GREEN: isolated clean build came up populated and the test suite passed"
}

case "${1:-green}" in
  green)  cmd_green ;;
  clean)  cmd_clean ;;
  up)     cmd_up ;;
  down)   cmd_down ;;
  verify) cmd_verify ;;
  test)   cmd_test ;;
  test-integration) cmd_test_integration ;;
  logs)   shift; cmd_logs "$@" ;;
  psql)   shift; cmd_psql "$@" ;;
  *)      die "unknown command '$1' (expected: green|clean|up|down|verify|test|test-integration|logs|psql)" ;;
esac
