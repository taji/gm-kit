from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import fitz  # type: ignore[import-untyped]

from gm_kit.pdf_convert.prep.contracts import AnnotationProposal, PrepGuidanceInput

BBOX_COORDINATE_COUNT = 4
_WORD_NORMALIZER = re.compile(r"[^a-z0-9\s]")
_WHITESPACE_NORMALIZER = re.compile(r"\s+")
_MIN_HORIZONTAL_OVERLAP_RATIO = 0.25


@dataclass(frozen=True)
class _TextBlock:
    block_index: int
    text: str
    normalized_text: str
    rect: fitz.Rect


@dataclass(frozen=True)
class _TextLine:
    block_index: int
    line_index: int
    text: str
    normalized_text: str
    rect: fitz.Rect


@dataclass(frozen=True)
class CalloutDetectionResult:
    proposals: list[AnnotationProposal]
    warnings: list[str]
    refinement_hints: list[CalloutRefinementHint]


@dataclass(frozen=True)
class CalloutRefinementHint:
    proposal_id: str
    page: int
    issue: str
    anchor_phrase: str
    anchor_text: str
    collected_block_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "page": self.page,
            "issue": self.issue,
            "anchor_phrase": self.anchor_phrase,
            "anchor_text": self.anchor_text,
            "collected_block_count": self.collected_block_count,
        }


@dataclass(frozen=True)
class _PageDetectionContext:
    blocks: list[_TextBlock]
    lines: list[_TextLine]
    anchor_phrases: list[str]
    guidance_input: PrepGuidanceInput
    refinement_hints: list[CalloutRefinementHint]


def detect_callout_proposals(
    pdf_path: Path,
    guidance_input: PrepGuidanceInput,
) -> list[AnnotationProposal]:
    """Detect callout regions from PDF text anchors and return annotation proposals."""
    return detect_callout_proposals_with_warnings(
        pdf_path=pdf_path,
        guidance_input=guidance_input,
    ).proposals


def detect_callout_proposals_with_warnings(
    pdf_path: Path,
    guidance_input: PrepGuidanceInput,
) -> CalloutDetectionResult:
    """Detect callout regions and return any recovery warnings."""
    guidance_input.validate()
    if not guidance_input.prefer_detect_callouts:
        return CalloutDetectionResult(proposals=[], warnings=[], refinement_hints=[])

    anchor_phrases = [
        _normalize_anchor_phrase(anchor_phrase)
        for anchor_phrase in guidance_input.callout_anchor_phrases
    ]
    proposals: list[AnnotationProposal] = []
    warnings: list[str] = []
    refinement_hints: list[CalloutRefinementHint] = []
    doc = fitz.open(pdf_path)

    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            blocks = _extract_text_blocks(page)
            if not blocks:
                continue

            page_proposals, page_warnings = _detect_page_callout_proposals(
                page_number=page_index + 1,
                context=_PageDetectionContext(
                    blocks=blocks,
                    lines=_extract_text_lines(page),
                    anchor_phrases=anchor_phrases,
                    guidance_input=guidance_input,
                    refinement_hints=refinement_hints,
                ),
            )
            proposals.extend(page_proposals)
            warnings.extend(page_warnings)
    finally:
        doc.close()

    return CalloutDetectionResult(
        proposals=sorted(proposals, key=lambda proposal: proposal.proposal_id),
        warnings=warnings,
        refinement_hints=refinement_hints,
    )


