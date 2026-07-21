"""Shared prep handlers for PDF-derived artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, cast

import fitz  # type: ignore[import-untyped]
import typer
import yaml  # type: ignore[import-untyped]

from gm_kit.pdf_convert.metadata import PDFMetadata, extract_metadata
from gm_kit.pdf_convert.preflight import PreflightReport, analyze_pdf
from gm_kit.pdf_convert.prep.analysis_artifacts import PrepAnalysisArtifactPaths
from gm_kit.pdf_convert.prep.callout_detection import (
    _pad_rect,
    _same_text_column,
    detect_callout_proposals_with_warnings,
)
from gm_kit.pdf_convert.prep.chunking import CHUNK_PAGE_BUDGET, build_chunk_plan, load_toc_sections
from gm_kit.pdf_convert.prep.contracts import (
    ANNOTATION_REVIEW_MODES,
    ANNOTATION_REVIEW_STATUSES,
    CALLOUT_REGION_LABELS,
    AnnotationProposal,
    AnnotationReviewEdits,
    PrepGuidanceInput,
    PrepGuidanceResolved,
)
from gm_kit.pdf_convert.prep.refinement import (
    CalloutRefinementCropEntry,
    PrepRefinementPause,
    build_callout_refinement_agent,
    build_callout_refinement_inputs,
    build_table_refinement_inputs,
    refine_callout_proposals,
)

TABLE_PLACEHOLDER_BBOX = [72.0, 240.0, 520.0, 610.0]
FULL_PAGE_PLACEHOLDER_BBOX = [0.0, 0.0, 612.0, 792.0]
DEFAULT_CALLOUT_REGION_LABEL = "callout_gm"
TRAILING_APPENDIX_MIN_CHUNKS = 2
TABLE_MIN_X0_CLUSTERS = 3
TABLE_MIN_ROW_FRAGMENTS = 2
TABLE_MAX_STRONG_AVG_LINE_LENGTH = 25.0
TABLE_MAX_NUMERIC_AVG_LINE_LENGTH = 45.0
TABLE_MAX_CLEAR_PROSE_AVG_LINE_LENGTH = 45.0
TABLE_MAX_TITLE_WORDS = 4
TABLE_MAX_TITLE_LABEL_LENGTH = 24
TABLE_MAX_TITLELESS_FIRST_LINE_WORDS = 4
TABLE_TITLE_PADDING_TOP = 28.0
TABLE_REGION_GAP = 26.0
TABLE_WEAK_REGION_GAP = 18.0
TABLE_WEAK_TEXT_MAX_LENGTH = 40
TABLE_BLOCK_LINE_GAP_TOLERANCE = 2.5
TABLE_HEADING_FONT_DELTA = 1.5
TABLE_HEADING_TEXT_MAX_LENGTH = 24
TABLE_LIGHT_BLUE_FILL = (0.6000000238418579, 0.7568627595901489, 0.9450980424880981)


class _ChunkEntry(TypedDict):
    source_section_id: str
    start_page: int
    end_page: int
    chunk_kind: str
    ordinal: int


@dataclass(frozen=True)
class _TableBlockProfile:
    block_index: int
    block: object
    line_count: int
    x0_clusters: int
    row_fragment_count: int
    numeric_token_count: int
    pipe_token_count: int
    average_line_length: float
    has_leading_label_colon: bool

    @property
    def is_strong(self) -> bool:
        return (
            self.x0_clusters >= TABLE_MIN_X0_CLUSTERS
            and self.line_count >= TABLE_MIN_ROW_FRAGMENTS + 1
            and self.row_fragment_count >= TABLE_MIN_ROW_FRAGMENTS
            and self.average_line_length <= TABLE_MAX_STRONG_AVG_LINE_LENGTH
        ) or (
            self.x0_clusters >= TABLE_MIN_ROW_FRAGMENTS
            and (self.numeric_token_count > 0 or self.pipe_token_count > 0)
            and self.row_fragment_count >= TABLE_MIN_ROW_FRAGMENTS
            and self.average_line_length <= TABLE_MAX_NUMERIC_AVG_LINE_LENGTH
        )

    @property
    def is_clear_prose(self) -> bool:
        return (
            self.line_count >= TABLE_MIN_ROW_FRAGMENTS
            and self.x0_clusters == 1
            and self.numeric_token_count == 0
            and self.pipe_token_count == 0
            and self.average_line_length >= TABLE_MAX_CLEAR_PROSE_AVG_LINE_LENGTH
            and not self.has_leading_label_colon
        )

    @property
    def is_table_like(self) -> bool:
        return self.is_strong


def parse_skip_ranges_input(raw_input: str, *, page_count: int) -> list[int]:
    """Parse comma-separated page numbers and inclusive ranges into unique pages."""
    if raw_input.strip() == "":
        return []

    pages: set[int] = set()
    for raw_token in raw_input.split(","):
        token = raw_token.strip()
        if not token:
            raise ValueError("Invalid skip range token: ''")

        if "-" not in token:
            page = _parse_skip_page_token(token)
            _validate_skip_page(page, page_count=page_count)
            pages.add(page)
            continue

        start_text, separator, end_text = token.partition("-")
        start_text = start_text.strip()
        end_text = end_text.strip()
        if separator != "-" or start_text == "" or end_text == "":
            raise ValueError(f"Invalid skip range token: '{token}'")
        start_page = _parse_skip_page_token(start_text)
        end_page = _parse_skip_page_token(end_text)
        if start_page > end_page:
            raise ValueError(
                f"Skip range start must be less than or equal to end: '{token}'"
            )
        for page in range(start_page, end_page + 1):
            _validate_skip_page(page, page_count=page_count)
            pages.add(page)

    return sorted(pages)


def extract_images_to_artifacts(pdf_path: Path, images_dir: Path) -> tuple[Path, int]:
    """Extract PDF images and write the image manifest artifact."""
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
                image_extension = base_image.get("ext", "png")
                if isinstance(image_extension, str) and image_extension.strip():
                    normalized_extension = image_extension.lstrip(".").lower()
                else:
                    normalized_extension = "png"
                img_filename = (
                    f"page{page_num + 1:03d}_img{img_index + 1:02d}."
                    f"{normalized_extension}"
                )
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
        json.dumps(
            {"images": image_manifest, "total_count": len(image_manifest)},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path, total_images


def create_no_images_pdf(pdf_path: Path, output_pdf_path: Path) -> int:
    """Create the no-images PDF and return removed image instance count."""
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
        doc.save(output_pdf_path, garbage=4, clean=True, deflate=True)
    finally:
        doc.close()

    return images_removed


def extract_toc_to_artifact(pdf_path: Path, output_path: Path) -> list[dict[str, object]]:
    """Extract the embedded TOC and write the artifact file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    toc_entries: list[dict[str, object]] = []
    doc = fitz.open(pdf_path)

    try:
        toc = cast(list[tuple[int, str, int]], doc.get_toc())
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
        level = cast(int, entry["level"])
        title = cast(str, entry["title"])
        page = cast(int, entry["page"])
        lines.append(f"{'  ' * (level - 1)}{title} (page {page})")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return toc_entries


