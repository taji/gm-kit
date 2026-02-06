# Tasks: PDF Code Pipeline

**Feature**: PDF Code Pipeline
**Branch**: `006-code-pdf-pipeline`
**Spec**: /home/todd/Dev/gm-kit/specs/006-code-pdf-pipeline/spec.md
**Plan**: /home/todd/Dev/gm-kit/specs/006-code-pdf-pipeline/plan.md

## Phase 1: Setup

- [ ] T001 Confirm phase/step ownership mapping from architecture doc in notes section of plan.md
- [ ] T002 Document artifact output paths and file naming conventions in plan.md

## Phase 2: Foundational

- [ ] T003 Define Phase registry interface to replace get_mock_phases in src/gm_kit/pdf_convert/phases/base.py
- [ ] T004 Update orchestrator phase loading to use real registry in src/gm_kit/pdf_convert/orchestrator.py
- [ ] T005 Add phase module structure under src/gm_kit/pdf_convert/phases/ for Phase0–Phase10 classes

## Phase 3: User Story 1 (P1) — Run Code-Driven Pipeline

**Goal**: Implement full code-step pipeline phases 0–8 with Phase 8 markdown as primary deliverable, and code-step portions of phases 9–10.

**Independent Test**: Run pipeline on Homebrewery fixture and verify phase4–phase8 outputs plus state updates.

- [ ] T006 [US1] Implement Phase0 (pre-flight analysis code steps 0.1–0.5) in src/gm_kit/pdf_convert/phases/phase0.py
- [ ] T007 [US1] Implement Phase1 (image extraction) in src/gm_kit/pdf_convert/phases/phase1.py
- [ ] T008 [US1] Implement Phase2 (image removal) in src/gm_kit/pdf_convert/phases/phase2.py
- [ ] T009 [US1] Implement Phase3 code steps (TOC extraction, font sampling, font-family-mapping.json generation) in src/gm_kit/pdf_convert/phases/phase3.py
- [ ] T010 [US1] Implement Phase4 code steps (chunking, text extraction, merge, two-column warning) in src/gm_kit/pdf_convert/phases/phase4.py
- [ ] T011 [US1] Implement Phase5 character-level fixes in src/gm_kit/pdf_convert/phases/phase5.py
- [ ] T012 [US1] Implement Phase6 word/token-level fixes (code steps only) in src/gm_kit/pdf_convert/phases/phase6.py
- [ ] T013 [US1] Implement Phase7 structural detection (code steps only) in src/gm_kit/pdf_convert/phases/phase7.py
- [ ] T014 [US1] Implement Phase8 hierarchy application (code steps only) in src/gm_kit/pdf_convert/phases/phase8.py
- [ ] T015 [US1] Implement Phase9 code step (markdown lint) in src/gm_kit/pdf_convert/phases/phase9.py
- [ ] T016 [US1] Implement Phase10 code steps (report + diagnostics bundle) in src/gm_kit/pdf_convert/phases/phase10.py
- [ ] T017 [US1] Wire real phase classes into registry and replace get_mock_phases usage in src/gm_kit/pdf_convert/phases/__init__.py
- [ ] T018 [US1] Update orchestrator to include per-phase outputs for phase4–phase8 in diagnostics bundle (if required by spec) in src/gm_kit/pdf_convert/orchestrator.py
- [ ] T019 [US1] Add integration tests for phase4–phase8 artifact generation in tests/integration/pdf_convert/

## Phase 4: User Story 2 (P2) — Run Individual Phases

**Goal**: Allow isolated phase execution with correct artifact handling.

**Independent Test**: Run a single phase (e.g., Phase5) with expected inputs present and verify only that output is created.

- [ ] T020 [US2] Add unit tests for phase-only execution path in tests/unit/pdf_convert/test_orchestrator.py
- [ ] T021 [US2] Add integration tests for `--phase` behavior in tests/integration/pdf_convert/test_cli_full_pipeline.py

## Phase 5: User Story 3 (P3) — Accurate Heading Signatures

**Goal**: Ensure heading inference uses full font signatures and supports same-family/different-style headings.

**Independent Test**: Run font sampling on Homebrewery fixture and verify distinct signatures by weight/style.

- [ ] T022 [US3] Update font signature model to include weight/style in src/gm_kit/pdf_convert/metadata.py
- [ ] T023 [US3] Update font-family-mapping.json generation to include full signature fields in src/gm_kit/pdf_convert/phases/phase3.py
- [ ] T024 [US3] Update heading inference to match on full signature in src/gm_kit/pdf_convert/phases/phase3.py
- [ ] T025 [US3] Add unit tests for same-family/different-style headings in tests/unit/pdf_convert/test_metadata.py
- [ ] T026 [US3] Add integration test using Homebrewery fixture in tests/integration/pdf_convert/test_cli_full_pipeline.py

## Phase 6: Polish & Cross-Cutting

- [ ] T027 Add regression-test harness for anomalies discovered during integration tests (document pattern in tests/README.md)
- [ ] T028 Verify error conditions map to architecture table in tests/unit/pdf_convert/test_errors.py
- [ ] T029 Update documentation for new pipeline artifacts in docs/user/user_guide.md

## Dependencies

- US1 must complete before US2 and US3 (US2/US3 depend on implemented phases).
- US3 relies on Phase3 implementation from US1.

## Parallel Execution Examples

- [P] T006–T012 can be implemented in parallel (distinct phase modules) once the registry structure is in place.
- [P] T020 and T021 can run in parallel after phase execution is implemented.
- [P] T022–T025 can run in parallel with other phase work once Phase3 scaffolding exists.

## Implementation Strategy

- MVP = User Story 1 (Phase 0–8 pipeline) with Phase 8 markdown output and diagnostics artifacts.
- Layer in User Story 2 (phase-only runs) once pipeline is functional.
- Finish with User Story 3 (full font signature inference + tests).
