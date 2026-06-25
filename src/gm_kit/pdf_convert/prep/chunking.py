from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

CHUNK_PAGE_BUDGET = 10

_TOC_LINE_PATTERN = re.compile(r"^(?P<indent>\s*)(?P<title>.+) \(page (?P<page>\d+)\)$")

_FRONT_MATTER_PREFIXES = (
    "acknowledgements",
    "contents",
    "credits",
    "foreword",
    "introduction",
    "preface",
    "prologue",
)


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


@dataclass(frozen=True)
class ChunkDefinition:
    chunk_id: str
    source_section_id: str
    chunk_kind: str
    ordinal: int
    start_page: int
    end_page: int
    page_count: int
    target_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk_id,
            "source_section_id": self.source_section_id,
            "chunk_kind": self.chunk_kind,
            "ordinal": self.ordinal,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "page_count": self.page_count,
            "target_path": self.target_path,
        }


@dataclass(frozen=True)
class _TocEntry:
    level: int
    title: str
    page: int


def load_toc_sections(toc_path: Path, page_count: int) -> list[TocSection]:
    toc_entries = _parse_toc_entries(toc_path)
    return _build_sections_from_toc(toc_entries, page_count)


def build_chunk_plan(
    sections: list[TocSection],
    page_budget: int = CHUNK_PAGE_BUDGET,
    workspace_dir: Path | None = None,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    if not sections:
        return None, None

    _validate_sections(sections)
    document_page_count = sections[-1].end_page
    if document_page_count <= page_budget:
        return None, None

    workspace_root = workspace_dir or Path(".")
    chapter_index = {
        "page_budget": page_budget,
        "document_page_count": document_page_count,
        "sections": [section.to_dict() for section in sections],
    }
    chunk_plan = {
        "page_budget": page_budget,
        "document_page_count": document_page_count,
        "chunks": [
            chunk.to_dict()
            for chunk in _build_chunks(
                sections,
                page_budget=page_budget,
                workspace_dir=workspace_root,
            )
        ],
    }
    return chapter_index, chunk_plan


def _parse_toc_entries(toc_path: Path) -> list[_TocEntry]:
    toc_entries: list[_TocEntry] = []
    for line in toc_path.read_text(encoding="utf-8").splitlines():
        match = _TOC_LINE_PATTERN.match(line)
        if match is None:
            continue

        indent = match.group("indent")
        toc_entries.append(
            _TocEntry(
                level=max(1, len(indent) // 2 + 1),
                title=match.group("title").strip(),
                page=int(match.group("page")),
            )
        )
    return toc_entries


def _build_sections_from_toc(
    toc_entries: list[_TocEntry],
    page_count: int,
) -> list[TocSection]:
    if not toc_entries:
        return []

    _validate_toc_entries(toc_entries, page_count)
    root_level = min(entry.level for entry in toc_entries)
    section_entries = [entry for entry in toc_entries if entry.level == root_level]
    if not section_entries:
        return []

    sections: list[TocSection] = []
    for index, entry in enumerate(section_entries):
        next_page = (
            section_entries[index + 1].page
            if index + 1 < len(section_entries)
            else page_count + 1
        )
        if next_page <= entry.page:
            raise ValueError("Top-level TOC entries on the same page are ambiguous")

        end_page = next_page - 1
        page_count_for_section = end_page - entry.page + 1
        kind = _classify_section_kind(entry.title)
        sections.append(
            TocSection(
                section_id=f"{index + 1:03d}-{kind}-{_slugify(entry.title)}",
                title=entry.title,
                level=entry.level,
                kind=kind,
                start_page=entry.page,
                end_page=end_page,
                page_count=page_count_for_section,
                split_needed=page_count_for_section > CHUNK_PAGE_BUDGET,
            )
        )

    return sections


def _validate_toc_entries(toc_entries: list[_TocEntry], page_count: int) -> None:
    previous_page = 0

    for entry in toc_entries:
        if not entry.title:
            raise ValueError("TOC entries must include a non-empty title")
        if entry.level < 1:
            raise ValueError("TOC entries must use positive levels")
        if entry.page < 1:
            raise ValueError("TOC entries must use positive page numbers")
        if entry.page > page_count:
            raise ValueError("TOC entries must not exceed the PDF page count")
        if entry.page < previous_page:
            raise ValueError("TOC entries must be non-decreasing by page")

        previous_page = entry.page


def _classify_section_kind(title: str) -> str:
    lower_title = title.lower()
    if lower_title.startswith("appendix"):
        return "appendix"
    if lower_title.startswith(_FRONT_MATTER_PREFIXES):
        return "front_matter"
    return "body"


def _slugify(title: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", title.lower())
    return normalized.strip("-") or "section"


def _validate_sections(sections: list[TocSection]) -> None:
    previous_end: int | None = None
    for section in sections:
        if section.start_page > section.end_page:
            raise ValueError("TOC sections must have non-empty page spans")
        if previous_end is not None and section.start_page <= previous_end:
            raise ValueError("TOC sections must be strictly increasing by page")
        previous_end = section.end_page


def _build_chunks(
    sections: list[TocSection],
    *,
    page_budget: int,
    workspace_dir: Path,
) -> list[ChunkDefinition]:
    chunks: list[ChunkDefinition] = []
    chunk_ordinal = 1

    for section in sections:
        if section.page_count <= page_budget:
            chunks.append(
                ChunkDefinition(
                    chunk_id=f"chunk-{chunk_ordinal:03d}",
                    source_section_id=section.section_id,
                    chunk_kind="chapter",
                    ordinal=1,
                    start_page=section.start_page,
                    end_page=section.end_page,
                    page_count=section.page_count,
                    target_path=str(
                        workspace_dir / "prep" / "chunks" / f"chunk-{chunk_ordinal:03d}.md"
                    ),
                )
            )
            chunk_ordinal += 1
            continue

        current_page = section.start_page
        split_ordinal = 1
        while current_page <= section.end_page:
            chunk_end = min(current_page + page_budget - 1, section.end_page)
            chunks.append(
                ChunkDefinition(
                    chunk_id=f"{section.section_id}-chunk-{split_ordinal:03d}",
                    source_section_id=section.section_id,
                    chunk_kind="page-split",
                    ordinal=split_ordinal,
                    start_page=current_page,
                    end_page=chunk_end,
                    page_count=chunk_end - current_page + 1,
                    target_path=str(
                        workspace_dir
                        / "prep"
                        / "chunks"
                        / f"{section.section_id}-chunk-{split_ordinal:03d}.md"
                    ),
                )
            )
            chunk_ordinal += 1
            current_page = chunk_end + 1
            split_ordinal += 1

    return chunks
