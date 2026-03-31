#!/usr/bin/env bash
# Run gmkit pdf-convert and automatically execute paused agent steps with Codex.
#
# This helper is intended for local debugging of the current handoff workflow:
# 1) run/continue gmkit
# 2) if gmkit pauses on an agent step, run codex on step-instructions.md
# 3) resume gmkit
# 4) repeat until status is completed (or failure)

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./devtools/scripts/pdf_convert_agent_handoff_loop.sh \
    --output-dir <dir> [--pdf <file> | --resume]

Required:
  --output-dir <dir>         Conversion workspace/output directory

Start mode (new run):
  --pdf <file>               Source PDF path for initial run

Resume mode:
  --resume                   Resume an existing conversion in --output-dir

Optional:
  --gm-callout-config-file <file>  Callout rules file passed to gmkit
  --agent <name>                   GM_AGENT value (default: codex)
  --codex-sandbox <mode>           Codex sandbox mode (default: workspace-write)
  --max-pauses <n>                 Safety cap for handoffs (default: 100)
  --uv-cache-dir <dir>             UV cache directory (default: /tmp/uvcache)
  -h, --help                       Show this help

Examples:
  ./devtools/scripts/pdf_convert_agent_handoff_loop.sh \
    --pdf "tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.pdf" \
    --output-dir "./tmp/sc004-loop" \
    --gm-callout-config-file "./tmp/sc004-callout-rules.input.json"

  ./devtools/scripts/pdf_convert_agent_handoff_loop.sh \
    --resume \
    --output-dir "./tmp/sc004-loop"
EOF
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

log() {
  printf '%s\n' "$*"
}

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PDF_PATH=""
OUTPUT_DIR=""
RESUME_MODE=0
GM_CALLOUT_CONFIG_FILE=""
GM_AGENT_VALUE="codex"
CODEX_SANDBOX="workspace-write"
MAX_PAUSES=100
UV_CACHE_DIR_VALUE="/tmp/uvcache"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pdf)
      PDF_PATH="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --resume)
      RESUME_MODE=1
      shift
      ;;
    --gm-callout-config-file)
      GM_CALLOUT_CONFIG_FILE="$2"
      shift 2
      ;;
    --agent)
      GM_AGENT_VALUE="$2"
      shift 2
      ;;
    --codex-sandbox)
      CODEX_SANDBOX="$2"
      shift 2
      ;;
    --max-pauses)
      MAX_PAUSES="$2"
      shift 2
      ;;
    --uv-cache-dir)
      UV_CACHE_DIR_VALUE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

[[ -n "$OUTPUT_DIR" ]] || die "--output-dir is required"
if [[ "$RESUME_MODE" -eq 1 && -n "$PDF_PATH" ]]; then
  die "Use either --pdf (new run) or --resume (existing run), not both"
fi
if [[ "$RESUME_MODE" -eq 0 && -z "$PDF_PATH" ]]; then
  die "Provide --pdf for a new run, or pass --resume"
fi

if [[ "$RESUME_MODE" -eq 0 ]]; then
  [[ -f "$PDF_PATH" ]] || die "PDF not found: $PDF_PATH"
fi
if [[ -n "$GM_CALLOUT_CONFIG_FILE" ]]; then
  [[ -f "$GM_CALLOUT_CONFIG_FILE" ]] || die "Callout config not found: $GM_CALLOUT_CONFIG_FILE"
fi

build_gmkit_cmd() {
  local resume_flag="$1"
  local -a cmd=(
    uv run --python "$(cat .python-version)" --extra dev --
    gmkit pdf-convert
  )

  if [[ "$resume_flag" -eq 1 ]]; then
    cmd+=(--resume "$OUTPUT_DIR")
  else
    cmd+=("$PDF_PATH" --output "$OUTPUT_DIR")
  fi

  cmd+=(--yes --agent-debug)
  if [[ -n "$GM_CALLOUT_CONFIG_FILE" ]]; then
    cmd+=(--gm-callout-config-file "$GM_CALLOUT_CONFIG_FILE")
  fi
  printf '%q ' "${cmd[@]}"
}

run_gmkit() {
  local resume_flag="$1"
  local cmd
  cmd="$(build_gmkit_cmd "$resume_flag")"
  log ""
  log ">>> Running: GM_AGENT=$GM_AGENT_VALUE UV_CACHE_DIR=$UV_CACHE_DIR_VALUE $cmd"

  set +e
  local output
  output="$(GM_AGENT="$GM_AGENT_VALUE" UV_CACHE_DIR="$UV_CACHE_DIR_VALUE" bash -lc "$cmd" 2>&1)"
  local rc=$?
  set -e

  printf '%s\n' "$output"
  GMKIT_LAST_OUTPUT="$output"
  GMKIT_LAST_RC="$rc"
}

extract_step_dir() {
  # Parse backtick-wrapped step dir from gmkit pause message.
  printf '%s\n' "$GMKIT_LAST_OUTPUT" | sed -n 's/.*`\([^`]*agent_steps\/step_[^`]*\)`.*/\1/p' | tail -1
}

status_is_completed() {
  local status_out
  set +e
  status_out="$(uv run --python "$(cat .python-version)" --extra dev -- gmkit pdf-convert --status "$OUTPUT_DIR" 2>&1)"
  local rc=$?
  set -e
  printf '%s\n' "$status_out"
  [[ "$rc" -eq 0 ]] && printf '%s\n' "$status_out" | rg -q 'Status:\s+completed'
}

run_step_with_codex() {
  local step_dir="$1"
  local instructions="$step_dir/step-instructions.md"
  [[ -d "$step_dir" ]] || die "Step directory not found: $step_dir"
  [[ -f "$instructions" ]] || die "Step instructions missing: $instructions"

  log ""
  log ">>> Running handoff step in: $step_dir"
  (
    cd "$step_dir"
    codex exec --full-auto -s "$CODEX_SANDBOX" --skip-git-repo-check - < step-instructions.md
  )
}

pause_count=0
next_resume="$RESUME_MODE"

while true; do
  run_gmkit "$next_resume"
  next_resume=1

  step_dir="$(extract_step_dir)"
  if [[ -n "$step_dir" ]]; then
    pause_count=$((pause_count + 1))
    if [[ "$pause_count" -gt "$MAX_PAUSES" ]]; then
      die "Exceeded --max-pauses ($MAX_PAUSES). Last paused step: $step_dir"
    fi
    run_step_with_codex "$step_dir"
    continue
  fi

  if status_is_completed; then
    log ""
    log "Conversion status is completed."
    exit 0
  fi

  if [[ "$GMKIT_LAST_RC" -ne 0 ]]; then
    die "gmkit failed (exit=$GMKIT_LAST_RC) and no pause step was detected"
  fi

  die "gmkit exited without pause/completion signal; inspect output above"
done
