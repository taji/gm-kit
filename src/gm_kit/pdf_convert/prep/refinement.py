from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import fitz  # type: ignore[import-untyped]
from PIL import Image

from gm_kit.pdf_convert.prep.callout_detection import CalloutRefinementHint, _same_text_column
from gm_kit.pdf_convert.prep.contracts import AnnotationProposal, PrepGuidanceInput

_DEFAULT_REFINEMENT_DPI = 150
_REFINEMENT_MODE_ENV = "GMKIT_CALL_OUT_REFINEMENT_MODE"
_SUPPORTED_REFINEMENT_MODES = {"mock", "skip", "vision", "handoff"}
_WHITE_CHANNEL_THRESHOLD = 245


@dataclass(frozen=True)
class CalloutRefinementCropEntry:
    proposal_id: str
    page: int
    bbox: list[float]
    anchor_phrase: str
    anchor_text: str
    issue: str
    collected_block_count: int
    image_path: str
    source_pdf_path: str
    crop_rect: list[float]

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "page": self.page,
            "bbox": [float(value) for value in self.bbox],
            "anchor_phrase": self.anchor_phrase,
            "anchor_text": self.anchor_text,
            "issue": self.issue,
            "collected_block_count": self.collected_block_count,
            "image_path": self.image_path,
            "source_pdf_path": self.source_pdf_path,
            "crop_rect": [float(value) for value in self.crop_rect],
        }


@dataclass(frozen=True)
class TableRefinementCropEntry:
    proposal_id: str
    page: int
    bbox: list[float]
    table_title: str
    table_text: str
    image_path: str
    source_pdf_path: str
    crop_rect: list[float]

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "page": self.page,
            "bbox": [float(value) for value in self.bbox],
            "table_title": self.table_title,
            "table_text": self.table_text,
            "image_path": self.image_path,
            "source_pdf_path": self.source_pdf_path,
            "crop_rect": [float(value) for value in self.crop_rect],
        }


@dataclass(frozen=True)
class CalloutRefinementDecision:
    proposal_id: str
    page: int
    action: str
    bbox: list[float]
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "page": self.page,
            "action": self.action,
            "bbox": [float(value) for value in self.bbox],
            "reason": self.reason,
        }


class PrepRefinementPause(BaseException):
    """Signal that prep has requested an external refinement handoff."""

    def __init__(self, request_path: str, recovery: str) -> None:
        self.request_path = request_path
        self.recovery = recovery
        super().__init__("Prep callout refinement awaiting external output")


class CalloutRefinementAgent(Protocol):
    def refine(
        self,
        *,
        proposal: AnnotationProposal,
        crop_entry: CalloutRefinementCropEntry,
    ) -> CalloutRefinementDecision:
        ...


@dataclass(frozen=True)
class MockCalloutRefinementAgent:
    """Deterministic, low-fidelity refinement proxy for tests and offline validation.

    This is intentionally rough: it exists to prove the analyze-flow contract,
    keep the pipeline moving, and provide a stable fallback for CI. It is not
    intended to match real agent quality.
    """

    def refine(
        self,
        *,
        proposal: AnnotationProposal,
        crop_entry: CalloutRefinementCropEntry,
    ) -> CalloutRefinementDecision:
        return _refine_callout_crop_with_mock_agent(proposal, crop_entry)


@dataclass(frozen=True)
class VisionCalloutRefinementAgent:
    """Placeholder for a real image-capable refinement backend."""

    def refine(
        self,
        *,
        proposal: AnnotationProposal,
        crop_entry: CalloutRefinementCropEntry,
    ) -> CalloutRefinementDecision:
        raise NotImplementedError(
            "Vision callout refinement agent is not wired yet"
        )


