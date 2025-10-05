#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to create the virtual environment" >&2
  exit 1
fi

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip

if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
else
  pip install -e .
fi

deactivate

echo "Virtual environment ready at $VENV_DIR"
