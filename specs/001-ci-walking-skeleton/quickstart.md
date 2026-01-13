# Quickstart: CI Pipeline for Walking Skeleton

## Goal
Validate that the walking skeleton CI runs on PRs to master with Linux quality gates and parity checks.

## Scenario: Trigger CI on a PR

1. Create a feature branch and open a PR targeting `master`.
2. Confirm CI starts and reports status for the Linux job.
3. Verify the Linux job runs quality gates and parity checks.

## Local Preview (Optional)

- Prerequisites: `just` and PowerShell (`pwsh`) installed locally.
- Run `just lint`, `just typecheck`, and `just test` to simulate the Linux CI gates.
- Use `just` to invoke parity checks; ensure `pwsh` is available locally before running them.
