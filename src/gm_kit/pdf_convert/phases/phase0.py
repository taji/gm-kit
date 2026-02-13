"""Phase 0: Pre-flight Analysis.

Code steps 0.1-0.5: PDF validation, metadata extraction, TOC detection,
text extractability check, and complexity analysis.
Step 0.6: Create default callout configuration file.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from gm_kit.pdf_convert.metadata import extract_metadata, save_metadata
from gm_kit.pdf_convert.phases.base import Phase, PhaseResult, PhaseStatus, StepResult
from gm_kit.pdf_convert.preflight import analyze_pdf

if TYPE_CHECKING:
    from gm_kit.pdf_convert.state import ConversionState

logger = logging.getLogger(__name__)

# Complexity thresholds for page count
HIGH_PAGE_THRESHOLD = 100
MEDIUM_PAGE_THRESHOLD = 50

# Complexity thresholds for font family count
HIGH_FONT_THRESHOLD = 10
MEDIUM_FONT_THRESHOLD = 5


class Phase0(Phase):
    """Phase 0: Pre-flight Analysis.

    Validates PDF and produces initial analysis without modifying state.
    User confirmation (step 0.6) is handled by orchestrator, not this phase.
    """

    @property
    def phase_num(self) -> int:
        return 0

    def execute(self, state: ConversionState) -> PhaseResult:  # noqa: PLR0912
        """Execute pre-flight analysis steps.

        Args:
            state: Current conversion state

        Returns:
            PhaseResult with analysis results
        """
        result = self.create_result()
        pdf_path = Path(state.pdf_path)

        # Step 0.1: Extract PDF metadata
        try:
            metadata = extract_metadata(pdf_path)
            save_metadata(metadata, Path(state.output_dir))
            result.add_step(
                StepResult(
                    step_id="0.1",
                    description="Extract PDF metadata",
                    status=PhaseStatus.SUCCESS,
                    message=f"Title: {metadata.title or 'N/A'}, Pages: {metadata.page_count}",
                )
            )
        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="0.1",
                    description="Extract PDF metadata",
                    status=PhaseStatus.ERROR,
                    message=str(e),
                )
            )
            result.add_error(f"Failed to extract metadata: {e}")
            result.complete()
            return result

        # Step 0.2: Detect embedded TOC
        try:
            has_toc = metadata.has_toc
            result.add_step(
                StepResult(
                    step_id="0.2",
                    description="Detect embedded TOC",
                    status=PhaseStatus.SUCCESS,
                    message=f"TOC present: {has_toc}",
                )
            )
        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="0.2",
                    description="Detect embedded TOC",
                    status=PhaseStatus.WARNING,
                    message=f"TOC detection error: {e}",
                )
            )
            result.add_warning(f"TOC detection error: {e}")

        # Step 0.3: Check text extractability
        report = None
        try:
            report = analyze_pdf(pdf_path)
            text_extractable = report.text_extractable
            status = PhaseStatus.SUCCESS if text_extractable else PhaseStatus.ERROR
            message = "Text extractable" if text_extractable else "Scanned PDF detected"
            result.add_step(
                StepResult(
                    step_id="0.3",
                    description="Check text extractability",
                    status=status,
                    message=message,
                )
            )
            if not text_extractable:
                result.add_error("Scanned PDF detected - very little extractable text")
        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="0.3",
                    description="Check text extractability",
                    status=PhaseStatus.WARNING,
                    message=f"Extractability check error: {e}",
                )
            )
            result.add_warning(f"Extractability check error: {e}")

        # Step 0.4: Detect images
        try:
            if report is not None:
                image_count = report.image_count
                result.add_step(
                    StepResult(
                        step_id="0.4",
                        description="Detect images",
                        status=PhaseStatus.SUCCESS,
                        message=f"Found {image_count} images",
                    )
                )
            else:
                result.add_step(
                    StepResult(
                        step_id="0.4",
                        description="Detect images",
                        status=PhaseStatus.WARNING,
                        message="Image detection skipped - preflight report unavailable",
                    )
                )
        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="0.4",
                    description="Detect images",
                    status=PhaseStatus.WARNING,
                    message=f"Image detection error: {e}",
                )
            )
            result.add_warning(f"Image detection error: {e}")

        # Step 0.5: Complexity analysis
        try:
            page_count = metadata.page_count
            font_families = 0  # Default value

            # Try to extract font information from PDF
            try:
                import fitz

                doc = fitz.open(pdf_path)
                font_set = set()
                for page in doc:
                    for font in page.get_fonts():
                        font_set.add(font[3])  # font name is at index 3
                font_families = len(font_set)
                doc.close()
            except Exception:  # nosec B110
                pass  # If font extraction fails, use default

            # Complexity heuristic
            if page_count > HIGH_PAGE_THRESHOLD or font_families > HIGH_FONT_THRESHOLD:
                complexity = "high"
            elif page_count > MEDIUM_PAGE_THRESHOLD or font_families > MEDIUM_FONT_THRESHOLD:
                complexity = "medium"
            else:
                complexity = "low"

            result.add_step(
                StepResult(
                    step_id="0.5",
                    description="Complexity analysis",
                    status=PhaseStatus.SUCCESS,
                    message=(
                        f"Complexity: {complexity} "
                        f"({page_count} pages, {font_families} font families)"
                    ),
                )
            )
        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="0.5",
                    description="Complexity analysis",
                    status=PhaseStatus.WARNING,
                    message=f"Complexity analysis error: {e}",
                )
            )
            result.add_warning(f"Complexity analysis error: {e}")

        # Step 0.6: Create default callout configuration file
        try:
            existing_config_path = state.config.get("gm_callout_config_file")
            if existing_config_path:
                result.add_step(
                    StepResult(
                        step_id="0.6",
                        description="Create default callout configuration",
                        status=PhaseStatus.SKIPPED,
                        message=f"Using user-provided callout config: {existing_config_path}",
                    )
                )
            else:
                output_path = Path(state.output_dir)
                callout_config_path = output_path / "callout_config.json"
                if not callout_config_path.exists():
                    with open(callout_config_path, "w", encoding="utf-8") as f:
                        json.dump([], f, indent=2)
                    result.add_step(
                        StepResult(
                            step_id="0.6",
                            description="Create default callout configuration",
                            status=PhaseStatus.SUCCESS,
                            message=f"Created default callout config: {callout_config_path}",
                        )
                    )
                else:
                    result.add_step(
                        StepResult(
                            step_id="0.6",
                            description="Create default callout configuration",
                            status=PhaseStatus.SUCCESS,
                            message="Callout config already exists",
                        )
                    )
                # Store default config path for later phases when none was supplied.
                state.config["gm_callout_config_file"] = str(callout_config_path)
        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="0.6",
                    description="Create default callout configuration",
                    status=PhaseStatus.WARNING,
                    message=f"Failed to create callout config: {e}",
                )
            )
            result.add_warning(f"Callout config creation error: {e}")

        result.complete()
        return result