def write_metadata_and_preflight_artifacts(
    metadata: PDFMetadata,
    report: PreflightReport,
    metadata_path: Path,
    preflight_report_path: Path,
) -> None:
    """Persist metadata and preflight analysis artifacts."""
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
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
    preflight_report_path.write_text(
        json.dumps(preflight_payload, indent=2) + "\n",
        encoding="utf-8",
    )


def handle_extract_metadata_and_preflight(
    *,
    pdf_path: Path,
    analysis_paths: PrepAnalysisArtifactPaths,
    **_context: object,
) -> None:
    """Persist metadata and preflight artifacts for prep."""
    metadata = extract_metadata(pdf_path)
    report = analyze_pdf(pdf_path, metadata=metadata)
    write_metadata_and_preflight_artifacts(
        metadata=metadata,
        report=report,
        metadata_path=analysis_paths.metadata,
        preflight_report_path=analysis_paths.preflight_report,
    )


def handle_extract_images(
    *,
    pdf_path: Path,
    analysis_paths: PrepAnalysisArtifactPaths,
    **_context: object,
) -> None:
    """Write extracted images and their manifest for prep."""
    extract_images_to_artifacts(pdf_path=pdf_path, images_dir=analysis_paths.images_dir)


def handle_create_no_images_pdf(
    *,
    pdf_path: Path,
    analysis_paths: PrepAnalysisArtifactPaths,
    **_context: object,
) -> None:
    """Write the no-images PDF for prep."""
    create_no_images_pdf(pdf_path=pdf_path, output_pdf_path=analysis_paths.no_images_pdf)


def handle_extract_canonical_toc(
    *,
    pdf_path: Path,
    analysis_paths: PrepAnalysisArtifactPaths,
    **_context: object,
) -> None:
    """Write the canonical TOC artifact for prep."""
    extract_toc_to_artifact(pdf_path=pdf_path, output_path=analysis_paths.toc)


