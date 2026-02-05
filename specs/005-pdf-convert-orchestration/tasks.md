# Tasks: PDF to Markdown Command Orchestration

**Input**: Design documents from `/specs/005-pdf-convert-orchestration/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Project initialization and basic structure for pdf_convert module

- [x] T001 Create pdf_convert package structure: `src/gm_kit/pdf_convert/__init__.py`
- [x] T002 [P] Create phases subpackage: `src/gm_kit/pdf_convert/phases/__init__.py`
- [x] T003 [P] Add PyMuPDF dependency to pyproject.toml (fitz >= 1.23.0)
- [x] T004 [P] Add pexpect/wexpect dependencies to pyproject.toml (test extras)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Data Models

- [x] T005 Implement ConversionState dataclass in `src/gm_kit/pdf_convert/state.py`:
  - Fields: version, pdf_path, output_dir, started_at, updated_at, current_phase, current_step, completed_phases, phase_results, status, error, diagnostics_enabled
  - State transitions per FR-019b
  - JSON serialization/deserialization

- [x] T006 [P] Implement PDFMetadata dataclass in `src/gm_kit/pdf_convert/metadata.py`:
  - Fields: title, author, creator, producer, copyright, page_count, file_size_bytes, has_toc, image_count, font_count, extracted_at
  - Handle empty/malformed fields per edge cases

- [x] T007 [P] Implement PreflightReport dataclass in `src/gm_kit/pdf_convert/preflight.py`:
  - Fields: pdf_name, file_size_display, page_count, image_count, text_extractable, toc_approach, font_complexity, overall_complexity, warnings, user_involvement_phases
  - Complexity derivation rules per FR-015

- [x] T008 [P] Implement PhaseResult dataclass in `src/gm_kit/pdf_convert/phases/base.py`:
  - Fields: phase_num, name, status, started_at, completed_at, steps, output_file, warnings, errors
  - Status enum: SUCCESS, WARNING, ERROR, SKIPPED

- [x] T009 [P] Implement StepResult dataclass in `src/gm_kit/pdf_convert/phases/base.py`:
  - Fields: step_id, description, status, duration_ms, output_file, message

- [x] T010 [P] Implement ErrorInfo dataclass in `src/gm_kit/pdf_convert/state.py`:
  - Fields: phase, step, code, message, recoverable, suggestion

### State Management

- [x] T011 Implement state file I/O in `src/gm_kit/pdf_convert/state.py`:
  - Atomic writes (temp file + rename) per FR-019a
  - File locking per edge case (5-second timeout)
  - JSON schema validation per FR-020
  - Version compatibility checking

- [x] T012 [P] Verify/Update JSON schemas in `specs/005-pdf-convert-orchestration/contracts/`:
  - `state-schema.json` per FR-018 (verified + added config field)
  - `metadata-schema.json` per FR-016 (verified + added toc_entries, toc_max_depth, dates)

### Phase Interface

- [x] T013 Define Phase interface (abstract base class) in `src/gm_kit/pdf_convert/phases/base.py`:
  - `execute(state: ConversionState) -> PhaseResult` method signature
  - Step-level tracking support per Integration Contracts

- [x] T014 [P] Implement mock phases in `src/gm_kit/pdf_convert/phases/stubs.py`:
  - MockPhase class for phases 1-10 returning SUCCESS
  - Configurable ERROR responses for testing
  - Respect --yes flag per Mock Phase Behavior

### Error Handling

- [x] T015 Define exit codes enum in `src/gm_kit/pdf_convert/errors.py`:
  - EXIT_SUCCESS = 0, EXIT_USER_ABORT = 1, EXIT_FILE_ERROR = 2, EXIT_PDF_ERROR = 3, EXIT_STATE_ERROR = 4, EXIT_DEPENDENCY_ERROR = 5

- [x] T016 [P] Define error message constants in `src/gm_kit/pdf_convert/errors.py`:
  - All FR-029 through FR-041 error messages
  - Actionable message format per FR-041b

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Convert PDF via Slash Command (Priority: P1)

**Goal**: Users can invoke `/gmkit.pdf-to-markdown` to start a conversion with pre-flight analysis

**Independent Test**: Invoke slash command with test PDF, verify CLI executes and pre-flight displays

### Tests for User Story 1

- [x] T017 [P] [US1] Unit test for metadata extraction in `tests/unit/pdf_convert/test_metadata.py`:
  - Test with reference PDF: `specs/005-pdf-convert-orchestration/test_inputs/The Homebrewery - NaturalCrit.pdf`
  - Verify all metadata fields extracted correctly

- [x] T018 [P] [US1] Unit test for preflight analysis in `tests/unit/pdf_convert/test_preflight.py`:
  - Test complexity calculation (low/moderate/high)
  - Test TOC detection (embedded/visual/none)
  - Test text extractability check (<100 chars = scanned)

- [x] T019 [P] [US1] Unit test for state creation in `tests/unit/pdf_convert/test_state.py`:
  - Test initial state creation
  - Test state serialization/deserialization
  - Test atomic write mechanism

- [x] T020 [US1] Integration test for CLI new conversion in `tests/integration/pdf_convert/test_cli_full_pipeline.py`:
  - Test `gmkit pdf-convert <pdf-path>` creates output directory
  - Test `.state.json` created with correct initial state
  - Test pre-flight report displays per FR-016a format
  - Use pexpect to verify user prompt and response handling

### Implementation for User Story 1

- [x] T021 [US1] Implement PDF metadata extraction in `src/gm_kit/pdf_convert/metadata.py`:
  - Use PyMuPDF (fitz) for extraction per FR-011
  - Handle empty/malformed fields per edge cases
  - Save to `metadata.json` per FR-016

- [x] T022 [US1] Implement pre-flight analysis in `src/gm_kit/pdf_convert/preflight.py`:
  - Image counting per FR-012
  - TOC detection per FR-013 (has_toc, toc_entries, toc_max_depth)
  - Text extractability per FR-014
  - Font analysis and complexity per FR-015

- [x] T023 [US1] Implement pre-flight report display in `src/gm_kit/pdf_convert/preflight.py`:
  - Format per FR-016a (rich terminal table with equals-sign header)
  - User confirmation prompt (Proceed/Abort)
  - Handle --yes flag for non-interactive mode

- [x] T024 [US1] Implement folder structure creation in `src/gm_kit/pdf_convert/orchestrator.py`:
  - Create structure per FR-021 (images/, preprocessed/, etc.)
  - Handle special characters in filenames per edge case
  - Handle permission errors per FR-032

- [x] T025 [US1] Implement CLI command in `src/gm_kit/cli.py`:
  - Register `pdf-convert` subcommand with typer
  - Accept `<pdf-path>` and `--output` arguments
  - Validate PDF exists and is readable
  - Handle encrypted PDFs per edge case

- [x] T026 [US1] Implement orchestrator initialization in `src/gm_kit/pdf_convert/orchestrator.py`:
  - Create ConversionState
  - Run Phase 0 (pre-flight)
  - Orchestrate mock phases 1-10 in sequence

- [x] T027 [US1] Create prompt file in `src/gm_kit/templates/prompts/gmkit.pdf-to-markdown.md`:
  - Structure per FR-002b
  - Error handling guidance with retry patterns (spec-kit lessons)
  - Reference to review-checklist.md

- [x] T028 [US1] Extend `gmkit init` to install prompt file per FR-002:
  - Install to agent-specific locations (Claude, Codex, Gemini, Qwen)
  - Modify existing init command in `src/gm_kit/init.py`

**Checkpoint**: User Story 1 complete - slash command works with pre-flight analysis

---

## Phase 4: User Story 2 - Convert PDF via CLI (Priority: P1)

**Goal**: Users can run `gmkit pdf-convert` directly with all flags working

**Independent Test**: Run CLI with test PDF, verify output folder and diagnostic bundle

### Tests for User Story 2

- [x] T029 [P] [US2] Unit test for CLI argument parsing in `tests/unit/pdf_convert/test_cli_args.py`:
  - Test all flag combinations
  - Test mutually exclusive flags error
  - Test invalid --phase and --from-step values

- [x] T030 [P] [US2] Unit test for diagnostic bundle in `tests/unit/pdf_convert/test_diagnostics.py`:
  - Test bundle creation with all required files per FR-010b
  - Test bundle naming per FR-010c
  - Test failure handling (disk full) per edge case

- [x] T031 [US2] Integration test for --diagnostics flag in `tests/integration/pdf_convert/test_cli_full_pipeline.py`:
  - Test `gmkit pdf-convert --diagnostics <pdf>` creates `diagnostic-bundle.zip`
  - Verify bundle contents per FR-010b

### Implementation for User Story 2

- [x] T032 [US2] Implement --diagnostics flag handling in `src/gm_kit/cli.py`:
  - Store flag in ConversionState.config
  - Pass to orchestrator

- [x] T033 [US2] Implement diagnostic bundle creation in `src/gm_kit/pdf_convert/orchestrator.py`:
  - Create at end of Phase 10 per FR-010d
  - Include all files per FR-010b
  - Handle disk space errors per edge case

- [x] T034 [US2] Implement --yes flag for non-interactive mode in `src/gm_kit/cli.py`:
  - Skip step 0.6 confirmation per FR-010a
  - Accept defaults for user prompts

- [x] T035 [US2] Implement help text per FR-004 requirements in `src/gm_kit/cli.py`:
  - Synopsis, all flags, usage examples
  - Version information

- [x] T036 [US2] Implement existing state detection in `src/gm_kit/pdf_convert/orchestrator.py`:
  - Detect existing `.state.json` per User Story 2 Scenario 3
  - Prompt: Overwrite/Resume/Abort
  - Handle response appropriately

**Checkpoint**: User Story 2 complete - CLI works with all basic flags

---

## Phase 5: User Story 3 - Resume Interrupted Conversion (Priority: P2)

**Goal**: Users can resume interrupted conversions from last checkpoint

**Independent Test**: Start conversion, simulate interruption, verify --resume continues from checkpoint

### Tests for User Story 3

- [x] T037 [P] [US3] Unit test for state validation in `tests/unit/pdf_convert/test_state.py`:
  - Test FR-020 validation rules
  - Test corrupt state detection
  - Test version compatibility

- [x] T038 [P] [US3] Unit test for resume logic in `tests/unit/pdf_convert/test_orchestrator.py`:
  - Test skip completed phases
  - Test continue from current step
  - Test missing output file detection

- [x] T039 [US3] Integration test for --resume in `tests/integration/pdf_convert/test_resume_workflow.py`:
  - Simulate interruption at Phase 3
  - Verify --resume continues from Phase 4
  - Verify completed phases not re-run

### Implementation for User Story 3

- [x] T040 [US3] Implement --resume flag handling in `src/gm_kit/cli.py`:
  - Load existing state from directory
  - Validate state file per FR-020

- [x] T041 [US3] Implement state validation in `src/gm_kit/pdf_convert/state.py`:
  - JSON parse validation
  - Schema validation
  - PDF path existence check
  - Version compatibility check
  - Specific error messages per FR-020

- [x] T042 [US3] Implement resume logic in `src/gm_kit/pdf_convert/orchestrator.py`:
  - Skip completed phases
  - Resume from current_step
  - Verify output files exist for completed phases
  - Handle stale lock (in_progress but no process) per edge case

- [x] T043 [US3] Implement resume error handling in `src/gm_kit/pdf_convert/orchestrator.py`:
  - Missing state file error per User Story 3 Scenario 3
  - Corrupt state file error
  - Missing phase output file error per edge case

**Checkpoint**: User Story 3 complete - resume functionality works

---

## Phase 6: User Story 4 - Re-run Specific Phase or Step (Priority: P2)

**Goal**: Users can re-run specific phases or steps without full restart

**Independent Test**: Complete conversion, run --phase 5, verify only Phase 5 re-runs

### Tests for User Story 4

- [x] T044 [P] [US4] Unit test for --phase validation in `tests/unit/pdf_convert/test_cli_args.py`:
  - Test valid phase numbers (0-10)
  - Test invalid inputs (negative, >10, non-integer)

- [x] T045 [P] [US4] Unit test for --from-step validation in `tests/unit/pdf_convert/test_cli_args.py`:
  - Test valid format (N.N)
  - Test invalid formats ("5", "5.3.1", "abc")
  - Test non-existent steps

- [x] T046 [US4] Integration test for --phase in `tests/integration/pdf_convert/test_resume_workflow.py`:
  - Complete conversion, run --phase 5
  - Verify only Phase 5 re-runs
  - Verify Phase 5 output updated

### Implementation for User Story 4

- [x] T047 [US4] Implement --phase flag handling in `src/gm_kit/cli.py`:
  - Validate phase number (0-10)
  - Check prerequisite phases completed per User Story 4 Scenario 3

- [x] T048 [US4] Implement --from-step flag handling in `src/gm_kit/cli.py`:
  - Validate step format (N.N regex)
  - Validate step exists in phase
  - Error messages per edge cases

- [x] T049 [US4] Implement phase re-run logic in `src/gm_kit/pdf_convert/orchestrator.py`:
  - Run single phase using previous phase output
  - Update state file appropriately
  - Handle missing prerequisite output

- [x] T050 [US4] Implement step-level resume in `src/gm_kit/pdf_convert/orchestrator.py`:
  - Skip steps before specified step
  - Track step completion in state
  - Overwrite step output on re-run (idempotent)

**Checkpoint**: User Story 4 complete - selective re-run functionality works

---

## Phase 7: User Story 5 - Check Conversion Status (Priority: P3)

**Goal**: Users can check status of conversions without running any processing

**Independent Test**: Create state at various stages, verify --status shows correct info

### Tests for User Story 5

- [x] T051 [P] [US5] Unit test for status display in `tests/unit/pdf_convert/test_orchestrator.py`:
  - Test status output format per FR-009a
  - Test in_progress display
  - Test completed display
  - Test failed display

- [x] T052 [US5] Integration test for --status in `tests/integration/pdf_convert/test_cli_full_pipeline.py`:
  - Create state at Phase 6
  - Verify --status shows phases 0-5 completed, 6 in_progress, 7-10 pending

### Implementation for User Story 5

- [x] T053 [US5] Implement --status flag handling in `src/gm_kit/cli.py`:
  - Load state file
  - Display formatted status per FR-009a

- [x] T054 [US5] Implement status display in `src/gm_kit/pdf_convert/orchestrator.py`:
  - Rich terminal table format per FR-009a
  - Show source PDF, overall status, per-phase status
  - Handle no state file case per User Story 5 Scenario 3

**Checkpoint**: User Story 5 complete - status checking works

---

## Phase 8: Copyright Notice & Final Output

**Purpose**: Insert copyright notice into final markdown output

- [x] T055 Implement copyright notice generation in `src/gm_kit/pdf_convert/orchestrator.py`:
  - Use metadata from metadata.json per FR-049
  - Format per FR-050a template
  - Insert before H1 per FR-049a
  - Handle missing metadata fields (fallbacks)

- [x] T056 [P] Unit test for copyright notice in `tests/unit/pdf_convert/test_orchestrator.py`:
  - Test template formatting
  - Test fallback values
  - Test insertion position

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T057 [P] Implement logging per Assumptions in `src/gm_kit/pdf_convert/`:
  - Use Python logging module
  - Default level INFO
  - Logs to stderr

- [x] T058 [P] Implement progress indicators per Assumptions in `src/gm_kit/pdf_convert/orchestrator.py`:
  - Rich library progress display
  - Format: "Phase N/10: <name> (step N.N)"
  - TTY vs non-TTY fallback

- [x] T059 [P] Add retry logic for file lock contention per Assumptions:
  - 3 retries with 1-second delay
  - Fail with actionable error after retries

- [x] T060 Run quickstart.md validation (manual):
  - Follow quickstart instructions
  - Verify all steps work
  - Update quickstart if needed (fixed path: src/gm_kit/)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (P1 - MVP)
- **User Story 2 (Phase 4)**: Depends on Foundational (P1 - extends CLI)
- **User Story 3 (Phase 5)**: Depends on Phase 3 & 4 (P2 - needs working conversion first)
- **User Story 4 (Phase 6)**: Depends on Phase 3 & 4 (P2 - needs working conversion first)
- **User Story 5 (Phase 7)**: Depends on Foundational (P3 - can test with manually created state)
- **Copyright (Phase 8)**: Depends on Phase 3
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational - Independent
- **User Story 2 (P1)**: After Foundational - Extends US1 CLI implementation
- **User Story 3 (P2)**: After US1/US2 - Needs working conversion to test resume
- **User Story 4 (P2)**: After US1/US2 - Needs working conversion to test re-run
- **User Story 5 (P3)**: After Foundational - Can test independently with mock state

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational data model tasks (T006-T010) can run in parallel
- Schema creation (T012) can run in parallel with other Foundational tasks
- Within each user story, tests marked [P] can run in parallel
- User Stories 3, 4, and 5 can run in parallel after US1/US2 complete

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (slash command + pre-flight)
4. Complete Phase 4: User Story 2 (CLI with all flags)
5. **STOP and VALIDATE**: Test conversion end-to-end with test PDF
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 + 2 → Test conversion → Deploy/Demo (MVP!)
3. Add User Story 3 → Test resume → Deploy/Demo
4. Add User Story 4 → Test re-run → Deploy/Demo
5. Add User Story 5 → Test status → Deploy/Demo
6. Polish phase → Final release

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Write tests first, verify they fail before implementing
- Commit after each task or logical group
- Mock phases return SUCCESS by default; configure for ERROR testing
- PyMuPDF minimum version: 1.23.0
- Test PDF: `specs/005-pdf-convert-orchestration/test_inputs/The Homebrewery - NaturalCrit.pdf`

---

## Edge Case & Exit Code Coverage Mapping

| Edge Case (from spec.md) | Covered By Task(s) | Exit Code |
|--------------------------|-------------------|-----------|
| Scanned PDF (<100 chars) | T018, T022 | 3 (PDF_ERROR) |
| Large PDF (>50MB) | T022 (warning) | 0 (continues) |
| Permission denied on output | T024 | 2 (FILE_ERROR) |
| Interrupted Agent step | T042, T043 | 4 (STATE_ERROR) |
| Phase depends on skipped output | T043, T049 | 4 (STATE_ERROR) |
| Paths with spaces/special chars | T025, T029 | - |
| Relative vs absolute paths | T025, T011 | - |
| Invalid --phase value | T029, T044 | 2 (FILE_ERROR) |
| Invalid --from-step format | T029, T045 | 2 (FILE_ERROR) |
| State schema version mismatch | T037, T041 | 4 (STATE_ERROR) |
| Concurrent access (file lock) | T011, T059 | 4 (STATE_ERROR) |
| Stale "in_progress" state | T042 | - (resumes) |
| Missing phase output on resume | T038, T043 | 4 (STATE_ERROR) |
| Disk space exhausted | T030, T033 | 3 (PDF_ERROR) |
| Resume after partial failure | T043 | - (resumes) |
| Empty/malformed PDF metadata | T006, T021 | - (uses defaults) |
| Permission denied on PDF read | T025 | 2 (FILE_ERROR) |
| Encrypted/password-protected PDF | T025 | 3 (PDF_ERROR) |
| Ctrl+C interruption | T011 (atomic writes) | - (resumable) |
| PyMuPDF import failure | T016 (error constant) | 5 (DEPENDENCY_ERROR) |
| Filename special characters | T024 | - (sanitized) |
| Diagnostic bundle disk full | T030 | 0 (warning only) |

**Exit Code Test Coverage**:
- Exit 0 (SUCCESS): T020, T031, T052 (successful conversion tests)
- Exit 1 (USER_ABORT): T020 (pexpect test for user decline)
- Exit 2 (FILE_ERROR): T029 (invalid args), T025 (file not found)
- Exit 3 (PDF_ERROR): T018 (scanned PDF), T025 (encrypted PDF)
- Exit 4 (STATE_ERROR): T037 (corrupt state), T043 (missing output)
- Exit 5 (DEPENDENCY_ERROR): Implicit in T016 (constant defined)
