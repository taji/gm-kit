#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

uv run --python "$(cat .python-version)" --extra dev --editable -- \
  python devtools/scripts/live_handoff_harness.py "$@"
