# Tasks: PDF→Markdown Agent-Driven Pipeline

**Input**: Design documents from `/specs/007-agent-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are required for this feature (FR-006 and plan Test Strategy).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

**Confirmed Clarifications**:
- Token threshold: 100,000 tokens default (via `GM_TOKEN_THRESHOLD` env var)
- Medium criticality: Flag + continue (not skip) for debugging visibility
- Step 7.7/8.7 images: Keep after pipeline; offer cleanup helper
- Corpus test commands: `test-corpus-homebrewery`, `test-corpus-b2`, `test-corpus-coc`
- Step 8.7 image paths: Relative to project root (e.g., `tests/fixtures/pdf_convert/agents/inputs/table_pages/...`)
- Step 9.1: Remove stub completely (not just no-op)

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the agent-step package/test skeleton and feature-specific fixture directories.

- [X] T001 Create agent package skeleton in `src/gm_kit/pdf_convert/agents/__init__.py`
- [X] T002 [P] Create agent package modules `src/gm_kit/pdf_convert/agents/base.py`, `src/gm_kit/pdf_convert/agents/errors.py`, and `src/gm_kit/pdf_convert/agents/contracts.py`
- [X] T003 [P] Create agent I/O and preflight module stubs in `src/gm_kit/pdf_convert/agents/agent_step.py` and `src/gm_kit/pdf_convert/agents/token_preflight.py`
- [X] T004 [P] Create instruction template directory and placeholder files in `src/gm_kit/pdf_convert/agents/instructions/` for steps `3.2`, `4.5`, `6.4`, `7.7`, `8.7`, `9.2-9.5`, `9.7-9.8`, `10.2-10.3`
- [X] T005 [P] Create schema and rubric directories in `src/gm_kit/pdf_convert/agents/schemas/` and `src/gm_kit/pdf_convert/agents/rubrics/`
- [X] T006 [P] Create test package skeletons in `tests/unit/pdf_convert/agents/`, `tests/contract/pdf_convert/agents/`, and `tests/integration/pdf_convert/agents/`
- [X] T007 [P] Create per-step fixture directories in `tests/fixtures/pdf_convert/agents/inputs/` and `tests/fixtures/pdf_convert/agents/golden/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared workspace handoff, schema validation, retry/error handling, and common definitions used by all stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T008 Implement shared step metadata/types in `src/gm_kit/pdf_convert/agents/base.py`
- [X] T009 Implement agent error classes (`AgentStepError`, `ContractViolation`) in `src/gm_kit/pdf_convert/agents/errors.py`
- [X] T010 Implement JSON Schema loading/validation helpers in `src/gm_kit/pdf_convert/agents/contracts.py`
- [X] T011 Implement workspace handoff write/read helpers (`step-input.json`, `step-instructions.md`, `step-output.json`) in `src/gm_kit/pdf_convert/agents/agent_step.py`
- [X] T012 Implement retry instruction append + retry budget handling in `src/gm_kit/pdf_convert/agents/agent_step.py`
- [X] T013 Implement FR-008 structured error envelope helpers in `src/gm_kit/pdf_convert/agents/agent_step.py`
- [X] T014 Implement token preflight threshold logic (`GM_TOKEN_THRESHOLD`, interactive skip, `--yes` auto-proceed) in `src/gm_kit/pdf_convert/agents/token_preflight.py`
- [X] T015 Implement shared step registry (13 in-scope steps, 9.1 excluded, criticality metadata) in `src/gm_kit/pdf_convert/agents/registry.py`
- [X] T016 Implement package exports for public API (`write_agent_inputs`, `read_agent_output`, errors, registry access) in `src/gm_kit/pdf_convert/agents/__init__.py`
- [X] T017 [P] Add unit tests for base types and step registry in `tests/unit/pdf_convert/agents/test_base.py`
- [X] T018 [P] Add unit tests for error envelopes and exception types in `tests/unit/pdf_convert/agents/test_errors.py`
- [X] T019 [P] Add unit tests for schema load/validation helpers in `tests/unit/pdf_convert/agents/test_contracts.py`
- [X] T020 [P] Add unit tests for workspace I/O + retry handoff in `tests/unit/pdf_convert/agents/test_agent_step.py`
- [X] T021 [P] Add unit tests for token preflight interactive skip and `--yes` auto-proceed branches in `tests/unit/pdf_convert/agents/test_token_preflight.py`

