#!/bin/bash
# provision-agents.sh
# Installs agents (if missing) and verifies they run.

set -euo pipefail

# Ensure user-local bins are available during non-interactive runs
export PATH="$HOME/.local/bin:$PATH"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/agents.registry.sh"

log() { printf "%s\n" "$*"; }
die() { echo "ERROR: $*" >&2; exit 1; }
have_cmd() { command -v "$1" >/dev/null 2>&1; }

run_bash_lc() { bash -lc "$1"; }

verify_in_path() {
  local name="$1" cmd="$2" args="$3"
  [[ -n "$cmd" ]] || die "${name}: verify command is empty (registry entry malformed)"
  log "Verifying ${name} via PATH (${cmd})..."
  have_cmd "$cmd" || die "${name} not found in PATH: ${cmd}"
  # shellcheck disable=SC2086
  "$cmd" $args
  log ""
}

for rec in "${AGENTS[@]}"; do
  IFS=$'\t' read -r name detect_cmd install_cmd verify_cmd verify_args uninstall_cmd purge_csv <<<"$rec"

  log "=== ${name} ==="

  # Generic CLI agent flow
  if have_cmd "$detect_cmd"; then
    log "${name} already present; skipping install."
  else
    log "${name} not detected; installing..."
    run_bash_lc "$install_cmd"
  fi

  verify_in_path "$name" "$verify_cmd" "$verify_args"
done

log "Provisioning complete."
