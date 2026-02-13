"""Phase 5: Character-Level Fixes.

Code steps 5.1-5.4: Backtick-wrap markdown-sensitive characters,
character-level normalization and fixes.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from gm_kit.pdf_convert.phases.base import Phase, PhaseResult, PhaseStatus, StepResult

if TYPE_CHECKING:
    from gm_kit.pdf_convert.state import ConversionState

logger = logging.getLogger(__name__)

# Pattern to match font signature markers: «sigXXX:text»
FONT_MARKER_PATTERN = re.compile(r"«(sig[a-z0-9]+):([^»]+)»")
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)

# Font size threshold below which text is likely footer/watermark content
FOOTER_WATERMARK_MAX_FONT_SIZE = 8.0


def _wrap_inner_content(inner: str) -> str:
    """Wrap markdown-sensitive elements in backticks within marker text.

    Operates on the text content extracted from inside a marker
    (no marker delimiters). Order matters: double curlies before
    singles to avoid partial matching.
    """
    # 1. HTML tags: <tag>, </tag>, <tag/>, <tag attr="...">
    inner = re.sub(
        r"(?<!`)(</?[a-zA-Z][a-zA-Z0-9]*(?:\s[^>]*)?/?>)(?!`)",
        r"`\1`",
        inner,
    )

    # 2. Double curly bracket groups: {{ ... }}
    inner = re.sub(
        r"(?<!`)(\{\{[^}]*\}\})(?!`)",
        r"`\1`",
        inner,
    )

    # 3. Single curly braces (not part of {{ }})
    inner = re.sub(
        r"(?<!`)(?<!\{)(\{)(?!\{)(?!`)",
        r"`\1`",
        inner,
    )
    inner = re.sub(
        r"(?<!`)(?<!\})(\})(?!\})(?!`)",
        r"`\1`",
        inner,
    )

    # 4. Pipe: \|
    inner = re.sub(
        r"(?<!`)(\\\|)(?!`)",
        r"`\1`",
        inner,
    )

    # 5. Backslash sequences: \word (not \« or \»)
    inner = re.sub(
        r"(?<!`)(\\(?![«»])[a-zA-Z]+)(?!`)",
        r"`\1`",
        inner,
    )

    # 6. Standalone colon: : not preceded by a word character
    inner = re.sub(
        r"(?<!\w)(?<!`)(:)(?!`)",
        r"`\1`",
        inner,
    )

    return inner


def _wrap_md_sensitive_chars(content: str) -> str:
    """Wrap markdown-sensitive elements in backticks in marked and unmarked text.

    Marker inner text is wrapped while preserving marker delimiters.
    Non-marker text is also wrapped, but HTML comments are preserved as-is
    so page metadata comments (for example ``<!-- Page N -->``) are not altered.
    """

    def _wrap_preserving_html_comments(text: str) -> str:
        wrapped_parts: list[str] = []
        last = 0
        for comment_match in HTML_COMMENT_PATTERN.finditer(text):
            wrapped_parts.append(_wrap_inner_content(text[last : comment_match.start()]))
            wrapped_parts.append(comment_match.group(0))
            last = comment_match.end()
        wrapped_parts.append(_wrap_inner_content(text[last:]))
        return "".join(wrapped_parts)

    def _replace_marker(match: re.Match) -> str:
        sig_id = match.group(1)
        inner = match.group(2)
        wrapped = _wrap_inner_content(inner)
        return f"«{sig_id}:{wrapped}»"

    result_parts: list[str] = []
    last = 0
    for marker_match in FONT_MARKER_PATTERN.finditer(content):
        result_parts.append(_wrap_preserving_html_comments(content[last : marker_match.start()]))
        result_parts.append(_replace_marker(marker_match))
        last = marker_match.end()
    result_parts.append(_wrap_preserving_html_comments(content[last:]))
    return "".join(result_parts)


class Phase5(Phase):
    """Phase 5: Character-Level Fixes.

    Applies backtick-wrapping of HTML tags and markdown-sensitive
    characters, then character-level normalization: whitespace cleanup,
    line break fixes, and smart-quote normalization.
    """

    @property
    def phase_num(self) -> int:
        return 5

    def _load_font_mapping(self, font_mapping_path: Path) -> tuple[dict | None, bool]:
        """Load font mapping from JSON file.

        Args:
            font_mapping_path: Path to the font-family-mapping.json file

        Returns:
            Tuple of (loaded mapping dict or None, error flag)
        """
        if not font_mapping_path.exists():
            logger.debug(
                f"font-family-mapping.json not found at {font_mapping_path}. "
                "Skipping font-signature-based marker removals."
            )
            return None, True

        try:
            with open(font_mapping_path, encoding="utf-8") as f:
                return json.load(f), False
        except json.JSONDecodeError:
            logger.warning(
                f"Could not parse font-family-mapping.json: {font_mapping_path}. "
                "Skipping font-signature-based marker removals."
            )
            return None, True
        except Exception as e:
            logger.warning(
                f"Error loading font-family-mapping.json: {e}. "
                "Skipping font-signature-based marker removals."
            )
            return None, True

    def _remove_icon_font_markers(
        self,
        content: str,
        output_dir: Path,
        loaded_font_mapping: dict | None,
        font_mapping_load_error: bool,
        result: PhaseResult,
    ) -> str:
        """Step 5.1.1: Remove icon font markers using icon_config.json.

        Args:
            content: Content to process
            output_dir: Output directory for finding icon_config.json
            loaded_font_mapping: Loaded font mapping or None
            font_mapping_load_error: Whether there was an error loading font mapping
            result: Phase result for adding step info

        Returns:
            Processed content
        """
        icon_signature_ids = set()

        # Try to load icon_config.json generated by Phase 3
        icon_config_path = output_dir / "icon_config.json"
        if icon_config_path.exists():
            try:
                with open(icon_config_path, encoding="utf-8") as f:
                    icon_config = json.load(f)

                for sig in icon_config.get("icon_signatures", []):
                    if sig_id := sig.get("sig_id"):
                        icon_signature_ids.add(sig_id)
            except Exception as e:
                logger.warning(f"Failed to load icon_config.json: {e}")

        # Fallback to legacy detection if no icon_config.json
        if not icon_signature_ids and not font_mapping_load_error and loaded_font_mapping:
            for sig in loaded_font_mapping.get("signatures", []):
                family = sig.get("family")
                if family in ["FontAwesome6Free-Solid", "FontAwesome6Free-Regular"] and (
                    sig_id := sig.get("id")
                ):
                    icon_signature_ids.add(sig_id)

        if icon_signature_ids:
            pattern_parts = [re.escape(s) for s in icon_signature_ids]
            icon_pattern = r"«(" + "|".join(pattern_parts) + r"):[^»]*»"
            content = re.sub(icon_pattern, "", content)
            content = re.sub(r"^\s*$", "", content, flags=re.MULTILINE)
            content = re.sub(r"\n{3,}", "\n\n", content)
            result.add_step(
                StepResult(
                    step_id="5.1.1",
                    description="Remove icon font markers",
                    status=PhaseStatus.SUCCESS,
                    message=(
                        f"Removed markers for icon signatures: "
                        f"{', '.join(icon_signature_ids) if icon_signature_ids else 'None'}"
                    ),
                )
            )
        else:
            result.add_step(
                StepResult(
                    step_id="5.1.1",
                    description="Remove icon font markers",
                    status=PhaseStatus.SKIPPED,
                    message=("No icon font signatures identified or icon_config.json not found."),
                )
            )

        return content

    def _remove_whitespace_markers(self, content: str, result: PhaseResult) -> str:
        """Step 5.1.2: Remove lines with only whitespace-bearing markers.

        Args:
            content: Content to process
            result: Phase result for adding step info

        Returns:
            Processed content
        """
        cleaned_lines = []
        for line in content.split("\n"):
            stripped_line = line.strip()
            if stripped_line:
                match = FONT_MARKER_PATTERN.fullmatch(stripped_line)
                if match:
                    inner_content = match.group(2)
                    if not inner_content.strip():
                        continue
            cleaned_lines.append(line)
        content = "\n".join(cleaned_lines)
        content = re.sub(r"\n{3,}", "\n\n", content)
        result.add_step(
            StepResult(
                step_id="5.1.2",
                description="Remove lines with only whitespace-bearing markers",
                status=PhaseStatus.SUCCESS,
                message=("Removed lines consisting solely of markers containing only whitespace."),
            )
        )
        return content

    def _remove_page_number_markers(
        self,
        content: str,
        loaded_font_mapping: dict | None,
        font_mapping_load_error: bool,
        result: PhaseResult,
    ) -> str:
        """Step 5.1.3: Remove page number markers.

        Args:
            content: Content to process
            loaded_font_mapping: Loaded font mapping or None
            font_mapping_load_error: Whether there was an error loading font mapping
            result: Phase result for adding step info

        Returns:
            Processed content
        """
        page_number_signature_ids = set()
        if not font_mapping_load_error and loaded_font_mapping:
            for sig in loaded_font_mapping.get("signatures", []):
                if sig.get("candidate_heading") is False and sig.get("label") is None:
                    samples = sig.get("samples", [])
                    if (
                        len(samples) == 1
                        and samples[0].isdigit()
                        and sig.get("frequency", 0) >= 1
                        and (sig_id := sig.get("id"))
                    ):
                        page_number_signature_ids.add(sig_id)

        if page_number_signature_ids:
            pattern_parts = [re.escape(s) for s in page_number_signature_ids]
            page_number_pattern = r"«(" + "|".join(pattern_parts) + r"):\d+»"
            content = re.sub(page_number_pattern, "", content)
            content = re.sub(r"^\s*$", "", content, flags=re.MULTILINE)
            content = re.sub(r"\n{3,}", "\n\n", content)
            result.add_step(
                StepResult(
                    step_id="5.1.3",
                    description="Remove page number markers",
                    status=PhaseStatus.SUCCESS,
                    message=(
                        "Removed page number markers for signatures: "
                        f"{', '.join(page_number_signature_ids)}"
                    ),
                )
            )
        else:
            result.add_step(
                StepResult(
                    step_id="5.1.3",
                    description="Remove page number markers",
                    status=PhaseStatus.SKIPPED,
                    message=(
                        "No page number signatures identified"
                        " or font-family-mapping.json not loaded/valid."
                    ),
                )
            )
        return content

    def _detect_footer_watermarks_from_config(self, output_dir: Path) -> set[str]:
        """Detect footer/watermark signatures from footer_config.json.

        Args:
            output_dir: Output directory for finding footer_config.json

        Returns:
            Set of detected signature IDs
        """
        footer_watermark_signature_ids = set()
        footer_config_path = output_dir / "footer_config.json"

        if footer_config_path.exists():
            try:
                with open(footer_config_path, encoding="utf-8") as f:
                    footer_config = json.load(f)

                for sig in footer_config.get("watermark_signatures", []):
                    if sig_id := sig.get("sig_id"):
                        footer_watermark_signature_ids.add(sig_id)
                for sig in footer_config.get("page_number_signatures", []):
                    if sig_id := sig.get("sig_id"):
                        footer_watermark_signature_ids.add(sig_id)
                for sig in footer_config.get("footer_signatures", []):
                    if sig_id := sig.get("sig_id"):
                        footer_watermark_signature_ids.add(sig_id)
            except Exception as e:
                logger.warning(f"Failed to load footer_config.json: {e}")

        return footer_watermark_signature_ids

    def _detect_footer_watermarks_legacy(self, loaded_font_mapping: dict | None) -> set[str]:
        """Detect footer/watermark signatures using legacy heuristics.

        Args:
            loaded_font_mapping: Loaded font mapping or None

        Returns:
            Set of detected signature IDs
        """
        footer_watermark_signature_ids = set()

        if loaded_font_mapping:
            for sig in loaded_font_mapping.get("signatures", []):
                if (
                    sig.get("size", 0) < FOOTER_WATERMARK_MAX_FONT_SIZE
                    and sig.get("candidate_heading") is False
                    and sig.get("label") is None
                ):
                    samples = sig.get("samples", [])
                    if (
                        samples
                        and (
                            "naturalcrit" in samples[0].lower()
                            or samples[0].upper().startswith("PART")
                        )
                        and (sig_id := sig.get("id"))
                    ):
                        footer_watermark_signature_ids.add(sig_id)

        return footer_watermark_signature_ids

    def _remove_footer_watermark_markers(
        self,
        content: str,
        output_dir: Path,
        loaded_font_mapping: dict | None,
        font_mapping_load_error: bool,
        result: PhaseResult,
    ) -> str:
        """Step 5.1.4: Remove footer/watermark markers using footer_config.json.

        Args:
            content: Content to process
            output_dir: Output directory for finding footer_config.json
            loaded_font_mapping: Loaded font mapping or None
            font_mapping_load_error: Whether there was an error loading font mapping
            result: Phase result for adding step info

        Returns:
            Processed content
        """
        footer_watermark_signature_ids = self._detect_footer_watermarks_from_config(output_dir)

        # Fallback to legacy detection if no footer_config.json
        if not footer_watermark_signature_ids and not font_mapping_load_error:
            footer_watermark_signature_ids = self._detect_footer_watermarks_legacy(
                loaded_font_mapping
            )

        if footer_watermark_signature_ids:
            pattern_parts = [re.escape(s) for s in footer_watermark_signature_ids]
            footer_watermark_pattern = r"«(" + "|".join(pattern_parts) + r"):[^»]*»"
            content = re.sub(footer_watermark_pattern, "", content)
            content = re.sub(r"^\s*$", "", content, flags=re.MULTILINE)
            content = re.sub(r"\n{3,}", "\n\n", content)
            result.add_step(
                StepResult(
                    step_id="5.1.4",
                    description="Remove footer/watermark markers",
                    status=PhaseStatus.SUCCESS,
                    message=(
                        "Removed footer/watermark markers for signatures: "
                        f"{', '.join(footer_watermark_signature_ids)}"
                    ),
                )
            )
        else:
            result.add_step(
                StepResult(
                    step_id="5.1.4",
                    description="Remove footer/watermark markers",
                    status=PhaseStatus.SKIPPED,
                    message=(
                        "No footer/watermark signatures identified or footer_config.json not found."
                    ),
                )
            )
        return content

    def _normalize_line_breaks(self, content: str, result: PhaseResult) -> str:
        """Step 5.2: Normalize line breaks.

        Args:
            content: Content to process
            result: Phase result for adding step info

        Returns:
            Processed content
        """
        # Remove extra blank lines
        content = re.sub(r"\n{3,}", "\n\n", content)

        # Fix line breaks within paragraphs
        lines = content.split("\n")
        merged_lines = []
        current_para = ""

        for line in lines:
            stripped = line.strip()

            if not stripped:
                if current_para:
                    merged_lines.append(current_para)
                    current_para = ""
                merged_lines.append("")
                continue

            is_special = (
                stripped.startswith("<!--")
                or stripped.startswith("#")
                or stripped.startswith("«")
                or stripped.isupper()
            )

            if is_special:
                if current_para:
                    merged_lines.append(current_para)
                    current_para = ""
                merged_lines.append(line)
            elif current_para:
                current_para += " " + stripped
            else:
                current_para = stripped

        if current_para:
            merged_lines.append(current_para)

        content = "\n".join(merged_lines)

        result.add_step(
            StepResult(
                step_id="5.2",
                description="Normalize line breaks",
                status=PhaseStatus.SUCCESS,
                message="Merged soft line breaks within paragraphs",
            )
        )
        return content

    def _fix_spacing(self, content: str, result: PhaseResult) -> str:
        """Step 5.3: Fix spacing issues.

        Args:
            content: Content to process
            result: Phase result for adding step info

        Returns:
            Processed content
        """
        content = re.sub(r" {2,}", " ", content)
        content = re.sub(r" ([.,;:!?])", r"\1", content)
        content = re.sub(r"([\[(]) ", r"\1", content)
        content = re.sub(r" ([\])])", r"\1", content)

        result.add_step(
            StepResult(
                step_id="5.3",
                description="Fix spacing issues",
                status=PhaseStatus.SUCCESS,
                message="Normalized spacing around punctuation",
            )
        )
        return content

    def _normalize_quotes(self, content: str, result: PhaseResult) -> str:
        """Step 5.4: Normalize smart quotes and dashes.

        Args:
            content: Content to process
            result: Phase result for adding step info

        Returns:
            Processed content
        """
        content = content.replace('"', '"').replace('"', '"')
        content = content.replace("'", "'").replace("'", "'")
        content = content.replace("—", "--").replace("–", "-")
        content = content.replace("…", "...")

        result.add_step(
            StepResult(
                step_id="5.4",
                description="Normalize smart quotes and dashes",
                status=PhaseStatus.SUCCESS,
                message="Converted smart quotes and dashes to ASCII",
            )
        )
        return content

    def execute(self, state: ConversionState) -> PhaseResult:
        """Execute character-level fix steps.

        Args:
            state: Current conversion state

        Returns:
            PhaseResult with fix results
        """
        result = self.create_result()
        output_dir = Path(state.output_dir)
        pdf_name = Path(state.pdf_path).stem

        input_path = output_dir / f"{pdf_name}-phase4.md"
        output_path = output_dir / f"{pdf_name}-phase5.md"
        font_mapping_path = output_dir / "font-family-mapping.json"

        if not input_path.exists():
            result.add_error(f"Phase input file not found - run previous phase first: {input_path}")
            result.status = PhaseStatus.ERROR
            result.complete()
            return result

        loaded_font_mapping, font_mapping_load_error = self._load_font_mapping(font_mapping_path)

        try:
            with open(input_path, encoding="utf-8") as f:
                content = f.read()

            # Step 5.1: Backtick-wrap HTML tags and markdown-sensitive characters
            content = _wrap_md_sensitive_chars(content)
            result.add_step(
                StepResult(
                    step_id="5.1",
                    description="Backtick-wrap HTML tags and markdown-sensitive characters",
                    status=PhaseStatus.SUCCESS,
                    message="Wrapped markdown-sensitive elements in backticks inside markers",
                )
            )

            # Steps 5.1.1 - 5.1.4
            content = self._remove_icon_font_markers(
                content, output_dir, loaded_font_mapping, font_mapping_load_error, result
            )
            content = self._remove_whitespace_markers(content, result)
            content = self._remove_page_number_markers(
                content, loaded_font_mapping, font_mapping_load_error, result
            )
            content = self._remove_footer_watermark_markers(
                content, output_dir, loaded_font_mapping, font_mapping_load_error, result
            )

            # Steps 5.2 - 5.4
            content = self._normalize_line_breaks(content, result)
            content = self._fix_spacing(content, result)
            content = self._normalize_quotes(content, result)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            result.output_file = str(output_path)

        except Exception as e:
            result.add_error(f"Character-level fixes failed: {e}")

        result.complete()
        return result
