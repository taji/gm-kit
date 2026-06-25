# Feature Specification: E7-01 Key-Based Prep Registry Foundation

**Feature Branch**: `010-key-based-prep-registry`  
**Created**: 2026-04-01  
**Status**: Draft  
**Input**: User description: "Feature: E7-01 Key-Based Prep Registry Foundation (Epic 7)\n\nCreate the specification for a key-based phase/step registry foundation for the new prep-first pipeline command `gmkit analyze-and-prep-pdf`.\n\nContext:\n- This is part of Epic 7 (Analyze-and-Prep Refactor).\n- E4-08a is superseded by Epic 7 and should be treated as historical pointer only.\n- We must preserve phase + step concepts, but remove hard coupling to numeric IDs in orchestrator/file naming.\n- Registry is code-first (no separate config requirement in v1).\n\nRequired outcomes:\n1) Define a typed registry model for phases and steps with:\n   - stable phase keys\n   - stable step keys\n   - explicit sortable execution order\n   - handler reference mechanism\n   - step metadata needed for orchestration/logging\n2) Define how display numbering is generated for logs/UI (alias only, not identity).\n3) Define orchestration behavior driven by key/order, not numeric filenames.\n4) Define insertion behavior (new steps can be added without renumbering existing IDs/files).\n5) Define acceptance criteria and tests for deterministic ordering, insertion safety, and readable logs.\n\nCanonical prep phase keys (must be used exactly):\n- prep.initialize-workspace\n- prep.analyze-document\n- prep.extract-assets\n- prep.derive-structure\n- prep.plan-chunks\n- prep.prepare-guidance\n- prep.propose-annotations\n- prep.review-annotations\n- prep.finalize-prep-artifacts\n\nExamples of step key style (use this naming pattern):\n- prep.derive-structure.acquire-canonical-toc\n- prep.plan-chunks.pack-chapters-to-budget\n- prep.review-annotations.capture-skip-page-ranges\n\nConstraints:\n- Keep TOC-first policy in mind (heading annotations out of scope).\n- Keep both interactive and non-interactive prep support in mind.\n- Do not require backward compatibility with pre-E4-08a artifacts.\n- Reuse/extract existing logic where possible in later features; this feature is foundation-only.\n\nOut of scope for E7-01:\n- Full analyze/prep command implementation\n- Full conversion gating integration\n- Full annotation/guidance/chunking implementation details beyond what’s needed to define registry interfaces\n\nSuccess looks like:\n- A clear, implementable registry spec with stable key conventions and phase/step boundaries.\n- Future Epic 7 features can plug into this registry without numeric renumbering churn."

## Clarifications

### Session 2026-04-03

- Q: How should the registry handle two steps in the same phase that have the same `order` value? → A: Require `order` to be unique within each phase; fail validation on duplicates.
- Q: Should `order` be scoped per phase or globally across all phases? → A: Per phase. Phase sequence is controlled by phase-level `order`; step sequence is controlled by step `order` within each phase. Logs should show a composite numeric display ID (for example `100.300` or equivalent).
- Q: When should handler references be validated (import/bind checks)? → A: Validate all handler references at registry initialization/startup and fail fast before execution begins.
- Q: Should the composite display ID format (e.g., `100.300`) be fixed in the contract or configurable? → A: Use default fixed format (`phaseOrder.stepOrder`) with formatter abstraction so presentation can evolve later without changing key identity semantics.
- Q: What numeric type should `order` use in registry definitions? → A: Integer only.
- Q: How should the registry handle two phases that have the same phase-level `order` value? → A: Require unique phase `order` values; fail validation on duplicates.
- Q: If an optional Agent-assisted handler fails validation/import at startup, what should registry initialization do? → A: Fail startup for required/core handlers; allow optional handlers to be disabled with explicit warning.
- Q: How should disabled optional handlers be represented in runtime/log output? → A: Register with status `DISABLED_OPTIONAL` and include startup warning + reason in logs/status output.
- Q: How should “required/core” vs “optional” classification be set for handlers? → A: Explicit field in each step definition (for example `handler_policy: required|optional`).
- Q: What should happen if a step definition omits the required handler policy field (`required|optional`)? → A: Fail registry validation/startup with actionable error.
- Q: What security/privacy rule should apply to registry validation errors and logs? → A: Errors/logs must redact secrets and avoid exposing sensitive absolute local paths.

## Current Implementation References (Non-Normative)

These references document where numeric coupling exists today in the conversion pipeline so E7-01 migration work can evolve existing logic instead of re-inventing it.

