# GEMINI.md

This checkout is a feature worktree. Treat it as the authoritative workspace for the active feature.

## Workspace rules

- Make code changes, tests, and documentation updates in this worktree, not in the root `gm-kit` checkout, unless the user explicitly says otherwise.
- When you give a command for validation or analysis, name the exact directory it must be run from.
- If a command depends on this feature, assume it should be run from `/home/todd/Dev/gm-kit/.worktrees/e7-15-annotation-placement-refinement`.
- Do not switch to the root checkout mid-task unless you explicitly call out that change and explain why.

## Command guidance

- Prefer commands that begin with `cd /home/todd/Dev/gm-kit/.worktrees/e7-15-annotation-placement-refinement && ...` when the command is meant for this feature.
- If output differs between the worktree and the root checkout, treat the worktree as the source of truth for this feature.
- When rerunning analysis or tests, restate the target checkout before the command.

## Handoff rule

- If there is any ambiguity about which checkout is active, stop and confirm the path before making changes.
