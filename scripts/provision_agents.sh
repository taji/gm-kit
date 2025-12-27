#!/bin/bash
# provision-agents.sh
# Installs agents (if missing) and verifies they run.

set -euo pipefail

# Ensure user-local bins are available during non-interactive runs
export PATH="$HOME/.local/bin:$HOME/.opencode/bin:$PATH"

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

install_copilot_vscode() {
  have_cmd code || die "copilot-vscode requires the VS Code 'code' command on PATH."

  log "Installing VS Code extensions for Copilot..."
  # These are safe to run repeatedly; VS Code will no-op if already installed.
  code --install-extension GitHub.copilot --force
  code --install-extension GitHub.copilot-chat --force
  log ""
}

# Copilot is an vscode extension, so we verify its presence differently.
verify_copilot_vscode() {
  have_cmd code || die "copilot-vscode requires the VS Code 'code' command on PATH."

  log "Verifying Copilot extensions are installed..."
  local exts
  exts="$(code --list-extensions || true)"

  echo "$exts" | grep -qx "GitHub.copilot" || die "VS Code extension missing: GitHub.copilot"
  echo "$exts" | grep -qx "GitHub.copilot-chat" || die "VS Code extension missing: GitHub.copilot-chat"

  log "Copilot for VS Code installed (GitHub.copilot, GitHub.copilot-chat)."
  log ""
}

for rec in "${AGENTS[@]}"; do
  IFS=$'\t' read -r name detect_cmd install_cmd verify_cmd verify_args uninstall_cmd purge_csv <<<"$rec"

  log "=== ${name} ==="

  # Special case: Copilot VS Code (extensions)
  if [[ "$name" == "copilot-vscode" ]]; then
    if ! have_cmd code; then
      die "copilot-vscode requested, but VS Code CLI 'code' is not on PATH."
    fi
    install_copilot_vscode
    verify_copilot_vscode
    continue
  fi

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