- Orchestration and numeric phase/step routing:
  - `src/gm_kit/pdf_convert/orchestrator.py`
  - `src/gm_kit/pdf_convert/phases/base.py`
- State model with numeric phase and `N.N` step assumptions:
  - `src/gm_kit/pdf_convert/state.py`
- Existing phase implementations with hard-coded numeric step IDs:
  - `src/gm_kit/pdf_convert/phases/phase0.py`
  - `src/gm_kit/pdf_convert/phases/phase4.py`
  - `src/gm_kit/pdf_convert/phases/phase6.py`
  - `src/gm_kit/pdf_convert/phases/phase8.py`
- Agent-step runtime and file/schema naming tied to numeric step IDs:
  - `src/gm_kit/pdf_convert/agents/agent_step.py`
  - `src/gm_kit/pdf_convert/agents/rubrics.py`
  - `src/gm_kit/pdf_convert/agents/schemas/step_*.schema.json`
  - `src/gm_kit/pdf_convert/agents/instructions/step_*.md`
  - `src/gm_kit/pdf_convert/agents/instructions/step_*.py`

These are baseline references only; requirements remain implementation-agnostic.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute Prep in Stable Registry Order (Priority: P1)

As a developer implementing the prep pipeline, I need orchestration to run prep phases and steps by stable keys and explicit order values so I can add or insert steps without renumbering filenames or breaking orchestration wiring.

**Why this priority**: This is the foundational dependency for all Epic 7 prep work and prevents repeated renumbering churn.

**Independent Test**: Register phases/steps with keys and order values, execute orchestration, and verify execution follows deterministic order even when a new mid-sequence step is inserted.

**Acceptance Scenarios**:

1. **Given** a prep registry with valid phase and step keys and sortable order values, **When** the orchestrator runs prep, **Then** execution follows the ordered registry rather than numeric file naming.
2. **Given** an existing registered step set, **When** a new step is inserted between two existing steps, **Then** existing keys remain unchanged and orchestration executes in the new intended order.

---

### User Story 2 - Use Human-Readable Display Numbering Without Identity Coupling (Priority: P2)

As an operator reading logs, I need readable phase/step numbering in output while the system internally identifies work by stable keys.

**Why this priority**: Logs must remain understandable without reintroducing coupling to numeric identities.

**Independent Test**: Execute registry-based prep and verify logs include generated display numbering while state/runtime references stable keys.

**Acceptance Scenarios**:

1. **Given** a registry-based prep execution, **When** logs are written, **Then** each phase/step has generated display numbering and key references remain authoritative in state/runtime artifacts.

---

### User Story 3 - Enforce Canonical Prep Phase Boundaries (Priority: P3)

As a feature developer, I need canonical prep phase keys and grouping boundaries so Epic 7 features can implement steps consistently across teams and sessions.

**Why this priority**: Stable boundaries reduce drift and conflicting implementations across follow-on features.

**Independent Test**: Validate that the registry accepts only canonical phase keys for prep v1 and rejects invalid or duplicate phase registration.

**Acceptance Scenarios**:

1. **Given** prep registry initialization, **When** canonical phase keys are registered, **Then** registry initialization succeeds and phase ordering is deterministic.
2. **Given** a duplicate or unknown phase key in prep registration, **When** registry validation runs, **Then** initialization fails with actionable error output.

---

### Edge Cases

- What happens when two steps have the same `order` value within a phase?
- How does the registry handle a step that references a non-existent phase key?
- What happens when a handler reference is invalid or cannot be imported?
- How does the system behave when one canonical phase has zero registered steps?
- What happens if generated display numbering changes after inserting steps between existing entries?
- How are startup validation/log messages sanitized so they do not leak secrets or sensitive absolute local paths?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define a code-first typed registry model for prep phases and steps.
- **FR-002**: The system MUST identify prep phases by stable phase keys and prep steps by stable step keys.
- **FR-003**: The system MUST support these exact canonical prep phase keys:
  - `prep.initialize-workspace`
  - `prep.analyze-document`
  - `prep.extract-assets`
  - `prep.derive-structure`
  - `prep.plan-chunks`
  - `prep.prepare-guidance`
  - `prep.propose-annotations`
  - `prep.review-annotations`
  - `prep.finalize-prep-artifacts`
