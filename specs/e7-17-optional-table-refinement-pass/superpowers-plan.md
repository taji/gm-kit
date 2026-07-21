# E7-17 Optional Table Refinement Pass Implementation Plan

> **For agentic workers:** Keep the worktree as the source of truth, compare the current table path to the callout path first, and avoid changing table heuristics unless the comparison shows a real gap.

**Goal:** Add an optional review/revise/resume path for table proposals that matches the callout refinement contract as closely as possible.

**Architecture:** Preserve the existing table proposal detection pass. Introduce a prep-side review boundary that renders one shared annotated PDF before pause, captures user or agent revisions in machine-readable artifacts, and resumes prep from those artifacts so downstream conversion can consume finalized table geometry.

**Tech Stack:** Python 3.13.7, existing prep modules under `src/gm_kit/pdf_convert/prep/`, PyMuPDF for review PDF generation, pytest for unit/integration coverage, `just` for repo checks.

---

## Planned File Areas

**Likely create or modify**
- `src/gm_kit/pdf_convert/prep/handlers.py`
- `src/gm_kit/pdf_convert/prep/orchestrator.py`
- `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- `src/gm_kit/pdf_convert/prep/contracts.py`
- `tests/unit/pdf_convert/prep/test_handlers.py`
- `tests/unit/pdf_convert/prep/test_orchestrator.py`
- `tests/integration/pdf_convert/test_table_refinement_pass.py`
- `specs/e7-17-optional-table-refinement-pass/feature_journal.md`

The actual diff should stay small if the callout pattern is reused instead of re-invented.

---

## Task 1: Compare the table flow to the callout flow

**Files:**
- Read current prep table-handling code
- Read the callout refinement code for structure

- [ ] **Step 1: Identify the current table artifacts and boundaries**

Document how table proposals are currently produced, rendered, and consumed.

- [ ] **Step 2: Identify the missing callout-equivalent pieces**

List the places where tables still diverge from the callout workflow, especially around review PDF emission and resume handling.

- [ ] **Step 3: Capture the comparison in tests or comments as needed**

Add targeted regression coverage if a mismatch is subtle enough that future edits could reintroduce it.

---

## Task 2: Add the table review handoff

**Files:**
- Modify `src/gm_kit/pdf_convert/prep/handlers.py`
- Modify `src/gm_kit/pdf_convert/prep/orchestrator.py`
- Modify `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- Modify `src/gm_kit/pdf_convert/prep/contracts.py`

- [ ] **Step 1: Render the annotated table review PDF before pause**

Ensure the shared reviewable PDF exists before the workflow pauses for manual or external refinement and that table annotations use the cyan visual cue.

- [ ] **Step 2: Add the refined table artifact contract if missing**

If the current code does not already persist a finalized table artifact, add one that matches the callout refinement shape closely enough to be understandable.

- [ ] **Step 3: Resume from the refined table artifact**

Teach the orchestrator to resume prep from the revised table artifact and to finalize the downstream guidance contract from it.

---

## Task 3: Add tests

**Files:**
- `tests/unit/pdf_convert/prep/test_handlers.py`
- `tests/unit/pdf_convert/prep/test_orchestrator.py`
- `tests/integration/pdf_convert/test_table_refinement_pass.py`

- [ ] **Step 1: Add a unit test for the review PDF boundary**

Verify the shared review PDF is present before any handoff pause and that table annotations are visually distinct from callouts.

- [ ] **Step 2: Add a unit test for the revised table artifact**

Verify the revise/resume path consumes the refined table artifact and produces the final downstream prep contract without requiring a second review pass.

- [ ] **Step 3: Add an integration test using a fixture PDF**

Exercise the current table flow against a representative PDF and confirm the handoff path behaves the same way as callouts, with one shared review PDF for both annotation types.

---

## Task 4: Update docs and journal

**Files:**
- `specs/e7-17-optional-table-refinement-pass/feature_journal.md`
- any relevant prep docs if user-facing behavior changes

- [ ] **Step 1: Record the implemented table refinement contract**

Append a factual journal entry summarizing the comparison, the artifacts, and the handoff behavior.

- [ ] **Step 2: Commit when stable**

```bash
git add \
  src/gm_kit/pdf_convert/prep \
  tests/unit/pdf_convert/prep \
  tests/integration/pdf_convert/test_table_refinement_pass.py \
  specs/e7-17-optional-table-refinement-pass/feature_journal.md

git commit -m "feat: add optional table refinement pass"
```
