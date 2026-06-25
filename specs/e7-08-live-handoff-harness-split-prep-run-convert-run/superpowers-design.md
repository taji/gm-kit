# E7-08 Live Handoff Harness Split Design

**Goal:** Split the live handoff harness into explicit prep-run, convert-run, and end-to-end modes so the prep/convert artifact boundary is visible, testable, and reusable for unattended regression runs.

## Decision
Keep the existing harness entrypoints, but add an explicit workflow mode that chooses between:
- `prep-only`
- `convert-only`
- `prep-and-convert`

This is the smallest change that makes the handoff boundary explicit without introducing a second harness or changing the conversion commands themselves.

## Architecture
The Python harness remains the source of truth for orchestration. The shell wrapper stays a thin pass-through.

Mode behavior:
- `prep-only` runs `gmkit analyze-and-prep-pdf` and stops after prep completion
- `convert-only` assumes a prepared workspace already exists and runs `gmkit pdf-convert` against it
- `prep-and-convert` runs prep first, validates the generated prep artifacts, then runs conversion from the same workspace

The harness continues to:
- execute commands non-interactively
- capture console output and trace events
- validate step outputs for agent-driven conversion pauses
- support the existing resume loop for `pdf-convert`

## Artifact Boundary
The boundary between prep and convert should be explicit and observable.

Prep completion should be considered valid only when the workspace contains the prep outputs required by conversion, including:
- prep completion marker/state
- prep manifest
- metadata/preflight outputs
- baseline guidance outputs
- any prep artifacts required by the chosen conversion path

Convert-only mode should refuse to start if the workspace does not already contain a completed prep handoff. That keeps the boundary honest for regression runs.

## Data Flow
1. The harness resolves the workspace and mode.
2. If prep is requested, it runs `gmkit analyze-and-prep-pdf`.
3. It validates that prep artifacts exist and that the workspace is ready for conversion.
4. If conversion is requested, it runs `gmkit pdf-convert` against the same workspace.
5. If `pdf-convert` pauses for agent work, the harness executes the agent step and resumes until completion.

## Error Handling
Errors should fail the harness early and clearly:
- invalid mode or incompatible flags
- missing PDF for prep runs
- missing workspace or prep artifacts for convert-only runs
- step-output contract violations during pause/resume handling

The harness should not silently synthesize prep outputs. If prep is required for the chosen mode, the harness must make that explicit.

## Testing Strategy
Add tests for:
- workflow mode parsing and validation
- command construction for prep-only, convert-only, and prep-and-convert
- prep artifact boundary validation
- resume loop behavior remains unchanged for conversion pauses
- non-interactive execution still works for unattended regression runs

Keep the tests close to the harness helpers so the mode split is easy to maintain.
