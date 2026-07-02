# E7-06 Annotation Review UX + Skip Intent Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add prep review artifacts, explicit skip page/range capture, a separate revision command, and reviewed-guidance regeneration on top of E7-05.

**Architecture:** Extend the existing prep contract and orchestrator rather than introducing a separate review subsystem. Keep the implementation split into focused units: review/edit contracts, artifact-path expansion, parsing/revision helpers, annotated-PDF rendering, a revision command, and conversion consumption of the reviewed artifact. `annotation-proposals.json` is immutable proposal evidence; `annotated-prep.pdf` is the human review surface; `annotation-review.edits.json` is the extracted review record; `prep-guidance.resolved.json` is the baseline downstream contract; and `prep-guidance.reviewed.json` becomes authoritative after revision.

**Tech Stack:** Python 3.13.7, stdlib `dataclasses`/`json`/`pathlib`/`re`, existing prep orchestrator/handler patterns, PyMuPDF (`fitz`) for annotated PDF rendering, pytest, ruff, mypy.

---

### Task 1: Add review-edit contracts and guidance extensions

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/contracts.py`
- Create: `tests/unit/pdf_convert/prep/test_review_contracts.py`

- [ ] **Step 1: Write the failing contract tests**

```python
from gm_kit.pdf_convert.prep.contracts import (
    AnnotationReviewEdits,
    PrepGuidanceInput,
)


def test_annotation_review_edits__should_roundtrip_review_state__when_payload_is_valid() -> None:
    edits = AnnotationReviewEdits(
        review_mode="interactive",
        review_status="revised",
        skip_ranges_input="2,5,12-14",
        skip_pages_explicit=[2, 5, 12, 13, 14],
        proposal_decisions={"ap-001": "accept", "ap-002": "reject"},
        updated_regions={
            "ap-003": {
                "page": 18,
                "bbox": [72.0, 250.0, 520.0, 600.0],
                "label": "table",
            }
        },
        notes="",
    )

    payload = edits.to_dict()
    restored = AnnotationReviewEdits.from_dict(payload)

    assert restored == edits


def test_prep_guidance_defaults__should_roundtrip_review_flags__when_review_fields_are_present() -> None:
    guidance = PrepGuidanceInput(
        prefer_detect_tables=True,
        prefer_detect_callouts=True,
        prefer_skip_full_page_artifacts=True,
        review_requested=True,
        auto_accept_annotations=False,
        capture_skip_intent=True,
    )

    payload = guidance.to_dict()
    restored = PrepGuidanceInput.from_dict(payload)

    assert restored == guidance


def test_annotation_review_edits__should_raise_value_error__when_review_mode_is_invalid() -> None:
    payload = {
        "review_mode": "manualish",
        "review_status": "pending",
        "skip_ranges_input": "",
        "skip_pages_explicit": [],
        "proposal_decisions": {},
        "updated_regions": {},
        "notes": "",
    }

    try:
        AnnotationReviewEdits.from_dict(payload)
    except ValueError as error:
        assert str(error) == "AnnotationReviewEdits.review_mode must be one of auto_accept, bypass, interactive"
    else:
        raise AssertionError("AnnotationReviewEdits.from_dict() should reject invalid review_mode")
```

- [ ] **Step 2: Run the new contract tests to confirm they fail**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_review_contracts.py -q
```

Expected: FAIL because `AnnotationReviewEdits` and the new `PrepGuidanceInput` review fields do not exist yet.

- [ ] **Step 3: Implement the review contract models in `contracts.py`**

Add new dataclasses and validation helpers:

```python
@dataclass(frozen=True)
class AnnotationReviewEdits:
    review_mode: str
    review_status: str
    skip_ranges_input: str
    skip_pages_explicit: list[int]
    proposal_decisions: dict[str, str]
    updated_regions: dict[str, dict[str, object]]
    notes: str = ""
```

Extend `PrepGuidanceInput` to carry review intent only:

```python
@dataclass(frozen=True)
class PrepGuidanceInput:
    prefer_detect_tables: bool = True
    prefer_detect_callouts: bool = True
    prefer_skip_full_page_artifacts: bool = True
    review_requested: bool = True
    auto_accept_annotations: bool = False
    capture_skip_intent: bool = True
```

Validation rules:
- `review_mode` must be one of `interactive`, `auto_accept`, `bypass`
- `review_status` must be one of `pending`, `accepted`, `revised`, `auto_accepted`
- `proposal_decisions` values must be one of `accept`, `reject`, `edit`
- `updated_regions` entries must contain `page`, `bbox`, and `label`
- edited `label` must be one of `table`, `callout`, `skip`
- `skip_pages_explicit` uses the same page-list validation as resolved guidance
- `AnnotationReviewEdits` is derived from PDF annotations and persists the review result for downstream use

- [ ] **Step 4: Run the contract tests to confirm they pass**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_review_contracts.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/contracts.py tests/unit/pdf_convert/prep/test_review_contracts.py
git commit -m "feat: add E7-06 review edit contracts"
```

### Task 2: Add review artifact paths and skip-range parsing helpers

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- Modify: `src/gm_kit/pdf_convert/prep/handlers.py`
- Modify: `tests/unit/pdf_convert/prep/test_analysis_artifacts.py`
- Create: `tests/unit/pdf_convert/prep/test_review_parsing.py`

- [ ] **Step 1: Write the failing path and parsing tests**

```python
from pathlib import Path

from gm_kit.pdf_convert.prep.analysis_artifacts import build_analysis_artifact_paths
from gm_kit.pdf_convert.prep.handlers import parse_skip_ranges_input


def test_build_analysis_artifact_paths__should_include_review_edits_artifact__when_workspace_is_provided(
    tmp_path: Path,
) -> None:
    paths = build_analysis_artifact_paths(tmp_path / "workspace", pdf_stem="sample")

    assert paths.annotation_review_edits == (
        tmp_path / "workspace" / "prep" / "annotation-review.edits.json"
    )


def test_parse_skip_ranges_input__should_expand_ranges_and_deduplicate_pages__when_input_is_valid() -> None:
    pages = parse_skip_ranges_input("2, 5, 12-14, 14", page_count=20)

    assert pages == [2, 5, 12, 13, 14]


def test_parse_skip_ranges_input__should_raise_value_error__when_page_exceeds_document_bounds() -> None:
    try:
        parse_skip_ranges_input("2,21", page_count=20)
    except ValueError as error:
        assert str(error) == "Skip page 21 is outside document bounds 1-20"
    else:
        raise AssertionError("parse_skip_ranges_input() should reject out-of-bounds pages")
```

- [ ] **Step 2: Run the focused tests to confirm they fail**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_analysis_artifacts.py tests/unit/pdf_convert/prep/test_review_parsing.py -q
```

Expected: FAIL because the review artifact path and skip parser do not exist yet.

- [ ] **Step 3: Extend artifact paths and add the skip parser**

Extend `PrepAnalysisArtifactPaths`:

```python
annotation_review_edits=prep_root / "annotation-review.edits.json",
```

Add focused parsing helper in `handlers.py`:

```python
def parse_skip_ranges_input(raw_input: str, *, page_count: int) -> list[int]:
    ...
```

Behavior:
- empty string returns `[]`
- supports comma-separated page numbers and inclusive ranges
- trims whitespace
- rejects malformed tokens like `3-` or `a`
- rejects descending ranges like `9-4`
- rejects pages outside `1..page_count`
- returns sorted unique pages

- [ ] **Step 4: Run the focused tests to confirm they pass**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_analysis_artifacts.py tests/unit/pdf_convert/prep/test_review_parsing.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/analysis_artifacts.py src/gm_kit/pdf_convert/prep/handlers.py tests/unit/pdf_convert/prep/test_analysis_artifacts.py tests/unit/pdf_convert/prep/test_review_parsing.py
git commit -m "feat: add E7-06 review artifact path and skip parser"
```

### Task 3: Seed review edits, render annotated PDF, and revise guidance

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/handlers.py`
- Create: `tests/unit/pdf_convert/prep/test_review_handlers.py`

