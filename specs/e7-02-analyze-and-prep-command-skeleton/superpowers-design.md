# E7-02 Analyze-and-Prep Command Skeleton + Artifact Contract Design

## Goal

Create the first real `gmkit analyze-and-prep-pdf` command surface, prep state skeleton, and validated prep artifact contract so Epic 7 has a runnable prep command before existing analysis logic is migrated.

## Scope

Included:
- `gmkit analyze-and-prep-pdf` CLI command definition
- prep-specific CLI helper and prep orchestrator skeleton
- prep workspace contract rooted at `<workspace>/prep/`
- prep state tracking and completion marker
- required prep manifest contract and versioning
- non-interactive flags and behavior required for harness/CI usage
- deterministic prep logging output contract for skeleton execution
- tests for command routing, artifact emission, status/resume behavior, and non-interactive failure handling

Excluded:
- rehosting existing conversion analysis logic
- hard gating `pdf-convert` on prep completion
- migration of numeric conversion phases or numeric `--phase` / `--from-step` controls
- full prep artifact payload production beyond what is required to establish and validate the contract
- agent slash-command wrappers around the CLI command

## Canonical Inputs

This design uses the `BACKLOG.md` E7-02 prompt as the canonical scope source and builds directly on the approved E7-01 registry foundation.

Previously settled constraints retained:
- prep artifacts live inside the normal conversion workspace as a `prep/` subtree
- `gmkit analyze-and-prep-pdf` creates or reuses the normal workspace from the input PDF path
- E7-02 defines the prep artifact contract now but does not yet hard-gate `pdf-convert`
- the stable product surface is the real `gmkit` CLI command; any future agent slash command is a separate wrapper layer

## Architecture

E7-02 adds a prep-specific execution path that parallels `pdf-convert` without reusing the numeric conversion phase engine.

Primary components:
- CLI entry in `src/gm_kit/cli.py` for `analyze-and-prep-pdf`
- prep CLI helper module parallel to `pdf_convert/cli_helpers.py`
- prep orchestrator module under `src/gm_kit/pdf_convert/prep/`
- prep artifact/state contract rooted at `<workspace>/prep/`
- prep logging surface driven by the E7-01 registry foundation

Boundary rules:
- no changes to numeric conversion phase execution semantics
- no hard conversion gating yet
- no rehosting of existing conversion analysis logic yet
- no numeric prep execution controls

This preserves the E7-01 separation between the new prep flow and the existing numeric conversion pipeline.

## Workspace Model

`gmkit analyze-and-prep-pdf <pdf-path>` creates or reuses the same normal conversion workspace model already used by `pdf-convert`.

Prep-specific artifacts live under:
- `<workspace>/prep/`

This prevents the introduction of a second workspace model and keeps future conversion/prep handoff local to one workspace tree.

## Command Surface

The real product command for E7-02 is:
- `gmkit analyze-and-prep-pdf <pdf-path>`

Minimum flags:
- `--output`
- `--resume`
- `--status`
- `--yes`

Deferred flags:
- numeric phase controls such as `--phase`
- numeric step controls such as `--from-step`
- any flags that imply reuse of the existing numeric phase engine

Rationale:
- E7-02 must be runnable directly by users, harnesses, and CI
- the command must not inherit numeric-control assumptions from `pdf-convert`

## CLI Behavior

Fresh run behavior:
- resolve the source PDF path
- create or reuse the normal conversion workspace
- create `<workspace>/prep/`
- initialize prep state and manifest skeleton artifacts
- run the prep orchestrator skeleton using the E7-01 registry
- write the completion marker only after the prep contract is consistent

Status behavior:
- `--status` reads prep state from the prep subtree
- status is prep-specific and does not proxy to numeric conversion status

Resume behavior:
- `--resume` continues a partial prep run from prep state
- resume does not depend on numeric conversion state machine semantics

Non-interactive behavior:
- `--yes` suppresses prompts
- ambiguous workspace selection or resume/status resolution must fail fast under `--yes`
- no interactive menus may appear in harness/CI mode

## Prep Artifact Contract