def handle_plan_chunks(
    *,
    analysis_paths: PrepAnalysisArtifactPaths,
    **_context: object,
) -> None:
    """Write the chunk plan artifacts when the document exceeds the chunk budget."""
    metadata_payload = json.loads(analysis_paths.metadata.read_text(encoding="utf-8"))
    page_count = int(metadata_payload["page_count"])
    if page_count <= CHUNK_PAGE_BUDGET:
        return

    if not analysis_paths.toc.exists():
        raise ValueError("toc-extracted.txt is required before chunk planning")

    toc_sections = load_toc_sections(analysis_paths.toc, page_count=page_count)
    if not toc_sections:
        raise ValueError("toc-extracted.txt did not contain any TOC entries")

    chapter_index, chunk_plan = build_chunk_plan(
        toc_sections,
        page_budget=CHUNK_PAGE_BUDGET,
        workspace_dir=analysis_paths.chapter_index.parent.parent,
    )
    if chapter_index is None or chunk_plan is None:
        return

    analysis_paths.chapter_index.write_text(
        json.dumps(chapter_index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    analysis_paths.chunk_plan.write_text(
        json.dumps(chunk_plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def handle_write_guidance_defaults(
    *,
    analysis_paths: PrepAnalysisArtifactPaths,
    **_context: object,
) -> None:
    """Write the default prep guidance artifact."""
    guidance_defaults = PrepGuidanceInput()
    analysis_paths.guidance_defaults.write_text(
        yaml.safe_dump(
            guidance_defaults.to_dict(),
            sort_keys=True,
            default_flow_style=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def handle_generate_annotation_proposals(
    *,
    pdf_path: Path,
    analysis_paths: PrepAnalysisArtifactPaths,
    **_context: object,
) -> None:
    """Write raw annotation proposals."""
    guidance_input = _load_guidance_defaults(analysis_paths.guidance_defaults)
    page_count = _load_page_count(analysis_paths.metadata)
    images_total_count = _load_images_total_count(analysis_paths.image_manifest)
    chunk_plan = _load_optional_json_mapping(analysis_paths.chunk_plan)
    toc_sections = _load_toc_sections(analysis_paths.toc, page_count=page_count)
    callout_detection = detect_callout_proposals_with_warnings(pdf_path, guidance_input)
    for warning in callout_detection.warnings:
        typer.echo(f"WARNING: {warning}")

    proposals = build_annotation_proposals(
        pdf_path=pdf_path,
        page_count=page_count,
        images_total_count=images_total_count,
        chunk_plan=chunk_plan,
        toc_sections=toc_sections,
        callout_proposals=callout_detection.proposals,
        guidance_input=guidance_input,
    )
    filtered_proposals = _filter_annotation_proposals(
        proposals,
        guidance_input=guidance_input,
    )
    analysis_paths.annotation_proposals.write_text(
        json.dumps(
            [proposal.to_dict() for proposal in proposals],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    analysis_paths.annotation_refinement_hints.write_text(
        json.dumps(
            [hint.to_dict() for hint in callout_detection.refinement_hints],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    skip_callout_refinement = bool(_context.get("skip_callout_refinement", False))
    refinement_entries = build_callout_refinement_inputs(
        pdf_path=pdf_path,
        proposals=[proposal for proposal in proposals if proposal.label == "callout"],
        refinement_hints=callout_detection.refinement_hints,
        guidance_input=guidance_input,
        manifest_path=analysis_paths.annotation_refinement_manifest,
        crops_dir=analysis_paths.annotation_refinement_crops_dir,
    )
    table_refinement_entries = build_table_refinement_inputs(
        pdf_path=pdf_path,
        proposals=[proposal for proposal in proposals if proposal.label == "table"],
        guidance_input=guidance_input,
        manifest_path=analysis_paths.annotation_table_refinement_manifest,
        crops_dir=analysis_paths.annotation_refinement_crops_dir,
    )
    refinement_mode = str(_context.get("callout_refinement_mode") or "").strip().lower()
    analysis_paths.annotation_refinement_request.write_text(
        json.dumps(
            {
                "source_pdf_path": str(pdf_path),
                "proposal_count": len(refinement_entries),
                "crops_dir": str(analysis_paths.annotation_refinement_crops_dir),
                "request_status": (
                    "ready_for_outer_agent"
                    if refinement_entries and not skip_callout_refinement
                    else "not_requested"
                ),
                "refinement_mode": refinement_mode or "mock",
                "instructions": [
                    "Review the crop images for each listed callout proposal.",
                    "Adjust only the proposals whose geometry is clearly too loose or too tight.",
                    (
                        "Write the updated proposal list to "
                        "annotation-refined-proposals.json in the prep root."
                    ),
                    "Leave proposals unchanged when the current geometry is already correct.",
                    (
                        "After writing the response artifact, resume prep with "
                        "gmkit analyze-and-prep-pdf --resume <workspace>."
                    ),
                ],
                "response_artifact": "annotation-refined-proposals.json",
                "resume_command": "gmkit analyze-and-prep-pdf --resume <workspace>",
                "items": [entry.to_dict() for entry in refinement_entries],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    analysis_paths.annotation_table_refinement_request.write_text(
        json.dumps(
            {
                "source_pdf_path": str(pdf_path),
                "proposal_count": len(table_refinement_entries),
                "crops_dir": str(analysis_paths.annotation_refinement_crops_dir),
                "request_status": (
                    "ready_for_review" if table_refinement_entries else "not_requested"
                ),
                "refinement_mode": "table-review",
                "instructions": [
                    "Review the crop images for each listed table proposal.",
                    (
                        "Adjust table boundaries when the current crop is clearly too "
                        "loose or too tight."
                    ),
                    (
                        "Write the updated proposal list to "
                        "annotation-refined-proposals.json in the prep root."
                    ),
                    "Leave proposals unchanged when the current geometry is already correct.",
                ],
                "response_artifact": "annotation-refined-proposals.json",
                "resume_command": "gmkit analyze-and-prep-pdf --resume <workspace>",
                "items": [entry.to_dict() for entry in table_refinement_entries],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if refinement_mode == "handoff" and refinement_entries and not skip_callout_refinement:
        render_annotated_prep_pdf(
            pdf_path=pdf_path,
            proposals=filtered_proposals,
            output_pdf_path=analysis_paths.annotated_pdf,
        )
        raise PrepRefinementPause(
            str(analysis_paths.annotation_refinement_request),
            "Write `annotation-refined-proposals.json` and resume prep after the handoff.",
        )
    refined_proposals = _maybe_refine_callout_proposals(
        analysis_paths=analysis_paths,
        proposals=proposals,
        refinement_entries=refinement_entries,
        skip_callout_refinement=skip_callout_refinement,
    )
    if refined_proposals is not None:
        analysis_paths.annotation_refined_proposals.write_text(
            json.dumps(
                [proposal.to_dict() for proposal in refined_proposals],
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    analysis_paths.guidance_resolved.write_text(
        json.dumps(
            build_resolved_guidance(
                _filter_annotation_proposals(
                    refined_proposals if refined_proposals is not None else filtered_proposals,
                    guidance_input=guidance_input,
                )
            ).to_dict(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def handle_seed_annotation_review(
    *,
    analysis_paths: PrepAnalysisArtifactPaths,
    auto_proceed: bool = False,
    **_context: object,
) -> None:
    """Seed the annotation review edit artifact."""
    guidance_input = _load_guidance_defaults(analysis_paths.guidance_defaults)
    review_mode = (
        "auto_accept"
        if auto_proceed or guidance_input.auto_accept_annotations
        else "interactive"
    )
    if not guidance_input.review_requested and not auto_proceed:
        review_mode = "bypass"

    edits = build_annotation_review_edits(
        review_mode=review_mode,
        skip_ranges_input="",
        skip_pages_explicit=[],
    )
    analysis_paths.annotation_review_edits.write_text(
        json.dumps(edits.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def handle_render_annotated_prep_pdf(
    *,
    pdf_path: Path,
    analysis_paths: PrepAnalysisArtifactPaths,
    **_context: object,
) -> None:
    """Render the annotated prep PDF used for manual review."""
    guidance_input = _load_guidance_defaults(analysis_paths.guidance_defaults)
    proposals = _load_effective_annotation_proposals(analysis_paths)
    proposals = _filter_annotation_proposals(
        proposals,
        guidance_input=guidance_input,
    )
    render_annotated_prep_pdf(
        pdf_path=pdf_path,
        proposals=proposals,
        output_pdf_path=analysis_paths.annotated_pdf,
    )


def handle_finalize_reviewed_guidance(
    *,
    analysis_paths: PrepAnalysisArtifactPaths,
    **_context: object,
) -> None:
    """Regenerate reviewed guidance from the review artifact."""
    proposals = _load_effective_annotation_proposals(analysis_paths)
    review_edits = _load_annotation_review_edits(analysis_paths.annotation_review_edits)
    page_count = _load_page_count(analysis_paths.metadata)
    explicit_skip_pages = list(review_edits.skip_pages_explicit)
    explicit_skip_pages.extend(
        parse_skip_ranges_input(review_edits.skip_ranges_input, page_count=page_count)
    )
    reviewed_proposals = apply_review_edits_to_proposals(proposals, review_edits)
    resolved_guidance = build_final_resolved_guidance(
        proposals=reviewed_proposals,
        skip_pages_explicit=explicit_skip_pages,
        review_mode=review_edits.review_mode,
        review_status=review_edits.review_status,
        skip_ranges_input=review_edits.skip_ranges_input,
    )
    analysis_paths.reviewed_guidance.write_text(
        json.dumps(resolved_guidance.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_annotation_proposals(  # noqa: PLR0913
    *,
    pdf_path: Path | None = None,
    page_count: int,
    images_total_count: int,
    chunk_plan: Mapping[str, object] | None,
    toc_sections: list[object] | None = None,
    callout_proposals: list[AnnotationProposal] | None = None,
    guidance_input: PrepGuidanceInput | None = None,
) -> list[AnnotationProposal]:
    """Build deterministic prep annotation proposals from cheap heuristics."""
    proposals: list[AnnotationProposal] = []
    chunk_entries = _normalize_chunk_entries(chunk_plan)
    detect_tables = guidance_input.prefer_detect_tables if guidance_input is not None else True

    if detect_tables:
        table_proposals: list[AnnotationProposal] = []
        if pdf_path is not None:
            table_proposals = _detect_table_proposals_from_pdf(
                pdf_path=pdf_path,
                page_count=page_count,
                toc_sections=toc_sections,
            )
            proposals.extend(table_proposals)
        if not table_proposals:
            proposals.extend(_build_chunk_seed_table_proposals(chunk_entries=chunk_entries))

    if callout_proposals:
        proposals.extend(callout_proposals)

    for page in _detect_trailing_appendix_skip_pages(chunk_entries):
        proposals.append(
            _build_proposal(
                label="skip",
                page=page,
                bbox=FULL_PAGE_PLACEHOLDER_BBOX,
                confidence=0.75,
                metadata={
                    "source": "code",
                    "scope": "full-page",
                    "reason": "trailing-appendix-span",
                },
            )
        )

    return sorted(proposals, key=lambda proposal: proposal.proposal_id)


def _build_chunk_seed_table_proposals(
    *,
    chunk_entries: list[_ChunkEntry],
) -> list[AnnotationProposal]:
    proposals: list[AnnotationProposal] = []
    for chunk_entry in chunk_entries:
        metadata = {
            "source": "code",
            "source_section_id": chunk_entry["source_section_id"],
            "chunk_kind": chunk_entry["chunk_kind"],
            "ordinal": chunk_entry["ordinal"],
        }
        proposals.append(
            _build_proposal(
                label="table",
                page=int(chunk_entry["start_page"]),
                bbox=TABLE_PLACEHOLDER_BBOX,
                confidence=0.5,
                metadata=metadata,
            )
        )
    return proposals


def _detect_table_proposals_from_pdf(
    *,
    pdf_path: Path,
    page_count: int,
    toc_sections: list[object] | None = None,
) -> list[AnnotationProposal]:
    proposals: list[AnnotationProposal] = []
    doc = fitz.open(pdf_path)
    try:
        for page_number in range(1, min(page_count, len(doc)) + 1):
            page = doc[page_number - 1]
            page_toc_sections = _toc_sections_starting_on_page(toc_sections, page_number)
            table_regions = _detect_table_regions_on_page(
                page,
                toc_sections=page_toc_sections,
            )
            for region_index, (
                region_rect,
                title_text,
                data_text,
            ) in enumerate(table_regions, start=1):
                proposals.append(
                    _build_proposal(
                        label="table",
                        page=page_number,
                        bbox=_pad_rect(
                            region_rect,
                            {
                                "left": 6.0,
                                "top": 4.0,
                                "right": 6.0,
                                "bottom": 6.0,
                            },
                        ),
                        confidence=0.75,
                        metadata={
                            "source": "code",
                            "trigger": "text-pattern",
                            "table_title": title_text,
                            "table_text": data_text,
                            "ordinal": region_index,
                        },
                    )
                )
    finally:
        doc.close()
    return proposals


def _detect_table_regions_on_page(
    page: fitz.Page,
    *,
    toc_sections: list[dict[str, object]] | None = None,
) -> list[tuple[fitz.Rect, str, str]]:  # noqa: PLR0912
    payload = page.get_text("dict")
    blocks: list[dict[str, object]] = [
        block
        for block in cast(list[dict[str, object]], payload.get("blocks", []))
        if block.get("type") == 0
    ]
    profiles = [
        _build_table_block_profile(block_index=index, block=block)
        for index, block in enumerate(blocks)
    ]
    regions: list[tuple[fitz.Rect, str, str]] = []
    consumed_block_indexes: set[int] = set()

    for profile in profiles:
        if profile.block_index in consumed_block_indexes or not profile.is_strong:
            continue

        start_index = profile.block_index
        end_index = start_index
        region_rect = _block_rect(blocks[start_index])
        title_text = ""

        if start_index > 0:
            previous = blocks[start_index - 1]
            previous_rect = _block_rect(previous)
            current_rect = _block_rect(blocks[start_index])
            previous_text = _block_text(previous)
            if (
                _looks_like_table_title(previous_text)
                and _same_text_column(previous_rect, current_rect)
                and current_rect.y0 - previous_rect.y1 <= TABLE_TITLE_PADDING_TOP
            ):
                start_index -= 1
                region_rect = previous_rect | region_rect
                title_text = previous_text.strip()

        while end_index + 1 < len(blocks):
            next_index = end_index + 1
            next_block = blocks[next_index]
            next_profile = profiles[next_index]
            next_rect = _block_rect(next_block)
            if _should_stop_table_region(
                page_number=page.number + 1,
                start_block=blocks[start_index],
                current_block=blocks[end_index],
                next_block=next_block,
                next_profile=next_profile,
                toc_sections=toc_sections,
            ):
                break
            region_rect = region_rect | next_rect
            end_index = next_index

        consumed_block_indexes.update(range(start_index, end_index + 1))
        region_text_blocks = [
            _block_text(blocks[index]).strip()
            for index in range(start_index, end_index + 1)
            if _block_text(blocks[index]).strip()
        ]
        if not region_text_blocks:
            continue
        if not title_text:
            first_line_text = _block_first_line_text(blocks[start_index])
            if (
                not _looks_like_table_title(first_line_text)
                or len(first_line_text.split()) < TABLE_MIN_ROW_FRAGMENTS
            ):
                continue
            if any(char.isdigit() for char in first_line_text):
                continue
            if first_line_text.count(",") > 1:
                continue
        region_rect, region_text_blocks = _trim_table_region_at_heading_line(
            blocks=blocks,
            start_index=start_index,
            end_index=end_index,
            region_rect=region_rect,
            title_text=title_text,
            toc_sections=toc_sections,
            page_number=page.number + 1,
        )
        if not region_text_blocks:
            continue
        regions.append((region_rect, title_text, " ".join(region_text_blocks)))
    return _deduplicate_table_regions(regions)


def _build_table_block_profile(*, block_index: int, block: object) -> _TableBlockProfile:
    block_text = _block_text(block)
    line_count = 0
    x0_values: list[float] = []
    y_values: list[float] = []
    numeric_token_count = 0
    pipe_token_count = 0
    total_line_length = 0.0
    leading_label_colon = False

    for line in _block_lines(block):
        line_text = _line_text(line).strip()
        if not line_text:
            continue
        line_rect = _line_rect(line)
        line_count += 1
        x0_values.append(float(line_rect.x0))
        y_values.append(float(line_rect.y0))
        total_line_length += float(len(line_text))
        numeric_token_count += sum(
            1
            for token in line_text.split()
            if any(char.isdigit() for char in token) or "/" in token
        )
        pipe_token_count += line_text.count("|")
        if (
            line_text.endswith(":")
            or line_text.upper().startswith("NOTE:")
            or line_text.upper().startswith("KEEPER")
        ):
            leading_label_colon = True

    return _TableBlockProfile(
        block_index=block_index,
        block=block,
        line_count=line_count,
        x0_clusters=_cluster_count(x0_values),
        row_fragment_count=_max_cluster_size(y_values, tolerance=2.5),
        numeric_token_count=numeric_token_count,
        pipe_token_count=pipe_token_count,
        average_line_length=(total_line_length / line_count) if line_count else 0.0,
        has_leading_label_colon=leading_label_colon or _has_leading_label_colon(block_text),
    )


def _block_text(block: object) -> str:
    text = cast(
        str | None,
        block.get("text") if isinstance(block, dict) else getattr(block, "text", None),
    )
    if text is not None:
        return text
    if isinstance(block, dict):
        block_text_parts: list[str] = []
        for line in cast(list[dict[str, object]], block.get("lines", [])):
            block_text_parts.append(_line_text(line))
        return " ".join(part for part in block_text_parts if part).strip()
    return ""


def _block_first_line_text(block: object) -> str:
    lines = _block_lines(block)
    if not lines:
        return _block_text(block)
    return _line_text(lines[0]).strip()


def _block_rect(block: object) -> fitz.Rect:
    bbox = cast(
        list[float] | tuple[float, ...] | None,
        block.get("bbox") if isinstance(block, dict) else getattr(block, "bbox", None),
    )
    if bbox is None:
        return fitz.Rect(0, 0, 0, 0)
    return fitz.Rect(*bbox)


def _block_lines(block: object) -> list[dict[str, object]]:
    if isinstance(block, dict):
        return cast(list[dict[str, object]], block.get("lines", []))
    return []


def _line_text(line: object) -> str:
    if isinstance(line, dict):
        return "".join(
            cast(str, span.get("text", ""))
            for span in cast(list[dict[str, object]], line.get("spans", []))
        )
    return cast(str, getattr(line, "text", ""))


def _line_rect(line: object) -> fitz.Rect:
    if isinstance(line, dict):
        bbox = cast(list[float] | tuple[float, ...] | None, line.get("bbox"))
        if bbox is not None:
            return fitz.Rect(*bbox)
    bbox = cast(list[float] | tuple[float, ...] | None, getattr(line, "bbox", None))
    if bbox is None:
        return fitz.Rect(0, 0, 0, 0)
    return fitz.Rect(*bbox)


def _block_first_font_size(block: object) -> float:
    lines = _block_lines(block)
    if not lines:
        return 0.0
    first_line = lines[0]
    spans = cast(list[dict[str, object]], first_line.get("spans", []))
    if not spans:
        return 0.0
    sizes = [float(cast(float | int, span.get("size", 0.0))) for span in spans if span.get("size")]
    return max(sizes) if sizes else 0.0


def _trim_table_region_at_heading_line(  # noqa: PLR0913
    *,
    blocks: list[dict[str, object]],
    start_index: int,
    end_index: int,
    region_rect: fitz.Rect,
    title_text: str,
    toc_sections: list[dict[str, object]] | None,
    page_number: int,
) -> tuple[fitz.Rect, list[str]]:
    region_text_blocks: list[str] = []
    trimmed_rect: fitz.Rect | None = None
    for block_index in range(start_index, end_index + 1):
        block = blocks[block_index]
        block_lines = _block_lines(block)
        if not block_lines:
            continue
        line_rects: list[fitz.Rect] = []
        for line_index, line in enumerate(block_lines):
            line_text = _line_text(line).strip()
            if not line_text:
                continue
            if block_index != start_index or line_index > 0:
                line_font_size = _line_font_size(line)
                previous_font_size = (
                    _line_font_size(block_lines[line_index - 1])
                    if line_index > 0
                    else _block_first_font_size(blocks[block_index - 1])
                    if block_index > 0
                    else 0.0
                )
                if _is_next_section_heading(
                    next_text=line_text,
                    next_font_size=line_font_size,
                    current_font_size=previous_font_size,
                    toc_sections=toc_sections,
                    page_number=page_number,
                ):
                    if line_rects:
                        trimmed_rect = _union_with_base(trimmed_rect, line_rects)
                    return trimmed_rect or region_rect, region_text_blocks
            region_text_blocks.append(line_text)
            line_rects.append(_line_rect(line))
        if line_rects:
            trimmed_rect = _union_with_base(trimmed_rect, line_rects)
    return trimmed_rect or region_rect, region_text_blocks


def _line_font_size(line: object) -> float:
    if isinstance(line, dict):
        spans = cast(list[dict[str, object]], line.get("spans", []))
        sizes = [
            float(cast(float | int, span.get("size", 0.0)))
            for span in spans
            if span.get("size")
        ]
        return max(sizes) if sizes else 0.0
    return 0.0


def _rect_union(rects: list[fitz.Rect]) -> fitz.Rect:
    combined = rects[0]
    for rect in rects[1:]:
        combined = combined | rect
    return combined


def _union_with_base(
    base_rect: fitz.Rect | None,
    rects: list[fitz.Rect],
) -> fitz.Rect:
    combined_rect = _rect_union(rects)
    if base_rect is None:
        return combined_rect
    return base_rect | combined_rect


def _should_stop_table_region(  # noqa: PLR0913,PLR0911
    *,
    page_number: int,
    start_block: object,
    current_block: object,
    next_block: object,
    next_profile: _TableBlockProfile,
    toc_sections: list[dict[str, object]] | None,
) -> bool:
    current_rect = _block_rect(current_block)
    next_rect = _block_rect(next_block)
    same_column = _same_text_column(current_rect, next_rect)
    if next_rect.y0 - current_rect.y1 > TABLE_REGION_GAP:
        return True
    if next_profile.is_clear_prose:
        return True

    next_text = _block_text(next_block).strip()
    next_font_size = _block_first_font_size(next_block)
    current_font_size = _block_first_font_size(current_block)
    if _is_next_section_heading(
        next_text=next_text,
        next_font_size=next_font_size,
        current_font_size=current_font_size,
        toc_sections=toc_sections,
        page_number=page_number,
    ):
        return True
    if _block_looks_like_table_continuation(next_profile=next_profile, next_text=next_text):
        return False
    if not same_column:
        return False
    return (
        not next_profile.is_table_like
        and len(next_text) <= TABLE_WEAK_TEXT_MAX_LENGTH
        and next_profile.line_count <= TABLE_MIN_ROW_FRAGMENTS
    ) or (
        not next_profile.is_table_like
        and next_profile.line_count >= TABLE_MIN_ROW_FRAGMENTS
        and next_rect.y0 - current_rect.y1 > TABLE_WEAK_REGION_GAP
    )


def _block_looks_like_table_continuation(
    *,
    next_profile: _TableBlockProfile,
    next_text: str,
) -> bool:
    if next_profile.is_table_like:
        return True
    if next_profile.line_count < TABLE_MIN_ROW_FRAGMENTS:
        return False
    if next_profile.has_leading_label_colon:
        return True
    if next_profile.numeric_token_count > 0 or next_profile.pipe_token_count > 0:
        return True
    return (
        next_profile.x0_clusters >= TABLE_MIN_ROW_FRAGMENTS
        and len(next_text) <= TABLE_MAX_NUMERIC_AVG_LINE_LENGTH
    )


def _toc_sections_starting_on_page(
    toc_sections: list[object] | None,
    page_number: int,
) -> list[dict[str, object]]:
    if toc_sections is None:
        return []
    return [
        cast(dict[str, object], section)
        for section in toc_sections
        if isinstance(section, dict) and section.get("start_page") == page_number
    ]


def _is_next_section_heading(
    *,
    next_text: str,
    next_font_size: float,
    current_font_size: float,
    toc_sections: list[dict[str, object]] | None,
    page_number: int,
) -> bool:
    if not next_text:
        return False
    stripped = " ".join(next_text.split())
    if len(stripped) > TABLE_HEADING_TEXT_MAX_LENGTH:
        return False
    if len(stripped.split()) > TABLE_MIN_ROW_FRAGMENTS:
        return False
    if (
        next_font_size
        and current_font_size
        and next_font_size - current_font_size >= TABLE_HEADING_FONT_DELTA
    ):
        return True
    if toc_sections:
        return any(
            _section_matches_heading(section, stripped, page_number)
            for section in toc_sections
        )
    return False


def _section_matches_heading(
    section: dict[str, object],
    heading_text: str,
    page_number: int,
) -> bool:
    if section.get("start_page") != page_number:
        return False
    title = str(section.get("title", "")).strip()
    if not title:
        return False
    return heading_text.lower() == title.lower() or heading_text.lower().startswith(title.lower())


def _cluster_count(values: list[float], *, tolerance: float = 8.0) -> int:
    if not values:
        return 0
    clusters = 0
    ordered = sorted(values)
    current_anchor = ordered[0]
    for value in ordered[1:]:
        if abs(value - current_anchor) > tolerance:
            clusters += 1
            current_anchor = value
    return clusters + 1


def _max_cluster_size(values: list[float], *, tolerance: float = 8.0) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    max_size = 1
    current_size = 1
    current_anchor = ordered[0]
    for value in ordered[1:]:
        if abs(value - current_anchor) <= tolerance:
            current_size += 1
            continue
        max_size = max(max_size, current_size)
        current_anchor = value
        current_size = 1
    return max(max_size, current_size)


def _has_leading_label_colon(text: str) -> bool:
    stripped = " ".join(text.split())
    if not stripped:
        return False
    first_token = stripped.split(" ", 1)[0]
    return first_token.endswith(":") and len(first_token) <= TABLE_MAX_TITLE_LABEL_LENGTH


def _looks_like_table_title(text: str) -> bool:
    stripped = " ".join(text.split())
    if not stripped:
        return False
    if len(stripped.split()) > TABLE_MAX_TITLE_WORDS:
        return False
    return stripped[0].isupper() and any(char.isalpha() for char in stripped)


def _deduplicate_table_regions(
    regions: list[tuple[fitz.Rect, str, str]],
) -> list[tuple[fitz.Rect, str, str]]:
    deduplicated: list[tuple[fitz.Rect, str, str]] = []
    for region in regions:
        rect, title_text, data_text = region
        if any(rect.intersects(existing_rect) for existing_rect, _, _ in deduplicated):
            continue
        deduplicated.append((rect, title_text, data_text))
    return deduplicated


def build_resolved_guidance(
    proposals: list[AnnotationProposal],
) -> PrepGuidanceResolved:
    """Normalize proposals into deterministic resolved guidance targets."""
    skip_pages: list[int] = []
    skip_regions: list[dict[str, object]] = []
    table_regions: list[dict[str, object]] = []
    callout_regions: list[dict[str, object]] = []

    for proposal in sorted(
        proposals,
        key=lambda item: (item.page, item.label, item.proposal_id),
    ):
        region = _proposal_region_payload(proposal)
        if proposal.label == "skip":
            if proposal.metadata.get("scope") == "full-page":
                if proposal.page not in skip_pages:
                    skip_pages.append(proposal.page)
                continue
            skip_regions.append(region)
            continue
        if proposal.label == "table":
            table_regions.append(region)
            continue
        if proposal.label == "callout":
            callout_regions.append(_callout_region_payload(proposal))

    resolved = PrepGuidanceResolved(
        skip_pages=skip_pages,
        skip_regions=skip_regions,
        table_regions=table_regions,
        callout_regions=callout_regions,
    )
    resolved.validate()
    return resolved


def build_annotation_review_edits(
    *,
    review_mode: str,
    skip_ranges_input: str,
    skip_pages_explicit: list[int],
) -> AnnotationReviewEdits:
    """Seed review edits with the default status for the requested review mode."""
    review_status = _review_status_for_mode(review_mode)
    edits = AnnotationReviewEdits(
        review_mode=review_mode,
        review_status=review_status,
        skip_ranges_input=skip_ranges_input,
        skip_pages_explicit=list(skip_pages_explicit),
        proposal_decisions={},
        updated_regions={},
        notes="",
    )
    edits.validate()
    return edits


def apply_review_edits_to_proposals(
    proposals: list[AnnotationProposal],
    edits: AnnotationReviewEdits,
) -> list[AnnotationProposal]:
    """Apply review decisions to raw proposals while preserving proposal IDs."""
    reviewed_proposals: list[AnnotationProposal] = []
    for proposal in proposals:
        decision = edits.proposal_decisions.get(proposal.proposal_id, "accept")
        if decision == "reject":
            continue
        if decision == "edit":
            reviewed_proposals.append(
                _apply_review_region_update(proposal, edits.updated_regions)
            )
            continue
        reviewed_proposals.append(proposal)
    return reviewed_proposals


def build_final_resolved_guidance(
    *,
    proposals: list[AnnotationProposal],
    skip_pages_explicit: list[int],
    review_mode: str,
    review_status: str,
    skip_ranges_input: str,
) -> PrepGuidanceResolved:
    """Normalize reviewed proposals into final resolved guidance."""
    _validate_review_choice(review_mode, "AnnotationReviewEdits.review_mode")
    _validate_review_status(review_status, "AnnotationReviewEdits.review_status")
    if not isinstance(skip_ranges_input, str):
        raise ValueError("AnnotationReviewEdits.skip_ranges_input must be a string")

    skip_pages: set[int] = set(
        _validate_review_page_list(
            skip_pages_explicit or [],
            "AnnotationReviewEdits.skip_pages_explicit",
        )
    )
    skip_regions: list[dict[str, object]] = []
    table_regions: list[dict[str, object]] = []
    callout_regions: list[dict[str, object]] = []

    for proposal in sorted(
        proposals,
        key=lambda item: (item.page, item.label, item.proposal_id),
    ):
        if proposal.label == "skip":
            if proposal.metadata.get("scope") == "full-page":
                skip_pages.add(proposal.page)
                continue
            skip_regions.append(_proposal_region_payload(proposal))

    for proposal in sorted(
        proposals,
        key=lambda item: (item.page, item.label, item.proposal_id),
    ):
        if proposal.label == "skip":
            continue
        if proposal.page in skip_pages:
            continue
        if _proposal_overlaps_skip_region(proposal, skip_regions):
            continue
        if proposal.label == "table":
            table_regions.append(_proposal_region_payload(proposal))
        elif proposal.label == "callout":
            callout_regions.append(_callout_region_payload(proposal))

    resolved = PrepGuidanceResolved(
        skip_pages=sorted(skip_pages),
        skip_regions=skip_regions,
        table_regions=table_regions,
        callout_regions=callout_regions,
    )
    resolved.validate()
    return resolved


def render_annotated_prep_pdf(
    *,
    pdf_path: Path,
    proposals: list[AnnotationProposal],
    output_pdf_path: Path,
) -> None:
    """Render a lightweight annotated PDF for review."""
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return

    page_count = len(doc)
    for proposal in sorted(
        proposals,
        key=lambda item: (item.page, item.label, item.proposal_id),
    ):
        if proposal.page < 1 or proposal.page > page_count:
            continue
        page = doc[proposal.page - 1]
        rect = fitz.Rect(*proposal.bbox)
        fill_color = TABLE_LIGHT_BLUE_FILL if proposal.label == "table" else (1, 1, 0)
        annot = page.add_freetext_annot(
            rect,
            f"{proposal.proposal_id} {proposal.label}",
            fontsize=6,
            fontname="helv",
            text_color=(0, 0, 0),
            fill_color=fill_color,
            border_width=1,
            opacity=0.5,
            align=2,
        )
        annot.set_info(
            title=proposal.proposal_id,
            subject=proposal.label,
        )
        annot.update()
    try:
        doc.save(output_pdf_path, garbage=4, clean=True, deflate=True)
    except Exception:
        return
    finally:
        doc.close()


def _build_proposal(
    *,
    label: str,
    page: int,
    bbox: list[float],
    confidence: float,
    metadata: dict[str, object],
) -> AnnotationProposal:
    proposal_id = _build_proposal_id(
        label=label,
        page=page,
        bbox=bbox,
        metadata=metadata,
    )
    proposal = AnnotationProposal(
        proposal_id=proposal_id,
        label=label,
        page=page,
        bbox=[float(value) for value in bbox],
        confidence=confidence,
        metadata=dict(metadata),
    )
    proposal.validate()
    return proposal


def _build_proposal_id(
    *,
    label: str,
    page: int,
    bbox: list[float],
    metadata: dict[str, object],
) -> str:
    serialized_metadata = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(
        f"{label}|{page}|{json.dumps(bbox)}|{serialized_metadata}".encode(),
        usedforsecurity=False,
    ).hexdigest()[:12]
    return f"ap-{digest}"


def _normalize_chunk_entries(
    chunk_plan: Mapping[str, object] | None,
) -> list[_ChunkEntry]:
    if chunk_plan is None:
        return []
    chunks = chunk_plan.get("chunks")
    if not isinstance(chunks, list):
        return []

    normalized: list[_ChunkEntry] = []
    for entry in chunks:
        if not isinstance(entry, dict):
            continue
        start_page = entry.get("start_page")
        end_page = entry.get("end_page")
        ordinal = entry.get("ordinal")
        source_section_id = entry.get("source_section_id")
        chunk_kind = entry.get("chunk_kind")
        if not isinstance(start_page, int) or isinstance(start_page, bool) or start_page < 1:
            continue
        if not isinstance(end_page, int) or isinstance(end_page, bool) or end_page < start_page:
            continue
        if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 1:
            continue
        if not isinstance(source_section_id, str) or not source_section_id:
            continue
        if not isinstance(chunk_kind, str) or not chunk_kind:
            continue
        normalized.append(
            _ChunkEntry(
                source_section_id=source_section_id,
                start_page=start_page,
                end_page=end_page,
                chunk_kind=chunk_kind,
                ordinal=ordinal,
            )
        )
    return sorted(
        normalized,
        key=lambda entry: (
            entry["start_page"],
            entry["end_page"],
            entry["ordinal"],
            entry["source_section_id"],
        ),
    )


def _detect_trailing_appendix_skip_pages(
    chunk_entries: list[_ChunkEntry],
) -> list[int]:
    if len(chunk_entries) < TRAILING_APPENDIX_MIN_CHUNKS:
        return []

    trailing_pages: list[int] = []
    for chunk_entry in reversed(chunk_entries[1:]):
        if chunk_entry["chunk_kind"] != "appendix":
            break
        start_page = chunk_entry["start_page"]
        end_page = chunk_entry["end_page"]
        if start_page != end_page:
            break
        trailing_pages.append(start_page)
    return sorted(trailing_pages)


def _load_guidance_defaults(path: Path) -> PrepGuidanceInput:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("prep-guidance.defaults.yml must contain a mapping")
    return PrepGuidanceInput.from_dict(payload)


def _load_page_count(path: Path) -> int:
    payload = _load_required_json_mapping(path)
    page_count = payload.get("page_count")
    if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 1:
        raise ValueError("metadata.json must contain page_count as an integer >= 1")
    return page_count


def _load_images_total_count(path: Path) -> int:
    payload = _load_required_json_mapping(path)
    total_count = payload.get("total_count")
    if not isinstance(total_count, int) or isinstance(total_count, bool) or total_count < 0:
        raise ValueError("images/image-manifest.json must contain total_count as an integer >= 0")
    return total_count


def _load_toc_sections(path: Path, *, page_count: int) -> list[dict[str, object]]:
    if not path.exists():
        return []
    sections = load_toc_sections(path, page_count=page_count)
    return [section.to_dict() for section in sections]


def _load_required_json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def _load_optional_json_mapping(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return _load_required_json_mapping(path)


def _load_annotation_proposals(path: Path) -> list[AnnotationProposal]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("annotation-proposals.json must contain a JSON array")
    proposals: list[AnnotationProposal] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("annotation-proposals.json entries must be JSON objects")
        proposals.append(AnnotationProposal.from_dict(item))
    return proposals


def _load_effective_annotation_proposals(
    analysis_paths: PrepAnalysisArtifactPaths,
) -> list[AnnotationProposal]:
    refined_path = analysis_paths.annotation_refined_proposals
    if refined_path.exists():
        return _load_annotation_proposals(refined_path)
    return _load_annotation_proposals(analysis_paths.annotation_proposals)


def _load_annotation_review_edits(path: Path) -> AnnotationReviewEdits:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("annotation-review.edits.json must contain a JSON object")
    return AnnotationReviewEdits.from_dict(payload)


def load_effective_prep_guidance(
    analysis_paths: PrepAnalysisArtifactPaths,
) -> PrepGuidanceResolved:
    """Load reviewed guidance when present, otherwise the baseline resolved guidance."""
    guidance_path = (
        analysis_paths.reviewed_guidance
        if analysis_paths.reviewed_guidance.exists()
        else analysis_paths.guidance_resolved
    )
    payload = json.loads(guidance_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{guidance_path.name} must contain a JSON object")
    return PrepGuidanceResolved.from_dict(payload)


def _parse_skip_page_token(token: str) -> int:
    if not token.isdigit():
        raise ValueError(f"Invalid skip range token: '{token}'")
    return int(token)


def _validate_skip_page(page: int, *, page_count: int) -> None:
    if page < 1 or page > page_count:
        raise ValueError(f"Skip page {page} is outside document bounds 1-{page_count}")


def _filter_annotation_proposals(
    proposals: list[AnnotationProposal],
    *,
    guidance_input: PrepGuidanceInput,
) -> list[AnnotationProposal]:
    filtered: list[AnnotationProposal] = []
    for proposal in proposals:
        if proposal.label == "table" and not guidance_input.prefer_detect_tables:
            continue
        if proposal.label == "callout" and not guidance_input.prefer_detect_callouts:
            continue
        if (
            proposal.label == "skip"
            and proposal.metadata.get("scope") == "full-page"
            and not guidance_input.prefer_skip_full_page_artifacts
        ):
            continue
        filtered.append(proposal)
    return filtered


def _maybe_refine_callout_proposals(
    *,
    analysis_paths: PrepAnalysisArtifactPaths,
    proposals: list[AnnotationProposal],
    refinement_entries: list[CalloutRefinementCropEntry],
    skip_callout_refinement: bool,
) -> list[AnnotationProposal] | None:
    if skip_callout_refinement:
        typer.echo("INFO: Callout refinement skipped by explicit flag")
        _remove_file_if_exists(analysis_paths.annotation_refined_proposals)
        return None

    selected_agent = build_callout_refinement_agent()
    if selected_agent is None:
        typer.echo(
            "INFO: Callout refinement skipped because the active agent "
            "cannot inspect images"
        )
        _remove_file_if_exists(analysis_paths.annotation_refined_proposals)
        return None
    if not refinement_entries:
        _remove_file_if_exists(analysis_paths.annotation_refined_proposals)
        return None

    refined_proposals, decisions = refine_callout_proposals(
        proposals=proposals,
        crop_entries=refinement_entries,
        agent=selected_agent,
        skip_refinement=False,
    )
    if decisions:
        analysis_paths.annotation_refined_proposals.write_text(
            json.dumps(
                [proposal.to_dict() for proposal in refined_proposals],
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    return refined_proposals


def _remove_file_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()


def _review_status_for_mode(review_mode: str) -> str:
    _validate_review_choice(review_mode, "AnnotationReviewEdits.review_mode")
    return {
        "interactive": "pending",
        "auto_accept": "auto_accepted",
        "bypass": "accepted",
    }[review_mode]


def _apply_review_region_update(
    proposal: AnnotationProposal,
    updated_regions: dict[str, dict[str, object]],
) -> AnnotationProposal:
    updated_region = updated_regions.get(proposal.proposal_id)
    if updated_region is None:
        raise ValueError(
            f"AnnotationReviewEdits.updated_regions.{proposal.proposal_id} is required"
        )
    reviewed_proposal = AnnotationProposal(
        proposal_id=proposal.proposal_id,
        label=cast(str, updated_region["label"]),
        page=cast(int, updated_region["page"]),
        bbox=list(cast(list[float], updated_region["bbox"])),
        confidence=proposal.confidence,
        metadata=dict(proposal.metadata),
    )
    reviewed_proposal.validate()
    return reviewed_proposal


def _proposal_region_payload(proposal: AnnotationProposal) -> dict[str, object]:
    return {
        "page": proposal.page,
        "bbox": [float(value) for value in proposal.bbox],
        "proposal_id": proposal.proposal_id,
    }


def _callout_region_payload(proposal: AnnotationProposal) -> dict[str, object]:
    region = _proposal_region_payload(proposal)
    region["label"] = _callout_region_label(proposal)
    return region


def _callout_region_label(proposal: AnnotationProposal) -> str:
    metadata_label = proposal.metadata.get("callout_label")
    if metadata_label is None:
        return DEFAULT_CALLOUT_REGION_LABEL
    if not isinstance(metadata_label, str) or metadata_label not in CALLOUT_REGION_LABELS:
        options = ", ".join(sorted(CALLOUT_REGION_LABELS))
        raise ValueError(
            f"AnnotationProposal.metadata.callout_label must be one of {options}"
        )
    return metadata_label


def _proposal_overlaps_skip_region(
    proposal: AnnotationProposal,
    skip_regions: list[dict[str, object]],
) -> bool:
    for skip_region in skip_regions:
        if proposal.page != skip_region["page"]:
            continue
        if _bbox_intersects(proposal.bbox, cast(list[float], skip_region["bbox"])):
            return True
    return False


def _bbox_intersects(first_bbox: list[float], second_bbox: list[float]) -> bool:
    first_left, first_top, first_right, first_bottom = first_bbox
    second_left, second_top, second_right, second_bottom = second_bbox
    return not (
        first_right <= second_left
        or second_right <= first_left
        or first_bottom <= second_top
        or second_bottom <= first_top
    )


def _validate_review_choice(value: object, field_name: str) -> str:
    if not isinstance(value, str) or value not in ANNOTATION_REVIEW_MODES:
        options = ", ".join(sorted(ANNOTATION_REVIEW_MODES))
        raise ValueError(f"{field_name} must be one of {options}")
    return value


def _validate_review_status(value: object, field_name: str) -> str:
    if not isinstance(value, str) or value not in ANNOTATION_REVIEW_STATUSES:
        options = ", ".join(sorted(ANNOTATION_REVIEW_STATUSES))
        raise ValueError(f"{field_name} must be one of {options}")
    return value


def _validate_review_page_list(value: object, field_name: str) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    pages: list[int] = []
    for item in value:
        if not isinstance(item, int) or isinstance(item, bool) or item < 1:
            raise ValueError(f"{field_name} entries must be integers >= 1")
        pages.append(item)
    return pages