- [ ] **Step 1: Write the failing review/revision tests**

```python
from pathlib import Path

from gm_kit.pdf_convert.prep.contracts import AnnotationProposal, AnnotationReviewEdits
from gm_kit.pdf_convert.prep.handlers import (
    apply_review_edits_to_proposals,
    build_annotation_review_edits,
    build_final_resolved_guidance,
)


def test_build_annotation_review_edits__should_seed_pending_interactive_state__when_auto_accept_is_false() -> None:
    edits = build_annotation_review_edits(
        review_mode="interactive",
        skip_ranges_input="",
        skip_pages_explicit=[],
    )

    assert edits.review_status == "pending"
    assert edits.review_mode == "interactive"


def test_apply_review_edits_to_proposals__should_apply_reject_and_edit_decisions__when_review_payload_is_valid() -> None:
    proposals = [
        AnnotationProposal(
            proposal_id="ap-001",
            label="table",
            page=5,
            bbox=[72.0, 240.0, 520.0, 610.0],
            confidence=0.5,
            metadata={"source": "code", "source_section_id": "s1", "chunk_kind": "chapter", "ordinal": 1},
        ),
        AnnotationProposal(
            proposal_id="ap-002",
            label="callout",
            page=6,
            bbox=[72.0, 80.0, 300.0, 220.0],
            confidence=0.5,
            metadata={"source": "code", "trigger": "image-heavy-page"},
        ),
    ]
    edits = AnnotationReviewEdits(
        review_mode="interactive",
        review_status="revised",
        skip_ranges_input="",
        skip_pages_explicit=[],
        proposal_decisions={"ap-001": "edit", "ap-002": "reject"},
        updated_regions={
            "ap-001": {"page": 5, "bbox": [70.0, 230.0, 500.0, 600.0], "label": "table"}
        },
        notes="",
    )

    reviewed = apply_review_edits_to_proposals(proposals, edits)

    assert [(proposal.proposal_id, proposal.label, proposal.page, proposal.bbox) for proposal in reviewed] == [
        ("ap-001", "table", 5, [70.0, 230.0, 500.0, 600.0])
    ]


def test_build_final_resolved_guidance__should_apply_skip_precedence__when_skip_overlaps_table_region() -> None:
    proposals = [
        AnnotationProposal(
            proposal_id="ap-skip",
            label="skip",
            page=5,
            bbox=[60.0, 220.0, 530.0, 620.0],
            confidence=0.9,
            metadata={"source": "code", "scope": "region", "reason": "cover-art"},
        ),
        AnnotationProposal(
            proposal_id="ap-table",
            label="table",
            page=5,
            bbox=[72.0, 240.0, 520.0, 610.0],
            confidence=0.5,
            metadata={"source": "code", "source_section_id": "s1", "chunk_kind": "chapter", "ordinal": 1},
        ),
    ]

    resolved = build_final_resolved_guidance(
        proposals=proposals,
        skip_pages_explicit=[],
        review_mode="interactive",
        review_status="accepted",
        skip_ranges_input="",
    )

    assert resolved.skip_regions == [{"page": 5, "bbox": [60.0, 220.0, 530.0, 620.0], "proposal_id": "ap-skip"}]
    assert resolved.table_regions == []
```

- [ ] **Step 2: Run the review-handler tests to confirm they fail**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_review_handlers.py -q
```

Expected: FAIL because the review-edit/revision helpers do not exist yet.

- [ ] **Step 3: Implement the review/revision helpers**

Add focused helpers in `handlers.py`:

```python
def build_annotation_review_edits(
    *,
    review_mode: str,
    skip_ranges_input: str,
    skip_pages_explicit: list[int],
) -> AnnotationReviewEdits:
    ...


