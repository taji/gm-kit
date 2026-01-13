# Quickstart: CI Pipeline for Walking Skeleton

## Goal
Validate that the walking skeleton CI runs on PRs to master with Linux quality gates, parity checks, and Windows source-based validation.

## Scenario: Trigger CI on a PR

1. Create a feature branch and open a PR targeting `master`.
2. Confirm CI starts and reports status for the Linux and Windows jobs.
3. Verify the Linux job runs quality gates and parity checks.
4. Verify the Windows job runs the source-based `gmkit init` and `/gmkit.hello-gmkit` validation.

## Local Preview (Optional)

- Prerequisites: `just` and PowerShell (`pwsh`) installed locally.
- Run `just lint`, `just typecheck`, and `just test` to simulate the Linux CI gates.
- Use `just` to invoke parity checks; ensure `pwsh` is available locally before running them.
