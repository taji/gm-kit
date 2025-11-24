set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

# Use the Python version pinned in .python-version for all commands.

# Sanity check that the development environment is set up correctly.
hello-python:
    uv run --python "$(cat .python-version)" -- python -c "print('hello from justfile')"