- **FR-004**: The system MUST execute phases and steps using explicit sortable `order` values rather than numeric filenames or numeric step identifiers.
- **FR-004a**: The system MUST determine phase execution order using a phase-level `order` field.
- **FR-004b**: The system MUST require integer `order` values for both phase-level and step-level ordering.
- **FR-004c**: The system MUST enforce unique phase-level `order` values and fail validation when duplicate phase orders are detected.
- **FR-005**: The system MUST treat key identity (`phase_key`, `step_key`) as authoritative for orchestration and runtime/state references.
- **FR-006**: The system MUST generate display numbering aliases for logs/UI without using those display numbers as runtime identity.
- **FR-006a**: The system MUST render a composite numeric display alias for logs/UI that reflects ordered phase and step positions (for example `100.300` or equivalent format), while keeping key identity authoritative.
- **FR-006b**: The system MUST use `phaseOrder.stepOrder` as the default display alias format and keep formatting behind an internal formatter abstraction to allow future display changes without changing runtime key identity.
- **FR-007**: The system MUST allow insertion of new steps between existing steps without requiring renaming of existing keys.
- **FR-008**: The system MUST validate registry integrity at initialization, including duplicate key detection, missing phase references, and non-sortable order values.
- **FR-008a**: The system MUST enforce unique `order` values per phase and fail registry validation when duplicates are detected within the same phase.
- **FR-009**: The system MUST support handler references for steps and fail with actionable errors when handler binding/import fails.
- **FR-009a**: The system MUST validate all registered handler references during initialization/startup and fail fast before any phase/step execution when validation fails.
- **FR-009b**: The system MUST classify handlers as required/core or optional. Startup validation failures in required/core handlers MUST fail initialization; failures in optional handlers MUST disable those handlers and emit explicit warnings.
- **FR-009c**: The system MUST require explicit handler policy classification in each step definition (for example `required` or `optional`) and MUST NOT infer policy solely from phase, namespace, or naming convention.
- **FR-009d**: The system MUST fail registry validation/startup when a step definition omits required handler policy classification and MUST emit an actionable error message.
- **FR-009e**: Actionable startup/validation errors MUST include, at minimum: failing `step_key` (or `phase_key` for phase-level errors), failure class, and a concrete remediation hint.
- **FR-010**: The system MUST preserve deterministic execution order for identical registry inputs.
- **FR-011**: The system MUST expose enough step metadata in the registry to support orchestration and logging (at minimum: phase key, step key, order, handler reference, display name).
- **FR-012**: The system MUST include unit tests for deterministic ordering and insertion behavior that prove no key renumbering is required when adding steps.
- **FR-013**: The system MUST include unit tests that verify generated display numbering remains log-readable while key identity remains authoritative.
- **FR-014**: The system MUST remain compatible with both interactive and non-interactive prep execution modes by keeping registry concerns mode-agnostic.
- **FR-015**: The system MUST NOT require backward compatibility for pre-E4-08a artifacts in this feature.
- **FR-016**: The system MUST scope E7-01 to registry foundation concerns and not require full analyze/prep implementation.
- **FR-017**: The registry foundation MUST support Epic 7 execution category boundaries: Code-first default handlers, optional Agent-assisted handlers, and User-interaction step registration, while keeping runtime identity key-based.
- **FR-018**: The registry foundation MUST support E4-07a-i logging parity by exposing phase/step metadata required to render standardized phase headers and step status entries with deterministic, testable formatting.
- **FR-018a**: The system MUST represent disabled optional handlers as `DISABLED_OPTIONAL` in status/log outputs and include the startup disable reason in emitted warnings/status messages.
- **FR-019**: The system MUST sanitize registry validation and startup log/error output so it does not expose secrets (tokens/keys/credentials) or sensitive absolute local filesystem paths.

### Key Entities *(include if feature involves data)*

- **PrepPhaseDefinition**: Registry entity describing a prep phase (`phase_key`, `order`, display metadata).
- **PrepStepDefinition**: Registry entity describing a prep step (`step_key`, `phase_key`, `order`, handler reference, display metadata, orchestration/logging metadata).
- **PrepRegistry**: Collection and validation layer for phase/step definitions plus deterministic ordering behavior.
- **DisplaySequenceMapping**: Derived mapping that assigns human-readable display numbering aliases from ordered phase/step definitions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new prep step can be inserted between two existing steps without changing any pre-existing phase or step keys.
- **SC-002**: Re-running orchestration with unchanged registry definitions yields the same ordered phase/step execution sequence across runs.
- **SC-003**: Registry initialization rejects duplicate keys, invalid phase references, and invalid order fields with explicit actionable errors.
- **SC-004**: Log output for registry-driven execution includes generated display numbering for 100% of executed phases/steps while runtime identity uses stable keys.
- **SC-005**: Registry metadata is sufficient for downstream prep logging to produce E4-07a-i style phase/step structures with deterministic assertions in tests.
