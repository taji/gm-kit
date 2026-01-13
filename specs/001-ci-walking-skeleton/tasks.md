---

description: "Task list for CI Pipeline for Walking Skeleton"
---

# Tasks: CI Pipeline for Walking Skeleton

**Input**: Design documents from `/specs/001-ci-walking-skeleton/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL; this feature relies on existing test suites and adds CI orchestration.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create CI workflow scaffold for PRs to master in `.github/workflows/ci.yml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Add `bandit` and `audit` tasks in `justfile` to run `bandit -r src` and `uv audit`
- [x] T003 Add `test-unit`, `test-integration`, and `test-parity` tasks in `justfile` and update `test` to run all three

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - PR Validation on Linux (Priority: P1) 🎯 MVP

**Goal**: Run Linux CI gates on PRs to master with parity checks and clear pass/fail status

**Independent Test**: Open a PR that intentionally fails one gate and confirm CI blocks merge with a clear failure status

### Implementation for User Story 1

- [x] T004 [US1] Implement Linux CI job that installs dependencies and runs `just lint` in `.github/workflows/ci.yml`
- [x] T005 [US1] Add steps for `just typecheck`, `just test-unit`, `just test-integration`, `just test-parity`, `just bandit`, and `just audit` in `.github/workflows/ci.yml`
- [x] T006 [US1] Add steps to install PowerShell (`pwsh`) on Linux and fail CI if installation fails in `.github/workflows/ci.yml`
- [x] T007 [US1] Run `just test-parity` after pwsh install and fail on parity mismatches in `.github/workflows/ci.yml`
- [x] T008 [US1] Ensure CI status is reported and gating on PRs to master in `.github/workflows/ci.yml`

**Checkpoint**: User Story 1 is fully functional and independently testable

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Documentation alignment and cleanup

- [x] T009 [P] Update `specs/001-ci-walking-skeleton/research.md` to remove Windows CI references and align with Linux-only scope
- [x] T010 [P] Update `specs/001-ci-walking-skeleton/data-model.md` to remove Windows job references
- [x] T011 [P] Update `specs/001-ci-walking-skeleton/quickstart.md` to remove Windows steps and align with Linux-only CI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on User Story 1 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Parallel Opportunities

- After Phase 3, tasks T009–T011 can run in parallel (different files)

---

## Parallel Example: User Story 1

```bash
Task: "Implement Linux CI job that installs dependencies and runs just lint in .github/workflows/ci.yml"
Task: "Add steps for just typecheck, just test-unit, just test-integration, just test-parity, just bandit, and just audit in .github/workflows/ci.yml"
Task: "Add steps to install PowerShell (pwsh) on Linux and fail CI if installation fails in .github/workflows/ci.yml"
Task: "Run just test-parity after pwsh install and fail on parity mismatches in .github/workflows/ci.yml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm CI runs gates and parity on PRs

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Merge
3. Complete documentation alignment tasks

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Avoid vague tasks or missing file paths