**Checkpoint**: Shared agent-step foundation is ready for per-step artifacts and integrations.

---

## Phase 3: User Story 1 - Produce reliable agent-step outputs (Priority: P1) 🎯 MVP

**Goal**: Deliver prompt templates, contracts, and test artifacts so each step can produce contract-valid outputs with reliable table handling and content-repair behavior.

**Independent Test**: Run unit + contract tests for step artifacts and verify sample outputs for in-scope steps conform to schemas, including `7.7/8.7` multimodal fixtures.

### Tests for User Story 1

- [X] T022 [P] [US1] Add instruction rendering tests (including `step_7_7.py` two-pass prompt selection) in `tests/unit/pdf_convert/agents/test_instructions.py`
- [X] T023 [P] [US1] Add contract tests for content-repair steps `3.2`, `4.5`, `6.4` in `tests/contract/pdf_convert/agents/test_step_3_2.py`, `tests/contract/pdf_convert/agents/test_step_4_5.py`, and `tests/contract/pdf_convert/agents/test_step_6_4.py`
- [X] T024 [P] [US1] Add contract tests for table steps `7.7` and `8.7` in `tests/contract/pdf_convert/agents/test_step_7_7.py` and `tests/contract/pdf_convert/agents/test_step_8_7.py`
- [X] T025 [P] [US1] Add contract tests for reporting steps `10.2` and `10.3` in `tests/contract/pdf_convert/agents/test_step_10_2.py` and `tests/contract/pdf_convert/agents/test_step_10_3.py`
- [X] T026 [P] [US1] Add contract tests for quality-assessment/review steps `9.2`, `9.3`, `9.4`, `9.5`, `9.7`, and `9.8` in `tests/contract/pdf_convert/agents/test_step_9_2.py`, `tests/contract/pdf_convert/agents/test_step_9_3.py`, `tests/contract/pdf_convert/agents/test_step_9_4.py`, `tests/contract/pdf_convert/agents/test_step_9_5.py`, `tests/contract/pdf_convert/agents/test_step_9_7.py`, and `tests/contract/pdf_convert/agents/test_step_9_8.py`

### Implementation for User Story 1

