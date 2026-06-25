# Data Model: E7-01 Key-Based Prep Registry Foundation

## Entities

## 1) PrepPhaseDefinition
- Purpose: Defines a prep phase in registry order.
- Fields:
  - `phase_key: str` (unique, canonical format `prep.<verb>-<noun>`)
  - `order: int` (required, unique across phases)
  - `display_name: str` (human-readable label)
  - `description: str | None`
- Validation:
  - `phase_key` must be unique.
  - `order` must be integer and unique.

## 2) PrepStepDefinition
- Purpose: Defines an executable step within a phase.
- Fields:
  - `step_key: str` (unique, canonical format `<phase_key>.<action>`)
  - `phase_key: str` (must reference an existing `PrepPhaseDefinition.phase_key`)
  - `order: int` (required, unique within phase)
  - `handler_ref: str` (import/call target)
  - `handler_policy: Literal["required", "optional"]`
  - `display_name: str`
  - `description: str | None`
- Validation:
  - `step_key` unique globally.
  - `order` integer, unique per phase.
  - `handler_policy` required and explicit (no inference).

## 3) PrepRegistry
- Purpose: Holds validated phase and step definitions and exposes deterministic execution order.
- Fields:
  - `phases: list[PrepPhaseDefinition]`
  - `steps: list[PrepStepDefinition]`
  - `disabled_optional_steps: list[DisabledStepRecord]`
- Derived:
  - Ordered phases: sort by `phase.order`.
  - Ordered steps per phase: sort by `step.order`.

## 4) DisabledStepRecord
- Purpose: Tracks optional handlers disabled during startup validation.
- Fields:
  - `step_key: str`
  - `reason: str`
  - `status: Literal["DISABLED_OPTIONAL"]`

## 5) DisplaySequenceMapping
- Purpose: Logging/UI mapping from key identity to composite numeric display alias.
- Fields:
  - `phase_key -> phase_display_order`
  - `step_key -> "<phaseOrder>.<stepOrder>"`
- Rules:
  - Display alias is not runtime identity.
  - Default format `phaseOrder.stepOrder`, formatter abstraction may evolve display format later.

## Relationships
- `PrepPhaseDefinition (1) -> (many) PrepStepDefinition`
- `PrepRegistry` aggregates all phases/steps and validation results.
- `DisabledStepRecord` references `PrepStepDefinition` entries where policy is `optional`.

## State/Validation Transitions
1. Load definitions.
2. Validate structural constraints (keys, order uniqueness, phase references, required fields).
3. Validate handler imports/binding at startup.
4. Fail initialization on required handler failures.
5. Mark optional failures as `DISABLED_OPTIONAL` and continue.
6. Emit sanitized diagnostics.
