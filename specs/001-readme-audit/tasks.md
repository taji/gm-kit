# Tasks: GM-Kit README & Structure Audit

**Input**: Design documents from `/specs/001-readme-audit/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align on planning sources before editing docs.

- [x] T001 Review Arcane Library goals in `planning/project-overview.md` to capture mission language for README updates.
- [x] T002 Review current epics/prompts in `planning/prompts.md` to confirm feature-creation instructions that will be referenced in README (no separate TODOs document).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish baseline repo readiness data and editing checkpoints.

- [x] T003 Run the current manual audit (`ls -a` + checklist) from repo root and log the output in `planning/Gm-Kit Development Journal.md` as a baseline before edits.
- [x] T004 Capture the existing structure of `README.md` and `.gitignore` (notes in `specs/001-readme-audit/plan.md` or journal) so changes can be summarized later.

---

## Phase 3: User Story 1 - Mission-first README (Priority: P1) 🎯 MVP

**Goal**: README communicates Arcane Library mission, workflow, and how to start features from prompts.

**Independent Test**: A newcomer reads README and can describe the mission plus follow the steps to run `/speckit.specify` using a prompt from `planning/prompts.md`.

### Implementation

- [x] T005 [US1] Update the mission section in `README.md` with Arcane Library focus, referencing `planning/project-overview.md`.
- [x] T006 [US1] Add a workflow summary in `README.md` that outlines prompts → specs → `/speckit.plan` → tasks → implementation → validation with links to planning docs.
- [x] T007 [US1] Create an “Add a Feature” subsection in `README.md` showing how to copy prompts from `planning/prompts.md` into `/speckit.specify` and proceed through clarify/plan/implement phases.

---

## Phase 4: User Story 2 - Ignore transient directories (Priority: P1)

**Goal**: `.gitignore` permanently excludes `spec-kit/` and `temp-resources/`.

**Independent Test**: Creating files under those directories and running `git status` shows no tracked changes.

### Implementation

- [x] T008 [US2] Append explicit entries for `spec-kit/` and `temp-resources/` at the end of `.gitignore`.
- [x] T009 [US2] From repo root, create temporary files under `spec-kit/.ignore-check` and `temp-resources/.ignore-check`, run `git status`, and document in `planning/Gm-Kit Development Journal.md` that both remain untracked; delete the temp files afterward.

---

## Phase 5: User Story 3 - Manual structure audit (Priority: P2)

**Goal**: README documents a repeatable manual audit (snapshot + checklist) that PR authors can follow.

**Independent Test**: Following README’s audit steps yields the same snapshot/checklist described and can be pasted into a PR.

### Implementation

- [x] T010 [US3] Add a “Manual Structure Audit” section to `README.md` covering the `ls -a`/`tree` snapshot, checklist items from `contracts/manual-audit.md`, and expectations for recording results.
- [x] T011 [US3] Document in `README.md` how and where to paste audit results (PR description and/or planning notes) and remind contributors to rerun audits after touching README or `.gitignore`.

---

## Phase 6: User Story 4 - Contributor lifecycle documentation (Priority: P2)

**Goal**: README contains a detailed lifecycle section describing todos → prompts → specs → `/speckit.plan` → tasks → implementation → validation plus sync expectations.

**Independent Test**: A reviewer can trace any feature from todo through validation by following the README lifecycle section alone.

### Implementation

- [x] T012 [US4] Write a “Contributor Lifecycle” section inside `README.md` that enumerates every stage, identifies file locations (planning docs, specs directory), and references the Spec-Kit commands used.
- [x] T013 [US4] Extend that section with sync guidance explaining how to capture decisions in Obsidian, sync back to git, and ensure README stays aligned with `planning/project-overview.md` and `planning/prompts.md`.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate documentation cohesion and readiness signals.

- [x] T014 Re-read the entire `README.md` to ensure mission, workflow, lifecycle, audit, and feature instructions flow logically and link to the correct files.
- [x] T015 Rerun the full manual audit from repo root, paste the updated snapshot/checklist into `planning/Gm-Kit Development Journal.md`, and confirm README instructions match the executed steps.

---

## Dependencies & Execution Order

- Phase 1 (Setup) must complete before modifying documentation to ensure references are accurate.
- Phase 2 (Foundational) captures the pre-change baseline; no user story tasks should start until it is done.
- User Story 1 (P1) is the MVP and depends on Phases 1–2; it must complete before any other story to provide context for the rest of the README updates.
- User Story 2 (P1) can begin after Phase 2 but should follow or run alongside US1 since it touches `.gitignore`, independent of README edits.
- User Stories 3 and 4 (P2) depend on US1 because they extend the README built there.
- Polish phase runs after all user stories to validate cross-cutting consistency.

**Story dependency graph**:
1. US1 (P1) – baseline README mission + workflow.
2. US2 (P1) – independent; can run parallel with US1 after foundational work.
3. US3 (P2) – depends on US1 (needs README scaffolding).
4. US4 (P2) – depends on US1 (same file) and should follow US3 to keep flow cohesive.

---

## Parallel Execution Examples

- **Parallel Option A**: While one contributor handles README mission/workflow sections (US1), another can update `.gitignore` and verify ignore behavior (US2) because they touch different files.
- **Parallel Option B**: Within US1, editing the mission text (T005) can run in parallel with drafting the workflow summary (T006) if collaborators coordinate merges carefully; T007 should follow once both references are finalized.
- **Parallel Option C**: After US1 completes, US3 and US4 can be developed in sequence or by different contributors editing distinct sections of README (audit vs lifecycle) as long as merge conflicts are managed.

---

## Implementation Strategy

1. **MVP**: Deliver Phase 1–4 (setup, foundational, US1, US2). At this point, README communicates mission/workflow and `.gitignore` protects transient folders—enough to unblock new contributors.
2. **Incremental Additions**: Layer in US3 (audit instructions) and US4 (lifecycle section) to provide comprehensive contributor guidance.
3. **Validation**: Complete the Polish phase by re-running the documented audit and confirming README alignment with planning docs.
4. **Handoff**: Reference `quickstart.md` to ensure future contributors can replicate the workflow described.
