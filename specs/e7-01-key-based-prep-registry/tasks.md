# Tasks: E7-01 Key-Based Prep Registry Foundation

**Input**: Design documents from `/specs/e7-01-key-based-prep-registry/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are required for this feature by project policy and specification requirements (FR-012, FR-013).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare module/test scaffolding for registry foundation work.

- [ ] T001 Create prep registry module scaffold in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T002 Create unit test module scaffold in `tests/unit/pdf_convert/test_prep_registry.py`
- [ ] T003 [P] Add shared type aliases/enums for handler policy and disabled status in `src/gm_kit/pdf_convert/prep_registry.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core registry models/validation primitives required by all user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Implement `PrepPhaseDefinition` and `PrepStepDefinition` models in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T005 Implement `PrepRegistry` container and deterministic ordering helpers in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T006 Implement structural validation for key uniqueness and phase references in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T007 Implement integer and uniqueness validation rules for phase/step `order` fields in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T008 [P] Add foundational unit tests for model creation and structural validation in `tests/unit/pdf_convert/test_prep_registry.py`

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Execute Prep in Stable Registry Order (Priority: P1) 🎯 MVP

**Goal**: Execute prep phases/steps deterministically via key-based registry and two-level ordering without numeric identity coupling.

**Independent Test**: Build a registry with multiple phases/steps, insert a new middle step, and verify deterministic execution order with unchanged pre-existing keys.

### Tests for User Story 1

- [ ] T009 [P] [US1] Add deterministic phase/step ordering test cases in `tests/unit/pdf_convert/test_prep_registry.py`
- [ ] T010 [P] [US1] Add insertion-without-key-renaming regression tests in `tests/unit/pdf_convert/test_prep_registry.py`
- [ ] T011 [US1] Add duplicate phase-order and duplicate step-order rejection tests in `tests/unit/pdf_convert/test_prep_registry.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement phase ordering by `phase.order` and step ordering by per-phase `step.order` in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T013 [US1] Implement explicit validation errors for duplicate phase `order` and duplicate per-phase step `order` in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T014 [US1] Implement registry query/iteration APIs that return stable key identity and ordered execution views in `src/gm_kit/pdf_convert/prep_registry.py`

**Checkpoint**: User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Use Human-Readable Display Numbering Without Identity Coupling (Priority: P2)

**Goal**: Provide composite numeric display aliases for logs/UI while keeping key identity authoritative.

**Independent Test**: Generate display mapping for a registry and verify alias format is deterministic (`phaseOrder.stepOrder`) and separate from runtime identity.

### Tests for User Story 2

- [ ] T015 [P] [US2] Add display mapping generation tests for default `phaseOrder.stepOrder` format in `tests/unit/pdf_convert/test_prep_registry.py`
- [ ] T016 [US2] Add tests that assert display aliases are non-authoritative and key identity remains canonical in `tests/unit/pdf_convert/test_prep_registry.py`
- [ ] T017 [US2] Add tests for formatter abstraction behavior and backward-compatible default output in `tests/unit/pdf_convert/test_prep_registry.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement `DisplaySequenceMapping` generation in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T019 [US2] Implement formatter abstraction with default `phaseOrder.stepOrder` output in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T020 [US2] Integrate display alias metadata exposure for downstream E4-07a-i style logging compatibility in `src/gm_kit/pdf_convert/prep_registry.py`

**Checkpoint**: User Story 2 is fully functional and independently testable.

---

## Phase 5: User Story 3 - Enforce Canonical Prep Phase Boundaries (Priority: P3)

**Goal**: Enforce canonical prep phase keys and strict startup handler validation policy (required vs optional).

**Independent Test**: Attempt registration with invalid/duplicate phases and invalid handler policy definitions; confirm startup validation behavior for required vs optional handlers.

### Tests for User Story 3