def apply_review_edits_to_proposals(
    proposals: list[AnnotationProposal],
    edits: AnnotationReviewEdits,
) -> list[AnnotationProposal]:
    ...


def build_final_resolved_guidance(
    *,
    proposals: list[AnnotationProposal],
    skip_pages_explicit: list[int],
    review_mode: str,
    review_status: str,
    skip_ranges_input: str,
) -> PrepGuidanceResolved:
    ...
```

Implement:
- interactive seed state → `pending`
- auto-accept seed state → `auto_accepted`
- reject removes proposal
- edit overrides `page`, `bbox`, and `label` but preserves original `proposal_id`
- explicit skip pages merge into resolved skip pages
- region/full-page `skip` proposals are applied before table/callout inclusion
- overlapping table/callout regions are removed when they intersect a skip region on the same page
- `annotation-review.edits.json` is populated from annotated PDF annotations, not hand-edited directly

Add annotated PDF renderer:

```python
def render_annotated_prep_pdf(
    *,
    pdf_path: Path,
    proposals: list[AnnotationProposal],
    output_pdf_path: Path,
) -> None:
    ...
```

Minimal rendering behavior:
- draw rectangles for proposals
- stamp `proposal_id` + `label`
- do not fail prep if rendering cannot be completed; handler layer decides tolerance

- [ ] **Step 4: Run the review-handler tests to confirm they pass**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_review_handlers.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/handlers.py tests/unit/pdf_convert/prep/test_review_handlers.py
git commit -m "feat: add E7-06 review revision helpers"
```

### Task 4: Add revision command and conversion consumption

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/orchestrator.py`
- Modify: `src/gm_kit/pdf_convert/prep/handlers.py`
- Modify: `src/gm_kit/pdf_convert/cli_helpers.py`
- Modify: `src/gm_kit/pdf_convert/orchestrator.py`
- Modify: `tests/unit/pdf_convert/prep/test_orchestrator.py`
- Modify: `tests/unit/pdf_convert/prep/test_contracts.py`
- Modify: `tests/unit/pdf_convert/prep/test_registry_runtime.py`
- Modify: `tests/unit/pdf_convert/test_orchestrator.py`

- [ ] **Step 1: Write the failing workflow tests**

```python
from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.prep.contracts import AnnotationReviewEdits


