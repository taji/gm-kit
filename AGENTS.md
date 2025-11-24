# Repository Guidelines

## Project Structure & Module Organization
- Main code lives in `spec-kit/src/specify_cli/__init__.py`; CLI entrypoint is `specify`.
- Templates that drive generated projects are in `spec-kit/templates/` (commands, tasks, prompts, etc.).
- Helper scripts for contributors are in `spec-kit/scripts/` (bash and PowerShell variants); docs and guides sit in `spec-kit/docs/`.
- Governance memory (e.g., `spec-kit/memory/constitution.md`) guides agents; update when process changes.
- Media/assets live in `spec-kit/media/`; published changelog and policies sit alongside (`CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`).

## Build, Test, and Development Commands
- First-time setup: `cd spec-kit && uv sync` (Python 3.11+ required).
- Fast local run without install: `cd spec-kit && python -m src.specify_cli --help` or `python -m src.specify_cli init demo --ai copilot --ignore-agent-tools --script sh`.
- Editable install: `cd spec-kit && uv pip install -e .` then `specify ...` is available on PATH.
- Simulate end-user flow from the current branch: `cd spec-kit && uvx --from . specify init demo-uvx --ai claude --ignore-agent-tools`.
- Package check: `cd spec-kit && uv build` (outputs to `dist/`).

## Coding Style & Naming Conventions
- Python code uses 4-space indent, type hints, and Typer commands with rich output; follow existing command patterns and helper utilities in `specify_cli`.
- Keep option/flag names kebab-case for the CLI and snake_case in Python; prefer small, composable functions over new globals.
- Templates are prefixed with `speckit.` and scripts use hyphenated names (e.g., `create-new-feature.sh`); match these patterns when adding files.
- Linting is light; keep imports tidy and run `python -c "import specify_cli"` for a quick sanity check.

## Testing Guidelines
- There is no automated test suite today; run smoke flows after changes:
  - `python -m src.specify_cli init demo --ai copilot --ignore-agent-tools` in a temp directory.
  - Verify generated scripts are executable (`ls -l scripts/*.sh`) and Windows-friendly (`.ps1` present).
- Adjust `templates/` and docs when behavior changes; manual validation is expected before PRs.

## Commit & Pull Request Guidelines
- Discuss large template/CLI changes with maintainers before opening a PR. Work on feature branches (`git checkout -b feature-name`).
- Commit messages should be clear and scoped; update `CHANGELOG.md` when altering user-facing behavior.
- PRs should describe intent, testing performed, and impacted templates/scripts; link related issues and screenshots/logs when relevant.
- Document any AI assistance in the PR (per `CONTRIBUTING.md`), ensure docs (`README.md`, `spec-driven.md`, `docs/*.md`) stay in sync, and avoid committing secrets (tokens like `GH_TOKEN` are for local use only).

## Active Technologies
- Python 3.11 (per project standard) + None beyond git + Markdown editing (001-readme-audit)
- N/A (documentation + repo metadata) (001-readme-audit)

## Recent Changes
- 001-readme-audit: Added Python 3.11 (per project standard) + None beyond git + Markdown editing
