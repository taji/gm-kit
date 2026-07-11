# E7-15 Callout Fallback Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure callout detection never silently drops a Keeper/GM note anchor by adding phrase-only fallback annotations and a warning summary when full-span expansion is unsafe.

**Architecture:** Keep the current text-anchor detector as the primary path, but split the output into two cases: full-span callout proposals when the region can be expanded safely, and fallback phrase-only proposals when expansion is uncertain or blocked by a boundary. Emit a compact warning artifact plus a prep-log warning whenever the detector’s anchor count and proposal count differ so the user can review the short annotations manually.

**Tech Stack:** Python 3.13.7, PyMuPDF (`fitz`), `pytest`, existing prep contracts/handlers, YAML guidance defaults, JSON warning artifacts.

---

### Task 1: Add fallback phrase-only callout proposals

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/callout_detection.py`
- Modify: `tests/unit/pdf_convert/prep/test_callout_detection.py`

- [ ] **Step 1: Write the failing test**

```python
def test_detect_callout_proposals__should_emit_phrase_only_fallback__when_a_note_block_cannot_expand_safely() -> None:
    # Build a PDF page with two Keeper's Note blocks in the same column.
    # Expect the second block to receive a short phrase-only annotation instead
    # of disappearing when the collector refuses to span into the next block.
    proposals = detect_callout_proposals(pdf_path, PrepGuidanceInput())
    fallback = next(item for item in proposals if item.metadata.get("fallback_reason"))
    assert fallback.metadata["fallback_mode"] == "phrase_only"
    assert fallback.bbox[2] - fallback.bbox[0] < 180.0
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:
`uv run --python "3.13.7" --extra dev -- pytest tests/unit/pdf_convert/prep/test_callout_detection.py::test_detect_callout_proposals__should_emit_phrase_only_fallback__when_a_note_block_cannot_expand_safely -q`

Expected: FAIL because the fallback path does not yet exist.

- [ ] **Step 3: Implement the minimal detector change**

```python
def detect_callout_proposals(...):
    # 1) detect all anchor lines
    # 2) try full-span expansion
    # 3) if expansion is uncertain or blocked, emit a phrase-only bbox
    #    around the anchor line with metadata:
    #    {"fallback_mode": "phrase_only", "fallback_reason": "..."}
```

```python
def _build_fallback_callout_proposal(...):
    # Use the anchor line rectangle plus a small padding window.
    # Keep the proposal label as "callout" so downstream review stays consistent.
```

- [ ] **Step 4: Run the test and confirm it passes**

Run:
`uv run --python "3.13.7" --extra dev -- pytest tests/unit/pdf_convert/prep/test_callout_detection.py::test_detect_callout_proposals__should_emit_phrase_only_fallback__when_a_note_block_cannot_expand_safely -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/callout_detection.py tests/unit/pdf_convert/prep/test_callout_detection.py
git commit -m "feat: add phrase-only fallback callout proposals"
```

### Task 2: Emit warning summary when anchors outnumber proposals

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- Modify: `src/gm_kit/pdf_convert/prep/handlers.py`
- Modify: `src/gm_kit/pdf_convert/prep/orchestrator.py`
- Modify: `tests/unit/pdf_convert/prep/test_analysis_artifacts.py`
- Modify: `tests/unit/pdf_convert/prep/test_guidance_handlers.py`
- Modify: `tests/unit/pdf_convert/prep/test_orchestrator.py`

- [ ] **Step 1: Write the failing test**

```python
def test_handle_generate_annotation_proposals__should_write_callout_warning_summary__when_fallbacks_were_used() -> None:
    # Stub the detector so one anchor becomes a fallback phrase-only proposal.
    # Assert the warning artifact exists and contains the page/anchor details.
    ...
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:
`uv run --python "3.13.7" --extra dev -- pytest tests/unit/pdf_convert/prep/test_guidance_handlers.py::test_handle_generate_annotation_proposals__should_write_callout_warning_summary__when_fallbacks_were_used -q`

Expected: FAIL because the warning artifact is not written yet.

- [ ] **Step 3: Add the warning artifact path and writer**

```python
# analysis_artifacts.py
callout_detection_warnings: Path

# handlers.py
def _write_callout_detection_warnings(...):
    # write JSON only when there are warnings
```

```python
# warning payload shape
{
  "total_anchors": 13,
  "full_span_count": 10,
  "fallback_count": 3,
  "warnings": [
    {"page": 18, "anchor_text": "KEEPER’S NOTE:", "reason": "next_block_boundary"},
  ]
}
```

- [ ] **Step 4: Run the test and confirm it passes**

Run:
`uv run --python "3.13.7" --extra dev -- pytest tests/unit/pdf_convert/prep/test_guidance_handlers.py tests/unit/pdf_convert/prep/test_orchestrator.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/analysis_artifacts.py src/gm_kit/pdf_convert/prep/handlers.py src/gm_kit/pdf_convert/prep/orchestrator.py tests/unit/pdf_convert/prep/test_analysis_artifacts.py tests/unit/pdf_convert/prep/test_guidance_handlers.py tests/unit/pdf_convert/prep/test_orchestrator.py
git commit -m "feat: add callout fallback warning summary"
```

### Task 3: Verify fixture behavior end to end

**Files:**
- Modify: `tests/unit/pdf_convert/prep/test_callout_detection.py`
- Modify: `tests/integration/pdf_convert/test_callout_bbox_refinement.py`
- Modify: `specs/e7-15-annotation-placement-refinement/feature_journal.md`

- [ ] **Step 1: Add a count-comparison regression**

```python
def test_detect_callout_proposals__should_warn_when_anchor_count_exceeds_full_span_count__when_coc_fixture_contains_multiple_keeper_notes() -> None:
    # Count KEEPER'S NOTE anchors in the fixture text and compare them to
    # emitted proposals. Assert the warning artifact records the difference.
```

- [ ] **Step 2: Run the detector and integration tests**

Run:
`uv run --python "3.13.7" --extra dev -- pytest tests/unit/pdf_convert/prep/test_callout_detection.py tests/integration/pdf_convert/test_callout_bbox_refinement.py -q`

Expected: PASS with the warning summary present for the CoC fixture.

- [ ] **Step 3: Re-run the fixture command manually**

Run:
`rm -rf tmp/coc-quickstart-prep && mkdir -p tmp && uv run --python "3.13.7" --extra dev --editable -- gmkit analyze-and-prep-pdf "tests/fixtures/pdf_convert/CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules.pdf" --output tmp/coc-quickstart-prep --yes`

Expected: the prep log reports a warning summary, `annotation-proposals.json` contains fallback phrase-only callouts where needed, and the rendered PDF still shows editable annotations.

- [ ] **Step 4: Update the feature journal**

Append a factual journal entry describing the fallback behavior, warning summary, and final fixture outcome.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/pdf_convert/prep/test_callout_detection.py tests/integration/pdf_convert/test_callout_bbox_refinement.py specs/e7-15-annotation-placement-refinement/feature_journal.md
git commit -m "test: cover callout fallback warnings"
```

