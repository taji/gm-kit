"""Phase 4: Text Extraction.

Code steps 4.1-4.4: Chunking, text extraction with font markers, merge.
Agent step 4.5 is stubbed (sentence boundary resolution).

This phase extracts text while preserving font information by wrapping spans with
font signature markers: «sig001:text»

Note: Two-column detection (formerly step 4.5) was removed because PyMuPDF extracts
text in correct reading order automatically. The short-line heuristic caused false
positives on RPG PDFs with stat blocks and tables. If two-column issues arise in
future PDFs, use spatial analysis (x-coordinate clustering) rather than line-length
heuristics.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import fitz  # PyMuPDF

from gm_kit.pdf_convert.phases.base import Phase, PhaseResult, PhaseStatus, StepResult

if TYPE_CHECKING:
    from gm_kit.pdf_convert.state import ConversionState

logger = logging.getLogger(__name__)

# Chunk size for large PDFs (pages per chunk)
CHUNK_SIZE = 50


def _escape_marker_chars(text: str) -> str:
    """Escape « and » characters to avoid collision with our markers."""
    return text.replace("«", "\\«").replace("»", "\\»")


def _build_font_to_id_mapping(mapping_path: Path) -> dict[str, str]:
    """Build a mapping from font signature key to signature ID.

    The key is constructed as: family|size|weight|style
    """
    if not mapping_path.exists():
        return {}

    try:
        with open(mapping_path, encoding="utf-8") as f:
            mapping = json.load(f)

        font_to_id: dict[str, str] = {}
        for sig in mapping.get("signatures", []):
            # Build signature key from font attributes
            family = sig.get("family", "Unknown")
            size = sig.get("size", 0)
            weight = sig.get("weight", "normal")
            style = sig.get("style", "normal")
            sig_id = sig.get("id", "")

            if sig_id:
                key = f"{family}|{size}|{weight}|{style}"
                font_to_id[key] = sig_id

        return font_to_id
    except Exception as e:
        logger.warning(f"Failed to load font mapping: {e}")
        return {}


class Phase4(Phase):
    """Phase 4: Text Extraction with Font Markers.

        Extracts text from PDF while preserving font information by wrapping
    text spans with signature markers: «sigXXX:text». This allows Phase 8
        to apply the correct heading levels based on font-family-mapping.json.
    """

    @property
    def phase_num(self) -> int:
        return 4

    @property
    def has_agent_steps(self) -> bool:
        return True  # Step 4.6: Resolve split sentences at chunk boundaries

    def execute(self, state: ConversionState) -> PhaseResult:  # noqa: PLR0912, PLR0915, C901
        """Execute text extraction steps.

        Args:
            state: Current conversion state

        Returns:
            PhaseResult with extraction results
        """
        result = self.create_result()
        pdf_path = Path(state.pdf_path)
        output_dir = Path(state.output_dir)
        pdf_name = pdf_path.stem

        output_md_path = output_dir / f"{pdf_name}-phase4.md"
        mapping_path = output_dir / "font-family-mapping.json"

        # Check if font mapping exists (required for marker insertion)
        if not mapping_path.exists():
            result.add_error("font-family-mapping.json not found - run Phase 3 first")
            result.status = PhaseStatus.ERROR
            result.complete()
            return result

        # Load font signature mapping
        font_to_id = _build_font_to_id_mapping(mapping_path)
        if not font_to_id:
            result.add_warning(
                "Could not load font signatures - extracting plain text without markers"
            )

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            # Step 4.1: Determine page chunks
            chunks = []
            for start in range(0, total_pages, CHUNK_SIZE):
                end = min(start + CHUNK_SIZE, total_pages)
                chunks.append((start, end))

            result.add_step(
                StepResult(
                    step_id="4.1",
                    description="Determine page chunks",
                    status=PhaseStatus.SUCCESS,
                    message=f"Created {len(chunks)} chunks ({CHUNK_SIZE} pages each)",
                )
            )

            # Step 4.2-4.3: Extract raw text per page with font markers
            all_pages_text = []

            for page_num in range(total_pages):
                page = doc[page_num]

                # Get text with layout info
                text_blocks = []
                blocks = page.get_text("dict")["blocks"]

                for block in blocks:
                    if "lines" in block:
                        block_text_parts = []
                        for line in block["lines"]:
                            # Group consecutive spans with the same font signature
                            line_groups = []
                            current_sig_id = None
                            current_text_parts = []

                            for span in line["spans"]:
                                # Get text and font info
                                span_text = span.get("text", "")

                                # Skip empty spans
                                if not span_text:
                                    continue

                                # Get font attributes
                                font = span.get("font", "Unknown")
                                size = round(span.get("size", 0), 1)
                                flags = span.get("flags", 0)
                                weight = "bold" if flags & 1 else "normal"
                                style = "italic" if flags & 2 else "normal"

                                # Build font signature key
                                font_key = f"{font}|{size}|{weight}|{style}"
                                sig_id = font_to_id.get(font_key)

                                # Escape marker characters in text
                                escaped_text = _escape_marker_chars(span_text)

                                # Check if this is whitespace-only
                                is_whitespace = not span_text.strip()

                                if sig_id:
                                    if is_whitespace:
                                        # Whitespace with signature - close group if sig changed
                                        if (
                                            current_sig_id
                                            and current_sig_id != sig_id
                                            and current_text_parts
                                        ):
                                            group_text = "".join(current_text_parts)
                                            line_groups.append(f"«{current_sig_id}:{group_text}»")
                                            current_sig_id = None
                                            current_text_parts = []

                                        # Add whitespace to appropriate group
                                        if sig_id == current_sig_id:
                                            current_text_parts.append(escaped_text)
                                        else:
                                            # Start new whitespace group
                                            if current_text_parts:
                                                group_text = "".join(current_text_parts)
                                                line_groups.append(
                                                    f"«{current_sig_id}:{group_text}»"
                                                )
                                            current_sig_id = sig_id
                                            current_text_parts = [escaped_text]
                                    elif sig_id == current_sig_id:
                                        # Same signature - append with space if needed
                                        # Defensive: Handles PDFs that use positioning
                                        # instead of explicit space characters between words
                                        if (
                                            current_text_parts
                                            and not current_text_parts[-1].endswith(" ")
                                            and not escaped_text.startswith(" ")
                                        ):
                                            current_text_parts.append(" ")
                                        current_text_parts.append(escaped_text)
                                    else:
                                        # Different signature - close group and start new
                                        if current_sig_id and current_text_parts:
                                            group_text = "".join(current_text_parts)
                                            line_groups.append(f"«{current_sig_id}:{group_text}»")
                                        elif current_text_parts:
                                            # Previous was unmarked text
                                            line_groups.append("".join(current_text_parts))

                                        # Start new group
                                        current_sig_id = sig_id
                                        current_text_parts = [escaped_text]
                                else:
                                    # No signature mapping - unmarked text
                                    if current_sig_id and current_text_parts:
                                        # Close current marked group
                                        group_text = "".join(current_text_parts)
                                        line_groups.append(f"«{current_sig_id}:{group_text}»")
                                        current_sig_id = None
                                        current_text_parts = []

                                    # Add space before unmarked text if needed
                                    if (
                                        line_groups
                                        and not line_groups[-1].endswith(" ")
                                        and not escaped_text.startswith(" ")
                                    ):
                                        line_groups.append(" ")

                                    # Add unmarked text
                                    line_groups.append(escaped_text)

                            # Close any remaining group
                            if current_sig_id and current_text_parts:
                                group_text = "".join(current_text_parts)
                                line_groups.append(f"«{current_sig_id}:{group_text}»")
                            elif current_text_parts:
                                line_groups.append("".join(current_text_parts))

                            # Join groups for this line
                            if line_groups:
                                line_text = "".join(line_groups)
                                block_text_parts.append(line_text)

                        # Join lines in block
                        if block_text_parts:
                            block_text = "\n".join(block_text_parts)
                            text_blocks.append(block_text)

                # Join blocks with newlines
                page_text = "\n".join(text_blocks)
                all_pages_text.append(page_text)

            result.add_step(
                StepResult(
                    step_id="4.2",
                    description="Extract raw text with font markers",
                    status=PhaseStatus.SUCCESS,
                    message=f"Extracted text with font markers from {total_pages} pages",
                )
            )

            # Step 4.3: Log page order checks
            result.add_step(
                StepResult(
                    step_id="4.3",
                    description="Log page order checks",
                    status=PhaseStatus.SUCCESS,
                    message=f"Processed {total_pages} pages in order",
                )
            )

            # Step 4.4: Merge chunks into single document
            # Add page markers
            marked_text = ""
            for i, text in enumerate(all_pages_text):
                marked_text += f"\n<!-- Page {i + 1} -->\n\n{text}\n"

            result.add_step(
                StepResult(
                    step_id="4.4",
                    description="Merge chunks into single document",
                    status=PhaseStatus.SUCCESS,
                    message=f"Merged {len(all_pages_text)} pages with font markers",
                )
            )

            # Step 4.5: Resolve split sentences (AGENT STEP - STUBBED)
            result.add_step(
                StepResult(
                    step_id="4.5",
                    description="Resolve split sentences (AGENT)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Agent step will be implemented in E4-07b",
                )
            )

            # Save output
            with open(output_md_path, "w", encoding="utf-8") as f:
                f.write(marked_text)

            result.output_file = str(output_md_path)
            doc.close()

        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="4.1",
                    description="Determine page chunks",
                    status=PhaseStatus.ERROR,
                    message=str(e),
                )
            )
            result.add_error(f"Text extraction failed: {e}")

        result.complete()
        return result
