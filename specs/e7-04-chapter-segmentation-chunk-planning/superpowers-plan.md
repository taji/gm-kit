# E7-04 Chapter Segmentation + Chunk Planning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add TOC-driven chapter segmentation and chunk planning so large PDFs emit deterministic chapter and chunk plan artifacts only when chunking is needed.

**Architecture:** E7-04 consumes the TOC artifact produced by E7-03, converts the top-level outline entries into a structured chapter index, and derives a deterministic chunk plan with a fixed 10-page budget. The planner keeps TOC-visible front matter and appendices in scope, ignores nested subsection bookmarks for chunk-boundary purposes, preserves chapter boundaries whenever possible, and splits only oversized sections on page boundaries. It remains prep-side only: no markdown generation and no default merge back into a single document.

**Tech Stack:** Python 3.13.7, stdlib `dataclasses`/`json`/`pathlib`, existing prep artifact patterns, PyMuPDF output already present in the prep flow, pytest, ruff, mypy.

---

### Task 1: Add TOC parsing and section models

**Files:**
- Create: `src/gm_kit/pdf_convert/prep/chunking.py`
- Create: `tests/unit/pdf_convert/prep/test_chunking.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from gm_kit.pdf_convert.prep.chunking import load_toc_sections


def test_load_toc_sections__should_classify_front_matter_body_and_appendix__when_toc_artifact_is_present(
    tmp_path: Path,
) -> None:
    toc_path = tmp_path / "toc-extracted.txt"
    toc_path.write_text(
        "# TOC Source: embedded\n"
        "# Extraction method: PDF metadata (prep/shared helper)\n"
        "# Total entries: 4\n"
        "\n"
        "Contents (page 1)\n"
        "Introduction (page 3)\n"
        "Chapter 1: Into the Mists (page 10)\n"
        "Appendix A: Character Options (page 210)\n",
        encoding="utf-8",
    )

    sections = load_toc_sections(toc_path, page_count=258)

    assert sections[0].title == "Contents"
    assert sections[0].kind == "front_matter"
    assert sections[0].start_page == 1
    assert sections[0].end_page == 2
    assert sections[1].title == "Introduction"
    assert sections[1].kind == "front_matter"
    assert sections[2].title == "Chapter 1: Into the Mists"
    assert sections[2].kind == "body"
    assert sections[3].title == "Appendix A: Character Options"
    assert sections[3].kind == "appendix"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_chunking.py::test_load_toc_sections__should_classify_front_matter_body_and_appendix__when_toc_artifact_is_present -v`
Expected: FAIL because `load_toc_sections` and the section model do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class TocSection:
    section_id: str
    title: str
    level: int
    kind: str
    start_page: int
    end_page: int
    page_count: int
    split_needed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "level": self.level,
            "kind": self.kind,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "page_count": self.page_count,
            "split_needed": self.split_needed,
        }


_TOC_LINE_PATTERN = re.compile(r"^(?P<indent>\s*)(?P<title>.+) \(page (?P<page>\d+)\)$")


