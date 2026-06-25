# E7-05 Guidance + Annotation Proposal System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add prep guidance artifacts, shared annotation proposal contracts, deterministic resolved guidance output, and optional annotated-PDF support on top of the existing prep pipeline.

**Architecture:** Extend the existing prep artifact contract and orchestrator rather than inventing a parallel subsystem. Keep the implementation split into focused units: data contracts, artifact-path definitions, proposal generation helpers, and prep runtime wiring. `prep-guidance.resolved.json` is the only authoritative downstream artifact; raw proposals remain separate evidence.

**Tech Stack:** Python 3.13.7, stdlib `dataclasses`/`json`/`pathlib`/`hashlib`, existing prep orchestrator and handler patterns, PyMuPDF (`fitz`) for optional annotated PDF rendering, pytest, ruff, mypy.

---

### Task 1: Add guidance and proposal contract models

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/contracts.py`
- Create: `tests/unit/pdf_convert/prep/test_guidance_contracts.py`

- [ ] **Step 1: Write the failing contract tests**

```python
from __future__ import annotations

from pathlib import Path

from gm_kit.pdf_convert.prep.contracts import (
    AnnotationProposal,
    PrepGuidanceInput,
    PrepGuidanceResolved,
)


def test_annotation_proposal__should_roundtrip_shared_base_schema__when_valid_payload_is_used() -> None:
    proposal = AnnotationProposal(
        proposal_id="p-001",
        label="table",
        page=18,
        bbox=[72.0, 240.0, 520.0, 610.0],
        confidence=0.88,
        metadata={"source": "code", "rows_estimate": 12},
    )

    payload = proposal.to_dict()
    restored = AnnotationProposal.from_dict(payload)

    assert restored == proposal


def test_prep_guidance_resolved__should_roundtrip_skip_page_and_region_data__when_valid_payload_is_used() -> None:
    resolved = PrepGuidanceResolved(
        skip_pages=[12],
        skip_regions=[{"page": 18, "bbox": [10.0, 10.0, 20.0, 20.0]}],
        table_regions=[{"page": 20, "bbox": [30.0, 30.0, 40.0, 40.0]}],
        callout_regions=[],
    )

    payload = resolved.to_dict()
    restored = PrepGuidanceResolved.from_dict(payload)

    assert restored == resolved


def test_prep_guidance_input__should_preserve_user_preferences__when_valid_payload_is_used() -> None:
    guidance = PrepGuidanceInput(
        prefer_detect_tables=True,
        prefer_detect_callouts=False,
        prefer_skip_full_page_artifacts=True,
    )

    payload = guidance.to_dict()
    restored = PrepGuidanceInput.from_dict(payload)

    assert restored == guidance
```

- [ ] **Step 2: Run the new tests to confirm they fail**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_guidance_contracts.py -q
```

Expected: FAIL because `AnnotationProposal`, `PrepGuidanceInput`, and `PrepGuidanceResolved` do not exist yet.

- [ ] **Step 3: Implement the contract models in `contracts.py`**

Add focused dataclasses plus validation helpers:

```python
@dataclass(frozen=True)
class AnnotationProposal:
    proposal_id: str
    label: str
    page: int
    bbox: list[float]
    confidence: float
    metadata: dict[str, object]


@dataclass(frozen=True)
class PrepGuidanceInput:
    prefer_detect_tables: bool = True
    prefer_detect_callouts: bool = True
    prefer_skip_full_page_artifacts: bool = True


@dataclass(frozen=True)
class PrepGuidanceResolved:
    skip_pages: list[int]
    skip_regions: list[dict[str, object]]
    table_regions: list[dict[str, object]]
    callout_regions: list[dict[str, object]]
```

Validation rules to implement:
- `label` must be one of `table`, `callout`, `skip`
- `page` must be `>= 1`
- `bbox` must contain exactly four numeric values
- `confidence` must be numeric and bounded to `0.0 <= confidence <= 1.0`
- resolved region entries must contain `page` and `bbox`

- [ ] **Step 4: Run the contract tests to confirm they pass**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_guidance_contracts.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/contracts.py tests/unit/pdf_convert/prep/test_guidance_contracts.py
git commit -m "feat: add E7-05 guidance and proposal contracts"
```

### Task 2: Extend prep artifact paths for E7-05 outputs

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- Modify: `tests/unit/pdf_convert/prep/test_analysis_artifacts.py`

- [ ] **Step 1: Write the failing artifact-path test**

```python
from pathlib import Path

