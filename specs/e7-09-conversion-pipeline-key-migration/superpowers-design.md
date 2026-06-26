# E7-09 Conversion Pipeline Key-Migration Design

## Goal

Replace numeric step coupling in the conversion pipeline with stable step-key identity, and rename conversion step workspaces to key-based directories so ordering can change without renumbering fallout.

## Scope

Included:
- stable internal identity for conversion steps
- explicit step registry keys and ordering
- conversion orchestrator lookup by key
- key-based on-disk step workspace naming
- user-facing logs that preserve numeric display ids
- resume behavior keyed off stable step identity
- tests for ordering, step lookup, resume, and workspace path generation

Excluded:
- prep pipeline identity changes
- backward-compatibility aliases for old numeric workspace paths
- fake-agent behavior
- TOC recovery
- sig marker replacement
- conversion feature changes unrelated to identity and workspace naming

## Decision

Use stable keys as the only internal identity for conversion steps.

Numeric step ids such as `9.2` and `10.4a` remain presentation labels only:
- they appear in logs and messages
- they are not used for directory naming
- they are not used for orchestrator lookup
- they are not used for resume identity

On-disk conversion step workspaces should use key-based names directly, not numeric aliases.

## Architecture

The conversion pipeline already has two different identity layers mixed together:
- numeric ids used for phase/step display and some file paths
- implicit execution ordering based on phase/step numbering

E7-09 separates those concerns.

The new model is:
- each conversion step has a stable `step_key`
- each step also has a `display_id`
- the orchestrator executes steps in an explicit registry-defined order
- workspace directories are derived from `step_key`

This keeps the conversion pipeline readable for humans while removing the renumbering coupling that currently comes from numeric ids being used as internal structure.

## Step Identity Model

Each conversion step should expose:
- `step_key`: authoritative identity for orchestrator, workspace, and resume
- `display_id`: human-readable numeric label such as `9.3`
- `display_name`: readable label for logs and status output
- `workspace_slug`: stable path-safe slug derived from the key

Rules:
- `step_key` is unique across the conversion pipeline
- `display_id` may remain numeric, but is not authoritative
- `workspace_slug` must be deterministic and path-safe
- the orchestrator must not infer identity from folder names or list position

Example shape:
- `step_key = "text-flow-assessment"`
- `display_id = "9.3"`
- `workspace_slug = "text-flow-assessment"`

## Workspace Layout

Conversion step workspaces should move from numeric folder names to key-based names.

Recommended shape:
- `phase-9/structural-clarity-assessment/`
- `phase-9/text-flow-assessment/`
- `phase-9/table-integrity-check/`
- `phase-10/quality-ratings/`

The exact parent layout may remain phase-based if that is already useful, but the step directory itself should be key-based.

This change should apply directly, without maintaining old numeric workspace names.

## Orchestrator Behavior

The orchestrator should consume a registry ordered by stable keys rather than relying on list position or numeric parsing to determine execution identity.

Required behavior:
- resolve the active step from the registry key
- persist the current step using the key
- resume by key, not by numeric directory name
- render phase and step progress in display order
- continue to show numeric labels in logs for readability

Resume handling should use the key stored in state or step metadata as the source of truth.

## Logging and Status Output

User-facing output should remain readable and familiar:
- logs should continue to say `Step 9.3`
- phase headers can continue to render numeric display numbering
- error messages should mention the display id when that helps diagnosis

Internal key values may be shown in debug contexts, but they should not replace the display labels in normal output.

## Error Handling

The new model should fail fast when key identity is inconsistent:
- missing `step_key` should be a configuration error
- duplicate `step_key` values should fail startup
- duplicate `display_id` values may fail if they would make status output ambiguous
- a resume request for an unknown key should fail deterministically
- a workspace path that does not match the expected key-based contract should fail clearly

Because backward compatibility is out of scope, the implementation should not spend effort trying to auto-detect or migrate numeric-only old directories.

## Testing Strategy

Add tests that prove:
- step registry ordering is explicit and key-driven
- the orchestrator resumes using stable keys
- logs still expose numeric display ids
- workspace paths are generated from step keys
- step insertion or reordering does not require renaming existing keys

The most important regression to prevent is accidental reintroduction of folder-name-driven identity.

## Implementation Boundaries

This feature should be limited to the conversion pipeline and the workspace layout it owns.

In scope:
- conversion orchestrator identity and resume plumbing
- conversion step registry identity model
- workspace path generation
- display-id rendering in logs
- tests for the new identity contract

Out of scope:
- prep registry refactors
- new agent behaviors
- review workflows
- artifact semantics beyond path identity

