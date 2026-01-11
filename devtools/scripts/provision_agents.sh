#!/bin/bash
# provision-agents.sh
# Installs agents (if missing) and verifies them.
#   --skip <agent> : skip installation of specified agent

set -euo pipefail

# Ensure user-local bins are available during non-interactive runs
export PATH="$HOME/.local/bin:$PATH"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/agents.registry.sh"

SKIP_AGENTS=()
usage() {
  cat <<'EOF'
Usage: ./provision-agents.sh [OPTIONS]

Installs and verifies AI agents from the registry.

OPTIONS:
  --skip <agents>   Skip installation of specified agents (comma-separated or multiple flags)
  -h, --help        Show this help message

EXAMPLES:
  ./provision-agents.sh                    # Install all agents
  ./provision-agents.sh --skip claude      # Skip claude installation
  ./provision-agents.sh --skip claude,codex-cli  # Skip multiple agents (comma-separated)
  ./provision-agents.sh --skip claude --skip codex-cli  # Skip multiple agents (multiple flags)

AVAILABLE AGENTS:
  claude, codex-cli, gemini, qwen
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
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

  # Skip if requested
  if [[ " ${SKIP_AGENTS[*]} " =~ " ${name} " ]]; then
    log "=== ${name} ==="
    log "Skipping (requested via --skip)"
    log ""
    continue
  fi

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