def _detect_page_callout_proposals(
    *,
    page_number: int,
    context: _PageDetectionContext,
) -> tuple[list[AnnotationProposal], list[str]]:
    proposals: list[AnnotationProposal] = []
    warnings: list[str] = []

    for block_index, block in enumerate(context.blocks):
        matched_phrase = _match_anchor_phrase(block.normalized_text, context.anchor_phrases)
        if matched_phrase is None:
            continue

        region_rect, matched_block_indices = _collect_callout_region(
            blocks=context.blocks,
            start_index=block_index,
            anchor_phrases=context.anchor_phrases,
            max_vertical_gap=context.guidance_input.callout_max_vertical_gap,
        )
        proposals.append(
            _build_callout_proposal(
                page_number=page_number,
                bbox=_pad_rect(region_rect, context.guidance_input.callout_bbox_padding),
                anchor_phrase=matched_phrase,
                anchor_text=block.text,
            )
        )
        if len(matched_block_indices) > 1:
            proposal = proposals[-1]
            context.refinement_hints.append(
                CalloutRefinementHint(
                    proposal_id=proposal.proposal_id,
                    page=page_number,
                    issue="expanded_across_multiple_text_blocks",
                    anchor_phrase=matched_phrase,
                    anchor_text=block.text,
                    collected_block_count=len(matched_block_indices),
                )
            )
            warnings.append(
                "Callout detector expanded a proposal across "
                f"{len(matched_block_indices)} text blocks on page {page_number}."
            )

    fallback_proposals = _build_phrase_only_fallback_proposals(
        page_number=page_number,
        lines=context.lines,
        anchor_phrases=context.anchor_phrases,
        existing_proposals=proposals,
        padding=context.guidance_input.callout_bbox_padding,
    )
    if fallback_proposals:
        warnings.append(
            "Callout detector used phrase-only fallback proposals on page "
            f"{page_number} for {len(fallback_proposals)} missed anchor(s)."
        )
        proposals.extend(fallback_proposals)

    return proposals, warnings


def _collect_callout_region(
    *,
    blocks: list[_TextBlock],
    start_index: int,
    anchor_phrases: list[str],
    max_vertical_gap: float,
) -> tuple[fitz.Rect, list[int]]:
    region_rect = blocks[start_index].rect
    matched_block_indices = [start_index]

    for candidate_index in range(start_index + 1, len(blocks)):
        candidate = blocks[candidate_index]
        if _match_anchor_phrase(candidate.normalized_text, anchor_phrases) is not None:
            break
        if not _same_text_column(region_rect, candidate.rect):
            break
        vertical_gap = candidate.rect.y0 - region_rect.y1
        if vertical_gap > max_vertical_gap:
            break
        region_rect = region_rect | candidate.rect
        matched_block_indices.append(candidate_index)

    return region_rect, matched_block_indices


def _build_phrase_only_fallback_proposals(
    *,
    page_number: int,
    lines: list[_TextLine],
    anchor_phrases: list[str],
    existing_proposals: list[AnnotationProposal],
    padding: dict[str, float],
) -> list[AnnotationProposal]:
    fallback_proposals: list[AnnotationProposal] = []
    for line in lines:
        matched_phrase = _match_anchor_phrase(line.normalized_text, anchor_phrases)
        if matched_phrase is None:
            continue
        line_rect = _pad_rect(line.rect, {"left": 0.0, "top": 0.0, "right": 0.0, "bottom": 0.0})
        if any(_bbox_intersects(proposal.bbox, line_rect) for proposal in existing_proposals):
            continue
        fallback_proposals.append(
            _build_callout_proposal(
                page_number=page_number,
                bbox=_pad_rect(line.rect, padding),
                anchor_phrase=matched_phrase,
                anchor_text=line.text,
            )
        )
    return fallback_proposals


def _extract_text_blocks(page: fitz.Page) -> list[_TextBlock]:
    payload = page.get_text("dict")
    blocks: list[_TextBlock] = []
    for block_index, block in enumerate(payload.get("blocks", [])):
        if block.get("type") != 0:
            continue
        block_text_parts: list[str] = []
        block_rect: fitz.Rect | None = None
        for line in block.get("lines", []):
            line_text = "".join(span.get("text", "") for span in line.get("spans", []))
            if not line_text.strip():
                continue
            line_bbox = line.get("bbox")
            if not isinstance(line_bbox, (list, tuple)) or len(line_bbox) != BBOX_COORDINATE_COUNT:
                continue
            block_text_parts.append(line_text.strip())
            line_rect = fitz.Rect(*line_bbox)
            block_rect = line_rect if block_rect is None else block_rect | line_rect
        if block_rect is None or not block_text_parts:
            continue
        blocks.append(
            _TextBlock(
                block_index=block_index,
                text=" ".join(block_text_parts).strip(),
                normalized_text=_normalize_anchor_text(" ".join(block_text_parts)),
                rect=block_rect,
            )
        )
    return sorted(
        blocks,
        key=lambda block: (block.rect.y0, block.rect.x0, block.rect.y1, block.rect.x1),
    )


