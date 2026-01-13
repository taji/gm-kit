set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

# Use the Python version pinned in .python-version for all commands.

# Sanity check that the development environment is set up correctly.
hello-python:
    uv run --python "3.13.7" -- python -c "print('hello from justfile')"

# Format code with black and isort
format:
    uv run --python "3.13.7" --extra dev -- black src
    uv run --python "3.13.7" --extra dev -- isort src

# Format imports only
format-imports:
    uv run --python "3.13.7" --extra dev -- isort src

# Lint code with ruff
lint:
    uv run --python "3.13.7" --extra dev -- ruff check src

# Type check with mypy
typecheck:
    uv run --python "3.13.7" --extra dev -- mypy src

# Run unit tests only
test-unit:
    uv run --python "3.13.7" --extra dev -- pytest tests/unit

# Run integration tests only
test-integration:
    uv run --python "3.13.7" --extra dev -- pytest tests/integration

# Run parity tests only
test-parity:
    uv run --python "3.13.7" --extra dev -- pytest tests/integration/test_script_parity.py

# Run all tests (unit + integration + parity)
test:
    just test-unit
    just test-integration
    just test-parity

# Security scan
bandit:
    uv run --python "3.13.7" --extra dev -- bandit -r src

# Dependency audit
audit:
    uv pip audit

# Build distribution artifacts with Hatch
build:
    hatch build

# Publish distribution artifacts with Hatch (requires auth)
publish:
    hatch publish

# Bump version via Hatch: just bump patch|minor|major
bump level:
    hatch version {{level}}

# Run gmkit init with a target path, e.g. `just run_gmkit_init /tmp/gmkit-test`
run_gmkit_init target_path:
    uv run --python "3.13.7" --extra dev --editable -- gmkit init {{target_path}}
