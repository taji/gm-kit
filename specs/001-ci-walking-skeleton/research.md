# Research: CI Pipeline for Walking Skeleton

## Decision 1: CI Platform
- **Decision**: Use GitHub Actions for CI.
- **Rationale**: Matches current repository hosting and provides first-class Linux and Windows runners.
- **Alternatives considered**: GitLab CI, CircleCI.

## Decision 2: Linux Parity Execution
- **Decision**: Run parity on Linux by comparing bash vs PowerShell-generated file outputs; install PowerShell on the runner if missing.
- **Rationale**: Enables single-step parity checks without waiting for a published package while keeping outputs comparable.
- **Alternatives considered**: Skip parity when pwsh is missing; run parity only on Windows.

## Decision 3: Windows Validation Scope
- **Decision**: Windows CI runs source-based validation of `gmkit init` and `/gmkit.hello-gmkit` without installing a published package.
- **Rationale**: CD/release pipeline does not exist yet; source-based validation still protects Windows users.
- **Alternatives considered**: Use published UV installs (deferred to CD).

## Decision 4: CI Trigger
- **Decision**: Run CI on pull requests targeting master.
- **Rationale**: Ensures PRs are gated before merge.
- **Alternatives considered**: Push-only CI or nightly validation.
