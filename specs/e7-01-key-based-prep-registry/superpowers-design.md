# E7-01 Key-Based Prep Registry Foundation Design

## Goal

Define a code-first registry foundation for the prep-first pipeline so prep phases and steps use stable key identity, deterministic ordering, and presentation-only numeric aliases.

## Scope

This design is limited to the registry foundation for `gmkit analyze-and-prep-pdf`.

Included:
- typed phase and step definitions
- canonical prep phase boundaries
- deterministic ordering rules
- generated display alias rules
- startup validation behavior
- handler availability policy
- logging metadata contract
- tests for ordering, insertion safety, validation, and sanitization

Excluded:
- `gmkit analyze-and-prep-pdf` CLI command implementation
- prep artifact generation
- prep/conversion gating integration
- migration of the existing numeric conversion pipeline
- annotation, guidance, chunking, or review workflow implementation

## Canonical Inputs

This design uses the `BACKLOG.md` E7-01 prompt as the canonical scope source and carries forward previously settled E7-01 decisions unless explicitly replaced.

Settled baseline decisions retained:
- `order` is integer-only
- phase `order` values must be unique
- step `order` values must be unique within each phase
- all handlers validate at startup
- required handler failures fail startup
- optional handler failures become `DISABLED_OPTIONAL`
- display alias defaults to `phaseOrder.stepOrder`
- validation and startup output must sanitize secrets and sensitive absolute local paths

## Architecture

E7-01 introduces a prep-registry subsystem that is separate from the current numeric conversion pipeline. The subsystem defines prep work as typed code objects, validates those objects at startup, and exposes one deterministic ordered view for future prep orchestration and logging.

Runtime identity is always key-based:
- `phase_key` is the authoritative phase identity
- `step_key` is the authoritative step identity

Numeric labels are generated only for human-readable presentation:
- display aliases are derived from validated phase and step `order` values
- display aliases are not used for orchestration, persistence identity, or handler lookup

This keeps the foundation clean and allows later Epic 7 features to build on it without numeric renumbering churn.

## Canonical Prep Phases

The registry must support these exact phase keys:
- `prep.initialize-workspace`
- `prep.analyze-document`
- `prep.extract-assets`
- `prep.derive-structure`
- `prep.plan-chunks`
- `prep.prepare-guidance`
- `prep.propose-annotations`
- `prep.review-annotations`
- `prep.finalize-prep-artifacts`

## Core Entities

### `PrepPhaseDefinition`

Required fields:
- `phase_key`
- `order`
- `display_name`

Responsibilities:
- define canonical prep phase identity
- define phase ordering relative to other prep phases
- expose display metadata needed by future logging and UI layers

### `PrepStepDefinition`

Required fields:
- `step_key`
- `phase_key`
- `order`
- `handler_ref`
- `handler_policy`
- `display_name`

Required behavior:
- `phase_key` must reference a registered prep phase
- `handler_policy` must be explicit: `required` or `optional`
- step ordering is scoped within the owning phase

Responsibilities:
- define stable prep step identity
- define deterministic in-phase execution order
- describe handler binding target
- expose metadata needed for orchestration and logging

### `PrepRegistry`

Responsibilities:
- register phase and step definitions
- validate registry integrity at startup
- resolve deterministic ordered execution views
- validate handler availability
- mark optional-handler failures as disabled status instead of startup-fatal

### `DisplaySequenceMapping`

Responsibilities:
- derive generated display aliases from validated ordered registry content
- expose readable phase/step numbering for logs and UI
- remain completely separate from runtime identity

## Ordering Rules

The system orders phases by phase-level integer `order`.

The system orders steps by step-level integer `order` within each phase.

Validation rules:
- duplicate phase keys fail startup
- duplicate phase `order` values fail startup
- duplicate step keys fail startup
- duplicate step `order` values within the same phase fail startup
- missing phase references fail startup
- non-integer `order` values fail startup

Determinism rules:
- identical registry definitions must yield identical ordered output across runs
- no hidden dependence on filenames, module numbering, or declaration order may exist once registry validation is complete

## Display Alias Rules

The default display alias format is `phaseOrder.stepOrder`.

Examples:
- a phase might display as `100`
- a step might display as `100.300`

Rules:
- aliases are generated from validated order values
- aliases are log/UI aids only
- aliases may change when order changes
- alias changes are acceptable because key identity remains authoritative

The alias formatter should remain an internal abstraction so the presentation format can evolve later without changing runtime semantics.

## Handler Validation and Status Policy

All handler references are validated at startup before any future prep execution begins.

Required handler behavior:
- import or bind failure is startup-fatal
- the system emits an actionable sanitized error

Optional handler behavior:
- import or bind failure is not startup-fatal
- the step is retained with status `DISABLED_OPTIONAL`
- the disable reason is recorded for deterministic logging/status output

The registry must never infer handler policy from naming or namespace conventions. Every step definition must declare `handler_policy` explicitly.

## Logging Metadata Contract

E7-01 does not implement prep logging, but it must provide enough metadata for later Epic 7 work to render readable prep logs in the established E4-07a-i style.

The registry foundation must expose, at minimum:
- phase key
- step key
- phase order
- step order
- display alias
- display name
- handler policy
- handler availability status
- disable reason for optional failures, when present

This preserves compatibility with later phase headers and step status entries while avoiding numeric identity coupling.

## Insertion and Change Safety

Adding a new step between two existing steps must not require renaming any existing `step_key` or `phase_key`.

Allowed change pattern:
- keep keys stable
- assign a new integer `order`
- regenerate ordered views and display aliases

Not allowed:
- encoding ordering in filenames
- encoding identity in display numbering
- coupling handler lookup to numeric step names

## Security and Sanitization

Validation errors and startup status output must sanitize:
- tokens
- credentials
- secrets
- sensitive absolute local filesystem paths

Error messages must remain actionable while avoiding disclosure of machine-specific or secret-bearing values.

Minimum actionable error content:
- failing `phase_key` or `step_key`
- failure class
- concrete remediation hint

## Testing Strategy

E7-01 test coverage must prove:
- canonical prep phases validate successfully
- invalid or duplicate phases fail with actionable errors
- per-phase step ordering is deterministic
- inserting a new mid-sequence step requires no key renaming
- generated display aliases remain readable while keys remain authoritative
- required handler failures stop startup
- optional handler failures produce `DISABLED_OPTIONAL`
- emitted errors and status output are sanitized

## Acceptance Outcome

E7-01 is complete when the project has a clear, implementable registry foundation that:
- establishes stable prep phase and step identity
- removes numeric-ID coupling from new prep registry design
- supports deterministic ordering and insertion safety
- provides the metadata needed for future prep orchestration and logging
- stays strictly limited to foundation concerns, leaving command wiring and migration mechanics to later Epic 7 features
