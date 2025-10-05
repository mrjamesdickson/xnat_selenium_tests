#!/usr/bin/env bash
set -euo pipefail

REPO_URL=${XNAT_COMPOSE_REPO:-https://github.com/NrgXnat/xnat-docker-compose.git}
TARGET_DIR=${XNAT_COMPOSE_DIR:-.xnat-test-env}

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

ensure_repo() {
    if [ ! -d "$TARGET_DIR/.git" ]; then
        echo "Cloning XNAT docker compose repo into $TARGET_DIR"
        git clone "$REPO_URL" "$TARGET_DIR"
    else
        echo "Updating existing repository in $TARGET_DIR"
        git -C "$TARGET_DIR" pull --ff-only
    fi
}

cmd=${1:-help}
case "$cmd" in
    init)
        ensure_repo
        ;;
    up)
        ensure_repo
        (cd "$TARGET_DIR" && docker compose up -d)
        ;;
    down)
        ensure_repo
        (cd "$TARGET_DIR" && docker compose down)
        ;;
    reset)
        ensure_repo
        (cd "$TARGET_DIR" && docker compose down -v)
        ;;
    status)
        ensure_repo
        (cd "$TARGET_DIR" && docker compose ps)
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
