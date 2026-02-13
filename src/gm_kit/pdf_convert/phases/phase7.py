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

    def _load_mapping(self, mapping_path: Path, result: PhaseResult) -> dict | None:
        """Step 7.2: Load font-family mapping JSON.

        Args:
            mapping_path: Path to font-family-mapping.json
            result: Phase result for adding errors

        Returns:
            Loaded mapping dict or None on error
        """
        if not mapping_path.exists():
            result.add_error("font-family-mapping.json not found - run Phase 3 first")
            result.status = PhaseStatus.ERROR
            return None

        try:
            with open(mapping_path, encoding="utf-8") as f:
                mapping: dict = json.load(f)
            result.add_step(
                StepResult(
                    step_id="7.2",
                    description="Load font-family mapping JSON",
                    status=PhaseStatus.SUCCESS,
                    message="Loaded font family mapping",
                )
            )
            return mapping
        except json.JSONDecodeError as e:
            result.add_error(f"Error decoding font-family-mapping.json: {e}")
            result.status = PhaseStatus.ERROR
            return None
        except Exception as e:
            result.add_error(f"Failed to load font-family-mapping.json: {e}")
            result.status = PhaseStatus.ERROR
            return None

    def _load_toc_entries(self, output_dir: Path, result: PhaseResult) -> list[dict]:
        """Step 7.1: Build heading map from TOC.

        Args:
            output_dir: Output directory containing toc-extracted.txt
            result: Phase result for adding step info

        Returns:
            List of TOC entries
        """
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
        return toc_entries

    def _calculate_body_font_size(self, mapping: dict) -> float:
        """Calculate body font size from mapping signatures.

        Args:
            mapping: Font family mapping dict

        Returns:
            Estimated body font size
        """
        font_sizes = [s.get("size", 0) for s in mapping.get("signatures", [])]
        body_font_size_candidates = [
            fs for fs in font_sizes if BODY_FONT_SIZE_MIN <= fs <= BODY_FONT_SIZE_MAX
        ]
        if body_font_size_candidates:
            return float(Counter(body_font_size_candidates).most_common(1)[0][0])
        return BODY_FONT_SIZE_DEFAULT

    def _load_callout_config(self, state: ConversionState, result: PhaseResult) -> list[dict]:
        """Load callout configuration from config file.

        Args:
            state: Current conversion state
            result: Phase result for adding warnings

        Returns:
            List of callout definitions
        """
        gm_callout_config_file_path = state.config.get("gm_callout_config_file")
        callout_definitions: list[dict] = []

        if gm_callout_config_file_path:
            try:
                config_path = Path(gm_callout_config_file_path)
                if config_path.exists():
                    if config_path.stat().st_size == 0:
                        logger.info(
                            f"GM callout config file '{gm_callout_config_file_path}' is empty"
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

        return callout_definitions

    def _detect_callouts_from_config(
        self,
        state: ConversionState,
        callout_definitions: list[dict],
    ) -> dict[str, list[str]]:
        """Detect callout text blocks from configuration.

        Args:
            state: Current conversion state
            callout_definitions: List of callout definitions

        Returns:
            Dictionary mapping label to list of text blocks
        """
        all_callout_texts_found_by_label: dict[str, list[str]] = {}

        for definition in callout_definitions:
            start_text = definition.get("start_text")
            end_text = definition.get("end_text")
            label = definition.get("label", "callout_gm")

            if start_text and end_text:
                callout_text_block = self._detect_callout_by_boundary(state, start_text, end_text)
                if callout_text_block:
                    all_callout_texts_found_by_label.setdefault(label, []).append(
                        callout_text_block
                    )
                    logger.info(
                        f"Callout block found by boundary '{start_text}'/'{end_text}' "
                        f"(Label: {label}): {callout_text_block[:100]}..."
                    )

        return all_callout_texts_found_by_label

    def _is_title_case(self, content: str) -> bool:
        """Check if content is in title case.

        Args:
            content: Text content to check

        Returns:
            True if content is title case
        """
        if not content or not content[0].isupper():
            return False

        words = content.split()
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
                    return False
            elif word.lower() not in minor_words and not word[0].isupper():
                return False
        return True

    def _detect_content_types(  # noqa: PLR0913
        self,
        phase6_content: str,
        mapping: dict,
        body_font_size: float,
        all_callout_texts_found_by_label: dict[str, list[str]],
        state: ConversionState,
        result: PhaseResult,
    ) -> tuple[dict, dict, set]:
        """Steps 7.3-7.6: Detect ALL CAPS, Title Case, GM notes, and read-aloud.

        Args:
            phase6_content: Content from phase 6
            mapping: Font family mapping
            body_font_size: Estimated body font size
            all_callout_texts_found_by_label: Detected callout text blocks
            state: Current conversion state
            result: Phase result for adding step info

        Returns:
            Tuple of (all_caps_candidates, gm_note_signatures, read_aloud_signatures)
        """
        all_caps_candidates: dict[str, list[str]] = {}
        title_case_candidates: dict[str, list[str]] = {}
        gm_note_signatures: dict[str, str] = {}
        read_aloud_signatures: set[str] = set()

        for sig_id, content in self._extract_markers_from_text(phase6_content):
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
            if is_potential_heading and self._is_title_case(content):
                title_case_candidates.setdefault(sig_id, []).append(content)

            # Step 7.5: Detect GM/Keeper note keywords
            assigned_label = self._detect_gm_note_label(
                sig_id, content, all_callout_texts_found_by_label, state
            )
            if assigned_label:
                gm_note_signatures[sig_id] = assigned_label

            # Step 7.6: Detect read-aloud text markers
            read_aloud_markers = ["read aloud", "read the following", "boxed text", "sidebar"]
            if any(rm in content.lower() for rm in read_aloud_markers):
                read_aloud_signatures.add(sig_id)

        result.add_step(
            StepResult(
                step_id="7.3",
                description="Detect ALL CAPS headings",
                status=PhaseStatus.SUCCESS,
                message=f"Found {len(all_caps_candidates)} signatures with ALL CAPS text",
            )
        )
        result.add_step(
            StepResult(
                step_id="7.4",
                description="Detect Title Case headings",
                status=PhaseStatus.SUCCESS,
                message=f"Found {len(title_case_candidates)} signatures with Title Case text",
            )
        )
        result.add_step(
            StepResult(
                step_id="7.5",
                description="Detect GM/Keeper note keywords",
                status=PhaseStatus.SUCCESS,
                message=f"Found {len(gm_note_signatures)} signatures with GM/Keeper note keywords",
            )
        )
        result.add_step(
            StepResult(
                step_id="7.6",
                description="Detect read-aloud text markers",
                status=PhaseStatus.SUCCESS,
                message=f"Found {len(read_aloud_signatures)} signatures with read-aloud keywords",
            )
        )

        return all_caps_candidates, gm_note_signatures, read_aloud_signatures

    def _detect_gm_note_label(
        self,
        sig_id: str,
        content: str,
        all_callout_texts_found_by_label: dict[str, list[str]],
        state: ConversionState,
    ) -> str | None:
        """Detect GM note label for a signature.

        Args:
            sig_id: Signature ID
            content: Text content
            all_callout_texts_found_by_label: Detected callout text blocks
            state: Current conversion state

        Returns:
            Detected label or None
        """
        # Check config-based callouts first
        for label_key, cb_texts in all_callout_texts_found_by_label.items():
            for cb_text in cb_texts:
                normalized_cb_lines = {line.strip() for line in cb_text.split("\n") if line.strip()}
                if content.strip() in normalized_cb_lines:
                    return label_key

        # Fallback to keyword search
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
            return "callout_gm"

        return None

    def _ensure_single_h1(self, mapping: dict) -> bool:
        """Ensure single H1 rule is enforced.

        Args:
            mapping: Font family mapping to update

        Returns:
            True if H1 was assigned, False otherwise
        """
        h1_present = any(s.get("label") == "H1" for s in mapping.get("signatures", []))
        if h1_present:
            return False

        largest_h_candidate = None
        largest_h_size = 0
        for sig in mapping.get("signatures", []):
            label = sig.get("label") or ""
            size = sig.get("size", 0)
            if label.startswith("H") and size > largest_h_size:
                largest_h_candidate = sig
                largest_h_size = size

        if largest_h_candidate and largest_h_candidate.get("label") != "H1":
            original_label = largest_h_candidate["label"]
            largest_h_candidate["label"] = "H1"
            for sig in mapping.get("signatures", []):
                if sig != largest_h_candidate and (sig.get("label") or "") == original_label:
                    sig["label"] = "H2"
            return True

        return False

    def _assign_labels_to_signatures(
        self,
        mapping: dict,
        all_caps_candidates: dict[str, list[str]],
        gm_note_signatures: dict[str, str],
        read_aloud_signatures: set[str],
        body_font_size: float,
    ) -> int:
        """Assign labels to signatures based on detection results.

        Args:
            mapping: Font family mapping to update
            all_caps_candidates: Detected ALL CAPS candidates
            gm_note_signatures: Detected GM note signatures
            read_aloud_signatures: Detected read-aloud signatures
            body_font_size: Estimated body font size

        Returns:
            Number of updated signatures
        """
        updated_count = 0

        for sig in mapping.get("signatures", []):
            sig_id = sig.get("id")
            if not sig_id:
                continue

            current_label = sig.get("label")
            font_size = sig.get("size", 0)

            # Assign heading labels
            if not current_label and sig_id in all_caps_candidates:
                suggested_label = None
                if font_size > body_font_size * 1.5:
                    suggested_label = "H2"
                elif font_size > body_font_size:
                    suggested_label = "H3"
                else:
                    suggested_label = "H4"

                if suggested_label:
                    sig["label"] = suggested_label
                    updated_count += 1

            # Apply special content labels
            if sig_id in gm_note_signatures:
                callout_label = gm_note_signatures[sig_id]
                if current_label not in ["H1", callout_label, "callout_read_aloud"]:
                    sig["label"] = callout_label
                    updated_count += 1
            elif sig_id in read_aloud_signatures:
                if current_label not in ["H1", "callout_gm", "callout_read_aloud"]:
                    sig["label"] = "callout_read_aloud"
                    updated_count += 1

        return updated_count

    def _update_mapping_labels(  # noqa: PLR0913
        self,
        mapping: dict,
        all_caps_candidates: dict[str, list[str]],
        gm_note_signatures: dict[str, str],
        read_aloud_signatures: set[str],
        body_font_size: float,
        result: PhaseResult,
    ) -> int:
        """Step 7.9: Update font-family-mapping.json with detection findings.

        Args:
            mapping: Font family mapping to update
            all_caps_candidates: Detected ALL CAPS candidates
            gm_note_signatures: Detected GM note signatures
            read_aloud_signatures: Detected read-aloud signatures
            body_font_size: Estimated body font size
            result: Phase result for adding step info

        Returns:
            Number of updated signatures
        """
        updated_count = self._assign_labels_to_signatures(
            mapping, all_caps_candidates, gm_note_signatures, read_aloud_signatures, body_font_size
        )

        if self._ensure_single_h1(mapping):
            updated_count += 1

        result.add_step(
            StepResult(
                step_id="7.9",
                description="Update font-family-mapping.json with ALL detection findings",
                status=PhaseStatus.SUCCESS,
                message=(f"Updated {updated_count} font signatures with detection findings"),
            )
        )

        return updated_count

    def _add_stub_steps(self, result: PhaseResult) -> None:
        """Add stub steps for agent and user steps.

        Args:
            result: Phase result for adding steps
        """
        result.add_step(
            StepResult(
                step_id="7.7",
                description="Detect table structures (AGENT)",
                status=PhaseStatus.SUCCESS,
                message="Stub: Agent step will be implemented in E4-07b",
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

    def execute(self, state: ConversionState) -> PhaseResult:
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

        # Step 7.2: Load mapping
        mapping = self._load_mapping(mapping_path, result)
        if mapping is None:
            result.complete()
            return result

        if not phase6_path.exists():
            result.add_error(f"{phase6_path.name} not found - run Phase 6 first")
            result.status = PhaseStatus.ERROR
            result.complete()
            return result

        try:
            with open(phase6_path, encoding="utf-8") as f:
                phase6_content = f.read()

            # Step 7.1: Load TOC entries
            self._load_toc_entries(output_dir, result)

            # Calculate body font size
            body_font_size = self._calculate_body_font_size(mapping)

            # Load callout config and detect callouts
            callout_definitions = self._load_callout_config(state, result)
            all_callout_texts = self._detect_callouts_from_config(state, callout_definitions)

            # Steps 7.3-7.6: Detect content types
            all_caps_candidates, gm_note_sigs, read_aloud_sigs = self._detect_content_types(
                phase6_content,
                mapping,
                body_font_size,
                all_callout_texts,
                state,
                result,
            )

            # Add stub steps
            self._add_stub_steps(result)

            # Step 7.9: Update mapping with labels
            self._update_mapping_labels(
                mapping,
                all_caps_candidates,
                gm_note_sigs,
                read_aloud_sigs,
                body_font_size,
                result,
            )

            # Save mapping
            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=2, sort_keys=False)
            result.output_file = str(mapping_path)

        except Exception as e:
            result.add_error(f"Structural detection failed: {e}")
            result.status = PhaseStatus.ERROR
            logger.error(f"Structural detection failed: {e}\n{traceback.format_exc()}")
            raise

        result.complete()
        return result
