"""Phase 7: Font Label Assignment.

Code steps 7.1-7.9: Structural detection including TOC map building,
heading detection, GM notes detection.
Agent step 7.7 is stubbed (table detection).
User steps 7.10-7.11 are stubbed (font label review).
"""

from __future__ import annotations

import json
import logging
import re
import traceback  # Import traceback for detailed error logging
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

import fitz  # PyMuPDF

from gm_kit.pdf_convert.phases.base import Phase, PhaseResult, PhaseStatus, StepResult

if TYPE_CHECKING:
    from gm_kit.pdf_convert.state import ConversionState

logger = logging.getLogger(__name__)

# Font size range for body text detection
BODY_FONT_SIZE_MIN = 8
BODY_FONT_SIZE_MAX = 12
# Default body font size when no candidates found
BODY_FONT_SIZE_DEFAULT = 10
# Minimum content length for ALL CAPS heading detection
ALL_CAPS_MIN_LENGTH = 3


class Phase7(Phase):
    """Phase 7: Font Label Assignment.

    Builds structural map from TOC, detects headings and special content.
    Updates font-family-mapping.json with structural labels.
    """

    @property
    def phase_num(self) -> int:
        return 7

    @property
    def has_agent_steps(self) -> bool:
        return True  # Step 7.7: Detect table structures

    @property
    def has_user_steps(self) -> bool:
        return True  # Steps 7.10-7.11: Font label review

    def _extract_markers_from_text(self, text_content: str):
        """Extracts signature IDs and text content from marker-formatted text."""
        # Regex to find «sigXXX:content»
        marker_pattern = re.compile(r"«(sig\d{3}):([^»]*)»")
        for match in marker_pattern.finditer(text_content):
            sig_id = match.group(1)
            content = match.group(2)
            yield sig_id, content

    def _detect_callout_by_boundary(
        self, state: ConversionState, start_text: str, end_text: str
    ) -> str:
        """Detects callout text by start and end text boundaries."""
        if not start_text or not end_text:
            return ""

        pdf_path = Path(state.pdf_path)
        doc = fitz.open(pdf_path)
        in_callout_block = False
        callout_text_parts = []

        for page in doc:
            blocks = page.get_text("blocks")
            for block in blocks:
                block_text = block[4]  # The text content of the block

                if start_text in block_text:
                    in_callout_block = True
                    start_index = block_text.find(start_text)
                    # If start and end are in the same block
                    if end_text in block_text:
                        end_index = block_text.find(end_text, start_index) + len(end_text)
                        callout_text_parts.append(block_text[start_index:end_index])
                        in_callout_block = False
                    else:
                        callout_text_parts.append(block_text[start_index:])

                elif end_text in block_text and in_callout_block:
                    end_index = block_text.find(end_text) + len(end_text)
                    callout_text_parts.append(block_text[:end_index])
                    in_callout_block = False

                elif in_callout_block:
                    callout_text_parts.append(block_text)

        return "".join(callout_text_parts)

    def execute(self, state: ConversionState) -> PhaseResult:  # noqa: PLR0912, PLR0915, C901
        """Execute structural detection steps.

        Args:
            state: Current conversion state

        Returns:
            PhaseResult with detection results
        """
        result = self.create_result()
        output_dir = Path(state.output_dir)
        pdf_name = Path(state.pdf_path).stem

        mapping_path = output_dir / "font-family-mapping.json"
        phase6_path = output_dir / f"{pdf_name}-phase6.md"

        # Step 7.2: Load font-family mapping JSON
        if not mapping_path.exists():
            result.add_error("font-family-mapping.json not found - run Phase 3 first")
            result.status = PhaseStatus.ERROR
            result.complete()
            return result
        try:
            with open(mapping_path, encoding="utf-8") as f:
                mapping = json.load(f)
            result.add_step(
                StepResult(
                    step_id="7.2",
                    description="Load font-family mapping JSON",
                    status=PhaseStatus.SUCCESS,
                    message="Loaded font family mapping",
                )
            )
        except json.JSONDecodeError as e:
            result.add_error(f"Error decoding font-family-mapping.json: {e}")
            result.status = PhaseStatus.ERROR
            result.complete()
            return result
        except Exception as e:
            result.add_error(f"Failed to load font-family-mapping.json: {e}")
            result.status = PhaseStatus.ERROR
            result.complete()
            return result

        if not phase6_path.exists():
            result.add_error(f"{phase6_path.name} not found - run Phase 6 first")
            result.status = PhaseStatus.ERROR
            result.complete()
            return result

        try:  # Main logic wrapped in try-except block
            # --- BEGIN MAIN LOGIC ---
            with open(phase6_path, encoding="utf-8") as f:
                phase6_content = f.read()

            # Step 7.1: Build heading map from TOC (unchanged from original, but re-checked)
            toc_path = output_dir / "toc-extracted.txt"
            toc_entries = []
            if toc_path.exists():
                with open(toc_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            match = re.match(r"^(.*)\s*\(page\s*(\d+)\)$", line)
                            if match:
                                toc_entries.append(
                                    {
                                        "title": match.group(1).strip(),
                                        "page": int(match.group(2)),
                                    }
                                )

            result.add_step(
                StepResult(
                    step_id="7.1",
                    description="Build heading map from TOC",
                    status=PhaseStatus.SUCCESS,
                    message=f"Loaded {len(toc_entries)} TOC entries",
                )
            )

            # Analyze font sizes to determine a baseline for body text
            font_sizes = [s.get("size", 0) for s in mapping.get("signatures", [])]
            body_font_size_candidates = [
                fs for fs in font_sizes if BODY_FONT_SIZE_MIN <= fs <= BODY_FONT_SIZE_MAX
            ]  # Common body text range
            if body_font_size_candidates:
                # Use the mode (most frequent) or median as a heuristic for body font size
                body_font_size = Counter(body_font_size_candidates).most_common(1)[0][0]
            else:
                body_font_size = BODY_FONT_SIZE_DEFAULT  # Default fallback

            # Dictionaries to store detected heading and special content candidates
            all_caps_candidates: dict[str, list[str]] = {}  # sig_id -> list of all-caps samples
            title_case_candidates: dict[str, list[str]] = {}  # sig_id -> list of title-case samples
            gm_note_signatures: dict[
                str, str
            ] = {}  # sig_id -> label (e.g., 'callout_gm', 'callout_sidebar')
            read_aloud_signatures: set[str] = set()

            # Detect callouts from config file
            gm_callout_config_file_path = state.config.get("gm_callout_config_file")
            callout_definitions: list[dict[str, str]] = []

            if gm_callout_config_file_path:
                try:
                    config_path = Path(gm_callout_config_file_path)
                    if config_path.exists():
                        # Check if file is empty
                        if config_path.stat().st_size == 0:
                            callout_definitions = []  # Treat empty file as empty list
                            logger.info(
                                f"GM callout config file "
                                f"'{gm_callout_config_file_path}' is empty,"
                                " treating as empty list."
                            )
                        else:
                            with open(config_path, encoding="utf-8") as f:
                                callout_definitions = json.load(f)
                    else:
                        result.add_warning(
                            f"GM callout config file not found: {gm_callout_config_file_path}"
                        )
                except json.JSONDecodeError as e:
                    result.add_warning(
                        f"Error decoding GM callout config JSON: {e}."
                        " Ensure it's valid JSON (e.g., [] for empty)."
                    )
                except Exception as e:
                    result.add_warning(f"Failed to load GM callout config file: {e}")

            all_callout_texts_found_by_label: dict[
                str, list[str]
            ] = {}  # label -> list of text blocks
            if callout_definitions:
                for definition in callout_definitions:
                    start_text = definition.get("start_text")
                    end_text = definition.get("end_text")
                    label = definition.get("label", "callout_gm")  # Default label if not specified

                    if start_text and end_text:
                        callout_text_block = self._detect_callout_by_boundary(
                            state, start_text, end_text
                        )
                        if callout_text_block:
                            all_callout_texts_found_by_label.setdefault(label, []).append(
                                callout_text_block
                            )
                            logger.info(
                                f"Callout block found by boundary "
                                f"'{start_text}'/'{end_text}' "
                                f"(Label: {label}): "
                                f"{callout_text_block[:100]}..."
                            )

            # Process phase6_content for markers
            for sig_id, content in self._extract_markers_from_text(phase6_content):
                # Get font signature details
                sig_details = next(
                    (s for s in mapping.get("signatures", []) if s.get("id") == sig_id), None
                )
                if not sig_details:
                    logger.warning(f"Signature {sig_id} not found in mapping.")
                    continue

                font_size = sig_details.get("size", 0)
                is_potential_heading = font_size > body_font_size or (
                    sig_details.get("label") or ""
                ).startswith("H")

                # Step 7.3: Detect ALL CAPS headings
                if (
                    is_potential_heading
                    and content.isupper()
                    and len(content) > ALL_CAPS_MIN_LENGTH
                    and not any(c.islower() for c in content)
                ):
                    all_caps_candidates.setdefault(sig_id, []).append(content)

                # Step 7.4: Detect Title Case headings
                if is_potential_heading and content and content[0].isupper():
                    words = content.split()
                    is_title_case = True
                    minor_words = {
                        "a",
                        "an",
                        "the",
                        "in",
                        "on",
                        "of",
                        "for",
                        "with",
                        "and",
                        "but",
                        "or",
                    }
                    for i, word in enumerate(words):
                        if not word:
                            continue
                        if i == 0:
                            if not word[0].isupper():
                                is_title_case = False
                                break
                        elif word.lower() not in minor_words and not word[0].isupper():
                            is_title_case = False
                            break
                    if is_title_case:
                        title_case_candidates.setdefault(sig_id, []).append(content)

                # Step 7.5: Detect GM/Keeper note keywords (or use boundary config)
                assigned_callout_label_from_config: str | None = None
                if all_callout_texts_found_by_label:
                    for label_key, cb_texts in all_callout_texts_found_by_label.items():
                        for cb_text in cb_texts:
                            # Normalize cb_text into lines for more precise matching
                            normalized_cb_lines = {
                                line.strip() for line in cb_text.split("\n") if line.strip()
                            }

                            if content.strip() in normalized_cb_lines:
                                gm_note_signatures[sig_id] = label_key
                                assigned_callout_label_from_config = label_key
                                break
                        if assigned_callout_label_from_config:
                            break

                if (
                    not assigned_callout_label_from_config
                ):  # Fallback to keyword search if not found by boundary config
                    gm_keywords = [
                        "gm note",
                        "gm notes",
                        "game master note",
                        "keeper note",
                        "keeper notes",
                        "dm note",
                        "dm notes",
                        "dungeon master note",
                    ]
                    custom_keywords = state.config.get("gm_keyword", [])
                    if custom_keywords:
                        gm_keywords.extend(custom_keywords)
                    if any(kw in content.lower() for kw in gm_keywords):
                        gm_note_signatures[sig_id] = (
                            "callout_gm"  # Default label for keyword detection
                        )

                # Step 7.6: Detect read-aloud text markers
                read_aloud_markers = ["read aloud", "read the following", "boxed text", "sidebar"]
                if any(rm in content.lower() for rm in read_aloud_markers):
                    read_aloud_signatures.add(sig_id)

            result.add_step(
                StepResult(
                    step_id="7.3",
                    description="Detect ALL CAPS headings",
                    status=PhaseStatus.SUCCESS,
                    message=(f"Found {len(all_caps_candidates)} signatures with ALL CAPS text"),
                )
            )
            result.add_step(
                StepResult(
                    step_id="7.4",
                    description="Detect Title Case headings",
                    status=PhaseStatus.SUCCESS,
                    message=(f"Found {len(title_case_candidates)} signatures with Title Case text"),
                )
            )
            result.add_step(
                StepResult(
                    step_id="7.5",
                    description="Detect GM/Keeper note keywords",
                    status=PhaseStatus.SUCCESS,
                    message=(
                        f"Found {len(gm_note_signatures)} signatures with GM/Keeper note keywords"
                    ),
                )
            )
            result.add_step(
                StepResult(
                    step_id="7.6",
                    description="Detect read-aloud text markers",
                    status=PhaseStatus.SUCCESS,
                    message=(
                        f"Found {len(read_aloud_signatures)} signatures with read-aloud keywords"
                    ),
                )
            )

            # Step 7.7: Detect table structures (AGENT STEP - STUBBED)
            result.add_step(
                StepResult(
                    step_id="7.7",
                    description="Detect table structures (AGENT)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Agent step will be implemented in E4-07b",
                )
            )

            # Step 7.8: Removed - inline heading detection not needed
            # TOC entries and headings appear as standalone lines/blocks
            # ALL CAPS and Title Case detection (7.3, 7.4) sufficient

            # Step 7.9: Update font-family-mapping.json with ALL detection findings
            updated_signatures_count = 0
            for sig in mapping.get("signatures", []):
                sig_id = sig.get("id")
                if not sig_id:
                    continue

                current_label = sig.get("label")
                font_size = sig.get("size", 0)

                # Only assign new labels if one isn't already present
                # (prioritize TOC/explicit labels)
                if not current_label:
                    suggested_label = None
                    if sig_id in all_caps_candidates or sig_id in title_case_candidates:
                        if font_size > body_font_size * 1.5:
                            suggested_label = "H2"
                        elif font_size > body_font_size:
                            suggested_label = "H3"
                        else:
                            suggested_label = "H4"

                    if suggested_label:
                        sig["label"] = suggested_label
                        updated_signatures_count += 1

                # Apply special content labels (GM Notes, Read Aloud)
                if sig_id in gm_note_signatures:
                    callout_label = gm_note_signatures[
                        sig_id
                    ]  # Get the specific label from detection
                    if current_label not in ["H1", callout_label, "callout_read_aloud"]:
                        sig["label"] = callout_label
                        updated_signatures_count += 1
                elif sig_id in read_aloud_signatures:
                    if current_label not in ["H1", "callout_gm", "callout_read_aloud"]:
                        sig["label"] = "callout_read_aloud"
                        updated_signatures_count += 1

            # After all labels are assigned, ensure single H1 rule.
            h1_present = any(s.get("label") == "H1" for s in mapping.get("signatures", []))
            if not h1_present:
                largest_h_candidate = None
                largest_h_size = 0
                for sig in mapping.get("signatures", []):
                    if (sig.get("label") or "").startswith("H") and sig.get(
                        "size", 0
                    ) > largest_h_size:
                        largest_h_candidate = sig
                        largest_h_size = sig.get("size", 0)
                if largest_h_candidate and largest_h_candidate.get("label") != "H1":
                    original_label = largest_h_candidate["label"]
                    largest_h_candidate["label"] = "H1"
                    for sig in mapping.get("signatures", []):
                        if (
                            sig != largest_h_candidate
                            and (sig.get("label") or "") == original_label
                        ):
                            sig["label"] = "H2"
                    updated_signatures_count += 1

            result.add_step(
                StepResult(
                    step_id="7.9",
                    description="Update font-family-mapping.json with ALL detection findings",
                    status=PhaseStatus.SUCCESS,
                    message=(
                        f"Updated {updated_signatures_count} font signatures"
                        " with detection findings"
                    ),
                )
            )

            result.add_step(
                StepResult(
                    step_id="7.9a",
                    description="Generate annotated PDF for label review (STUBBED)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Annotated PDF generation will be implemented later",
                )
            )

            result.add_step(
                StepResult(
                    step_id="7.10",
                    description="Present font-family labels for review (USER)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: User step will be implemented in E4-07c",
                )
            )

            result.add_step(
                StepResult(
                    step_id="7.11",
                    description="Capture user corrections (USER)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: User step will be implemented in E4-07c",
                )
            )

            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=2, sort_keys=False)

            result.output_file = str(mapping_path)

            # --- END MAIN LOGIC ---
        except Exception as e:
            result.add_error(f"Structural detection failed: {e}")
            result.status = PhaseStatus.ERROR
            logger.error(f"Structural detection failed: {e}\n{traceback.format_exc()}")
            raise

        result.complete()
        return result
