#!/usr/bin/env bash
set -euo pipefail

# --- CONFIG ---
CODE_APP="${CODE_APP:-code}"
TERMINAL_APP="${TERMINAL_APP:-gnome-terminal}"
TERMINAL_CLASS="${TERMINAL_CLASS:-gnome-terminal-server.Gnome-terminal}"
CONFIG_FILE="${CONFIG_FILE:-startcode.config.json}"

# --- ENSURE PREREQUISITE TOOLS ARE IN PLACE ---
require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "❌ Required command \"$1\" not found on PATH."
    exit 1
  fi
}

require_cmd "$CODE_APP"
require_cmd "$TERMINAL_APP"
require_cmd wmctrl
require_cmd xdotool
require_cmd python3

if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ $CONFIG_FILE not found. Run the scaffold scripts first."
  exit 1
fi

# --- CREATE SCRIPT TO LOG ENV VARIABLES TO STDOUT ---
if ! CONFIG_VARS="$(python3 - "$CONFIG_FILE" <<'PY'
import json, shlex, sys

cfg = json.load(open(sys.argv[1]))

def emit(key, val):
    if isinstance(val, bool):
        val = str(val).lower()
    elif val is None:
        val = ''
    print(f"{key}={shlex.quote(str(val))}")

emit("LANGUAGE", cfg.get("language", "python"))
emit("VSCODE_PROFILE_NAME", cfg.get("vscodeProfileName", ""))
emit("VSCODE_PROFILE_PATH", cfg.get("vscodeProfilePath", ""))
PY
)"; then
  echo "❌ Failed to parse $CONFIG_FILE"
  exit 1
fi

# --- RUN THE SCRIPT ---
eval "$CONFIG_VARS"


# --- ENSURE SCRIPT DEPENDENCIES EXIST ---
SETUP_SCRIPT="./setup_${LANGUAGE}_dev.sh"
if [ ! -x "$SETUP_SCRIPT" ]; then
  echo "⚠️ Expected setup script $SETUP_SCRIPT not found or not executable."
fi

CODE_ARGS=()
if [ -n "$VSCODE_PROFILE_NAME" ]; then
  CODE_ARGS+=("--profile" "$VSCODE_PROFILE_NAME")
fi

if [ -n "$VSCODE_PROFILE_PATH" ] && [ -f "$VSCODE_PROFILE_PATH" ]; then
  echo "ℹ️ If you have not imported the VS Code profile yet, run: Profiles: Import Profile → $VSCODE_PROFILE_PATH"
fi

echo "⏳ Opening VS Code..."
"$CODE_APP" "${CODE_ARGS[@]}" . >/dev/null 2>&1 &

sleep 1

# --- FIND THE ACTIVE VSCODE WINDOW AND MAXIMIZE IT ---
CODE_WIN=$(wmctrl -lx 2>/dev/null | awk '/code.Code/ {win=$1} END {print win}')
if [ -n "$CODE_WIN" ]; then
  wmctrl -i -r "$CODE_WIN" -b add,maximized_vert,maximized_horz || true
fi

# --- RETRIEVE SCREEN HEIGHT/WIDTH OF THE PC DISPLAY ---
if ! eval "$(xdotool getdisplaygeometry --shell)"; then
  echo "⚠️ Could not detect display geometry; skipping window placement."
  WIDTH=""; HEIGHT=""
fi

# CAPTURE CURRENTLY OPEN TERMINAL WINDOWS SO WE CAN FIND THE NEWLY LAUNCHED ONE LATER.
EXISTING_TERMS=$(wmctrl -lx 2>/dev/null | awk -v cls="$TERMINAL_CLASS" '$3 == cls {print $1}')

echo "⏳ Launching terminal to run $SETUP_SCRIPT..."
# OPEN A TERMINAL, RUN THE SETUP SCRIPT IF PRESENT, THEN LEAVE THE SHELL OPEN.
"$TERMINAL_APP" -- bash -ic "
  echo 'SETTING UP DEV ENV AND ENSURING DEPENDENCIES...'
  export CODEX_HOME='$PWD/.codex'
  SETUP_SCRIPT='$SETUP_SCRIPT'
  if [ -x \"\$SETUP_SCRIPT\" ]; then
    \"\$SETUP_SCRIPT\"
  else
    echo '⚠️ Skipping dev setup; '
    echo \"   missing or non-executable: \$SETUP_SCRIPT\"
  fi
  echo
  echo 'CODEX_HOME is:' \"\$CODEX_HOME\"
  exec bash
" >/dev/null 2>&1 &

sleep 1.2

NEW_TERMS=$(wmctrl -lx 2>/dev/null | awk -v cls="$TERMINAL_CLASS" '$3 == cls {print $1}')

TERM_WIN=""
if [ -n "$NEW_TERMS" ]; then
  # PREFER THE WINDOW THAT WASN'T PRESENT BEFORE; FALLBACK TO THE LAST MATCHING WINDOW.
  TERM_WIN=$(comm -13 <(echo "$EXISTING_TERMS" | tr ' ' '\n' | sort -u) <(echo "$NEW_TERMS" | tr ' ' '\n' | sort -u) | tail -n 1)
  if [ -z "$TERM_WIN" ]; then
    TERM_WIN=$(echo "$NEW_TERMS" | tr ' ' '\n' | tail -n 1)
  fi
fi

if [ -n "${TERM_WIN:-}" ] && [ -n "${WIDTH:-}" ] && [ -n "${HEIGHT:-}" ]; then
  # TILE THE NEW TERMINAL TO THE RIGHT HALF OF THE SCREEN.
  wmctrl -i -r "$TERM_WIN" -e 0,$((WIDTH/2)),0,$((WIDTH/2)),$HEIGHT || true
elif [ -z "$TERM_WIN" ]; then
  echo "⚠️ Could not find a newly launched terminal window; leaving layout unchanged."
fi
