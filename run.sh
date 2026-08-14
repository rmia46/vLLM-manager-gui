#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_VENV="$SCRIPT_DIR/.venv/bin/python"

if [ ! -f "$PROJECT_VENV" ]; then
    echo "Creating project venv..."
    uv venv "$SCRIPT_DIR/.venv" --python 3.12
    uv pip install --python "$PROJECT_VENV" PySide6 requests psutil huggingface_hub qtawesome
fi

"$PROJECT_VENV" "$SCRIPT_DIR/main.py" "$@"
