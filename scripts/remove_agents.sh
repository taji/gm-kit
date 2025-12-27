#!/bin/bash
# remove-agents.sh
# Uninstalls agents; supports:
#   --dry-run : print actions only
#   --purge   : also remove known config/cache/share dirs from registry
#   --skip <agent> : skip removal of specified agent

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/agents.registry.sh"

DRY_RUN=0
PURGE=0
SKIP_AGENTS=()
usage() {
  cat <<'EOF'
Usage: ./remove-agents.sh [OPTIONS]

Uninstalls AI agents from the registry.

OPTIONS:
  --dry-run         Print actions without executing them
  --purge           Also remove config/cache/share directories
  --skip <agents>   Skip removal of specified agents (comma-separated or multiple flags)
  -h, --help        Show this help message

EXAMPLES:
  ./remove-agents.sh                     # Remove all agents
  ./remove-agents.sh --dry-run           # Preview removal actions
  ./remove-agents.sh --purge             # Remove agents and purge data
  ./remove-agents.sh --skip claude       # Skip claude removal
  ./remove-agents.sh --skip gemini,qwen  # Skip multiple agents (comma-separated)
  ./remove-agents.sh --dry-run --purge --skip gemini  # Preview with purge, skip gemini

AVAILABLE AGENTS:
  claude, codex-cli, gemini, qwen
EOF
}

log() { printf "%s\n" "$*"; }
warn() { echo "WARN: $*" >&2; }
die() { echo "ERROR: $*" >&2; exit 1; }
have_cmd() { command -v "$1" >/dev/null 2>&1; }

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf "[dry-run] %q " "$@"; printf "\n"
    return 0
  fi
  "$@"
}

run_bash_lc() {
  local cmd="$1"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] bash -lc $(printf %q "$cmd")"
    return 0
  fi
  bash -lc "$cmd"
}

rm_rf() {
  local path="$1"
  [[ -z "$path" ]] && die "rm_rf called with empty path"
  if [[ -e "$path" ]]; then
    run rm -rf -- "$path"
  else
    log "Skipping (not found): $path"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --purge)   PURGE=1; shift ;;
    --skip) 
      # Split comma-separated list into array
      IFS=',' read -ra agents <<<"$2"
      SKIP_AGENTS+=("${agents[@]}")
      shift 2 
      ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown arg: $1" ;;
  esac
done

log "Starting removal (dry-run=${DRY_RUN} purge=${PURGE})"
log ""

for rec in "${AGENTS[@]}"; do
  IFS=$'\t' read -r name detect_cmd install_cmd verify_cmd verify_args uninstall_cmd purge_csv <<<"$rec"

  # Skip if requested
  if [[ " ${SKIP_AGENTS[*]} " =~ " ${name} " ]]; then
    log "=== ${name} ==="
    log "Skipping (requested via --skip)"
    log ""
    continue
  fi

  log "=== ${name} ==="

  if [[ -n "$uninstall_cmd" ]]; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
      run_bash_lc "$uninstall_cmd"
    else
      run_bash_lc "$uninstall_cmd" || log "Skipping (uninstall failed or not installed): ${name}"
    fi
  else
    warn "No uninstall_cmd defined for ${name}; skipping."
  fi

  if [[ "$PURGE" -eq 1 ]]; then
    IFS=',' read -r -a paths <<<"$purge_csv"
    for p in "${paths[@]}"; do rm_rf "$p"; done
  fi

  log ""
done

log "Removal complete."
