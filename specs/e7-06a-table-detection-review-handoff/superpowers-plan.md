# E7-06a Table Detection Review Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move table review into prep so the user reviews annotated PDFs while conversion consumes finalized table decisions from `prep-guidance.resolved.json`.

**Architecture:** Prep remains the source of truth for table candidate generation, review rendering, and review finalization. Conversion stops relying on `tables-manifest.json` and instead loads the resolved prep guidance artifact as the authoritative table contract. The user-facing review surface stays the annotated PDF; JSON artifacts remain machine-facing.

**Tech Stack:** Python 3.13, `typer`, `fitz`/PyMuPDF, `pytest`, existing `gm_kit.pdf_convert.prep` contracts/handlers/orchestrator, conversion phases under `src/gm_kit/pdf_convert/phases/`.

---

### Task 1: Lock the prep table review contract

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/contracts.py`
- Modify: `src/gm_kit/pdf_convert/prep/handlers.py`
- Test: `tests/unit/pdf_convert/prep/test_guidance_contracts.py`
- Test: `tests/unit/pdf_convert/prep/test_review_handlers.py`

- [ ] **Step 1: Write the failing tests**

Add tests that prove `PrepGuidanceResolved.table_regions` round-trips `proposal_id`, `page`, and `bbox`, and that `build_final_resolved_guidance()` preserves reviewed table regions after proposal edits.

- [ ] **Step 2: Run the targeted tests**

Run: `pytest tests/unit/pdf_convert/prep/test_guidance_contracts.py tests/unit/pdf_convert/prep/test_review_handlers.py -q`
Expected: failure where table regions are not yet retained or normalized as required.

- [ ] **Step 3: Make the resolved table contract explicit**

Update the prep-side normalization path so finalized table decisions remain in `prep-guidance.resolved.json` with stable `proposal_id` values and normalized region payloads.

- [ ] **Step 4: Re-run the targeted tests**

Run: `pytest tests/unit/pdf_convert/prep/test_guidance_contracts.py tests/unit/pdf_convert/prep/test_review_handlers.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/contracts.py src/gm_kit/pdf_convert/prep/handlers.py tests/unit/pdf_convert/prep/test_guidance_contracts.py tests/unit/pdf_convert/prep/test_review_handlers.py
git commit -m "feat: preserve finalized table guidance in prep"
```

### Task 2: Keep prep review output PDF-first

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- Modify: `src/gm_kit/pdf_convert/prep/orchestrator.py`
- Modify: `src/gm_kit/pdf_convert/prep/cli_helpers.py`
- Test: `tests/unit/pdf_convert/prep/test_analysis_artifacts.py`
- Test: `tests/unit/pdf_convert/prep/test_orchestrator.py`
- Test: `tests/unit/pdf_convert/prep/test_cli_helpers.py`

- [ ] **Step 1: Write the failing tests**

Add/adjust tests so prep continues to materialize `annotation-proposals.json`, `annotated-prep.pdf`, and `prep-guidance.reviewed.json` in the workspace, and so `revise_prep_guidance()` routes through the existing finalize-review path.

- [ ] **Step 2: Run the targeted tests**

Run: `pytest tests/unit/pdf_convert/prep/test_analysis_artifacts.py tests/unit/pdf_convert/prep/test_orchestrator.py tests/unit/pdf_convert/prep/test_cli_helpers.py -q`
Expected: failure only where the workspace artifact set or revise path still assumes the older table workflow.

- [ ] **Step 3: Wire the prep review flow to the existing shared artifacts**

Keep the user-facing review surface limited to `annotated-prep.pdf` and ensure the revise command finalizes review edits into `prep-guidance.reviewed.json` without introducing a table-specific manifest.

- [ ] **Step 4: Re-run the targeted tests**

Run: `pytest tests/unit/pdf_convert/prep/test_analysis_artifacts.py tests/unit/pdf_convert/prep/test_orchestrator.py tests/unit/pdf_convert/prep/test_cli_helpers.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/analysis_artifacts.py src/gm_kit/pdf_convert/prep/orchestrator.py src/gm_kit/pdf_convert/prep/cli_helpers.py tests/unit/pdf_convert/prep/test_analysis_artifacts.py tests/unit/pdf_convert/prep/test_orchestrator.py tests/unit/pdf_convert/prep/test_cli_helpers.py
git commit -m "feat: keep prep table review pdf-first"
```

### Task 3: Remove table rediscovery from conversion

**Files:**
- Modify: `src/gm_kit/pdf_convert/phases/phase7.py`
- Modify: `src/gm_kit/pdf_convert/phases/phase8.py`
- Modify: `src/gm_kit/pdf_convert/phases/phase9.py`
- Modify: `src/gm_kit/pdf_convert/phases/phase10.py`
- Test: `tests/unit/pdf_convert/test_phase7.py`
- Test: `tests/unit/pdf_convert/test_phase8.py`
- Test: `tests/unit/pdf_convert/test_phase9.py`
- Test: `tests/unit/pdf_convert/test_phase10.py`

- [ ] **Step 1: Write the failing tests**

Add regression tests that fail if conversion still reads `tables-manifest.json` as the source of truth or silently continues when resolved table guidance is missing. Cover:

1. phase 7 no longer emits a downstream table manifest for conversion
2. phase 8 reads finalized table regions from prep guidance instead of rediscovering tables
3. phase 9 table integrity checks use the prep guidance contract and emit actionable errors when it is absent
4. later phases continue to see reviewed guidance through the existing prep-guidance loader path

- [ ] **Step 2: Run the targeted tests**

Run: `pytest tests/unit/pdf_convert/test_phase7.py tests/unit/pdf_convert/test_phase8.py tests/unit/pdf_convert/test_phase9.py tests/unit/pdf_convert/test_phase10.py -q`
Expected: failure where legacy table-manifest reads still exist.

- [ ] **Step 3: Switch conversion to the prep guidance contract**

Update the conversion phases so finalized table decisions come from `prep-guidance.reviewed.json` / resolved prep guidance, not `tables-manifest.json`. Keep the error path explicit when the resolved table contract is missing.

- [ ] **Step 4: Re-run the targeted tests**

Run: `pytest tests/unit/pdf_convert/test_phase7.py tests/unit/pdf_convert/test_phase8.py tests/unit/pdf_convert/test_phase9.py tests/unit/pdf_convert/test_phase10.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/phases/phase7.py src/gm_kit/pdf_convert/phases/phase8.py src/gm_kit/pdf_convert/phases/phase9.py src/gm_kit/pdf_convert/phases/phase10.py tests/unit/pdf_convert/test_phase7.py tests/unit/pdf_convert/test_phase8.py tests/unit/pdf_convert/test_phase9.py tests/unit/pdf_convert/test_phase10.py
git commit -m "feat: consume resolved prep guidance for tables"
```

### Task 4: Update the user-facing docs and handoff notes

**Files:**
- Modify: `docs/user/user_guide.md`
- Modify: `specs/e7-06a-table-detection-review-handoff/feature_journal.md`
- Modify: `BACKLOG.md` only if the implemented behavior changes the E7-06a scope

- [ ] **Step 1: Write the failing docs checks**

Add assertions or manual review checks in the relevant docs tests, if present, to reflect that users review the annotated PDF and do not inspect table JSON directly.

- [ ] **Step 2: Update the docs**

Document the prep table-review workflow in the user guide:

1. run prep
2. inspect `annotated-prep.pdf`
3. revise the detected tables
4. finalize `prep-guidance.reviewed.json`
5. run conversion

- [ ] **Step 3: Update the feature journal**

Append a session entry recording the contract decision, the conversion migration boundary, and the next implementation step.

- [ ] **Step 4: Re-run any docs-related checks**

Run the smallest available docs or regression checks that cover the edited guidance.

- [ ] **Step 5: Commit**

```bash
git add docs/user/user_guide.md specs/e7-06a-table-detection-review-handoff/feature_journal.md BACKLOG.md
git commit -m "docs: describe prep-first table review workflow"
```

## Coverage Check

- Prep contract and review finalization: Task 1
- PDF-first review workflow and artifact layout: Task 2
- Conversion migration away from table rediscovery: Task 3
- User docs and handoff record: Task 4

## Risks

- The current code still has legacy `tables-manifest.json` consumers in conversion phases, so Task 3 is the main migration risk.
- If the shared resolved guidance schema is too small for future table metadata, the next iteration should extend `PrepGuidanceResolved` instead of creating a second table-only manifest.
- Keep the user-facing workflow anchored on the annotated PDF; do not expand the review UX into JSON editing.
