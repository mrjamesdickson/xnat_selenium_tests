#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=${SCRIPT_DIR%/*}
MANAGER="$SCRIPT_DIR/manage_xnat_test_env.sh"

BASE_URL=${XNAT_BASE_URL:-http://localhost}
USERNAME=${XNAT_USERNAME:-admin}
PASSWORD=${XNAT_PASSWORD:-admin}
BROWSER=${BROWSER:-chrome}
PYTEST=${PYTEST_BIN:-pytest}

should_use_mock() {
    local flag=${1:-}
    case "$flag" in
        1|true|TRUE|True|yes|YES|Yes|on|ON|On)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

RUN_MOCK=false
if should_use_mock "${XNAT_USE_MOCK:-}"; then
    RUN_MOCK=true
elif ! command -v docker >/dev/null 2>&1; then
    echo "Docker not available; falling back to the in-process mock XNAT server."
    RUN_MOCK=true
fi

TEARDOWN=${TEARDOWN_ON_EXIT:-true}
WAIT_TIMEOUT=${WAIT_TIMEOUT:-300}
SLEEP_INTERVAL=5

stack_started=false

run_pytest() {
    local base_url=$1
    shift
    echo "Running pytest against $base_url as $USERNAME"
    cd "$PROJECT_ROOT"
    local base_cmd=("$PYTEST" --base-url "$base_url" --username "$USERNAME" --password "$PASSWORD" --browser "$BROWSER" "$@")
    if [ -z "${PYTHONPATH:-}" ]; then
        PYTHONPATH="src"
    fi
    PYTHONPATH="$PYTHONPATH" "${base_cmd[@]}"
}

if [ "$RUN_MOCK" = "true" ]; then
    export XNAT_USE_MOCK=1
    BASE_URL=mock://xnat
    run_pytest "$BASE_URL"
    exit 0
fi

cleanup() {
    if [ "$TEARDOWN" = "true" ] && [ "$stack_started" = "true" ]; then
        echo "Stopping XNAT test environment..."
        if ! "$MANAGER" down; then
            echo "Warning: unable to stop XNAT stack" >&2
        fi
    elif [ "$TEARDOWN" != "true" ] && [ "$stack_started" = "true" ]; then
        echo "Leaving XNAT stack running (TEARDOWN_ON_EXIT=false)."
    fi
}

wait_for_xnat() {
    local deadline shell_now
    deadline=$(( $(date +%s) + WAIT_TIMEOUT ))
    echo "Waiting for XNAT to become available at $BASE_URL (timeout: ${WAIT_TIMEOUT}s)"
    until curl --fail --silent --head "$BASE_URL" >/dev/null 2>&1; do
        shell_now=$(date +%s)
        if [ "$shell_now" -ge "$deadline" ]; then
            echo "XNAT did not become ready within ${WAIT_TIMEOUT}s" >&2
            return 1
        fi
        sleep "$SLEEP_INTERVAL"
    done
}

trap cleanup EXIT

echo "Starting XNAT test environment via docker compose..."
"$MANAGER" up
stack_started=true

wait_for_xnat

run_pytest "$BASE_URL"
