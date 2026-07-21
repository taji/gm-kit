#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PYTHON_VERSION_FILE="$ROOT_DIR/.python-version"
if [[ ! -f "$PYTHON_VERSION_FILE" ]]; then
  PYTHON_VERSION_FILE="$(cd -- "$ROOT_DIR/../.." && pwd)/.python-version"
fi

uv run --python "$(cat "$PYTHON_VERSION_FILE")" --extra dev --editable -- \
  python devtools/scripts/live_handoff_harness.py "$@"
