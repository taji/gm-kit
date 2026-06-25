# E7-03 Rehost Existing Analysis Logic into Prep Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `gmkit analyze-and-prep-pdf` emit real analysis artifacts by reusing existing metadata/preflight, image extraction, `no-images PDF`, and TOC acquisition behavior through the prep-first pipeline.

**Architecture:** Extend the E7-02 prep orchestrator with real registry-backed steps and prep handlers, while selectively extracting narrow shared helpers from numeric phases only where current behavior is too entangled to reuse directly. Keep prep responsible for artifact placement and manifest/state ownership, and keep numeric conversion behavior stable by routing both callers through the same extracted behavior where needed.

**Tech Stack:** Python 3.13.7, Typer, pathlib, json/dataclasses, PyMuPDF (`fitz`), existing `metadata.py`, `preflight.py`, phase implementations, pytest, mypy, ruff.

---

## Planned File Structure

**Create**
- `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- `src/gm_kit/pdf_convert/prep/handlers.py`
- `tests/unit/pdf_convert/prep/test_analysis_artifacts.py`
- `tests/unit/pdf_convert/prep/test_handlers.py`

**Modify**
- `src/gm_kit/pdf_convert/prep/orchestrator.py`
- `src/gm_kit/pdf_convert/prep/__init__.py`
- `src/gm_kit/pdf_convert/prep/contracts.py`
- `src/gm_kit/pdf_convert/phases/phase1.py`
- `src/gm_kit/pdf_convert/phases/phase2.py`
- `src/gm_kit/pdf_convert/phases/phase3.py`
- `src/gm_kit/pdf_convert/errors.py`
- `tests/unit/pdf_convert/prep/test_orchestrator.py`
- `tests/unit/pdf_convert/test_phase1.py`
- `tests/unit/pdf_convert/test_phase2.py`
- `tests/unit/pdf_convert/test_phase3.py`
- `specs/e7-03-rehost-existing-analysis-logic/feature_journal.md`

**Do Not Modify In E7-03**
- `src/gm_kit/pdf_convert/orchestrator.py` (except if unavoidable for harmless import movement, which should be avoided)
- `src/gm_kit/pdf_convert/state.py`
- any chapter/chunk/guidance/annotation logic
- `gmkit pdf-convert` gating behavior

## Artifact Conventions

Prep artifacts should remain prep-owned and live under `<workspace>/prep/`.

Planned artifact paths for E7-03:
- `prep/metadata.json`
- `prep/preflight-report.json`
- `prep/images/image-manifest.json`
- `prep/images/*.png`
- `prep/preprocessed/<pdf-stem>-no-images.pdf`
- `prep/toc-extracted.txt`
- `prep/prep-manifest.json`
- `prep/prep-state.json`
- `prep/prep-complete.json`
- `prep/logs/prep.log`

These names intentionally preserve the existing conversion-side filenames where doing so reduces migration risk.

---

### Task 1: Add Prep Artifact Path Helpers and Manifest Inventory Expansion

**Files:**
- Create: `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- Modify: `src/gm_kit/pdf_convert/prep/contracts.py`
- Test: `tests/unit/pdf_convert/prep/test_analysis_artifacts.py`
- Test: `tests/unit/pdf_convert/prep/test_contracts.py`

- [ ] **Step 1: Write the failing artifact path tests**

```python
from pathlib import Path

from gm_kit.pdf_convert.prep.analysis_artifacts import build_analysis_artifact_paths


def test_build_analysis_artifact_paths__should_return_expected_paths__when_workspace_is_provided(
    tmp_path: Path,
) -> None:
    paths = build_analysis_artifact_paths(tmp_path / "workspace")

    assert paths.metadata == tmp_path / "workspace" / "prep" / "metadata.json"
    assert paths.preflight_report == tmp_path / "workspace" / "prep" / "preflight-report.json"
    assert paths.images_dir == tmp_path / "workspace" / "prep" / "images"
    assert paths.image_manifest == tmp_path / "workspace" / "prep" / "images" / "image-manifest.json"
    assert paths.preprocessed_dir == tmp_path / "workspace" / "prep" / "preprocessed"
    assert paths.toc == tmp_path / "workspace" / "prep" / "toc-extracted.txt"
```

- [ ] **Step 2: Run the focused path test to verify it fails**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_analysis_artifacts.py -v`
Expected: FAIL because `analysis_artifacts.py` does not exist yet.

- [ ] **Step 3: Write the failing manifest inventory test for real prep artifacts**

```python
from pathlib import Path

from gm_kit.pdf_convert.prep.analysis_artifacts import build_analysis_artifact_paths
from gm_kit.pdf_convert.prep.orchestrator import _build_artifacts


def test_build_artifacts__should_include_analysis_outputs__when_analysis_paths_are_available(
    tmp_path: Path,
) -> None:
    prep_paths = build_prep_paths(tmp_path / "workspace")
    analysis_paths = build_analysis_artifact_paths(tmp_path / "workspace")

    artifacts = _build_artifacts(prep_paths, analysis_paths)

    assert [artifact.name for artifact in artifacts] == [
        "prep-manifest.json",
        "prep-state.json",
        "prep-complete.json",
        "logs/prep.log",
        "metadata.json",
        "preflight-report.json",
        "images/image-manifest.json",
        f"preprocessed/{tmp_path.name}-no-images.pdf",
        "toc-extracted.txt",
    ]
```

- [ ] **Step 4: Implement the prep artifact path module**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gm_kit.pdf_convert.prep.contracts import build_prep_paths


@dataclass(frozen=True)
class PrepAnalysisArtifactPaths:
    metadata: Path
    preflight_report: Path
    images_dir: Path
    image_manifest: Path
    preprocessed_dir: Path
    no_images_pdf: Path
    toc: Path


def build_analysis_artifact_paths(workspace_dir: Path, pdf_stem: str | None = None) -> PrepAnalysisArtifactPaths:
    prep_paths = build_prep_paths(workspace_dir)
    stem = pdf_stem or "source"
    return PrepAnalysisArtifactPaths(
        metadata=prep_paths.root / "metadata.json",
        preflight_report=prep_paths.root / "preflight-report.json",
        images_dir=prep_paths.root / "images",
        image_manifest=prep_paths.root / "images" / "image-manifest.json",
        preprocessed_dir=prep_paths.root / "preprocessed",
        no_images_pdf=prep_paths.root / "preprocessed" / f"{stem}-no-images.pdf",
        toc=prep_paths.root / "toc-extracted.txt",
    )
```

- [ ] **Step 5: Expand artifact inventory construction to accept analysis artifact paths**

```python
def _build_artifacts(
    prep_paths: PrepPaths,
    analysis_paths: PrepAnalysisArtifactPaths,
) -> list[PrepArtifactEntry]:
    return [
        PrepArtifactEntry(name=prep_paths.manifest.name, status="ready"),
        PrepArtifactEntry(name=prep_paths.state.name, status="ready"),
        PrepArtifactEntry(name=prep_paths.complete.name, status="ready"),
        PrepArtifactEntry(name=prep_paths.log.relative_to(prep_paths.root).as_posix(), status="ready"),
        PrepArtifactEntry(name=analysis_paths.metadata.relative_to(prep_paths.root).as_posix(), status="ready"),
        PrepArtifactEntry(name=analysis_paths.preflight_report.relative_to(prep_paths.root).as_posix(), status="ready"),
        PrepArtifactEntry(name=analysis_paths.image_manifest.relative_to(prep_paths.root).as_posix(), status="ready"),
        PrepArtifactEntry(name=analysis_paths.no_images_pdf.relative_to(prep_paths.root).as_posix(), status="ready"),
        PrepArtifactEntry(name=analysis_paths.toc.relative_to(prep_paths.root).as_posix(), status="ready"),
    ]
```

- [ ] **Step 6: Run the focused artifact tests**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_analysis_artifacts.py tests/unit/pdf_convert/prep/test_contracts.py -v`
Expected: PASS

- [ ] **Step 7: Commit the prep artifact-path foundation**

```bash
git add src/gm_kit/pdf_convert/prep/analysis_artifacts.py \
  src/gm_kit/pdf_convert/prep/contracts.py \
  tests/unit/pdf_convert/prep/test_analysis_artifacts.py \
  tests/unit/pdf_convert/prep/test_contracts.py
git commit -m "feat(prep): add analysis artifact path helpers"
```

---

### Task 2: Extract Shared Image and No-Images PDF Helpers from Phases 1 and 2

**Files:**
- Create: `src/gm_kit/pdf_convert/prep/handlers.py`
- Modify: `src/gm_kit/pdf_convert/phases/phase1.py`
- Modify: `src/gm_kit/pdf_convert/phases/phase2.py`
- Test: `tests/unit/pdf_convert/prep/test_handlers.py`
- Test: `tests/unit/pdf_convert/test_phase1.py`
- Test: `tests/unit/pdf_convert/test_phase2.py`

- [ ] **Step 1: Write the failing shared image extraction test**

```python
from pathlib import Path
from unittest.mock import MagicMock, patch

from gm_kit.pdf_convert.prep.handlers import extract_images_to_artifacts


def test_extract_images_to_artifacts__should_write_manifest_and_images__when_pdf_has_images(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    images_dir = tmp_path / "images"

    with patch("fitz.open") as mock_open:
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_page = MagicMock()
        mock_page.get_images.return_value = [(1,)]
        mock_page.get_image_rects.return_value = [MagicMock(x0=1, y0=2, width=3, height=4)]
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_doc.extract_image.return_value = {"image": b"png-bytes"}
        mock_open.return_value = mock_doc

        manifest_path, total_images = extract_images_to_artifacts(pdf_path=pdf_path, images_dir=images_dir)

    assert total_images == 1
    assert manifest_path == images_dir / "image-manifest.json"
    assert (images_dir / "page001_img01.png").read_bytes() == b"png-bytes"
```

- [ ] **Step 2: Write the failing shared no-images PDF test**

```python
from pathlib import Path
from unittest.mock import MagicMock, patch

from gm_kit.pdf_convert.prep.handlers import create_no_images_pdf


def test_create_no_images_pdf__should_save_expected_output__when_pdf_is_processed(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    output_pdf = tmp_path / "sample-no-images.pdf"

    with patch("fitz.open") as mock_open:
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_page = MagicMock()
        mock_page.get_images.return_value = []
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_open.return_value = mock_doc

        images_removed = create_no_images_pdf(pdf_path=pdf_path, output_pdf_path=output_pdf)

    assert images_removed == 0
    mock_doc.save.assert_called_once_with(output_pdf)
```

- [ ] **Step 3: Run the focused handler tests to verify they fail**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_handlers.py -v`
Expected: FAIL because shared helper functions do not exist yet.

- [ ] **Step 4: Implement shared image and no-images helpers in `prep/handlers.py`**

```python
from __future__ import annotations

import json
from pathlib import Path

import fitz  # type: ignore[import-untyped]


def extract_images_to_artifacts(pdf_path: Path, images_dir: Path) -> tuple[Path, int]:
    images_dir.mkdir(parents=True, exist_ok=True)
    image_manifest: list[dict[str, object]] = []
    total_images = 0
    doc = fitz.open(pdf_path)
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            for img_index, img in enumerate(page.get_images()):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                img_filename = f"page{page_num + 1:03d}_img{img_index + 1:02d}.png"
                img_path = images_dir / img_filename
                img_path.write_bytes(image_bytes)
                rects = page.get_image_rects(xref)
                rect = rects[0] if rects else None
                image_manifest.append(
                    {
                        "page": page_num + 1,
                        "filename": img_filename,
                        "position": {
                            "x": getattr(rect, "x0", 0),
                            "y": getattr(rect, "y0", 0),
                            "width": getattr(rect, "width", 0),
                            "height": getattr(rect, "height", 0),
                        },
                        "alt_text": f"[Figure on page {page_num + 1}]",
                    }
                )
                total_images += 1
    finally:
        doc.close()

    manifest_path = images_dir / "image-manifest.json"
    manifest_path.write_text(
        json.dumps({"images": image_manifest, "total_count": len(image_manifest)}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path, total_images


def create_no_images_pdf(pdf_path: Path, output_pdf_path: Path) -> int:
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    images_removed = 0
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            for img in page.get_images():
                xref = img[0]
                for rect in page.get_image_rects(xref):
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                    images_removed += 1
        doc.save(output_pdf_path)
    finally:
        doc.close()
    return images_removed
```

- [ ] **Step 5: Refactor `Phase1` and `Phase2` to call the shared helpers without changing behavior**

```python
# in phase1.py
from gm_kit.pdf_convert.prep.handlers import extract_images_to_artifacts

manifest_path, total_images = extract_images_to_artifacts(pdf_path=pdf_path, images_dir=images_dir)

# in phase2.py
from gm_kit.pdf_convert.prep.handlers import create_no_images_pdf

images_removed = create_no_images_pdf(pdf_path=pdf_path, output_pdf_path=output_pdf_path)
```

- [ ] **Step 6: Update the phase tests to prove the old callers still behave the same**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/test_phase1.py tests/unit/pdf_convert/test_phase2.py tests/unit/pdf_convert/prep/test_handlers.py -v`
Expected: PASS

- [ ] **Step 7: Commit the extracted image/no-images behavior**

```bash
git add src/gm_kit/pdf_convert/prep/handlers.py \
  src/gm_kit/pdf_convert/phases/phase1.py \
  src/gm_kit/pdf_convert/phases/phase2.py \
  tests/unit/pdf_convert/prep/test_handlers.py \
  tests/unit/pdf_convert/test_phase1.py \
  tests/unit/pdf_convert/test_phase2.py
git commit -m "refactor(prep): share image and no-images pdf helpers"
```

---

### Task 3: Extract Shared TOC Acquisition and Prep Metadata/Preflight Writers

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/handlers.py`
- Modify: `src/gm_kit/pdf_convert/phases/phase3.py`
- Test: `tests/unit/pdf_convert/prep/test_handlers.py`
- Test: `tests/unit/pdf_convert/test_phase3.py`

- [ ] **Step 1: Write the failing TOC extraction helper test**

```python
from pathlib import Path
from unittest.mock import MagicMock, patch

from gm_kit.pdf_convert.prep.handlers import extract_toc_to_artifact


def test_extract_toc_to_artifact__should_write_embedded_toc_file__when_toc_exists(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    output_path = tmp_path / "toc-extracted.txt"

    with patch("fitz.open") as mock_open:
        mock_doc = MagicMock()
        mock_doc.get_toc.return_value = [[1, "Introduction", 1], [2, "Maps", 3]]
        mock_open.return_value = mock_doc

        toc_entries = extract_toc_to_artifact(pdf_path=pdf_path, output_path=output_path)

    assert len(toc_entries) == 2
    assert "Introduction (page 1)" in output_path.read_text(encoding="utf-8")
```

- [ ] **Step 2: Write the failing metadata/preflight writer test**

```python
from pathlib import Path
from unittest.mock import patch

from gm_kit.pdf_convert.metadata import PDFMetadata
from gm_kit.pdf_convert.preflight import Complexity, PreflightReport, TOCApproach
from gm_kit.pdf_convert.prep.handlers import write_metadata_and_preflight_artifacts


def test_write_metadata_and_preflight_artifacts__should_persist_json_outputs__when_analysis_succeeds(
    tmp_path: Path,
) -> None:
    metadata = PDFMetadata(page_count=1, file_size_bytes=10)
    report = PreflightReport(
        pdf_name="sample.pdf",
        file_size_display="10 B",
        page_count=1,
        image_count=0,
        text_extractable=True,
        toc_approach=TOCApproach.NONE,
        font_complexity=Complexity.LOW,
        overall_complexity=Complexity.LOW,
    )

    write_metadata_and_preflight_artifacts(
        metadata=metadata,
        report=report,
        metadata_path=tmp_path / "metadata.json",
        preflight_report_path=tmp_path / "preflight-report.json",
    )

    assert (tmp_path / "metadata.json").exists()
    assert (tmp_path / "preflight-report.json").exists()
```

- [ ] **Step 3: Implement shared TOC and metadata/preflight helpers**

```python
def extract_toc_to_artifact(pdf_path: Path, output_path: Path) -> list[dict[str, object]]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    toc_entries: list[dict[str, object]] = []
    doc = fitz.open(pdf_path)
    try:
        toc = doc.get_toc()
        for level, title, page in toc:
            toc_entries.append({"level": level, "title": title, "page": page})
    finally:
        doc.close()

    lines = [
        f"# TOC Source: {'embedded' if toc_entries else 'none'}",
        "# Extraction method: PDF metadata (prep/shared helper)",
        f"# Total entries: {len(toc_entries)}",
        "",
    ]
    for entry in toc_entries:
        lines.append(f"{'  ' * (entry['level'] - 1)}{entry['title']} (page {entry['page']})")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return toc_entries


def write_metadata_and_preflight_artifacts(
    metadata: PDFMetadata,
    report: PreflightReport,
    metadata_path: Path,
    preflight_report_path: Path,
) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata.to_dict(), indent=2) + "\n", encoding="utf-8")
    preflight_payload = {
        "pdf_name": report.pdf_name,
        "file_size_display": report.file_size_display,
        "page_count": report.page_count,
        "image_count": report.image_count,
        "text_extractable": report.text_extractable,
        "toc_approach": report.toc_approach.value,
        "font_complexity": report.font_complexity.value,
        "overall_complexity": report.overall_complexity.value,
        "warnings": report.warnings,
        "user_involvement_phases": report.user_involvement_phases,
        "copyright_notice": report.copyright_notice,
    }
    preflight_report_path.write_text(json.dumps(preflight_payload, indent=2) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Refactor `Phase3._extract_toc()` to reuse the shared TOC helper**

```python
from gm_kit.pdf_convert.prep.handlers import extract_toc_to_artifact


def _extract_toc(self, pdf_path: Path, output_dir: Path, result: PhaseResult) -> list[dict]:
    toc_path = output_dir / "toc-extracted.txt"
    toc_entries = extract_toc_to_artifact(pdf_path=pdf_path, output_path=toc_path)
    ...
```

- [ ] **Step 5: Run the shared TOC and phase regression tests**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_handlers.py tests/unit/pdf_convert/test_phase3.py -v`
Expected: PASS

- [ ] **Step 6: Commit the shared TOC and metadata/preflight helpers**

```bash
git add src/gm_kit/pdf_convert/prep/handlers.py \
  src/gm_kit/pdf_convert/phases/phase3.py \
  tests/unit/pdf_convert/prep/test_handlers.py \
  tests/unit/pdf_convert/test_phase3.py
git commit -m "refactor(prep): share toc and preflight artifact helpers"
```

---

### Task 4: Wire Real Prep Registry Steps and Artifact Emission into the Prep Orchestrator

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/orchestrator.py`
- Modify: `src/gm_kit/pdf_convert/prep/__init__.py`
- Modify: `src/gm_kit/pdf_convert/errors.py`
- Test: `tests/unit/pdf_convert/prep/test_orchestrator.py`

- [ ] **Step 1: Write the failing prep runtime test for real artifact emission**

```python
from pathlib import Path

from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.prep.orchestrator import PrepOrchestrator


def test_run_new_prep__should_emit_real_analysis_artifacts__when_analysis_steps_succeed(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    workspace_path = tmp_path / "workspace"

    exit_code = PrepOrchestrator().run_new_prep(pdf_path=pdf_path, output_dir=workspace_path)

    assert exit_code == ExitCode.SUCCESS
    assert (workspace_path / "prep" / "metadata.json").exists()
    assert (workspace_path / "prep" / "preflight-report.json").exists()
    assert (workspace_path / "prep" / "images" / "image-manifest.json").exists()
    assert (workspace_path / "prep" / "preprocessed" / "sample-no-images.pdf").exists()
    assert (workspace_path / "prep" / "toc-extracted.txt").exists()
```

- [ ] **Step 2: Write the failing prep runtime test for incomplete runs**

```python
from pathlib import Path
from unittest.mock import patch

from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.prep.orchestrator import PrepOrchestrator


def test_run_new_prep__should_not_write_complete_marker__when_required_step_fails(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    workspace_path = tmp_path / "workspace"

    with patch(
        "gm_kit.pdf_convert.prep.handlers.extract_images_to_artifacts",
        side_effect=RuntimeError("boom"),
    ):
        exit_code = PrepOrchestrator().run_new_prep(pdf_path=pdf_path, output_dir=workspace_path)

    assert exit_code == ExitCode.FILE_ERROR
    assert not (workspace_path / "prep" / "prep-complete.json").exists()
```

- [ ] **Step 3: Implement real prep step definitions and handler execution**

```python
PrepStepDefinition(
    step_key="prep.analyze-document.extract-metadata",
    phase_key="prep.analyze-document",
    order=100,
    handler_ref="gm_kit.pdf_convert.prep.handlers:handle_extract_metadata_and_preflight",
    handler_policy=HandlerPolicy.REQUIRED,
    display_name="Extract Metadata And Preflight",
)
PrepStepDefinition(
    step_key="prep.extract-assets.extract-images",
    phase_key="prep.extract-assets",
    order=100,
    handler_ref="gm_kit.pdf_convert.prep.handlers:handle_extract_images",
    handler_policy=HandlerPolicy.REQUIRED,
    display_name="Extract Images",
)
PrepStepDefinition(
    step_key="prep.extract-assets.create-no-images-pdf",
    phase_key="prep.extract-assets",
    order=200,
    handler_ref="gm_kit.pdf_convert.prep.handlers:handle_create_no_images_pdf",
    handler_policy=HandlerPolicy.REQUIRED,
    display_name="Create No-Images PDF",
)
PrepStepDefinition(
    step_key="prep.derive-structure.acquire-canonical-toc",
    phase_key="prep.derive-structure",
    order=100,
    handler_ref="gm_kit.pdf_convert.prep.handlers:handle_extract_canonical_toc",
    handler_policy=HandlerPolicy.REQUIRED,
    display_name="Acquire Canonical TOC",
)
```

- [ ] **Step 4: Implement a small prep execution loop inside `PrepOrchestrator.run_new_prep()`**

```python
for phase in self._registry.get_ordered_phases():
    for step in self._registry.get_ordered_steps(phase.phase_key):
        handler = self._registry.get_handler(step.step_key)
        if handler is None:
            continue
        handler(
            pdf_path=resolved_pdf_path,
            workspace_dir=workspace_dir,
            prep_paths=prep_paths,
            analysis_paths=analysis_paths,
        )
        completed_steps.append(step.step_key)
        save_prep_state(
            prep_paths.state,
            PrepRunState(
                status=PrepStatus.RUNNING,
                current_phase_key=phase.phase_key,
                completed_steps=completed_steps.copy(),
            ),
        )
```

- [ ] **Step 5: Update error handling and finalization rules**

```python
except Exception as error:
    prep_paths.log.write_text(
        f"Prep started\nActive phase: {current_phase_key}\nERROR: {sanitize_for_log(str(error))}\n",
        encoding="utf-8",
    )
    save_prep_state(
        prep_paths.state,
        PrepRunState(
            status=PrepStatus.FAILED,
            current_phase_key=current_phase_key,
            completed_steps=completed_steps,
        ),
    )
    return ExitCode.FILE_ERROR
```

Also update `TEXT_PDF_ERROR` in `src/gm_kit/pdf_convert/errors.py` to `NO_IMAGES_PDF_ERROR` or equivalent user-facing copy that says `no-images PDF`.

- [ ] **Step 6: Run the focused prep orchestrator tests**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_orchestrator.py -v`
Expected: PASS

- [ ] **Step 7: Commit the real prep runtime wiring**

```bash
git add src/gm_kit/pdf_convert/prep/orchestrator.py \
  src/gm_kit/pdf_convert/prep/__init__.py \
  src/gm_kit/pdf_convert/errors.py \
  tests/unit/pdf_convert/prep/test_orchestrator.py
git commit -m "feat(prep): rehost analysis steps into prep orchestrator"
```

---

### Task 5: Full E7-03 Regression Verification and Terminology Cleanup

**Files:**
- Modify: `tests/unit/pdf_convert/prep/test_orchestrator.py`
- Modify: `tests/unit/pdf_convert/test_phase2.py`
- Modify: `specs/e7-03-rehost-existing-analysis-logic/feature_journal.md`

- [ ] **Step 1: Add regression assertions for prep manifest inventory and no-images terminology**

```python
def test_run_new_prep__should_reference_no_images_pdf_in_manifest__when_prep_succeeds(...):
    ...
    assert "preprocessed/sample-no-images.pdf" in [artifact["name"] for artifact in manifest_payload["artifacts"]]


def test_phase2__should_report_no_images_pdf_wording__when_successful(...):
    ...
    assert step_2_2[0].description == "Create no-images PDF"
```

- [ ] **Step 2: Run the targeted E7-03 verification suite**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep tests/unit/pdf_convert/test_phase1.py tests/unit/pdf_convert/test_phase2.py tests/unit/pdf_convert/test_phase3.py -q`
Expected: PASS

- [ ] **Step 3: Run prep-focused lint and type checks**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- ruff check src/gm_kit/pdf_convert/prep src/gm_kit/pdf_convert/phases/phase1.py src/gm_kit/pdf_convert/phases/phase2.py src/gm_kit/pdf_convert/phases/phase3.py tests/unit/pdf_convert/prep tests/unit/pdf_convert/test_phase1.py tests/unit/pdf_convert/test_phase2.py tests/unit/pdf_convert/test_phase3.py`
Expected: PASS

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- mypy src/gm_kit/pdf_convert/prep src/gm_kit/pdf_convert/phases/phase1.py src/gm_kit/pdf_convert/phases/phase2.py src/gm_kit/pdf_convert/phases/phase3.py tests/unit/pdf_convert/prep`
Expected: PASS

- [ ] **Step 4: Append the E7-03 implementation handoff to the feature journal**

```markdown
Session: 2026-06-14 - E7-03 Implementation Complete
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-14

Work Completed:
1. Rehosted metadata/preflight, image extraction, no-images PDF generation, and TOC acquisition into the prep flow.
2. Extracted narrow shared helpers so prep and numeric conversion reuse the same core behavior.
3. Verified prep artifact emission, manifest inventory, and regression-sensitive phase behavior.

Key Decisions:
- Kept prep as artifact owner while reusing existing conversion logic.
- Standardized `no-images PDF` terminology in prep/runtime outputs.

Current State:
- E7-03 implementation is complete and verified.

Next Steps:
1. Begin E7-04 design for chapter segmentation and chunk planning.

Recorded by: codex (gpt-5)
```

- [ ] **Step 5: Commit the final E7-03 verification updates**

```bash
git add tests/unit/pdf_convert/prep/test_orchestrator.py \
  tests/unit/pdf_convert/test_phase2.py \
  specs/e7-03-rehost-existing-analysis-logic/feature_journal.md
git commit -m "test(prep): verify e7-03 artifact and terminology behavior"
```

---

## Self-Review

- Spec coverage: metadata/preflight reuse, image extraction, no-images PDF generation, TOC extraction, prep artifact emission, regression protection, and targeted validation are all mapped to Tasks 1-5.
- Placeholder scan: all tasks include explicit file paths, commands, and concrete code or assertion direction; no TODO/TBD placeholders remain.
- Type consistency: the plan consistently uses `no-images PDF`, `PrepAnalysisArtifactPaths`, `extract_images_to_artifacts()`, `create_no_images_pdf()`, `extract_toc_to_artifact()`, and prep handler naming across all tasks.