- [X] T027 [P] [US1] Implement markdown instruction templates for content-repair steps in `src/gm_kit/pdf_convert/agents/instructions/step_3_2.md`, `src/gm_kit/pdf_convert/agents/instructions/step_4_5.md`, and `src/gm_kit/pdf_convert/agents/instructions/step_6_4.md`
- [X] T028 [P] [US1] Implement two-pass table detection prompt builder in `src/gm_kit/pdf_convert/agents/instructions/step_7_7.py`
- [X] T029 [P] [US1] Implement table conversion prompt template with normalization guidance (spacing/readability) in `src/gm_kit/pdf_convert/agents/instructions/step_8_7.md`
- [X] T030 [P] [US1] Implement quality-assessment/review prompt templates in `src/gm_kit/pdf_convert/agents/instructions/step_9_2.md`, `src/gm_kit/pdf_convert/agents/instructions/step_9_3.md`, `src/gm_kit/pdf_convert/agents/instructions/step_9_4.md`, `src/gm_kit/pdf_convert/agents/instructions/step_9_5.md`, `src/gm_kit/pdf_convert/agents/instructions/step_9_7.md`, and `src/gm_kit/pdf_convert/agents/instructions/step_9_8.md`
- [X] T031 [P] [US1] Implement reporting prompt templates in `src/gm_kit/pdf_convert/agents/instructions/step_10_2.md` and `src/gm_kit/pdf_convert/agents/instructions/step_10_3.md`
- [X] T032 [P] [US1] Define JSON Schemas for content-repair step outputs in `src/gm_kit/pdf_convert/agents/schemas/step_3_2.schema.json`, `src/gm_kit/pdf_convert/agents/schemas/step_4_5.schema.json`, and `src/gm_kit/pdf_convert/agents/schemas/step_6_4.schema.json`
- [X] T033 [P] [US1] Define JSON Schemas for table-processing outputs in `src/gm_kit/pdf_convert/agents/schemas/step_7_7.schema.json` and `src/gm_kit/pdf_convert/agents/schemas/step_8_7.schema.json`
- [X] T034 [P] [US1] Define JSON Schemas for quality-assessment/review outputs in `src/gm_kit/pdf_convert/agents/schemas/step_9_2.schema.json`, `src/gm_kit/pdf_convert/agents/schemas/step_9_3.schema.json`, `src/gm_kit/pdf_convert/agents/schemas/step_9_4.schema.json`, `src/gm_kit/pdf_convert/agents/schemas/step_9_5.schema.json`, `src/gm_kit/pdf_convert/agents/schemas/step_9_7.schema.json`, and `src/gm_kit/pdf_convert/agents/schemas/step_9_8.schema.json`
- [X] T035 [P] [US1] Define JSON Schemas for reporting outputs in `src/gm_kit/pdf_convert/agents/schemas/step_10_2.schema.json` and `src/gm_kit/pdf_convert/agents/schemas/step_10_3.schema.json`
- [X] T036 [US1] Implement shared step artifact factories / input payload builders for content-repair, quality-assessment/review, and reporting steps in `src/gm_kit/pdf_convert/agents/step_builders.py`
- [X] T037 [US1] Implement table step helpers for on-demand page image rendering + bbox/image path payload generation in `src/gm_kit/pdf_convert/agents/table_steps.py`
- [ ] T038 [US1] Finalize multimodal fixture inventory and README notes in `tests/fixtures/pdf_convert/agents/README.md`
- [X] T039 [US1] Finalize and normalize B2 / Homebrewery / CoC table step fixtures under `tests/fixtures/pdf_convert/agents/inputs/step_7_7/`, `tests/fixtures/pdf_convert/agents/inputs/step_8_7/`, and `tests/fixtures/pdf_convert/agents/inputs/table_pages/`
- [X] T040 [US1] Finalize `7.7` bbox golden files and `8.7` markdown golden files (including edge-case non-canonical annotation for Homebrewery span table) in `tests/fixtures/pdf_convert/agents/golden/step_7_7/` and `tests/fixtures/pdf_convert/agents/golden/step_8_7/`
- [ ] T041 [US1] Add CoC fixture acquisition/documentation check using `tests/fixtures/pdf_convert/download_cofc_fixture.sh` in `tests/fixtures/pdf_convert/README.md`
- [X] T042 [US1] Add contract fixture outputs for content-repair, quality-assessment/review, and reporting steps in `tests/fixtures/pdf_convert/agents/golden/step_3_2/`, `tests/fixtures/pdf_convert/agents/golden/step_4_5/`, `tests/fixtures/pdf_convert/agents/golden/step_6_4/`, `tests/fixtures/pdf_convert/agents/golden/step_9_2/`, `tests/fixtures/pdf_convert/agents/golden/step_9_3/`, `tests/fixtures/pdf_convert/agents/golden/step_9_4/`, `tests/fixtures/pdf_convert/agents/golden/step_9_5/`, `tests/fixtures/pdf_convert/agents/golden/step_9_7/`, `tests/fixtures/pdf_convert/agents/golden/step_9_8/`, `tests/fixtures/pdf_convert/agents/golden/step_10_2/`, and `tests/fixtures/pdf_convert/agents/golden/step_10_3/`
- [X] T043 [US1] Add unit coverage for table helpers and image-path payload generation in `tests/unit/pdf_convert/agents/test_table_steps.py`

**Checkpoint**: User Story 1 delivers contract-valid step artifacts and multimodal fixture coverage for `7.7/8.7` without live-agent dependency.

---

## Phase 4: User Story 2 - Validate agent outputs consistently (Priority: P2)

**Goal**: Implement rubric definitions and evaluation flow so output quality can be scored consistently and deterministically across runs.

**Independent Test**: Apply rubric evaluation to fixed outputs and verify repeatable pass/fail decisions, explicit threshold handling, and critical-failure behavior.

### Tests for User Story 2

- [X] T044 [P] [US2] Add unit tests for rubric loading/scoring threshold logic in `tests/unit/pdf_convert/agents/test_rubrics.py`
- [X] T045 [P] [US2] Add unit tests for evaluation result parsing and critical-failure handling in `tests/unit/pdf_convert/agents/test_rubrics.py`

### Implementation for User Story 2

