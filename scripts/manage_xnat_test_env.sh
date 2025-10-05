#!/usr/bin/env bash
set -euo pipefail

REPO_URL=${XNAT_COMPOSE_REPO:-https://github.com/NrgXnat/xnat-docker-compose.git}
TARGET_DIR=${XNAT_COMPOSE_DIR:-.xnat-test-env}
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BUNDLED_DIR=${SCRIPT_DIR%/*}/resources/xnat-docker-compose
CLONE_LOG=/tmp/xnat_clone_err.log

usage() {
    cat <<USAGE
Usage: $0 <command>

Commands:
  init       Clone or update the xnat-docker-compose repository locally
  up         Start the XNAT test stack with docker compose (implies init)
  down       Stop the stack and remove containers (implies init)
  reset      Remove the stack and persistent volumes (implies init)
  status     Show stack status via docker compose ps (implies init)
  help       Show this message

Environment variables:
  XNAT_COMPOSE_REPO  Override the git repository URL. Defaults to
                     https://github.com/NrgXnat/xnat-docker-compose.git
  XNAT_COMPOSE_DIR   Directory where the repository is cloned.
                     Defaults to .xnat-test-env
USAGE
}

have_git_repo() {
    [ -d "$TARGET_DIR/.git" ]
}

have_compose_files() {
    [ -f "$TARGET_DIR/docker-compose.yml" ]
}

copy_bundled_files() {
    if [ ! -d "$BUNDLED_DIR" ]; then
        return 1
    fi

    echo "Copying bundled XNAT docker compose files into $TARGET_DIR"
    rm -rf "$TARGET_DIR"
    mkdir -p "$TARGET_DIR"
    cp -R "$BUNDLED_DIR/." "$TARGET_DIR/"
}

ensure_repo() {
    if have_compose_files; then
        return 0
    fi

    echo "Cloning XNAT docker compose repo into $TARGET_DIR"
    if git clone "$REPO_URL" "$TARGET_DIR" 2>"$CLONE_LOG"; then
        return 0
    fi

    echo "Git clone failed, attempting to use bundled compose files." >&2
    if [ -f "$CLONE_LOG" ]; then
        cat "$CLONE_LOG" >&2
    fi

    if copy_bundled_files; then
        return 0
    fi

    echo "Unable to obtain docker compose files for XNAT." >&2
    exit 1
}

update_repo() {
    if have_git_repo; then
        echo "Updating existing repository in $TARGET_DIR"
        git -C "$TARGET_DIR" pull --ff-only
    fi
}

ensure_docker() {
    if command -v docker >/dev/null 2>&1; then
        return 0
    fi

    echo "Docker is required to manage the XNAT test environment but was not found in PATH." >&2
    exit 1
}

run_compose() {
    ensure_docker
    if docker compose version >/dev/null 2>&1; then
        (cd "$TARGET_DIR" && docker compose "$@")
    elif command -v docker-compose >/dev/null 2>&1; then
        (cd "$TARGET_DIR" && docker-compose "$@")
    else
        echo "Neither 'docker compose' nor 'docker-compose' is available." >&2
        exit 1
    fi
}

cmd=${1:-help}
case "$cmd" in
    init)
        ensure_repo
        update_repo
        ;;
    up)
        ensure_repo
        update_repo
        run_compose up -d
        ;;
    down)
        ensure_repo
        run_compose down
        ;;
    reset)
        ensure_repo
        run_compose down -v
        ;;
    status)
        ensure_repo
        run_compose ps
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo "Unknown command: $cmd" >&2
        echo
        usage
        exit 1
        ;;
esac
