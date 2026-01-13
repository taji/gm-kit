# Architecture

This document captures the canonical design decisions for GM-Kit. Feature-specific plans and research are merged here after specification work completes.

## CI Pipeline (Walking Skeleton)

### Scope
- Linux-only CI pipeline for PRs to `master`.
- Windows validation is deferred to a future CD feature.

### Workflow
- CI runs on pull requests to `master`.
- Quality gates are executed via `just` tasks.
- Parity checks compare bash vs PowerShell-generated outputs on Linux; CI fails if PowerShell cannot be installed.

### Quality Gates
- `just lint`
- `just typecheck`
- `just test-unit`
- `just test-integration`
- `just test-parity`
- `just bandit`
- `just audit` (pip-audit via `uv tool run`)

### Parity Strategy
- Compare generated hello-gmkit outputs produced by bash and PowerShell scripts.
- PowerShell is installed on the Linux runner if missing; parity failure blocks the PR.

### Constraints
- CI must fail if PowerShell install fails.
- No CD or published-package validation in CI.

### Data Model Notes
- CI artifacts are ephemeral; no persistent data model is introduced.