def test_run_new_prep__should_emit_review_artifacts_and_exit__when_non_interactive_mode_is_used(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_sample_pdf(
        pdf_path,
        page_count=12,
        toc=[
            [1, "Contents", 1],
            [1, "Chapter 1: Barovia", 2],
            [1, "Appendix A: Resources", 11],
        ],
    )

    exit_code = PrepOrchestrator().run_new_prep(
        pdf_path=pdf_path,
        output_dir=tmp_path / "workspace",
        auto_proceed=True,
    )

    prep_root = tmp_path / "workspace" / "prep"
    review_payload = json.loads((prep_root / "annotation-review.edits.json").read_text(encoding="utf-8"))
    resolved_payload = json.loads((prep_root / "prep-guidance.resolved.json").read_text(encoding="utf-8"))

    assert exit_code == ExitCode.SUCCESS
    assert review_payload["review_mode"] == "auto_accept"
    assert review_payload["review_status"] == "auto_accepted"
    assert "review_summary" in resolved_payload
    assert not (prep_root / "prep-guidance.reviewed.json").exists()


def test_revise_prep_guidance__should_write_reviewed_guidance__when_review_artifact_is_edited(
    tmp_path: Path,
) -> None:
    ...


def test_convert__should_use_reviewed_guidance__when_reviewed_artifact_exists(
    tmp_path: Path,
) -> None:
    ...
```

- [ ] **Step 2: Run the orchestrator tests to confirm they fail**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_contracts.py tests/unit/pdf_convert/prep/test_orchestrator.py tests/unit/pdf_convert/prep/test_registry_runtime.py tests/unit/pdf_convert/test_orchestrator.py -q
```

Expected: FAIL because the revision command and reviewed-guidance consumer are not wired yet.

- [ ] **Step 3: Wire the new prep phases, revision command, and reviewed-guidance consumer**

Update `_build_default_registry()` with required steps:

```python
PrepStepDefinition(
    step_key="prep.review-annotations.seed-review-artifacts",
    phase_key="prep.review-annotations",
    order=100,
    handler_ref="gm_kit.pdf_convert.prep.handlers:handle_seed_annotation_review",
    handler_policy=HandlerPolicy.REQUIRED,
    display_name="Seed Annotation Review",
),
PrepStepDefinition(
    step_key="prep.review-annotations.render-annotated-pdf",
    phase_key="prep.review-annotations",
    order=200,
    handler_ref="gm_kit.pdf_convert.prep.handlers:handle_render_annotated_prep_pdf",
    handler_policy=HandlerPolicy.REQUIRED,
    display_name="Render Annotated Prep PDF",
),
```

Add runtime handlers in `handlers.py`:
- `handle_seed_annotation_review`
- `handle_render_annotated_prep_pdf`
- `handle_revise_prep_guidance`

Runtime behavior:
- `auto_proceed=True` → write `annotation-review.edits.json`, write `prep-guidance.resolved.json`, and exit
- interactive prep → seed the review artifact, render the PDF, and exit with review instructions
- `revise_prep_guidance()` → extract review edits from the annotated PDF, parse skip input, and write `prep-guidance.reviewed.json`
- conversion prefers `prep-guidance.reviewed.json` when present; otherwise it uses `prep-guidance.resolved.json`

Also update:
- `_build_artifacts()` to include `annotation-review.edits.json` and `annotated-prep.pdf` when present
- `__all__` exports if new public helpers/contracts are surfaced

- [ ] **Step 4: Run the orchestrator and contract tests to confirm they pass**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_contracts.py tests/unit/pdf_convert/prep/test_orchestrator.py tests/unit/pdf_convert/prep/test_registry_runtime.py tests/unit/pdf_convert/test_orchestrator.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/orchestrator.py src/gm_kit/pdf_convert/prep/handlers.py src/gm_kit/pdf_convert/prep/__init__.py src/gm_kit/pdf_convert/orchestrator.py src/gm_kit/pdf_convert/cli_helpers.py tests/unit/pdf_convert/prep/test_contracts.py tests/unit/pdf_convert/prep/test_orchestrator.py tests/unit/pdf_convert/prep/test_registry_runtime.py tests/unit/pdf_convert/test_orchestrator.py
git commit -m "feat: wire E7-06 review revision workflow"
```

### Task 5: Run full verification and close the feature handoff

**Files:**
- Modify: `specs/e7-06-annotation-review-ux-skip-intent-capture/feature_journal.md`

- [ ] **Step 1: Run the focused prep verification**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep -q
uv run --python "$(cat .python-version)" --extra dev --editable -- ruff check src/gm_kit/pdf_convert/prep tests/unit/pdf_convert/prep
uv run --python "$(cat .python-version)" --extra dev --editable -- mypy src/gm_kit/pdf_convert/prep tests/unit/pdf_convert/prep
```

Expected:
- pytest PASS
- ruff clean
- mypy clean

- [ ] **Step 2: Run the repo-wide gate**

Run:
```bash
just all_ci_actions
```

Expected: PASS.

- [ ] **Step 3: Update the feature journal**

Append a session entry describing:
- review artifact and skip parser implementation
- revision command and reviewed-guidance consumer design
- interactive versus non-interactive behavior
- verification outcome
- next steps for E7-07

- [ ] **Step 4: Commit**

```bash
git add specs/e7-06-annotation-review-ux-skip-intent-capture/feature_journal.md
git commit -m "docs: record E7-06 workflow revision"
```