def build_callout_refinement_agent(
    refinement_mode: str | None = None,
) -> CalloutRefinementAgent | None:
    """Select a refinement adapter based on mode or environment."""
    mode = (
        os.environ.get(_REFINEMENT_MODE_ENV, "mock")
        if refinement_mode is None
        else refinement_mode
    )
    normalized_mode = mode.strip().lower()
    if normalized_mode not in _SUPPORTED_REFINEMENT_MODES:
        normalized_mode = "mock"
    if normalized_mode == "skip":
        return None
    if normalized_mode == "handoff":
        return None
    if normalized_mode == "mock":
        return MockCalloutRefinementAgent()
    if normalized_mode == "vision":
        return VisionCalloutRefinementAgent()
    return MockCalloutRefinementAgent()


def build_callout_refinement_inputs(  # noqa: PLR0913
    *,
    pdf_path: Path,
    proposals: list[AnnotationProposal],
    refinement_hints: list[CalloutRefinementHint],
    guidance_input: PrepGuidanceInput,
    manifest_path: Path,
    crops_dir: Path,
    dpi: int = _DEFAULT_REFINEMENT_DPI,
) -> list[CalloutRefinementCropEntry]:
    """Render source-PDF crops for callout proposals that need refinement."""
    guidance_input.validate()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    crops_dir.mkdir(parents=True, exist_ok=True)

    proposal_by_id = {proposal.proposal_id: proposal for proposal in proposals}
    eligible_hints = [
        hint
        for hint in refinement_hints
        if hint.issue == "expanded_across_multiple_text_blocks"
        and hint.proposal_id in proposal_by_id
    ]

    entries: list[CalloutRefinementCropEntry] = []
    doc = fitz.open(pdf_path)
    try:
        for hint in eligible_hints:
            proposal = proposal_by_id[hint.proposal_id]
            if proposal.page < 1 or proposal.page > len(doc):
                continue

            page = doc[proposal.page - 1]
            crop_rect = _expanded_callout_crop_rect(
                page=page,
                bbox=proposal.bbox,
                padding=guidance_input.callout_bbox_padding,
                max_vertical_gap=guidance_input.callout_max_vertical_gap,
            )
            crop_path = crops_dir / f"callout-{proposal.proposal_id}_p{proposal.page:03d}.png"
            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0),
                clip=crop_rect,
                alpha=False,
            )
            pixmap.save(crop_path)

            entries.append(
                CalloutRefinementCropEntry(
                    proposal_id=proposal.proposal_id,
                    page=proposal.page,
                    bbox=[float(value) for value in proposal.bbox],
                    anchor_phrase=hint.anchor_phrase,
                    anchor_text=hint.anchor_text,
                    issue=hint.issue,
                    collected_block_count=hint.collected_block_count,
                    image_path=str(crop_path),
                    source_pdf_path=str(pdf_path),
                    crop_rect=[
                        float(crop_rect.x0),
                        float(crop_rect.y0),
                        float(crop_rect.x1),
                        float(crop_rect.y1),
                    ],
                )
            )
    finally:
        doc.close()

    manifest_payload: dict[str, Any] = {
        "source_pdf_path": str(pdf_path),
        "candidate_count": len(entries),
        "crops_dir": str(crops_dir),
        "items": [entry.to_dict() for entry in entries],
    }
    manifest_path.write_text(
        json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return entries


def build_table_refinement_inputs(  # noqa: PLR0913
    *,
    pdf_path: Path,
    proposals: list[AnnotationProposal],
    guidance_input: PrepGuidanceInput,
    manifest_path: Path,
    crops_dir: Path,
    dpi: int = _DEFAULT_REFINEMENT_DPI,
) -> list[TableRefinementCropEntry]:
    """Render source-PDF crops for table proposals."""
    guidance_input.validate()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    crops_dir.mkdir(parents=True, exist_ok=True)

    entries: list[TableRefinementCropEntry] = []
    doc = fitz.open(pdf_path)
    try:
        for proposal in proposals:
            if proposal.label != "table":
                continue
            if proposal.page < 1 or proposal.page > len(doc):
                continue
            page = doc[proposal.page - 1]
            table_padding = _table_crop_padding(guidance_input.callout_bbox_padding)
            crop_rect = _expanded_crop_rect(
                proposal.bbox,
                page.rect,
                table_padding,
            )
            crop_path = crops_dir / f"table-{proposal.proposal_id}_p{proposal.page:03d}.png"
            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0),
                clip=crop_rect,
                alpha=False,
            )
            pixmap.save(crop_path)
            metadata = proposal.metadata
            entries.append(
                TableRefinementCropEntry(
                    proposal_id=proposal.proposal_id,
                    page=proposal.page,
                    bbox=[float(value) for value in proposal.bbox],
                    table_title=str(metadata.get("table_title", "")),
                    table_text=str(metadata.get("table_text", "")),
                    image_path=str(crop_path),
                    source_pdf_path=str(pdf_path),
                    crop_rect=[
                        float(crop_rect.x0),
                        float(crop_rect.y0),
                        float(crop_rect.x1),
                        float(crop_rect.y1),
                    ],
                )
            )
    finally:
        doc.close()

    manifest_payload: dict[str, Any] = {
        "source_pdf_path": str(pdf_path),
        "candidate_count": len(entries),
        "crops_dir": str(crops_dir),
        "items": [entry.to_dict() for entry in entries],
    }
    manifest_path.write_text(
        json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return entries


def refine_callout_proposals(
    *,
    proposals: list[AnnotationProposal],
    crop_entries: list[CalloutRefinementCropEntry],
    agent: CalloutRefinementAgent | None = None,
    skip_refinement: bool = False,
) -> tuple[list[AnnotationProposal], list[CalloutRefinementDecision]]:
    """Refine eligible callout proposals using the local mock vision agent."""
    if skip_refinement:
        return proposals, []

    selected_agent = agent if agent is not None else build_callout_refinement_agent()
    if selected_agent is None:
        return proposals, []

    proposal_by_id = {proposal.proposal_id: proposal for proposal in proposals}
    refined_proposals = list(proposals)
    decisions: list[CalloutRefinementDecision] = []

    for crop_entry in crop_entries:
        proposal = proposal_by_id.get(crop_entry.proposal_id)
        if proposal is None:
            continue
        decision = selected_agent.refine(proposal=proposal, crop_entry=crop_entry)
        decisions.append(decision)
        refined_proposals = [
            decision_proposal
            if decision_proposal.proposal_id != decision.proposal_id
            else _apply_refined_bbox(decision_proposal, decision.bbox)
            for decision_proposal in refined_proposals
        ]

    return refined_proposals, decisions


def _refine_callout_crop_with_mock_agent(
    proposal: AnnotationProposal,
    crop_entry: CalloutRefinementCropEntry,
) -> CalloutRefinementDecision:
    with Image.open(crop_entry.image_path) as image:
        non_white_bbox = _find_non_white_bbox(image)
        if non_white_bbox is None:
            return CalloutRefinementDecision(
                proposal_id=proposal.proposal_id,
                page=proposal.page,
                action="leave_unchanged",
                bbox=[float(value) for value in proposal.bbox],
                reason="crop_has_no_visible_content",
            )

        refined_bbox = _map_crop_bbox_to_pdf_points(
            non_white_bbox=non_white_bbox,
            image_size=image.size,
            crop_rect=crop_entry.crop_rect,
        )

    if _bbox_width(refined_bbox) <= 0 or _bbox_height(refined_bbox) <= 0:
        return CalloutRefinementDecision(
            proposal_id=proposal.proposal_id,
            page=proposal.page,
            action="leave_unchanged",
            bbox=[float(value) for value in proposal.bbox],
            reason="invalid_refined_bbox",
        )

    return CalloutRefinementDecision(
        proposal_id=proposal.proposal_id,
        page=proposal.page,
        action="refine",
        bbox=refined_bbox,
        reason="mock_agent_detected_tight_content_bounds",
    )


def _find_non_white_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    rgb_image = image.convert("RGB")
    width, height = rgb_image.size
    pixels = rgb_image.load()

    min_x = width
    min_y = height
    max_x = -1
    max_y = -1

    for y in range(height):
        for x in range(width):
            red, green, blue = pixels[x, y]
            if (
                red >= _WHITE_CHANNEL_THRESHOLD
                and green >= _WHITE_CHANNEL_THRESHOLD
                and blue >= _WHITE_CHANNEL_THRESHOLD
            ):
                continue
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)

    if max_x < 0 or max_y < 0:
        return None
    return min_x, min_y, max_x + 1, max_y + 1


