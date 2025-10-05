#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=${SCRIPT_DIR%/*}
DOCKER_BIN=${DOCKER_BIN:-docker}
IMAGE_NAME=${XNAT_TEST_IMAGE:-xnat-selenium-tests}
SHM_SIZE=${DOCKER_SHM_SIZE:-2g}
PYTEST_ARGS=("$@")

if ! command -v "$DOCKER_BIN" >/dev/null 2>&1; then
    echo "Docker is required to build and run the test container." >&2
    exit 1
fi

BUILD_ARGS=("$DOCKER_BIN" build --pull -t "$IMAGE_NAME" -f "$PROJECT_ROOT/Dockerfile" "$PROJECT_ROOT")
if [ "${DOCKER_BUILD_NO_CACHE:-}" = "1" ] || [ "${DOCKER_BUILD_NO_CACHE:-}" = "true" ]; then
    BUILD_ARGS+=(--no-cache)
fi

echo "Building Docker image '$IMAGE_NAME'..."
"${BUILD_ARGS[@]}"

declare -a DOCKER_ENV
PRESERVE_VARS=(
    XNAT_BASE_URL
    XNAT_USERNAME
    XNAT_PASSWORD
    XNAT_HEADLESS
    XNAT_USE_MOCK
    SELENIUM_REMOTE_URL
    BROWSER
    PYTEST_ADDOPTS
)

for var in "${PRESERVE_VARS[@]}"; do
    if [ -n "${!var:-}" ]; then
        DOCKER_ENV+=("-e" "$var=${!var}")
    fi
done

if [ -n "${NO_PROXY:-}" ]; then
    DOCKER_ENV+=("-e" "NO_PROXY=${NO_PROXY}")
fi
if [ -n "${no_proxy:-}" ]; then
    DOCKER_ENV+=("-e" "no_proxy=${no_proxy}")
fi
if [ -n "${HTTPS_PROXY:-}" ]; then
    DOCKER_ENV+=("-e" "HTTPS_PROXY=${HTTPS_PROXY}")
fi
if [ -n "${https_proxy:-}" ]; then
    DOCKER_ENV+=("-e" "https_proxy=${https_proxy}")
fi
if [ -n "${HTTP_PROXY:-}" ]; then
    DOCKER_ENV+=("-e" "HTTP_PROXY=${HTTP_PROXY}")
fi
if [ -n "${http_proxy:-}" ]; then
    DOCKER_ENV+=("-e" "http_proxy=${http_proxy}")
fi

RUN_ARGS=("$DOCKER_BIN" run --rm --shm-size "$SHM_SIZE")
if [ -n "${DOCKER_RUN_EXTRA_ARGS:-}" ]; then
    # shellcheck disable=SC2206
    extra=( ${DOCKER_RUN_EXTRA_ARGS} )
    RUN_ARGS+=("${extra[@]}")
fi

RUN_ARGS+=("${DOCKER_ENV[@]}" "$IMAGE_NAME")

if [ ${#PYTEST_ARGS[@]} -gt 0 ]; then
    RUN_ARGS+=("${PYTEST_ARGS[@]}")
fi

echo "Running tests inside '$IMAGE_NAME'..."
"${RUN_ARGS[@]}"