def _extract_text_lines(page: fitz.Page) -> list[_TextLine]:
    payload = page.get_text("dict")
    lines: list[_TextLine] = []
    for block_index, block in enumerate(payload.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for line_index, line in enumerate(block.get("lines", [])):
            line_text = "".join(span.get("text", "") for span in line.get("spans", []))
            if not line_text.strip():
                continue
            line_bbox = line.get("bbox")
            if not isinstance(line_bbox, (list, tuple)) or len(line_bbox) != BBOX_COORDINATE_COUNT:
                continue
            lines.append(
                _TextLine(
                    block_index=block_index,
                    line_index=line_index,
                    text=line_text.strip(),
                    normalized_text=_normalize_anchor_text(line_text),
                    rect=fitz.Rect(*line_bbox),
                )
            )
    return sorted(
        lines,
        key=lambda line: (
            line.rect.y0,
            line.rect.x0,
            line.rect.y1,
            line.rect.x1,
            line.block_index,
            line.line_index,
        ),
    )


def _match_anchor_phrase(normalized_text: str, anchor_phrases: list[str]) -> str | None:
    for anchor_phrase in anchor_phrases:
        if normalized_text.startswith(anchor_phrase):
            return anchor_phrase
    return None


def _normalize_anchor_phrase(text: str) -> str:
    return _normalize_anchor_text(text)


def _normalize_anchor_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("’", "'")
    normalized = normalized.lower()
    normalized = normalized.replace("notes", "note")
    normalized = normalized.replace("'", "")
    normalized = _WORD_NORMALIZER.sub(" ", normalized)
    normalized = _WHITESPACE_NORMALIZER.sub(" ", normalized).strip()
    return normalized


def _pad_rect(rect: fitz.Rect, padding: dict[str, float]) -> list[float]:
    return [
        float(rect.x0 - padding["left"]),
        float(rect.y0 - padding["top"]),
        float(rect.x1 + padding["right"]),
        float(rect.y1 + padding["bottom"]),
    ]


def _same_text_column(first_rect: fitz.Rect, second_rect: fitz.Rect) -> bool:
    overlap_width = min(first_rect.x1, second_rect.x1) - max(first_rect.x0, second_rect.x0)
    if overlap_width <= 0:
        return False
    first_width = first_rect.width
    second_width = second_rect.width
    if first_width <= 0 or second_width <= 0:
        return False
    overlap_ratio = overlap_width / min(first_width, second_width)
    return overlap_ratio >= _MIN_HORIZONTAL_OVERLAP_RATIO


def _bbox_intersects(first_bbox: list[float], second_bbox: list[float]) -> bool:
    first_left, first_top, first_right, first_bottom = first_bbox
    second_left, second_top, second_right, second_bottom = second_bbox
    return not (
        first_right <= second_left
        or second_right <= first_left
        or first_bottom <= second_top
        or second_bottom <= first_top
    )


def _build_callout_proposal(
    *,
    page_number: int,
    bbox: list[float],
    anchor_phrase: str,
    anchor_text: str,
) -> AnnotationProposal:
    metadata: dict[str, object] = {
        "source": "code",
        "trigger": "text-anchor",
        "anchor_phrase": anchor_phrase,
        "anchor_text": anchor_text,
        "callout_label": "callout_gm",
    }
    proposal_id = _build_proposal_id(
        label="callout",
        page=page_number,
        bbox=bbox,
        metadata=metadata,
    )
    proposal = AnnotationProposal(
        proposal_id=proposal_id,
        label="callout",
        page=page_number,
        bbox=[float(value) for value in bbox],
        confidence=0.88,
        metadata=metadata,
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
    serialized_metadata = repr(sorted(metadata.items()))
    digest = hashlib.sha1(
        f"{label}|{page}|{bbox}|{serialized_metadata}".encode(),
        usedforsecurity=False,
    ).hexdigest()[:12]
    return f"ap-{digest}"

__all__ = [
    "CalloutDetectionResult",
    "CalloutRefinementHint",
    "detect_callout_proposals",
    "detect_callout_proposals_with_warnings",
]
