#!/bin/bash
# remove-agents.sh
# Uninstalls agents; supports:
#   --dry-run : print actions only
#   --purge   : also remove known config/cache/share dirs from registry
#   --yes     : force where possible (opencode)

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/agents.registry.sh"

DRY_RUN=0
PURGE=0
YES=0

usage() {
  cat <<'EOF'
Usage: ./remove-agents.sh [--dry-run] [--purge] [--yes]
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

remove_cursor_agent() {
  if have_cmd cursor-agent; then
    local bin
    bin="$(command -v cursor-agent)"
    log "Removing cursor-agent binary: $bin"
    rm_rf "$bin"
  else
    log "cursor-agent not found in PATH; skipping binary removal."
  fi
}

uninstall_opencode() {
  if have_cmd opencode; then
    if [[ "$YES" -eq 1 ]]; then
      if [[ "$DRY_RUN" -eq 1 ]]; then
        run opencode uninstall --dry-run
      else
        run opencode uninstall --force
      fi
    else
      if [[ "$DRY_RUN" -eq 1 ]]; then
        run opencode uninstall --dry-run
      else
        run opencode uninstall
      fi
    fi
  else
    log "opencode not found in PATH; skipping built-in uninstall."
  fi
}

uninstall_copilot_vscode() {
  if ! have_cmd code; then
    warn "VS Code CLI 'code' not found; cannot uninstall Copilot extensions automatically."
    return 0
  fi

  log "Uninstalling VS Code Copilot extensions..."
  # Uninstall may error if not installed; keep it forgiving.
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] code --uninstall-extension GitHub.copilot"
    log "[dry-run] code --uninstall-extension GitHub.copilot-chat"
  else
    code --uninstall-extension GitHub.copilot >/dev/null 2>&1 || log "Skipping: GitHub.copilot not installed"
    code --uninstall-extension GitHub.copilot-chat >/dev/null 2>&1 || log "Skipping: GitHub.copilot-chat not installed"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --purge)   PURGE=1; shift ;;
    --yes)     YES=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown arg: $1" ;;
  esac
done

log "Starting removal (dry-run=${DRY_RUN} purge=${PURGE} yes=${YES})"
log ""

for rec in "${AGENTS[@]}"; do
  IFS=$'\t' read -r name detect_cmd install_cmd verify_cmd verify_args uninstall_cmd purge_csv <<<"$rec"
  log "=== ${name} ==="

  if [[ "$name" == "copilot-vscode" ]]; then
    uninstall_copilot_vscode
  elif [[ "$uninstall_cmd" == "__REMOVE_CURSOR_AGENT__" ]]; then
    remove_cursor_agent
  elif [[ "$uninstall_cmd" == "__UNINSTALL_OPENCODE__" ]]; then
    uninstall_opencode
  else
    if [[ -n "$uninstall_cmd" ]]; then
      if [[ "$DRY_RUN" -eq 1 ]]; then
        run_bash_lc "$uninstall_cmd"
      else
        run_bash_lc "$uninstall_cmd" || log "Skipping (uninstall failed or not installed): ${name}"
      fi
    else
      warn "No uninstall_cmd defined for ${name}; skipping."
    fi
  fi

  if [[ "$PURGE" -eq 1 ]]; then
    IFS=',' read -r -a paths <<<"$purge_csv"
    for p in "${paths[@]}"; do rm_rf "$p"; done
  fi

  log ""
done

log "Removal complete."