E7-02 establishes a minimal but strict prep contract under `<workspace>/prep/`:
- `prep-manifest.json`
- `prep-state.json`
- `prep-complete.json`
- `logs/prep.log`

### `prep-manifest.json`

Responsibilities:
- define contract version
- record source PDF identity and workspace identity
- record registry-driven phase/step summary
- record artifact inventory and artifact readiness state

E7-02 requirement:
- the manifest shape must be real, versioned, and validated even if many downstream payload artifacts are still placeholders

### `prep-state.json`

Responsibilities:
- track prep command lifecycle state
- record in-progress vs complete vs failed prep status
- support deterministic status/resume behavior

### `prep-complete.json`

Responsibilities:
- act as the machine-readable completion marker for later Epic 7 work
- exist only when the prep contract is internally consistent

Write rule:
- must be written only after manifest and state are consistent
- must never exist for partial or failed prep runs

### `logs/prep.log`

Responsibilities:
- serve as the canonical persisted prep log for skeleton execution
- support deterministic test assertions on prep log shape

## Manifest Content Requirements

At minimum, the prep manifest must expose:
- `contract_version`
- source PDF path or normalized source identity
- workspace path or normalized workspace identity
- prep command metadata
- registry phase summary
- registry step summary
- artifact inventory with status per artifact
- prep completion status

The manifest is the authoritative index of prep outputs for later features.

## Prep State Model

The prep state model should be independent from the numeric conversion state machine.

Minimum states:
- initialized
- running
- completed
- failed

The state file must support:
- status inspection
- safe resume detection
- deterministic test assertions

E7-02 does not need full recovery sophistication; it only needs a reliable skeleton lifecycle.

## Prep Logging Contract

E7-02 does not implement full prep logic, but it must define and emit the visual logging structure that later Epic 7 work will fill in.

The prep log contract must align with E4-07a-i style expectations:
- phase header blocks
- step status blocks
- warnings and errors rendered distinctly
- deterministic ordering for assertions

E7-02 logging output must be driven by E7-01 registry metadata, including:
- phase key
- step key
- display alias
- display name
- handler policy
- handler status
- disable reason when present

The output can remain skeleton-grade, but its structure must be stable and testable.

## Orchestrator Skeleton

The prep orchestrator is a new prep-only runtime surface under `gm_kit.pdf_convert.prep`.

Responsibilities:
- initialize prep workspace artifacts
- read the E7-01 registry
- render deterministic skeleton progress/logging for phases and steps
- update prep state as execution proceeds
- write manifest/state/complete outputs in the correct order

Non-responsibilities:
- migrating existing metadata/preflight/image/text-only logic
- invoking the numeric phase registry
- enforcing prep requirements on `pdf-convert`

## Error Handling

E7-02 error handling must be explicit and narrow:
- invalid PDF path fails before workspace creation
- ambiguous workspace resolution fails fast under `--yes`
- prep manifest/state/complete writes must avoid partial false-complete states
- registry startup/handler errors must surface through the E7-01 validation model
- prep status/resume must not silently fall back to numeric conversion state behavior

The command should fail clearly rather than guessing when prep workspace state is ambiguous.

## Testing Strategy

E7-02 test coverage must prove:
- the CLI command is registered and routes to prep helpers correctly
- a workspace can be created from a PDF input path
- the prep subtree is created inside the normal conversion workspace
- prep status and resume behavior use prep state, not conversion state
- `prep-manifest.json`, `prep-state.json`, `prep-complete.json`, and `logs/prep.log` are emitted on successful skeleton execution
- non-interactive `--yes` behavior fails fast on ambiguous conditions
- prep log output shape is deterministic and registry-driven
- the completion marker is written only after manifest and state consistency is established

## Acceptance Outcome

E7-02 is complete when the project has a runnable `gmkit analyze-and-prep-pdf` command that:
- creates or reuses the normal workspace
- emits a validated `prep/` subtree contract
- tracks prep lifecycle independently from numeric conversion state
- supports non-interactive harness/CI usage
- provides a stable prep command/orchestrator foundation for E7-03 and later Epic 7 work
