# Research: CI Pipeline for Walking Skeleton

## Decision 1: CI Platform
- **Decision**: Use GitHub Actions for CI (Linux-only in CI).
- **Rationale**: Matches current repository hosting and provides a stable Linux runner for PR gating.
- **Alternatives considered**: GitLab CI, CircleCI.

## Decision 2: Linux Parity Execution
- **Decision**: Run parity on Linux by comparing bash vs PowerShell-generated file outputs; install PowerShell on the runner if missing.
- **Rationale**: Enables single-step parity checks without waiting for a published package while keeping outputs comparable.
- **Alternatives considered**: Skip parity when pwsh is missing; run parity only on Windows.

## Decision 3: Windows Validation Scope
- **Decision**: Defer Windows validation to a future CD feature.
- **Rationale**: CI is Linux-only and focused on fast PR gating; CD will cover Windows end-to-end validation later.
- **Alternatives considered**: Add a Windows CI job in this feature.

## Decision 4: CI Trigger
- **Decision**: Run CI on pull requests targeting master.
- **Rationale**: Ensures PRs are gated before merge.
- **Alternatives considered**: Push-only CI or nightly validation.
