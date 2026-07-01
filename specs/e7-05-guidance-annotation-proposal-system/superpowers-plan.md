# E7-05 Guidance + Annotation Proposal System Closure Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify the implemented E7-05 guidance/proposal contract matches the approved design, then close out the feature cleanly.

**Architecture:** No new product code is expected in this plan. The work is a validation-and-handoff pass over the already-implemented prep contract: confirm the defaults artifact, proposal artifact, resolved contract, and required annotated PDF behave consistently; then update the backlog and journal to reflect completion.

**Tech Stack:** Python 3.13.7, existing prep runtime code, pytest, ruff, mypy, git, the repo journals/backlog docs.

---

### Task 1: Verify the E7-05 contract surface

**Files:**
- Inspect: `src/gm_kit/pdf_convert/prep/contracts.py`
- Inspect: `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- Inspect: `src/gm_kit/pdf_convert/prep/handlers.py`
- Inspect: `src/gm_kit/pdf_convert/prep/orchestrator.py`
- Inspect: `docs/user/user_guide.md`
- Inspect: `BACKLOG.md`

- [ ] **Step 1: Confirm the runtime contract names are aligned**

Run:
```bash
rg -n "prep-guidance\.defaults\.json|annotation-proposals\.json|prep-guidance\.resolved\.json|annotated-prep\.pdf|handle_write_guidance_defaults|guidance_defaults" src/gm_kit/pdf_convert/prep docs/user/user_guide.md BACKLOG.md
```

Expected:
- matches show `prep-guidance.defaults.json` as the seed artifact
- matches show `annotation-proposals.json` and `prep-guidance.resolved.json` as separate downstream artifacts
- matches show `annotated-prep.pdf` as a required prep output in the docs

- [ ] **Step 2: Confirm the schema names match the design**

Run:
```bash
rg -n "class AnnotationProposal|class PrepGuidanceInput|class PrepGuidanceResolved" src/gm_kit/pdf_convert/prep/contracts.py
```

Expected:
- `AnnotationProposal` exposes `proposal_id`, `label`, `page`, `bbox`, `confidence`, and `metadata`
- `PrepGuidanceInput` exposes the six boolean workflow toggles
- `PrepGuidanceResolved` exposes `skip_pages`, `skip_regions`, `table_regions`, and `callout_regions`

### Task 2: Verify the prep behavior with focused tests

**Files:**
- Inspect: `tests/unit/pdf_convert/prep/test_analysis_artifacts.py`
- Inspect: `tests/unit/pdf_convert/prep/test_contracts.py`
- Inspect: `tests/unit/pdf_convert/prep/test_orchestrator.py`
- Inspect: `tests/unit/pdf_convert/prep/test_review_handlers.py`

- [ ] **Step 1: Run the prep unit suite**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep -q
```

Expected:
- all prep unit tests pass
- the suite confirms the renamed defaults file and the required annotated-PDF outputs

- [ ] **Step 2: Run lint**

Run:
```bash
just lint
```

Expected:
- ruff reports no issues

- [ ] **Step 3: Run typecheck**

Run:
```bash
just typecheck
```

Expected:
- current repo state still reports the existing unrelated `phase7.py:883` mypy error
- record that failure as pre-existing and unrelated to E7-05 closure

### Task 3: Close the feature record

**Files:**
- Modify: `specs/e7-05-guidance-annotation-proposal-system/feature_journal.md`
- Modify: `BACKLOG.md`

- [ ] **Step 1: Update the feature journal**

Append a session entry that records:
- the E7-05 contract was verified against the implemented runtime
- `annotated-prep.pdf` is required
- `annotation-proposals.json` remains the machine evidence trail
- `prep-guidance.resolved.json` remains the authoritative downstream contract
- the verification command results

- [ ] **Step 2: Mark E7-05 complete in the backlog if verification succeeded**

Update the Epic 7 backlog entry for E7-05 from planned to completed only after the verification steps above succeed.

Expected result:
- the backlog reflects the implemented state
- the journal gives the next agent a clear handoff into E7-06

---

## Self-Review

- Spec coverage is complete for the current E7-05 closure goal: contract names, required annotated PDF, proposal evidence, resolved guidance, tests, lint, and typecheck all map to concrete validation tasks.
- Placeholder scan is clean: every step uses exact files or exact commands.
- Type consistency is aligned with the implemented runtime: `guidance_defaults`, `AnnotationProposal`, `PrepGuidanceInput`, `PrepGuidanceResolved`, and `annotated-prep.pdf` are used consistently across the plan.
