#!/usr/bin/env bash

# --- CONFIG ---
CODE_APP="code"
TERMINAL_CLASS="gnome-terminal-server.Gnome-terminal"

# --- STEP 1: Open VS Code ---
$CODE_APP . &

# Give it a moment to appear
sleep 0.8

# Maximize VS Code window
CODE_WIN=$(wmctrl -lx | awk '/code.Code/ {win=$1} END {print win}')
if [ -n "$CODE_WIN" ]; then
  wmctrl -i -r "$CODE_WIN" -b add,maximized_vert,maximized_horz
fi

# --- STEP 2: Detect display geometry ---
eval "$(xdotool getdisplaygeometry --shell)"

# NOTE: run "which opencode" to find the path to Open Code if needed

gnome-terminal -- bash -ic '
  echo "SETTING UP DEV ENV AND ENSURING DEPENDENCIES..."
  export CODEX_HOME="$PWD/.codex"
  ./setup_dev.sh
  echo
  echo "CODEX_HOME is: $CODEX_HOME"
  exec bash
' &

# Give it a moment to appear
sleep 0.8

# Find and move terminal to right half of the screen
TERM_WIN=$(wmctrl -lx | awk -v cls="$TERMINAL_CLASS" '$3 == cls {win=$1} END {print win}')
if [ -n "$TERM_WIN" ]; then
  wmctrl -i -r "$TERM_WIN" -e 0,$((WIDTH/2)),0,$((WIDTH/2)),$HEIGHT
else
  echo "Could not find GNOME Terminal window via wmctrl."
fi