def _map_crop_bbox_to_pdf_points(
    *,
    non_white_bbox: tuple[int, int, int, int],
    image_size: tuple[int, int],
    crop_rect: list[float],
) -> list[float]:
    image_width, image_height = image_size
    crop_left, crop_top, crop_right, crop_bottom = crop_rect
    crop_width = crop_right - crop_left
    crop_height = crop_bottom - crop_top
    if image_width <= 0 or image_height <= 0:
        return [float(crop_left), float(crop_top), float(crop_right), float(crop_bottom)]

    left_px, top_px, right_px, bottom_px = non_white_bbox
    scale_x = crop_width / image_width
    scale_y = crop_height / image_height
    return [
        float(crop_left + left_px * scale_x),
        float(crop_top + top_px * scale_y),
        float(crop_left + right_px * scale_x),
        float(crop_top + bottom_px * scale_y),
    ]


def _apply_refined_bbox(
    proposal: AnnotationProposal,
    bbox: list[float],
) -> AnnotationProposal:
    refined_proposal = AnnotationProposal(
        proposal_id=proposal.proposal_id,
        label=proposal.label,
        page=proposal.page,
        bbox=[float(value) for value in bbox],
        confidence=proposal.confidence,
        metadata=dict(proposal.metadata),
    )
    refined_proposal.validate()
    return refined_proposal


