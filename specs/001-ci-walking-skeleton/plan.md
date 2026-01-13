# Implementation Plan: CI Pipeline for Walking Skeleton

**Branch**: `001-ci-walking-skeleton` | **Date**: 2026-01-13 | **Spec**: `specs/001-ci-walking-skeleton/spec.md`
**Input**: Feature specification from `/specs/001-ci-walking-skeleton/spec.md`

## Summary

Establish a GitHub Actions CI pipeline for PRs to master that enforces quality gates, runs unit and integration tests, and validates Linux parity by comparing bash vs PowerShell-generated files (with pwsh install attempts). CD and any Windows validation are explicitly out of scope.

## Technical Context

**Language/Version**: Python 3.13.7
**Primary Dependencies**: typer, rich, uv, pytest, ruff, black, isort, mypy, bandit
**Storage**: N/A (CI configuration only)
**Testing**: pytest, ruff, mypy, bandit, uv audit (invoked via `just` tasks including `test-unit`, `test-integration`, `test-parity`)
**Target Platform**: GitHub Actions runner (ubuntu-latest)
**Project Type**: single CLI repository
**Performance Goals**: Linux CI job under 15 minutes for typical PRs, with overruns reported
**Constraints**: CI must fail if PowerShell cannot be installed on Linux for parity; CI must invoke gates via `just` (unit, integration, parity split); no CD or Windows validation in CI
**Scale/Scope**: single repository, PR gating only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- I. Library-First: Not applicable (CI configuration only); no new libraries introduced.
- II. CLI Interface: No new CLI surface; existing CLI remains unchanged.
- III. Test-First: CI enforces existing tests and quality gates.
- IV. Integration Testing: CI runs integration tests for `gmkit init` and `/gmkit.hello-gmkit`.
- V. Observability/Versioning/Simplicity: CI output is standard job logs; no extra complexity added.
- VI. AI Agent Integration: No changes to agent prompts or assets.
- VII. Interactive CLI Testing: CI runs existing interactive test suite using pexpect.
- VIII. Cross-Platform Installation: Windows validation deferred to CD; CI uses Linux parity with pwsh installed on Linux.

**Gate Results (Pre-Phase 0)**: PASS
**Gate Results (Post-Phase 1)**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-ci-walking-skeleton/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
.github/workflows/
├── ci.yml

src/gm_kit/
├── __init__.py
├── agent_config.py
├── cli.py
├── init.py
├── script_generator.py
├── template_manager.py
├── validator.py
└── assets/
    ├── memory/
    │   └── constitution.md
    ├── scripts/
    │   ├── bash/
    │   │   └── say-hello.sh
    │   └── powershell/
    │       └── say-hello.ps1
    └── templates/
        ├── hello-gmkit-template.md
        └── commands/
            └── gmkit.hello-gmkit.md

tests/
├── contract/
│   └── test_cli_init_contract.py
├── integration/
│   ├── test_agent_validation.py
│   ├── test_full_init_flow.py
│   ├── test_script_parity.py
│   └── test_toml_validation.py
└── unit/
    ├── test_agent_config.py
    ├── test_init.py
    ├── test_script_generator.py
    └── test_template_manager.py
```

**Structure Decision**: Single project CLI repo with CI configuration in `.github/workflows/` and code/tests under `src/` and `tests/`.

## Complexity Tracking

No constitution violations requiring justification.
