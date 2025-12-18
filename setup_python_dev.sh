#!/usr/bin/env bash
set -euo pipefail

echo "--- Setting up Python dev environment (uv, ephemeral runs) ---"

# Enable uv preview features (needed for tool.uv.scripts support)
export UV_PREVIEW=1

if ! command -v uv >/dev/null 2>&1; then
  echo "❌ uv is not installed. Please install it (e.g., via mise)."
  exit 1
fi

if [ ! -f ".python-version" ]; then
  echo "❌ .python-version not found. Add the desired Python version and re-run."
  exit 1
fi

PYTHON_VERSION="$(cat .python-version)"

echo "⏳ Ensuring Python ${PYTHON_VERSION} is available..."
uv python install "${PYTHON_VERSION}"

if [ -f pyproject.toml ]; then
  echo "⏳ Priming uv cache with project (editable) + dev deps..."
  uv run --python "${PYTHON_VERSION}" --extra dev --editable -- python - <<'PY'
print("uv cache primed")
PY
else
  echo "ℹ️ pyproject.toml not found; skipping uv cache prime."
fi

export CODEX_HOME="${CODEX_HOME:-"$PWD/.codex"}"

# Create symbolic link between .codex/prompts and .opencode/command for spec-kit.
PROMPTS_LINK=".codex/prompts"
PROMPTS_TARGET="../.opencode/command"
if [ -L "$PROMPTS_LINK" ] && [ "$(readlink "$PROMPTS_LINK")" = "$PROMPTS_TARGET" ]; then
  echo "🔗 $PROMPTS_LINK already points to $PROMPTS_TARGET; skipping."
elif [ -e "$PROMPTS_LINK" ]; then
  echo "⚠️ $PROMPTS_LINK exists and is not the expected symlink; leaving it unchanged."
else
  ln -s "$PROMPTS_TARGET" "$PROMPTS_LINK"
fi

echo ""
echo "🎉 --- Setup complete! --- 🎉"
echo "You can now run project scripts with uv (no venv activation needed)."
echo "Examples:"
echo "  uv run --extra dev -- python -m pytest"
echo "  uv run --extra dev -- python -m ruff check"
