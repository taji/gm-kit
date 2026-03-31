#!/usr/bin/env bash
set -euo pipefail

UV_CACHE_DIR=/tmp/uvcache python devtools/scripts/run_step7_7_agent.py \
  --model "${1:-opencode/gpt-5.3-codex}" \
  --fixture "${2:-tests/fixtures/pdf_convert/agents/inputs/step_7_7/Homebrewery_WeaponsTable_Phase4.md}" \
  --workspace "${3:-tmp/step_7_7_agent}"