- [ ] T021 [P] [US3] Add canonical phase-key acceptance/rejection tests in `tests/unit/pdf_convert/test_prep_registry.py`
- [ ] T022 [P] [US3] Add handler policy requirement tests (`required|optional` must be explicit) in `tests/unit/pdf_convert/test_prep_registry.py`
- [ ] T023 [US3] Add startup validation tests for required handler failure (hard fail) and optional failure (`DISABLED_OPTIONAL`) in `tests/unit/pdf_convert/test_prep_registry.py`
- [ ] T024 [US3] Add diagnostics sanitization tests for secret/path redaction in `tests/unit/pdf_convert/test_prep_registry.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement canonical prep phase key validation in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T026 [US3] Implement explicit handler policy enforcement and missing-policy startup failure in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T027 [US3] Implement startup handler validation with required-fail and optional-disable behavior in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T028 [US3] Implement `DISABLED_OPTIONAL` status/reason tracking and exposure in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T029 [US3] Implement sanitized validation/log message utilities for secrets and sensitive absolute paths in `src/gm_kit/pdf_convert/prep_registry.py`

**Checkpoint**: User Story 3 is fully functional and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final integration quality checks and documentation sync for E7-01 output artifacts.

- [ ] T030 [P] Update `specs/e7-01-key-based-prep-registry/quickstart.md` with any implementation-specific command/path adjustments
- [ ] T031 [P] Add/refresh inline docstrings/comments for non-obvious registry validation logic in `src/gm_kit/pdf_convert/prep_registry.py`
- [ ] T032 Run targeted unit suite for registry foundation (`tests/unit/pdf_convert/test_prep_registry.py`) and capture pass status in feature journal
- [ ] T033 Run project quality gates (`just lint`, `just typecheck`, `just test-unit`) and resolve issues in touched files
- [ ] T034 Append implementation session details to `specs/e7-01-key-based-prep-registry/feature_journal.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2; MVP slice.
- **Phase 4 (US2)**: Depends on US1 foundational ordering APIs.
- **Phase 5 (US3)**: Depends on Phase 2; can be developed after US1/US2 interfaces are stable.
- **Phase 6 (Polish)**: Depends on completion of selected user stories.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational; no dependency on other stories.
- **US2 (P2)**: Depends on ordered registry outputs from US1.
- **US3 (P3)**: Depends on foundational registry models; independent of US2 display formatting logic.

### Within Each User Story

- Tests first (write/verify fail), then implementation.
- Validation rules before exposure/integration helpers.
- Story checkpoint must pass independently before advancing.

### Parallel Opportunities

- Setup tasks marked `[P]` can run in parallel.
- Foundational tests (T008) can run in parallel with model refinement after initial scaffold.
- US1 test tasks T009/T010 can run in parallel.
- US2 test tasks T015/T017 can run in parallel.
- US3 test tasks T021/T022 can run in parallel.
- Polish docs/journal updates (T030/T034) can run parallel with final verification prep.

---

## Parallel Example: User Story 1

```bash
# Parallel US1 tests
Task: "T009 [US1] deterministic ordering tests in tests/unit/pdf_convert/test_prep_registry.py"
Task: "T010 [US1] insertion-without-key-renaming tests in tests/unit/pdf_convert/test_prep_registry.py"

# Parallel US1 implementation split
Task: "T012 [US1] ordering engine in src/gm_kit/pdf_convert/prep_registry.py"
Task: "T013 [US1] duplicate-order validation in src/gm_kit/pdf_convert/prep_registry.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup).
2. Complete Phase 2 (Foundational).
3. Complete Phase 3 (US1).
4. Validate US1 independently (deterministic ordering + insertion behavior).

### Incremental Delivery

1. Deliver US1 (ordering core).
2. Deliver US2 (display alias mapping/log metadata).
3. Deliver US3 (canonical phase boundaries + startup policy/security sanitization).
4. Finalize with polish + quality gates.

### Parallel Team Strategy

1. Team completes Setup + Foundational together.
2. Then split:
   - Dev A: US1 core ordering
   - Dev B: US2 display mapping
   - Dev C: US3 handler policy + startup validation
3. Merge at polish phase and run full gates.

---

## Notes

- `[P]` tasks touch disjoint files or logically independent sections.
- Story labels map directly to spec user stories for traceability.
- Each user story must remain independently testable.
- Commit in small logical slices and keep tests aligned with each requirement batch.
