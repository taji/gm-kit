"""Phase 3: TOC & Font Extraction.

Code steps 3.1, 3.3-3.6: Extract TOC, sample fonts, generate font-family-mapping.json.
Agent step 3.2 is stubbed (visual TOC parsing).
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

# Maximum number of text samples to store per font signature
MAX_FONT_SAMPLES = 3

# Maximum heading level for candidate detection
MAX_HEADING_LEVEL = 3


class Phase3(Phase):
    """Phase 3: TOC & Font Extraction.

    Extracts embedded TOC, samples fonts with full signatures
    (family + size + weight + style), and generates font-family-mapping.json.
    """

    @property
    def phase_num(self) -> int:
        return 3

    @property
    def has_agent_steps(self) -> bool:
        return True  # Step 3.2: Parse visual TOC page

    def _extract_toc(self, pdf_path: Path, output_dir: Path, result: PhaseResult) -> list[dict]:
        """Step 3.1: Extract embedded TOC from PDF.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Output directory for saving TOC file
            result: Phase result for adding warnings

        Returns:
            List of TOC entries
        """
        toc_entries = []
        try:
            doc = fitz.open(pdf_path)
            toc = doc.get_toc()

            if toc:
                for level, title, page in toc:
                    toc_entries.append(
                        {
                            "level": level,
                            "title": title,
                            "page": page,
                        }
                    )
                message = f"Found {len(toc_entries)} TOC entries"
                status = PhaseStatus.SUCCESS
            else:
                message = "No embedded TOC found"
                status = PhaseStatus.WARNING
                result.add_warning("No embedded TOC found - will use font-based detection only")

            doc.close()

            # Save TOC to file
            toc_path = output_dir / "toc-extracted.txt"
            with open(toc_path, "w", encoding="utf-8") as f:
                for entry in toc_entries:
                    indent = "  " * (entry["level"] - 1)
                    f.write(f"{indent}{entry['title']} (page {entry['page']})\n")

            result.add_step(
                StepResult(
                    step_id="3.1",
                    description="Extract embedded TOC",
                    status=status,
                    message=message,
                )
            )

        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="3.1",
                    description="Extract embedded TOC",
                    status=PhaseStatus.WARNING,
                    message=f"TOC extraction error: {e}",
                )
            )
            result.add_warning(f"TOC extraction error: {e}")

        return toc_entries

    def _sample_fonts(self, pdf_path: Path, result: PhaseResult) -> list[dict] | None:
        """Step 3.3: Sample fonts from body text.

        Args:
            pdf_path: Path to the PDF file
            result: Phase result for adding errors

        Returns:
            List of font signatures, or None if error
        """
        font_signatures: list[dict] = []
        try:
            doc = fitz.open(pdf_path)

            # Sample fonts from first few pages
            for page_num in range(min(5, len(doc))):
                page = doc[page_num]
                text_dict = page.get_text("dict")  # type: ignore[no-untyped-call]
                blocks: list[dict] = text_dict.get("blocks", [])  # type: ignore[no-untyped-call]

                for block in blocks:
                    if "lines" in block:
                        for line in block.get("lines", []):  # type: ignore[no-untyped-call]
                            for span in line.get("spans", []):  # type: ignore[no-untyped-call]
                                font_info = {
                                    "family": span.get("font", "Unknown"),  # type: ignore[no-untyped-call]
                                    "size": round(span.get("size", 0), 1),  # type: ignore[no-untyped-call]
                                    "flags": span.get("flags", 0),  # type: ignore[no-untyped-call]
                                    "text_sample": span.get("text", "")[:50],  # type: ignore[no-untyped-call]
                                }

                                # Extract weight/style from flags
                                # flags: 1=bold, 2=italic
                                flags = span.get("flags", 0)  # type: ignore[no-untyped-call]
                                font_info["weight"] = "bold" if flags & 1 else "normal"
                                font_info["style"] = "italic" if flags & 2 else "normal"

                                # Create full signature
                                signature_key = (
                                    f"{font_info['family']}|"
                                    f"{font_info['size']}|"
                                    f"{font_info['weight']}|"
                                    f"{font_info['style']}"
                                )

                                # Add if not already seen
                                if not any(
                                    s.get("signature_key") == signature_key for s in font_signatures
                                ):
                                    font_info["signature_key"] = signature_key
                                    font_signatures.append(font_info)

            doc.close()

            result.add_step(
                StepResult(
                    step_id="3.3",
                    description="Sample fonts from body text",
                    status=PhaseStatus.SUCCESS,
                    message=f"Found {len(font_signatures)} unique font signatures",
                )
            )

            return font_signatures

        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="3.3",
                    description="Sample fonts from body text",
                    status=PhaseStatus.ERROR,
                    message=str(e),
                )
            )
            result.add_error(f"Font sampling failed: {e}")
            return None

    def _build_frequency_map(self, font_signatures: list[dict], result: PhaseResult) -> dict | None:
        """Step 3.4: Build frequency map from font signatures.

        Args:
            font_signatures: List of font signatures
            result: Phase result for adding errors

        Returns:
            Frequency map dictionary, or None if error
        """
        try:
            # Group by full signature (family + size + weight + style)
            frequency_map = {}
            for sig in font_signatures:
                key = sig["signature_key"]
                if key not in frequency_map:
                    frequency_map[key] = {
                        "family": sig["family"],
                        "size": sig["size"],
                        "weight": sig["weight"],
                        "style": sig["style"],
                        "count": 0,
                        "samples": [],
                    }
                frequency_map[key]["count"] += 1
                if len(frequency_map[key]["samples"]) < MAX_FONT_SAMPLES:
                    frequency_map[key]["samples"].append(sig["text_sample"])

            result.add_step(
                StepResult(
                    step_id="3.4",
                    description="Build frequency map",
                    status=PhaseStatus.SUCCESS,
                    message=f"Mapped {len(frequency_map)} unique signatures",
                )
            )

            return frequency_map

        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="3.4",
                    description="Build frequency map",
                    status=PhaseStatus.ERROR,
                    message=str(e),
                )
            )
            result.add_error(f"Frequency map build failed: {e}")
            return None

    def _detect_candidate_headings(self, frequency_map: dict, result: PhaseResult) -> None:
        """Step 3.5: Detect candidate headings from frequency map.

        Args:
            frequency_map: Frequency map dictionary (modified in place)
            result: Phase result for adding warnings
        """
        try:
            # Sort by size (descending) - larger fonts are likely headings
            sorted_sigs = sorted(
                frequency_map.values(),
                key=lambda x: (x["size"], x["count"]),
                reverse=True,
            )

            # Mark top candidates as headings
            for i, sig in enumerate(sorted_sigs[:5]):
                sig["candidate_heading"] = True
                sig["suggested_level"] = i + 1 if i < MAX_HEADING_LEVEL else MAX_HEADING_LEVEL

            result.add_step(
                StepResult(
                    step_id="3.5",
                    description="Detect candidate headings",
                    status=PhaseStatus.SUCCESS,
                    message=f"Identified {min(5, len(sorted_sigs))} candidate heading signatures",
                )
            )

        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="3.5",
                    description="Detect candidate headings",
                    status=PhaseStatus.WARNING,
                    message=f"Heading detection error: {e}",
                )
            )
            result.add_warning(f"Heading detection error: {e}")

    def _generate_font_mapping(
        self, frequency_map: dict, output_dir: Path, result: PhaseResult
    ) -> dict | None:
        """Step 3.6: Generate font-family-mapping.json.

        Args:
            frequency_map: Frequency map dictionary
            output_dir: Output directory for saving mapping file
            result: Phase result for adding errors

        Returns:
            Mapping dictionary, or None if error
        """
        try:
            signatures: list[dict] = []
            for _sig_key, sig_data in frequency_map.items():
                signatures.append(
                    {
                        "family": sig_data["family"],
                        "size": sig_data["size"],
                        "weight": sig_data["weight"],
                        "style": sig_data["style"],
                        "frequency": sig_data["count"],
                        "samples": sig_data["samples"],
                        "candidate_heading": sig_data.get("candidate_heading", False),
                        "suggested_level": sig_data.get("suggested_level"),
                        "label": None,  # To be filled by user/agent
                    }
                )

            # Sort signatures by size (descending) for consistency
            signatures.sort(
                key=lambda x: (x["size"], x["frequency"]),
                reverse=True,
            )

            # Add unique IDs to each signature (sig001, sig002, etc.)
            for i, sig in enumerate(signatures, start=1):
                sig["id"] = f"sig{i:03d}"

            mapping: dict = {
                "version": "1.0",
                "signatures": signatures,
                "metadata": {
                    "total_signatures": len(frequency_map),
                    "candidate_headings": sum(
                        1 for s in frequency_map.values() if s.get("candidate_heading")
                    ),
                },
            }

            mapping_path = output_dir / "font-family-mapping.json"
            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=2, sort_keys=False)

            result.add_step(
                StepResult(
                    step_id="3.6",
                    description="Generate font-family-mapping.json",
                    status=PhaseStatus.SUCCESS,
                    message=f"Saved {len(mapping['signatures'])} signatures to {mapping_path}",
                )
            )
            result.output_file = str(mapping_path)

            return mapping

        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="3.6",
                    description="Generate font-family-mapping.json",
                    status=PhaseStatus.ERROR,
                    message=str(e),
                )
            )
            result.add_error(f"Failed to generate font mapping: {e}")
            return None

    def _run_footer_watermark_detection(
        self, pdf_path: Path, mapping: dict, output_dir: Path, result: PhaseResult
    ) -> None:
        """Step 3.7: Detect footer, watermark, and page number signatures.

        Args:
            pdf_path: Path to the PDF file
            mapping: Font family mapping dictionary
            output_dir: Output directory for saving config
            result: Phase result for adding warnings
        """
        try:
            footer_analysis = self._analyze_footer_watermarks(pdf_path, mapping, output_dir)

            total_detected = (
                len(footer_analysis.get("watermark_signatures", []))
                + len(footer_analysis.get("page_number_signatures", []))
                + len(footer_analysis.get("footer_signatures", []))
            )

            if total_detected > 0:
                result.add_step(
                    StepResult(
                        step_id="3.7",
                        description="Detect footer and watermark signatures",
                        status=PhaseStatus.SUCCESS,
                        message=(
                            f"Detected {total_detected} patterns: "
                            f"W:{len(footer_analysis.get('watermark_signatures', []))},"
                            f" P:{len(footer_analysis.get('page_number_signatures', []))},"
                            f" F:{len(footer_analysis.get('footer_signatures', []))}"
                        ),
                    )
                )
            else:
                result.add_step(
                    StepResult(
                        step_id="3.7",
                        description="Detect footer and watermark signatures",
                        status=PhaseStatus.SUCCESS,
                        message="No footer/watermark patterns detected",
                    )
                )

        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="3.7",
                    description="Detect footer and watermark signatures",
                    status=PhaseStatus.WARNING,
                    message=f"Footer detection error: {e}",
                )
            )
            result.add_warning(f"Footer/watermark detection error: {e}")

    def _run_icon_font_detection(
        self, pdf_path: Path, mapping: dict, output_dir: Path, result: PhaseResult
    ) -> None:
        """Step 3.8: Detect icon font signatures.

        Args:
            pdf_path: Path to the PDF file
            mapping: Font family mapping dictionary
            output_dir: Output directory for saving config
            result: Phase result for adding warnings
        """
        try:
            icon_analysis = self._analyze_icon_fonts(pdf_path, mapping, output_dir)

            if icon_analysis.get("icon_signatures"):
                result.add_step(
                    StepResult(
                        step_id="3.8",
                        description="Detect icon font signatures",
                        status=PhaseStatus.SUCCESS,
                        message=(
                            f"Detected {len(icon_analysis['icon_signatures'])} icon font signatures"
                        ),
                    )
                )
            else:
                result.add_step(
                    StepResult(
                        step_id="3.8",
                        description="Detect icon font signatures",
                        status=PhaseStatus.SUCCESS,
                        message="No icon font signatures detected",
                    )
                )

        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="3.8",
                    description="Detect icon font signatures",
                    status=PhaseStatus.WARNING,
                    message=f"Icon font detection error: {e}",
                )
            )
            result.add_warning(f"Icon font detection error: {e}")

    def execute(self, state: ConversionState) -> PhaseResult:
        """Execute TOC and font extraction steps.

        Args:
            state: Current conversion state

        Returns:
            PhaseResult with extraction results
        """
        result = self.create_result()
        pdf_path = Path(state.pdf_path)
        output_dir = Path(state.output_dir)

        # Step 3.1: Extract embedded TOC
        self._extract_toc(pdf_path, output_dir, result)

        # Step 3.2: Parse visual TOC page (AGENT STEP - STUBBED)
        result.add_step(
            StepResult(
                step_id="3.2",
                description="Parse visual TOC page (AGENT)",
                status=PhaseStatus.SUCCESS,
                message="Stub: Agent step will be implemented in E4-07b",
            )
        )

        # Step 3.3: Sample fonts from body text
        font_signatures = self._sample_fonts(pdf_path, result)
        if font_signatures is None:
            result.complete()
            return result

        # Step 3.4: Build frequency map
        frequency_map_result = self._build_frequency_map(font_signatures, result)
        if frequency_map_result is None:
            result.complete()
            return result
        frequency_map: dict = frequency_map_result

        # Step 3.5: Detect candidate headings
        self._detect_candidate_headings(frequency_map, result)

        # Step 3.6: Generate font-family-mapping.json
        mapping_result = self._generate_font_mapping(frequency_map, output_dir, result)
        if mapping_result is None:
            result.complete()
            return result
        mapping: dict = mapping_result

        # Step 3.7: Detect footer, watermark, and page number signatures
        self._run_footer_watermark_detection(pdf_path, mapping, output_dir, result)

        # Step 3.8: Detect icon font signatures
        self._run_icon_font_detection(pdf_path, mapping, output_dir, result)

        result.complete()
        return result

    def _analyze_footer_watermarks(self, pdf_path: Path, mapping: dict, output_dir: Path) -> dict:  # noqa: PLR0912
        """Analyze PDF for footer, watermark, and page number signatures.

        Detection order:
        1. Watermarks: 100% frequency, identical content
        2. Page numbers: 100% frequency, sequential content, top/bottom position
        3. Footers: >80% frequency, bottom position

        Args:
            pdf_path: Path to the PDF file
            mapping: The font-family-mapping.json dict with signatures
            output_dir: Output directory path

        Returns:
            Dictionary with detected signature IDs by category
        """
        import fitz

        doc = fitz.open(pdf_path)
        total_pages = doc.page_count

        # Build lookup from signature attributes to sig_id
        sig_lookup: dict[tuple, str] = {}
        for sig in mapping.get("signatures", []):
            key = (sig.get("family", ""), sig.get("size", 0))
            sig_lookup[key] = sig.get("id", "")

        # Track signature occurrences across pages
        sig_occurrences: dict[str, list[dict]] = {}

        for page_idx in range(total_pages):
            page = doc[page_idx]
            blocks = page.get_text("dict")["blocks"]  # type: ignore[index]
            page_height = page.rect.height

            for block in blocks:
                if "lines" not in block:
                    continue

                for line in block["lines"]:  # type: ignore[index]
                    for span in line["spans"]:  # type: ignore[index]
                        font_name = span.get("font", "Unknown")  # type: ignore[attr-defined]
                        font_size = span.get("size", 0)  # type: ignore[attr-defined]
                        text = span.get("text", "").strip()  # type: ignore[attr-defined]

                        if not text:
                            continue

                        # Get position
                        y_pos = span.get("origin", [0, 0])[1]  # type: ignore[attr-defined]
                        is_top = y_pos < page_height * 0.15
                        is_bottom = y_pos > page_height * 0.85

                        # Find matching signature ID
                        FONT_SIZE_TOLERANCE = 0.5
                        matched_sig_id = None
                        for (fam, size), sig_id in sig_lookup.items():
                            if fam == font_name and abs(size - font_size) < FONT_SIZE_TOLERANCE:
                                matched_sig_id = sig_id
                                break

                        if not matched_sig_id:
                            continue

                        if matched_sig_id not in sig_occurrences:
                            sig_occurrences[matched_sig_id] = []

                        sig_occurrences[matched_sig_id].append(
                            {
                                "page": page_idx,
                                "text": text,
                                "y_pos": y_pos,
                                "is_top": is_top,
                                "is_bottom": is_bottom,
                                "font_size": font_size,
                            }
                        )

        doc.close()

        # Analyze patterns
        watermark_sigs = []
        page_number_sigs = []
        footer_sigs = []

        for sig_id, occurrences in sig_occurrences.items():
            frequency = len(occurrences) / total_pages
            MIN_FOOTER_FREQUENCY = 0.8

            if frequency < MIN_FOOTER_FREQUENCY:
                continue

            texts = [occ["text"] for occ in occurrences]
            unique_texts = set(texts)

            is_identical = len(unique_texts) == 1
            is_top_consistent = all(occ["is_top"] for occ in occurrences)
            is_bottom_consistent = all(occ["is_bottom"] for occ in occurrences)

            avg_font_size = sum(occ["font_size"] for occ in occurrences) / len(occurrences)
            SMALL_FONT_THRESHOLD = 9.0
            is_small_font = avg_font_size < SMALL_FONT_THRESHOLD

            is_sequential = self._is_sequential_page_numbers(texts)

            # Detection order: Watermark -> Page Number -> Footer
            if frequency == 1.0 and is_identical:
                watermark_sigs.append(
                    {
                        "sig_id": sig_id,
                        "sample": list(unique_texts)[0],
                        "confidence": "high",
                    }
                )
            elif frequency == 1.0 and is_sequential and (is_top_consistent or is_bottom_consistent):
                position = "top" if is_top_consistent else "bottom"
                page_number_sigs.append(
                    {
                        "sig_id": sig_id,
                        "sample": texts[0] if texts else "",
                        "position": position,
                        "confidence": "high",
                    }
                )
            elif is_bottom_consistent or (is_small_font and frequency > 0.9):  # noqa: PLR2004
                footer_sigs.append(
                    {
                        "sig_id": sig_id,
                        "sample": texts[0] if texts else "",
                        "position": "bottom" if is_bottom_consistent else "mixed",
                        "confidence": "medium" if is_bottom_consistent else "low",
                    }
                )

        result = {
            "watermark_signatures": watermark_sigs,
            "page_number_signatures": page_number_sigs,
            "footer_signatures": footer_sigs,
        }

        # Write footer_config.json
        footer_config_path = output_dir / "footer_config.json"
        with open(footer_config_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        return result

    def _is_sequential_page_numbers(self, texts: list[str]) -> bool:
        """Check if texts represent sequential page numbers."""
        MIN_TEXTS_FOR_SEQUENCE = 2
        if len(texts) < MIN_TEXTS_FOR_SEQUENCE:
            return False

        # Try integers
        try:
            numbers = [int(t) for t in texts if t.isdigit()]
            if len(numbers) >= MIN_TEXTS_FOR_SEQUENCE:
                return all(numbers[i] == numbers[i - 1] + 1 for i in range(1, len(numbers)))
        except ValueError:
            pass

        # Try roman numerals
        roman_values = {
            "i": 1,
            "ii": 2,
            "iii": 3,
            "iv": 4,
            "v": 5,
            "vi": 6,
            "vii": 7,
            "viii": 8,
            "ix": 9,
            "x": 10,
        }
        try:
            lower_texts = [t.lower() for t in texts if t.lower() in roman_values]
            numbers = [roman_values[t] for t in lower_texts]
            if len(numbers) >= MIN_TEXTS_FOR_SEQUENCE:
                return all(numbers[i] == numbers[i - 1] + 1 for i in range(1, len(numbers)))
        except (ValueError, KeyError):
            pass

        return False

    def _check_is_icon_font_name(self, family: str) -> bool:
        """Check if font family name matches known icon font patterns.

        Args:
            family: Font family name (lowercase)

        Returns:
            True if font name indicates an icon font
        """
        icon_patterns = [
            "fontawesome",
            "material",
            "glyphicons",
            "icomoon",
            "icon",
            "symbol",
            "wingdings",
            "webdings",
        ]
        return any(pattern in family for pattern in icon_patterns)

    def _check_has_private_use_chars(self, texts: list[str]) -> bool:
        """Check if any text contains private-use-area Unicode characters.

        Args:
            texts: List of text strings to check

        Returns:
            True if any text contains U+E000-U+F8FF characters
        """
        for text in texts:
            for char in text:
                if "\ue000" <= char <= "\uf8ff":
                    return True
        return False

    def _check_is_short_content(self, texts: list[str]) -> bool:
        """Check if content is mostly very short (glyphs).

        Args:
            texts: List of text strings to check

        Returns:
            True if average length is <= 2 characters
        """
        ICON_MAX_LENGTH = 2
        if not texts:
            return False
        avg_length = sum(len(t) for t in texts) / len(texts)
        return avg_length <= ICON_MAX_LENGTH

    def _analyze_single_icon_signature(
        self,
        sig_id: str,
        texts: list[str],
        mapping: dict,
    ) -> dict | None:
        """Analyze a single signature for icon font characteristics.

        Args:
            sig_id: Signature ID
            texts: List of text content for this signature
            mapping: Font family mapping

        Returns:
            Icon signature dict or None if not an icon font
        """
        # Get font family name
        family = ""
        for sig in mapping.get("signatures", []):
            if sig.get("id") == sig_id:
                family = sig.get("family", "").lower()
                break

        is_icon_font_name = self._check_is_icon_font_name(family)
        has_private_use_chars = self._check_has_private_use_chars(texts)
        is_short_content = self._check_is_short_content(texts)

        # High confidence: matches icon font name OR has private use chars
        if is_icon_font_name or has_private_use_chars:
            reason = []
            if is_icon_font_name:
                reason.append(f"font name: {family}")
            if has_private_use_chars:
                reason.append("private-use Unicode")
            return {
                "sig_id": sig_id,
                "font_family": family,
                "confidence": "high",
                "reason": "; ".join(reason),
                "sample": texts[0] if texts else "",
            }
        elif is_short_content:
            # Medium confidence: very short content only
            return {
                "sig_id": sig_id,
                "font_family": family,
                "confidence": "medium",
                "reason": "very short content (likely glyphs)",
                "sample": texts[0] if texts else "",
            }
        return None

    def _collect_sig_content_from_pdf(self, pdf_path: Path, mapping: dict) -> dict[str, list[str]]:
        """Collect text content per signature from PDF.

        Args:
            pdf_path: Path to the PDF file
            mapping: Font family mapping

        Returns:
            Dictionary mapping sig_id to list of text content
        """
        import fitz

        doc = fitz.open(pdf_path)
        sig_content: dict[str, list[str]] = {}
        FONT_SIZE_TOLERANCE = 0.5

        # Build lookup
        sig_lookup: dict[tuple, str] = {}
        for sig in mapping.get("signatures", []):
            key = (sig.get("family", ""), sig.get("size", 0))
            sig_lookup[key] = sig.get("id", "")

        for page in doc:
            text_dict = page.get_text("dict")  # type: ignore[no-untyped-call]
            blocks: list[dict] = text_dict.get("blocks", [])  # type: ignore[no-untyped-call]

            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block.get("lines", []):  # type: ignore[no-untyped-call]
                    for span in line.get("spans", []):  # type: ignore[no-untyped-call]
                        font_name = span.get("font", "Unknown")  # type: ignore[no-untyped-call]
                        font_size = span.get("size", 0)  # type: ignore[no-untyped-call]
                        text = span.get("text", "")  # type: ignore[no-untyped-call]

                        # Find matching signature
                        matched_sig_id = None
                        for (fam, size), sig_id in sig_lookup.items():
                            if fam == font_name and abs(size - font_size) < FONT_SIZE_TOLERANCE:
                                matched_sig_id = sig_id
                                break

                        if matched_sig_id:
                            sig_content.setdefault(matched_sig_id, []).append(text)

        doc.close()
        return sig_content

    def _analyze_icon_fonts(self, pdf_path: Path, mapping: dict, output_dir: Path) -> dict:
        """Analyze PDF for icon font signatures.

        Icon fonts are detected by:
        1. Known icon font names (FontAwesome, Material Icons, etc.)
        2. Private-use-area Unicode characters (U+E000-U+F8FF)
        3. Empty or very short content (glyphs)

        Args:
            pdf_path: Path to the PDF file
            mapping: The font-family-mapping.json dict with signatures
            output_dir: Output directory path

        Returns:
            Dictionary with detected icon signature IDs
        """
        # Collect text content per signature
        sig_content = self._collect_sig_content_from_pdf(pdf_path, mapping)

        # Analyze signatures for icon font characteristics
        icon_sigs = []
        for sig_id, texts in sig_content.items():
            icon_sig = self._analyze_single_icon_signature(sig_id, texts, mapping)
            if icon_sig:
                icon_sigs.append(icon_sig)

        result = {"icon_signatures": icon_sigs}

        # Write icon_config.json
        icon_config_path = output_dir / "icon_config.json"
        with open(icon_config_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        return result