- [X] T046 [P] [US2] Implement rubric definitions for content-repair and table steps in `src/gm_kit/pdf_convert/agents/rubrics.py`
- [X] T047 [P] [US2] Implement rubric definitions for quality-assessment/review/reporting steps in `src/gm_kit/pdf_convert/agents/rubrics.py`
- [X] T048 [US2] Implement rubric registry and lookup helpers in `src/gm_kit/pdf_convert/agents/evaluator.py`
- [X] T049 [US2] Implement evaluation result model and pass/fail threshold evaluator in `src/gm_kit/pdf_convert/agents/evaluator.py`
- [X] T050 [US2] Implement step-level validation + rubric evaluation orchestration in `src/gm_kit/pdf_convert/agents/evaluator.py`
- [ ] T051 [US2] Add fixed evaluation fixtures and expected scoring outputs in `tests/fixtures/pdf_convert/agents/golden/evaluations/`
- [ ] T052 [US2] Add deterministic/repeatability tests for repeated rubric evaluation runs in `tests/unit/pdf_convert/agents/test_determinism.py`

**Checkpoint**: User Story 2 delivers repeatable rubric-based acceptance logic with explicit thresholds and critical-failure handling.

---

## Phase 5: User Story 3 - Integrate agent steps with the code pipeline (Priority: P3)

**Goal**: Replace E4-07a stubs with agent-step library calls while preserving pipeline inputs/outputs and resume behavior.

**Independent Test**: Execute the pipeline through agent-step pause/resume flow and verify downstream phases consume unchanged interfaces, including warning/skip paths.

### Tests for User Story 3

- [ ] T053 [P] [US3] Add unit tests for phase-to-agent payload mapping and stub replacement compatibility in `tests/unit/pdf_convert/test_phase_agent_integration.py`
- [ ] T054 [US3] Add integration tests for pause/resume agent workflow in `tests/integration/pdf_convert/agents/test_agent_pipeline.py`
- [ ] T055 [US3] Add integration tests for `GM_AGENT` selection and skipped-step warning behavior in `tests/integration/pdf_convert/agents/test_agent_pipeline.py`

### Implementation for User Story 3

- [ ] T056 [US3] Implement agent dispatch / CLI invocation mapping (`GM_AGENT`) in `src/gm_kit/pdf_convert/agents/dispatch.py`
- [ ] T057 [US3] Implement phase integration adapter functions for step execution + resume in `src/gm_kit/pdf_convert/agents/runtime.py`
- [ ] T058 [US3] Replace Phase 3 step `3.2` stub with agent-step integration in `src/gm_kit/pdf_convert/phases/phase3.py`
- [ ] T059 [US3] Replace Phase 4 step `4.5` stub with agent-step integration in `src/gm_kit/pdf_convert/phases/phase4.py`
- [ ] T060 [US3] Replace Phase 6 step `6.4` stub with agent-step integration in `src/gm_kit/pdf_convert/phases/phase6.py`
- [x] T061 [US3] Replace Phase 7 step `7.7` stub with agent-step integration and page-image handoff in `src/gm_kit/pdf_convert/phases/phase7.py`
- [x] T062 [US3] Replace Phase 8 step `8.7` stub with agent-step integration and in-place markdown edit handling in `src/gm_kit/pdf_convert/phases/phase8.py`
- [x] T063 [US3] Replace Phase 9 stubs (`9.2-9.5`, `9.7-9.8`) while preserving `9.1` no-op behavior in `src/gm_kit/pdf_convert/phases/phase9.py`
- [ ] T064 [US3] Replace Phase 10 stubs (`10.2`, `10.3`) with agent-step integration in `src/gm_kit/pdf_convert/phases/phase10.py`
- [ ] T065 [US3] Wire agent-step package into conversion orchestrator resume flow (`AWAITING_AGENT` → validate → retry/escalate) in `src/gm_kit/pdf_convert/orchestrator.py`
- [ ] T066 [US3] Update workspace state persistence for current step and retry metadata in `src/gm_kit/pdf_convert/state.py`
- [ ] T067 [US3] Add end-to-end compatibility regression assertions for stub replacement (SC-004) in `tests/integration/pdf_convert/agents/test_agent_pipeline.py`

**Checkpoint**: User Story 3 enables end-to-end pause/resume agent execution with existing pipeline interfaces preserved.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish documentation, fixture guidance, and quality validation across all stories.

