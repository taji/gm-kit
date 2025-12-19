set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

# Use the Python version pinned in .python-version for all commands.

# Sanity check that the development environment is set up correctly.
hello-python:
    uv run --python "$(cat .python-version)" -- python -c "print('hello from justfile')"

# Format code with black and isort
format:
    uv run --python "$(cat .python-version)" --extra dev -- black src
    uv run --python "$(cat .python-version)" --extra dev -- isort src

# Format imports only
format-imports:
    uv run --python "$(cat .python-version)" --extra dev -- isort src

# Lint code with ruff
lint:
    uv run --python "$(cat .python-version)" --extra dev -- ruff check src

# Type check with mypy
typecheck:
    uv run --python "$(cat .python-version)" --extra dev -- mypy src

# Run tests
test:
    uv run --python "$(cat .python-version)" --extra dev -- pytest