from gm_kit.pdf_convert.prep.analysis_artifacts import build_analysis_artifact_paths


def test_build_analysis_artifact_paths__should_include_guidance_and_annotation_outputs__when_workspace_is_provided(
    tmp_path: Path,
) -> None:
    paths = build_analysis_artifact_paths(tmp_path / "workspace", pdf_stem="sample")

    assert paths.guidance_input == tmp_path / "workspace" / "prep" / "prep-guidance.input.json"
    assert paths.annotation_proposals == tmp_path / "workspace" / "prep" / "annotation-proposals.json"
    assert paths.guidance_resolved == tmp_path / "workspace" / "prep" / "prep-guidance.resolved.json"
    assert paths.annotated_pdf == tmp_path / "workspace" / "prep" / "annotated-prep.pdf"
```

- [ ] **Step 2: Run the path test to confirm it fails**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_analysis_artifacts.py -q
```

Expected: FAIL because the E7-05 artifact paths do not exist yet.

- [ ] **Step 3: Extend `PrepAnalysisArtifactPaths`**

Add these fields and paths:

```python
guidance_input=prep_root / "prep-guidance.input.json",
annotation_proposals=prep_root / "annotation-proposals.json",
guidance_resolved=prep_root / "prep-guidance.resolved.json",
annotated_pdf=prep_root / "annotated-prep.pdf",
```

- [ ] **Step 4: Re-run the path test**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_analysis_artifacts.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/analysis_artifacts.py tests/unit/pdf_convert/prep/test_analysis_artifacts.py
git commit -m "feat: add E7-05 prep artifact paths"
```

### Task 3: Add proposal-generation and normalization helpers

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/handlers.py`
- Create: `tests/unit/pdf_convert/prep/test_guidance_handlers.py`

- [ ] **Step 1: Write the failing generation tests**

```python
from __future__ import annotations

import json
from pathlib import Path

from gm_kit.pdf_convert.prep.handlers import (
    build_annotation_proposals,
    build_resolved_guidance,
)


def test_build_annotation_proposals__should_generate_deterministic_ids_and_skip_modes__when_inputs_are_valid() -> None:
    proposals = build_annotation_proposals(
        page_count=12,
        images_total_count=2,
        chunk_plan={"chunks": [{"start_page": 1, "end_page": 10}]},
    )

    assert all(proposal.proposal_id for proposal in proposals)
    assert {proposal.label for proposal in proposals}.issubset({"table", "callout", "skip"})
    assert any(proposal.metadata.get("scope") == "full-page" for proposal in proposals if proposal.label == "skip")


def test_build_resolved_guidance__should_normalize_skip_table_and_callout_targets__when_given_proposals() -> None:
    proposals = build_annotation_proposals(
        page_count=12,
        images_total_count=2,
        chunk_plan={"chunks": [{"start_page": 1, "end_page": 10}]},
    )

    resolved = build_resolved_guidance(proposals)
    payload = resolved.to_dict()

    assert sorted(payload.keys()) == ["callout_regions", "skip_pages", "skip_regions", "table_regions"]
```

- [ ] **Step 2: Run the generation tests to confirm they fail**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_guidance_handlers.py -q
```

Expected: FAIL because the helper functions do not exist yet.

- [ ] **Step 3: Implement deterministic proposal and normalization helpers**

Add focused helpers in `handlers.py`:

```python
def build_annotation_proposals(
    *,
    page_count: int,
    images_total_count: int,
    chunk_plan: dict[str, object] | None,
) -> list[AnnotationProposal]:
    ...


def build_resolved_guidance(
    proposals: list[AnnotationProposal],
) -> PrepGuidanceResolved:
    ...