- [x] T068 [P] Add developer-facing agent fixture conventions and table-fixture naming guidance in `tests/fixtures/pdf_convert/agents/README.md`
- [x] T069 [P] Update `specs/007-agent-pipeline/quickstart.md` with implemented test commands/notes if paths or flags changed during implementation
- [x] T070 [P] Update `specs/007-agent-pipeline/contracts/agent-steps.md` with final schema/rubric file references and step mapping
- [x] T071 Add regression notes for known edge-case non-canonical Homebrewery span table behavior in `tests/fixtures/pdf_convert/agents/golden/step_8_7/homebrewery_with_toc_p002_example_table.step_8_7.golden.md`
- [x] T072 Run and document unit + contract test pass commands for agent-step package in `specs/007-agent-pipeline/feature-implementation-journal.txt`
- [x] T073 Run and document targeted integration smoke run (manual/live agent) results in `specs/007-agent-pipeline/feature-implementation-journal.txt`
- [x] T074 Perform final code cleanup and export surface review in `src/gm_kit/pdf_convert/agents/__init__.py`
- [x] T075 Run quickstart validation flow and reconcile any drift in `specs/007-agent-pipeline/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2; MVP starts here
- **User Story 2 (Phase 4)**: Depends on Phase 2 and benefits from US1 artifact patterns (schemas/prompts/tests)
- **User Story 3 (Phase 5)**: Depends on Phase 2 and requires US1 + US2 outputs (prompts/contracts/rubrics)
- **Polish (Phase 6)**: Depends on desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational
- **US2 (P2)**: Can begin after Foundational, but assumes core prompt/schema patterns from US1 are established
- **US3 (P3)**: Depends on US1 and US2 artifacts to wire live step execution safely

### Parallel Opportunities

- Setup skeleton creation tasks (`T002-T007`) can run in parallel
- Foundational test tasks (`T017-T021`) can run in parallel after shared modules exist
- US1 contract/prompt/schema tasks (`T026-T035`) can run in parallel by step group
- US1 fixture/golden finalization (`T038-T042`) can run in parallel with prompt/schema authoring
- US2 rubric and evaluator tasks (`T044-T052`) can run in parallel by step group after US1 artifacts stabilize
- Phase file stub replacement tasks (`T058-T064`) can be split across contributors after runtime adapter is stable

---

## Parallel Example: User Story 1

```bash
# In parallel after foundational helpers exist:
Task: "Implement content-repair instruction templates in src/gm_kit/pdf_convert/agents/instructions/step_3_2.md, step_4_5.md, step_6_4.md"
Task: "Define table-processing schemas in src/gm_kit/pdf_convert/agents/schemas/step_7_7.schema.json and step_8_7.schema.json"
Task: "Finalize multimodal table fixtures under tests/fixtures/pdf_convert/agents/inputs/step_7_7/ and tests/fixtures/pdf_convert/agents/inputs/step_8_7/"
Task: "Add contract tests for steps 7.7 and 8.7 in tests/contract/pdf_convert/agents/test_step_7_7.py and test_step_8_7.py"
```

---

## Parallel Example: User Story 3

```bash
# After runtime adapter and dispatch are merged:
Task: "Replace phase stubs in src/gm_kit/pdf_convert/phases/phase3.py, phase4.py, phase6.py"
Task: "Replace table step stubs in src/gm_kit/pdf_convert/phases/phase7.py and phase8.py"
Task: "Replace review/report stubs in src/gm_kit/pdf_convert/phases/phase9.py and phase10.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup)
2. Complete Phase 2 (Foundational)
3. Complete Phase 3 (US1) to deliver prompt/contracts and multimodal fixtures
4. Validate contract tests and `7.7/8.7` goldens before continuing

### Incremental Delivery

1. US1: reliable outputs + fixtures/contracts
2. US2: rubric/evaluator determinism and acceptance gating
3. US3: pipeline integration and end-to-end pause/resume compatibility
4. Polish: documentation and validation cleanup

### Multi-Agent Parallel Strategy

1. One agent handles US1 step artifacts + fixtures while another handles US2 rubrics/tests after Phase 2
2. Merge on shared registry/contracts conventions before US3
3. Reserve US3 phase-file wiring for a single integrator to reduce merge conflicts in `src/gm_kit/pdf_convert/phases/`