def _bbox_width(bbox: list[float]) -> float:
    return float(bbox[2] - bbox[0])


def _bbox_height(bbox: list[float]) -> float:
    return float(bbox[3] - bbox[1])


def _expanded_crop_rect(
    bbox: list[float],
    page_rect: fitz.Rect,
    padding: dict[str, float],
) -> fitz.Rect:
    rect = fitz.Rect(*bbox)
    expanded = fitz.Rect(
        rect.x0 - padding["left"],
        rect.y0 - padding["top"],
        rect.x1 + padding["right"],
        rect.y1 + padding["bottom"],
    )
    return fitz.Rect(
        max(page_rect.x0, expanded.x0),
        max(page_rect.y0, expanded.y0),
        min(page_rect.x1, expanded.x1),
        min(page_rect.y1, expanded.y1),
    )


def _table_crop_padding(base_padding: dict[str, float]) -> dict[str, float]:
    return {
        "left": max(base_padding["left"], 8.0),
        "top": max(base_padding["top"], 12.0),
        "right": max(base_padding["right"], 8.0),
        "bottom": max(base_padding["bottom"], 36.0),
    }


def _expanded_callout_crop_rect(
    *,
    page: fitz.Page,
    bbox: list[float],
    padding: dict[str, float],
    max_vertical_gap: float,
) -> fitz.Rect:
    page_rect = page.rect
    expanded = _expanded_crop_rect(bbox, page_rect, padding)
    blocks = [
        block
        for block in page.get_text("dict").get("blocks", [])
        if isinstance(block, dict) and block.get("type") == 0
    ]
    for block in sorted(blocks, key=lambda item: float(item.get("bbox", (0.0, 0.0, 0.0, 0.0))[1])):
        block_rect = fitz.Rect(*block.get("bbox", (0.0, 0.0, 0.0, 0.0)))
        if block_rect.y1 < expanded.y0:
            continue
        if block_rect.y0 - expanded.y1 > max_vertical_gap:
            break
        if not _same_text_column(expanded, block_rect):
            continue
        expanded = expanded | block_rect
    return fitz.Rect(
        max(page_rect.x0, expanded.x0),
        max(page_rect.y0, expanded.y0),
        min(page_rect.x1, expanded.x1),
        min(page_rect.y1, expanded.y1),
    )
