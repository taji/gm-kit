# Research: E7-01 Key-Based Prep Registry Foundation

## Decision 1: Registry shape should be code-first dataclasses/protocols
- Decision: Implement phase/step registry definitions as typed Python objects (dataclasses/TypedDict + validation), not external YAML/JSON config in v1.
- Rationale: E7-01 is a foundation refactor in an existing Python CLI codebase; typed in-code definitions reduce parsing surface, keep refactors local, and align with mypy/pytest workflow.
- Alternatives considered:
  - External config-first registry files: deferred to later if runtime configurability becomes a requirement.

## Decision 2: Deterministic ordering uses two levels (`phase.order`, `step.order`)
- Decision: Use integer phase-level ordering and integer step-level ordering with uniqueness constraints.
- Rationale: Matches clarifications in spec (`FR-004a/b/c`, `FR-008a`) and supports insertion without renumbering key identity.
- Alternatives considered:
  - Global step ordering only: rejected for maintainability and readability.
  - Float or lexical ordering: rejected due to nondeterminism risk and validation complexity.

## Decision 3: Runtime identity must be key-based; numeric IDs are display-only
- Decision: Use stable `phase_key` and `step_key` for orchestration/state identity; generate composite display alias (`phaseOrder.stepOrder`) for logs/UI.
- Rationale: Preserves migration goal away from numeric coupling while retaining operator-friendly output and parity with E4-07a-i logging style.
- Alternatives considered:
  - Numeric identity as source of truth: rejected (current pain point).

## Decision 4: Startup validation policy is strict for required handlers
- Decision: Validate all handlers at startup; fail fast for required/core handlers; disable optional handlers with explicit warning and status `DISABLED_OPTIONAL`.
- Rationale: Supports code-first reliability and optional Agent-assisted extension model from Epic 7.
- Alternatives considered:
  - Lazy validation at execution time: rejected due to late failures and harder diagnostics.

## Decision 5: Security/privacy in diagnostics must be explicit
- Decision: Registry validation and startup errors/logs must sanitize secrets and sensitive absolute local paths.
- Rationale: Prevents accidental leakage in local logs and CI outputs while keeping actionable diagnostics.
- Alternatives considered:
  - Best-effort/no explicit rule: rejected due to ambiguity and audit risk.

## Decision 6: Contracts should be internal-facing for this feature
- Decision: Define internal registry contracts for phase/step definitions and validation outputs in feature docs/contracts.
- Rationale: E7-01 does not add a new public external API; contract artifacts still reduce ambiguity for E7-02+ implementation.
- Alternatives considered:
  - No contracts folder: rejected because this feature is foundation architecture and benefits from explicit interface boundaries.
