# Feature Specification: CI Pipeline for Walking Skeleton

**Feature Branch**: `001-ci-walking-skeleton`  
**Created**: 2026-01-13  
**Status**: Draft  
**Input**: User description: "refer to E2-03 feature item in BACKLOG.md for details. Please confirm any questions before proceeding with spec.md creation."

## Clarifications

### Session 2026-01-13

- Q: What should the Linux parity check compare? → A: Parity compares only generated file contents.
- Q: If PowerShell (pwsh) is unavailable on Linux for parity, how should CI behave? → A: Attempt to install pwsh on Linux; if parity still cannot run, CI fails.
- Q: Should CI time limits be hard targets or best-effort guidance? → A: Best-effort guidance.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - PR Validation on Linux (Priority: P1)

As a maintainer, I want every PR to master to run quality gates and core tests so regressions are caught before merge.

**Why this priority**: This prevents broken installs or regressions from landing in the mainline.

**Independent Test**: Open a PR with a known failing lint/test/parity condition and confirm CI blocks the merge with a clear failure status.

**Acceptance Scenarios**:

1. **Given** a PR to master with valid changes, **When** CI runs, **Then** quality gates and required tests pass and the PR is unblocked.
2. **Given** a PR to master with a lint/test/parity failure, **When** CI runs, **Then** CI fails with a clear reason and blocks the PR.
3. **Given** a PR to master, **When** CI reports a failure status, **Then** the PR is blocked from merging until CI passes.

---

### Edge Cases

- What happens when the Windows shell runtime is unavailable on Linux for parity checks?
- What happens when lint, test, or parity gates fail?
- What happens if parity outputs are partially generated or mismatched?
- Are CI reruns manual only, or should failures be retried automatically?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: CI MUST run on every pull request targeting the master branch.
- **FR-002**: CI MUST run linting, formatting checks, and type checks as gating steps using `just` tasks.
- **FR-003**: CI MUST run unit tests (`just test-unit`) and integration tests (`just test-integration`) for `gmkit init` and `/gmkit.hello-gmkit` across supported agents (claude, codex-cli, gemini, qwen). Integration tests execute the scripts directly and validate outputs; they do not invoke the agents.
- **FR-004**: CI MUST run a Linux parity check (`just test-parity`) that compares Unix-shell and Windows-shell generated file contents. CI MUST attempt to install PowerShell on Linux if it is unavailable; if parity still cannot run, CI MUST fail with a clear error.
- **FR-005**: CI MUST publish a pass/fail status that is visible on the PR and blocks merging on failure.

**Quality Gate Tasks**: `just lint`, `just typecheck`, `just test-unit`, `just test-integration`, `just test-parity`, `bandit -r src`, and `uv audit` are required gates. `just test` runs unit + integration + parity together. `just format` and `just format-imports` are optional and not gating.

**Parity Comparison Scope**: Parity compares the generated hello-gmkit outputs (the greeting file and rendered template outputs) produced by bash vs PowerShell scripts.

**Expected Artifacts**: `gmkit init` must create agent prompt files and `.gmkit` subfolders; `/gmkit.hello-gmkit` must produce the greeting output file and template output in the target workspace.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of PRs to master produce a CI status with pass/fail results.
- **SC-002**: The Linux CI job completes in under 15 minutes for typical PRs, with overruns reported.
- **SC-004**: CI detects and fails on script parity mismatches or missing expected outputs.
- **SC-005**: CI validates that the expected hello-gmkit output files are produced by the Linux job.

**Typical PR**: A change that does not modify dependencies and touches fewer than 50 files.

## Assumptions

- The project uses a standard hosted CI system with Linux runners.
- CD/release automation is out of scope for this feature and will be handled separately.
- Full end-to-end validation via published UV installs will be specified in a future CD feature.
- Windows validation (source-based or via published installs) is deferred to a future CD feature.
- CI reliability/uptime targets are out of scope for this feature.