```

Recommended minimal deterministic strategy for E7-05:
- emit a full-page `skip` proposal for pages beyond the first chunk only when chunk plan pages reveal trailing appendix-like single-page spans
- emit `table` proposals from chunk-plan regions using a placeholder deterministic bbox such as `[72.0, 240.0, 520.0, 610.0]`
- emit `callout` proposals from image-heavy pages using a deterministic bbox such as `[72.0, 80.0, 300.0, 220.0]`
- generate `proposal_id` deterministically from label, page, bbox, and source via `hashlib.sha1(...).hexdigest()[:12]`

Normalization rules to implement:
- full-page `skip` proposals populate `skip_pages`
- region `skip` proposals populate `skip_regions`
- `table` and `callout` proposals populate `table_regions` and `callout_regions`
- output ordering must be stable by `(page, label, proposal_id)`

- [ ] **Step 4: Run the generation tests**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_guidance_handlers.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/handlers.py tests/unit/pdf_convert/prep/test_guidance_handlers.py
git commit -m "feat: add E7-05 proposal generation helpers"
```

### Task 4: Wire E7-05 artifacts into the prep runtime

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/orchestrator.py`
- Modify: `src/gm_kit/pdf_convert/prep/__init__.py`
- Modify: `tests/unit/pdf_convert/prep/test_orchestrator.py`
- Modify: `tests/unit/pdf_convert/prep/test_contracts.py`

- [ ] **Step 1: Write the failing orchestrator test**

```python
def test_run_new_prep__should_emit_guidance_and_annotation_artifacts__when_prep_succeeds(
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
    )

    prep_root = tmp_path / "workspace" / "prep"
    assert exit_code == ExitCode.SUCCESS
    assert (prep_root / "prep-guidance.input.json").exists()
    assert (prep_root / "annotation-proposals.json").exists()
    assert (prep_root / "prep-guidance.resolved.json").exists()
```

- [ ] **Step 2: Run the orchestrator test to confirm it fails**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_orchestrator.py -q
```

Expected: FAIL because E7-05 registry steps and artifacts are not wired yet.

- [ ] **Step 3: Wire E7-05 into the orchestrator and artifact inventory**

Add two required steps to `_build_default_registry()`:

```python
PrepStepDefinition(
    step_key="prep.prepare-guidance.write-guidance-input",
    phase_key="prep.prepare-guidance",
    order=100,
    handler_ref="gm_kit.pdf_convert.prep.handlers:handle_write_guidance_input",
    handler_policy=HandlerPolicy.REQUIRED,
    display_name="Write Guidance Input",
),
PrepStepDefinition(
    step_key="prep.propose-annotations.generate-annotation-proposals",
    phase_key="prep.propose-annotations",
    order=100,
    handler_ref="gm_kit.pdf_convert.prep.handlers:handle_generate_annotation_proposals",
    handler_policy=HandlerPolicy.REQUIRED,
    display_name="Generate Annotation Proposals",
),
```

Also update `_build_artifacts()` to include E7-05 files when they exist:
- `prep-guidance.input.json`
- `annotation-proposals.json`
- `prep-guidance.resolved.json`
- `annotated-prep.pdf`

- [ ] **Step 4: Re-run orchestrator and contract tests**

Run:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_contracts.py tests/unit/pdf_convert/prep/test_orchestrator.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/orchestrator.py src/gm_kit/pdf_convert/prep/__init__.py tests/unit/pdf_convert/prep/test_contracts.py tests/unit/pdf_convert/prep/test_orchestrator.py
git commit -m "feat: wire E7-05 guidance artifacts into prep runtime"
```

### Task 5: Run quality gates and close the feature handoff

**Files:**
- Modify: `specs/e7-05-guidance-annotation-proposal-system/feature_journal.md`

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

Append a session entry that records:
- the added E7-05 contract artifacts
- the deterministic proposal-generation strategy
- the fact that `prep-guidance.resolved.json` is authoritative
- the verification commands and outcomes
- the next handoff into E7-06

- [ ] **Step 4: Commit**

```bash
git add specs/e7-05-guidance-annotation-proposal-system/feature_journal.md
git commit -m "docs: record E7-05 completion handoff"
```

---

## Self-Review

- Spec coverage is complete for the approved E7-05 design: input guidance artifact, raw proposal artifact, resolved authoritative artifact, optional annotated PDF, shared proposal schema, provenance-aware generation, normalization, and failure/test expectations all map to concrete tasks above.
- Placeholder scan is clean: each task lists exact files, code targets, verification commands, and expected outcomes.
- Type consistency is aligned across the plan: `AnnotationProposal`, `PrepGuidanceInput`, `PrepGuidanceResolved`, `build_annotation_proposals()`, and `build_resolved_guidance()` are used consistently across contract, handler, and orchestrator tasks.
