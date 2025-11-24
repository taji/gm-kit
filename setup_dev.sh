#!/bin/bash
set -e

echo "--- Setting up development environment ---"

# 1. Ensure mise is installed
if ! command -v mise &> /dev/null; then
    echo "❌ mise is not installed. Please install it from https://mise.jdx.dev/"
    exit 1
fi

# 2. Ensure uv is installed globally via mise
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please ensure mise installs uv."
    exit 1
fi


# 3. Set .python-version to 3.13.7
echo "3.13.7" > .python-version

# 4. Create virtual environment with uv using Python 3.13.7
echo "⏳ Creating virtual environment..."
uv venv --python 3.13.7 --clear
echo "✅ Virtual environment created."

# 5. Install Python dependencies with uv
echo "⏳ Installing Python dependencies..."
uv sync
echo "✅ Python dependencies installed."

# 6. Create a flag file to indicate setup is complete
touch .venv/.setup_complete

# 7. Set any necessary environment variables (if needed)
export CODEX_HOME="$PWD/.codex"

# 8. Create symbolic link between .codex/prompts to .opencode/commands folder as they serve the same purpose for spec-kit.
rm -rf .codex/prompts
ln -s ../.opencode/command .codex/prompts

echo ""
echo "🎉 --- Setup complete! --- 🎉"
echo "You can now run the tools."
