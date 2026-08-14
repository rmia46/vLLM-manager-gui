#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="/data/rspace/codespace/libs/python_env/3.12/.venv/bin/python"

"$PYTHON_BIN" "$SCRIPT_DIR/main.py" "$@"
