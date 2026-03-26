#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

usage() {
  cat <<'EOF'
Usage: ./resume.sh [agent]

Resume a coding session for an agent with project-write + terminal-execution permissions.

Supported agents:
  codex
  opencode
  claude
  gemini
  qwen
EOF
}

normalize_agent() {
  local raw="${1:-}"
  raw="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"
  case "$raw" in
    codex|opencode|claude|gemini|qwen)
      printf '%s\n' "$raw"
      ;;
    *)
      return 1
      ;;
  esac
}

ensure_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "❌ Required command \"$cmd\" is not available on PATH." >&2
    exit 1
  fi
}

select_agent_interactive() {
  local choice
  echo "Select agent to resume:"
  echo "  1) codex"
  echo "  2) opencode"
  echo "  3) claude"
  echo "  4) gemini"
  echo "  5) qwen"
  printf "Enter choice [1-5]: "
  read -r choice
  case "$choice" in
    1) echo "codex" ;;
    2) echo "opencode" ;;
    3) echo "claude" ;;
    4) echo "gemini" ;;
    5) echo "qwen" ;;
    *)
      echo "❌ Invalid selection: $choice" >&2
      exit 1
      ;;
  esac
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

AGENT=""
if [ $# -gt 0 ]; then
  if ! AGENT="$(normalize_agent "$1")"; then
    echo "❌ Unsupported agent: $1" >&2
    usage
    exit 1
  fi
else
  AGENT="$(select_agent_interactive)"
fi

case "$AGENT" in
  codex)
    ensure_cmd codex
    exec codex -a never -s workspace-write resume --last
    ;;
  opencode)
    ensure_cmd opencode
    # OpenCode permission defaults are typically configured in opencode settings.
    exec opencode --continue
    ;;
  claude)
    ensure_cmd claude
    exec claude --resume --permission-mode bypassPermissions
    ;;
  gemini)
    ensure_cmd gemini
    exec gemini --resume latest --yolo
    ;;
  qwen)
    ensure_cmd qwen
    exec qwen --continue --approval-mode=yolo
    ;;
esac