def load_toc_sections(toc_path: Path, page_count: int) -> list[TocSection]:
    toc_entries: list[dict[str, object]] = []
    for line in toc_path.read_text(encoding="utf-8").splitlines():
        match = _TOC_LINE_PATTERN.match(line)
        if match is None:
            continue
        indent = match.group("indent")
        level = max(1, len(indent) // 2 + 1)
        toc_entries.append(
            {
                "level": level,
                "title": match.group("title"),
                "page": int(match.group("page")),
            }
        )

    return _build_sections_from_toc(toc_entries, page_count)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_chunking.py::test_load_toc_sections__should_classify_front_matter_body_and_appendix__when_toc_artifact_is_present -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/chunking.py tests/unit/pdf_convert/prep/test_chunking.py
git commit -m "feat: add TOC section parsing for E7-04"
```

### Task 2: Add deterministic chunk planning and serialization

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/chunking.py:1-360`
- Modify: `tests/unit/pdf_convert/prep/test_chunking.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from gm_kit.pdf_convert.prep.chunking import build_chunk_plan


def test_build_chunk_plan__should_return_none_for_both_artifacts__when_sections_fit_budget() -> None:
    sections = [
        {
            "section_id": "chapter-1",
            "title": "Into the Mists",
            "level": 1,
            "kind": "body",
            "start_page": 10,
            "end_page": 23,
            "page_count": 14,
            "split_needed": False,
        }
    ]

    chapter_index, chunk_plan = build_chunk_plan(
        sections=sections,
        page_budget=20,
        workspace_dir=Path("/tmp/workspace"),
    )

    assert chapter_index is None
    assert chunk_plan is None


def test_build_chunk_plan__should_split_oversized_chapter_into_page_chunks__when_section_exceeds_budget(
    tmp_path: Path,
) -> None:
    sections = [
        {
            "section_id": "chapter-4",
            "title": "Castle Ravenloft",
            "level": 1,
            "kind": "body",
            "start_page": 50,
            "end_page": 95,
            "page_count": 46,
            "split_needed": True,
        }
    ]

    chapter_index, chunk_plan = build_chunk_plan(
        sections=sections,
        page_budget=10,
        workspace_dir=tmp_path / "workspace",
    )

    assert chapter_index is not None
    assert chunk_plan is not None
    assert chapter_index["page_budget"] == 10
    assert len(chunk_plan["chunks"]) == 5
    assert chunk_plan["chunks"][0]["chunk_kind"] == "page-split"
    assert chunk_plan["chunks"][0]["start_page"] == 50
    assert chunk_plan["chunks"][0]["end_page"] == 59
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_chunking.py -v`
Expected: FAIL because `build_chunk_plan` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from pathlib import Path


def build_chunk_plan(
    sections: list[TocSection],
    page_budget: int,
    workspace_dir: Path,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    needs_chunking = any(section.page_count > page_budget for section in sections)
    if not needs_chunking:
        return None, None

    chapter_index = {
        "page_budget": page_budget,
        "sections": [section.to_dict() for section in sections],
    }
    chunks: list[dict[str, object]] = []

    for section in sections:
        if section.page_count <= page_budget:
            chunks.append(
                {
                    "chunk_id": section.section_id,
                    "source_section_id": section.section_id,
                    "chunk_kind": "chapter",
                    "ordinal": 1,
                    "start_page": section.start_page,
                    "end_page": section.end_page,
                    "page_count": section.page_count,
                    "target_path": str(workspace_dir / "prep" / "chunks" / f"{section.section_id}.md"),
                }
            )
            continue

        ordinal = 1
        current_page = section.start_page
        while current_page <= section.end_page:
            chunk_end = min(current_page + page_budget - 1, section.end_page)
            chunks.append(
                {
                    "chunk_id": f"{section.section_id}-chunk-{ordinal}",
                    "source_section_id": section.section_id,
                    "chunk_kind": "page-split",
                    "ordinal": ordinal,
                    "start_page": current_page,
                    "end_page": chunk_end,
                    "page_count": chunk_end - current_page + 1,
                    "target_path": str(workspace_dir / "prep" / "chunks" / f"{section.section_id}-chunk-{ordinal}.md"),
                }
            )
            current_page = chunk_end + 1
            ordinal += 1

    return chapter_index, {"page_budget": page_budget, "chunks": chunks}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_chunking.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/chunking.py tests/unit/pdf_convert/prep/test_chunking.py
git commit -m "feat: add deterministic E7-04 chunk planning"
```

### Task 3: Wire the plan into prep artifacts and registry

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/orchestrator.py:1-420`
- Modify: `src/gm_kit/pdf_convert/prep/contracts.py:1-260`
- Modify: `src/gm_kit/pdf_convert/prep/registry.py:1-260`
- Modify: `src/gm_kit/pdf_convert/prep/__init__.py:1-60`
- Modify: `src/gm_kit/pdf_convert/prep/handlers.py:1-240`
- Test: `tests/unit/pdf_convert/prep/test_orchestrator.py`
- Test: `tests/unit/pdf_convert/prep/test_contracts.py`
- Test: `tests/unit/pdf_convert/prep/test_registry_runtime.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.prep import PrepOrchestrator
from gm_kit.pdf_convert.prep import chunking as chunking_module


def test_run_new_prep__should_write_chunk_artifacts_only_when_needed__when_planner_returns_chunks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    workspace = tmp_path / "workspace"

    def fake_build_chunk_plan(*, sections, page_budget, workspace_dir):
        return (
            {"page_budget": page_budget, "sections": [section.to_dict() for section in sections]},
            {
                "page_budget": page_budget,
                "chunks": [
                    {
                        "chunk_id": "chapter-1",
                        "source_section_id": "chapter-1",
                        "chunk_kind": "chapter",
                        "ordinal": 1,
                        "start_page": 1,
                        "end_page": 10,
                        "page_count": 10,
                        "target_path": str(workspace_dir / "prep" / "chunks" / "chapter-1.md"),
                    }
                ],
            },
        )

    monkeypatch.setattr(chunking_module, "build_chunk_plan", fake_build_chunk_plan)

    exit_code = PrepOrchestrator().run_new_prep(pdf_path=pdf_path, output_dir=workspace)

    assert exit_code == ExitCode.SUCCESS
    assert (workspace / "prep" / "chapter-index.json").exists()
    assert (workspace / "prep" / "chunk-plan.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_orchestrator.py -k chunk -v`
Expected: FAIL because the prep orchestrator does not yet emit chunk artifacts.

- [ ] **Step 3: Write minimal implementation**

```python
from gm_kit.pdf_convert.prep.chunking import build_chunk_plan, load_toc_sections

# Add a prep.plan-chunks step to the existing prep registry.
# The step reads prep/toc-extracted.txt, computes the chapter index,
# and writes chapter-index.json and chunk-plan.json only when build_chunk_plan()
# returns artifacts.
```

- [ ] **Step 4: Update the prep manifest artifact inventory path**

```python
# Extend the final manifest update path so chapter-index.json and chunk-plan.json
# are included in prep-manifest.json only when those files were actually written.
```

- [ ] **Step 5: Run the focused tests to verify the wiring**

Run:
- `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_contracts.py tests/unit/pdf_convert/prep/test_registry_runtime.py tests/unit/pdf_convert/prep/test_orchestrator.py -v`
- `uv run --python "$(cat .python-version)" --extra dev --editable -- ruff check src/gm_kit/pdf_convert/prep tests/unit/pdf_convert/prep`
- `uv run --python "$(cat .python-version)" --extra dev --editable -- mypy src/gm_kit/pdf_convert/prep tests/unit/pdf_convert/prep`

Expected:
- tests pass
- lint clean
- typecheck clean

- [ ] **Step 6: Commit**

```bash
git add src/gm_kit/pdf_convert/prep tests/unit/pdf_convert/prep
git commit -m "feat: wire E7-04 chunk planning into prep"
```

### Task 4: Validate the E7-04 feature slice and repo gate

**Files:**
- Test: `tests/unit/pdf_convert/prep/test_chunking.py`
- Test: `tests/unit/pdf_convert/prep/test_orchestrator.py`
- Test: `tests/unit/pdf_convert/prep/test_contracts.py`
- Test: `tests/unit/pdf_convert/prep/test_registry_runtime.py`

- [ ] **Step 1: Run the focused prep tests**

Run:
`uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep -q`

Expected:
- all prep tests pass
- no regressions in E7-03 prep artifacts or registry behavior

- [ ] **Step 2: Run lint and typecheck**

Run:
`uv run --python "$(cat .python-version)" --extra dev --editable -- ruff check src/gm_kit/pdf_convert/prep tests/unit/pdf_convert/prep`
`uv run --python "$(cat .python-version)" --extra dev --editable -- mypy src/gm_kit/pdf_convert/prep tests/unit/pdf_convert/prep`

Expected:
- no lint errors
- no mypy errors

- [ ] **Step 3: Run the full repo gate**

Run:
`just all_ci_actions`

Expected:
- lint pass
- typecheck pass
- unit tests pass
- integration tests pass
- parity pass
- bandit pass
- audit pass

- [ ] **Step 4: Commit the completed feature**

```bash
git add src/gm_kit/pdf_convert/prep tests/unit/pdf_convert/prep specs/e7-04-chapter-segmentation-chunk-planning/feature_journal.md
git commit -m "feat: add E7-04 chapter segmentation and chunk planning"
```
