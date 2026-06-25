from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from gm_kit.pdf_convert.prep.chunking import build_chunk_plan, load_toc_sections


def test_load_toc_sections__should_classify_front_matter_body_and_appendix__when_toc_artifact_is_valid(
    tmp_path: Path,
) -> None:
    toc_path = tmp_path / "toc-extracted.txt"
    toc_path.write_text(
        "\n".join(
            [
                "# TOC Source: embedded",
                "# Extraction method: PDF metadata (prep/shared helper)",
                "# Total entries: 4",
                "",
                "Contents (page 1)",
                "  Introduction (page 3)",
                "Chapter 1: The Village of Barovia (page 5)",
                "Appendix A: Appendix Resources (page 11)",
                "",
            ]
        ),
        encoding="utf-8",
    )

    sections = load_toc_sections(toc_path=toc_path, page_count=14)

    assert [section.kind for section in sections] == [
        "front_matter",
        "body",
        "appendix",
    ]
    assert [(section.start_page, section.end_page, section.page_count) for section in sections] == [
        (1, 4, 4),
        (5, 10, 6),
        (11, 14, 4),
    ]
    assert sections[0].to_dict() == {
        "section_id": "001-front_matter-contents",
        "title": "Contents",
        "level": 1,
        "kind": "front_matter",
        "start_page": 1,
        "end_page": 4,
        "page_count": 4,
        "split_needed": False,
    }


def test_load_toc_sections__should_ignore_same_page_nested_entries__when_outline_has_subsections(
    tmp_path: Path,
) -> None:
    toc_path = tmp_path / "toc-extracted.txt"
    toc_path.write_text(
        "\n".join(
            [
                "# TOC Source: embedded",
                "# Extraction method: PDF metadata (prep/shared helper)",
                "# Total entries: 6",
                "",
                "Introduction (page 6)",
                "  Running the Adventure (page 6)",
                "    Story Overview (page 6)",
                "Chapter 1: Into the Mists (page 10)",
                "  Strahd Von Zarovich (page 10)",
                "Appendix A: Character Options (page 210)",
                "",
            ]
        ),
        encoding="utf-8",
    )

    sections = load_toc_sections(toc_path=toc_path, page_count=258)

    assert [section.title for section in sections] == [
        "Introduction",
        "Chapter 1: Into the Mists",
        "Appendix A: Character Options",
    ]
    assert [(section.start_page, section.end_page) for section in sections] == [
        (6, 9),
        (10, 209),
        (210, 258),
    ]


def test_load_toc_sections__should_fail_cleanly__when_same_page_sibling_entries_are_ambiguous(
    tmp_path: Path,
) -> None:
    toc_path = tmp_path / "toc-extracted.txt"
    toc_path.write_text(
        "\n".join(
            [
                "Chapter 1: Into the Mists (page 10)",
                "Chapter 2: The Lands of Barovia (page 10)",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="ambiguous"):
        load_toc_sections(toc_path=toc_path, page_count=258)


def test_build_chunk_plan__should_return_none_for_small_documents__when_total_pages_fit_budget(
    tmp_path: Path,
) -> None:
    toc_path = tmp_path / "toc-extracted.txt"
    toc_path.write_text(
        "\n".join(
            [
                "# TOC Source: embedded",
                "# Extraction method: PDF metadata (prep/shared helper)",
                "# Total entries: 3",
                "",
                "Contents (page 1)",
                "Chapter 1: The Village of Barovia (page 3)",
                "Appendix A: Appendix Resources (page 8)",
                "",
            ]
        ),
        encoding="utf-8",
    )

    sections = load_toc_sections(toc_path=toc_path, page_count=9)
    chapter_index, chunk_plan = build_chunk_plan(
        sections,
        workspace_dir=tmp_path / "workspace",
    )

    assert chapter_index is None
    assert chunk_plan is None


def test_build_chunk_plan__should_emit_one_chunk_per_chapter__when_document_exceeds_budget(
    tmp_path: Path,
) -> None:
    toc_path = tmp_path / "toc-extracted.txt"
    toc_path.write_text(
        "\n".join(
            [
                "# TOC Source: embedded",
                "# Extraction method: PDF metadata (prep/shared helper)",
                "# Total entries: 4",
                "",
                "Contents (page 1)",
                "Chapter 1: The Village of Barovia (page 2)",
                "Chapter 2: The Castle (page 6)",
                "Appendix A: Resources (page 11)",
                "",
            ]
        ),
        encoding="utf-8",
    )

    sections = load_toc_sections(toc_path=toc_path, page_count=14)
    chapter_index, chunk_plan = build_chunk_plan(
        sections,
        workspace_dir=tmp_path / "workspace",
    )

    assert chapter_index is not None
    assert chunk_plan is not None
    assert chapter_index["document_page_count"] == 14
    chunk_sections = cast(list[dict[str, object]], chapter_index["sections"])
    chunks = cast(list[dict[str, object]], chunk_plan["chunks"])

    assert [entry["section_id"] for entry in chunk_sections] == [
        "001-front_matter-contents",
        "002-body-chapter-1-the-village-of-barovia",
        "003-body-chapter-2-the-castle",
        "004-appendix-appendix-a-resources",
    ]
    assert [chunk["chunk_kind"] for chunk in chunks] == [
        "chapter",
        "chapter",
        "chapter",
        "chapter",
    ]
    assert [chunk["source_section_id"] for chunk in chunks] == [
        "001-front_matter-contents",
        "002-body-chapter-1-the-village-of-barovia",
        "003-body-chapter-2-the-castle",
        "004-appendix-appendix-a-resources",
    ]
    assert [chunk["ordinal"] for chunk in chunks] == [1, 1, 1, 1]


def test_build_chunk_plan__should_split_oversized_sections_into_page_chunks__when_section_exceeds_budget(
    tmp_path: Path,
) -> None:
    toc_path = tmp_path / "toc-extracted.txt"
    toc_path.write_text(
        "\n".join(
            [
                "# TOC Source: embedded",
                "# Extraction method: PDF metadata (prep/shared helper)",
                "# Total entries: 1",
                "",
                "Chapter 1: Castle Ravenloft (page 1)",
                "",
            ]
        ),
        encoding="utf-8",
    )

    sections = load_toc_sections(toc_path=toc_path, page_count=26)
    chapter_index, chunk_plan = build_chunk_plan(
        sections,
        workspace_dir=tmp_path / "workspace",
    )

    assert chapter_index is not None
    assert chunk_plan is not None
    chunk_sections = cast(list[dict[str, object]], chapter_index["sections"])
    chunks = cast(list[dict[str, object]], chunk_plan["chunks"])

    assert chunk_sections[0]["split_needed"] is True
    assert [chunk["chunk_kind"] for chunk in chunks] == [
        "page-split",
        "page-split",
        "page-split",
    ]
    assert [chunk["source_section_id"] for chunk in chunks] == [
        "001-body-chapter-1-castle-ravenloft",
        "001-body-chapter-1-castle-ravenloft",
        "001-body-chapter-1-castle-ravenloft",
    ]
    assert [chunk["ordinal"] for chunk in chunks] == [1, 2, 3]
    assert [(chunk["start_page"], chunk["end_page"]) for chunk in chunks] == [
        (1, 10),
        (11, 20),
        (21, 26),
    ]
