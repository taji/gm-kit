---

description: "Task list template for feature implementation"
---

# Tasks: Installation and Walking Skeleton

**Input**: Design documents from `/specs/002-installer-skeleton/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included (spec requires test-first development and automated integration tests).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create template source files in `src/gm_kit/assets/templates/commands/gmkit.hello-gmkit.md` and `src/gm_kit/assets/templates/hello-gmkit-template.md`
- [X] T002 Create script templates in `src/gm_kit/assets/scripts/bash/say-hello.sh` and `src/gm_kit/assets/scripts/powershell/say-hello.ps1`
- [X] T003 Create constitution source in `src/gm_kit/assets/memory/constitution.md`
- [X] T004 [P] Create test package skeletons with `__init__.py` in `tests/unit/`, `tests/integration/`, and `tests/contract/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement agent configuration mapping in `src/gm_kit/agent_config.py`
- [X] T006 Implement path and OS validation helpers in `src/gm_kit/validator.py`
- [X] T007 Implement template manager scaffolding (single-source + tomllib validation) in `src/gm_kit/template_manager.py`
- [X] T008 Implement script generator scaffolding in `src/gm_kit/script_generator.py`
- [X] T009 Implement CLI app scaffolding and shared error handling in `src/gm_kit/cli.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Install GM-Kit and Initialize Project (Priority: P1) 🎯 MVP

**Goal**: Install gmkit via uv and initialize a temp workspace with agent-specific prompts, templates, scripts, and memory files.

**Independent Test**: Install gmkit, run `gmkit init`, and verify all expected files are created for the selected agent/OS.

### Tests for User Story 1 (Test-first)

- [X] T010 [P] [US1] Create CLI contract test for `gmkit init` in `tests/contract/test_cli_init_contract.py`
- [X] T011 [P] [US1] Add init prompt/arg validation tests in `tests/unit/test_init.py`
- [X] T013 [P] [US1] Add full init flow integration test in `tests/integration/test_full_init_flow.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement `gmkit init` flow in `src/gm_kit/init.py` (folder creation, template/script copy)
- [X] T016 [US1] Wire `gmkit init` command into CLI in `src/gm_kit/cli.py`
- [X] T017 [US1] Ensure console entrypoint is configured in `pyproject.toml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Platform Script Generation (Priority: P2)

**Goal**: Generate bash and PowerShell scripts with identical behavior and output.

**Independent Test**: Generate scripts for linux/windows and confirm identical outputs for the same inputs.

### Tests for User Story 2 (Test-first)

- [X] T018 [P] [US2] Add script generation unit tests in `tests/unit/test_script_generator.py`
- [X] T019 [P] [US2] Add bash vs PowerShell parity tests (via `pwsh` on Linux) in `tests/integration/test_script_parity.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement bash script generation in `src/gm_kit/script_generator.py`
- [X] T021 [US2] Implement PowerShell script generation in `src/gm_kit/script_generator.py`
- [X] T022 [US2] Ensure OS selection routes to correct script template in `src/gm_kit/init.py`

**Checkpoint**: User Story 2 should be independently testable and produce identical outputs across platforms

---

## Phase 5: User Story 3 - Agent Prompt Integration (Priority: P3)

**Goal**: Generate agent-specific prompt files in the correct locations and formats for all supported agents.

**Independent Test**: Run `gmkit init` with each agent and verify the prompt file path and format.

### Tests for User Story 3 (Test-first)

- [X] T023 [P] [US3] Add agent config mapping tests in `tests/unit/test_agent_config.py`
- [X] T024 [P] [US3] Add prompt generation tests for md/toml in `tests/unit/test_template_manager.py`
- [X] T025 [P] [US3] Add TOML validation tests in `tests/integration/test_toml_validation.py`
- [X] T026 [P] [US3] Add agent validation tests in `tests/integration/test_agent_validation.py`

### Implementation for User Story 3

- [X] T027 [US3] Implement agent prompt file generation in `src/gm_kit/template_manager.py`
- [X] T028 [US3] Implement TOML embedding/validation in `src/gm_kit/template_manager.py`
- [X] T029 [US3] Implement agent install checks and errors in `src/gm_kit/validator.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [P] Validate quickstart steps and update if needed in `specs/002-installer-skeleton/quickstart.md`
- [X] T031 Run lint/typecheck/test commands documented in `justfile`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/config before services
- Services before CLI wiring
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Create CLI contract test for gmkit init in tests/contract/test_cli_init_contract.py"
Task: "Add init prompt/arg validation tests in tests/unit/test_init.py"
Task: "Add full init flow integration test in tests/integration/test_full_init_flow.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch tests for User Story 2 together:
Task: "Add script generation unit tests in tests/unit/test_script_generator.py"
Task: "Add cross-platform script parity tests in tests/integration/test_script_parity.py"
```

---

## Parallel Example: User Story 3

```bash
# Launch tests for User Story 3 together:
Task: "Add agent config mapping tests in tests/unit/test_agent_config.py"
Task: "Add prompt generation tests for md/toml in tests/unit/test_template_manager.py"
Task: "Add TOML validation tests in tests/integration/test_toml_validation.py"
Task: "Add agent validation tests in tests/integration/test_agent_validation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
