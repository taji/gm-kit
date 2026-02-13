"""Phase 10: Report Generation.

Code steps 10.1, 10.4-10.6: Generate conversion report and diagnostics bundle.
Agent steps 10.2-10.3: Quality ratings and issue documentation.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from gm_kit.pdf_convert.metadata import load_metadata
from gm_kit.pdf_convert.phases.base import Phase, PhaseResult, PhaseStatus, StepResult

if TYPE_CHECKING:
    from gm_kit.pdf_convert.state import ConversionState

logger = logging.getLogger(__name__)


# Phase descriptions for the conversion report
PHASE_DETAILS: dict[int, dict[str, str]] = {
    0: {
        "name": "Pre-flight Analysis",
        "changes": (
            "Extracts PDF metadata, detects embedded TOC,"
            " analyzes text extractability,"
            " counts images, assesses complexity"
        ),
        "outputs": "metadata.json",
        "compare": (
            "Compare metadata.json with PDF properties;"
            " verify image count matches visual inspection"
        ),
    },
    1: {
        "name": "Image Extraction",
        "changes": (
            "Extracts all images from PDF pages,"
            " generates alt-text placeholders,"
            " creates image-manifest.json"
        ),
        "outputs": "images/*.png, images/image-manifest.json",
        "compare": (
            "Check images/ folder contains expected images;"
            " verify image-manifest.json has correct positions"
        ),
    },
    2: {
        "name": "Image Removal",
        "changes": (
            "Creates text-only PDF by covering images with"
            " white rectangles; preserves layout for"
            " text extraction"
        ),
        "outputs": "preprocessed/*-no-images.pdf",
        "compare": (
            "Open preprocessed/*-no-images.pdf and verify"
            " images are removed but text layout is preserved"
        ),
    },
    3: {
        "name": "TOC & Font Extraction",
        "changes": (
            "Extracts embedded TOC, samples fonts with full"
            " signatures (family+size+weight+style),"
            " generates font-family-mapping.json"
        ),
        "outputs": "toc-extracted.txt, font-family-mapping.json",
        "compare": (
            "Check toc-extracted.txt against PDF bookmarks;"
            " verify font signatures capture different"
            " heading styles"
        ),
    },
    4: {
        "name": "Text Extraction",
        "changes": (
            "Extracts raw text with font signature markers"
            " (e.g., \u00absig001:text\u00bb), detects two-column"
            " issues, chunks large documents,"
            " merges into single document"
        ),
        "outputs": "*-phase4.md (with font markers)",
        "compare": (
            "Review *-phase4.md for font markers;"
            " verify \u00absigXXX:text\u00bb markers wrap heading text"
        ),
    },
    5: {
        "name": "Character-Level Fixes",
        "changes": (
            "Normalizes line breaks, fixes spacing issues,"
            " converts smart quotes and dashes to ASCII"
        ),
        "outputs": "*-phase5.md",
        "compare": ("Compare *-phase5.md with *-phase4.md for" " spacing and character cleanup"),
    },
    6: {
        "name": "Structural Formatting",
        "changes": (
            "Fixes hyphenation at line breaks, detects and"
            " formats bullet lists, preserves indented"
            " sub-items"
        ),
        "outputs": "*-phase6.md",
        "compare": (
            "Check *-phase6.md for proper list formatting" " and removed hyphenation artifacts"
        ),
    },
    7: {
        "name": "Font Label Assignment",
        "changes": (
            "Builds heading map from TOC, detects heading"
            " patterns (ALL CAPS, Title Case),"
            " applies font labels"
        ),
        "outputs": "Updated font-family-mapping.json",
        "compare": (
            "Review font-family-mapping.json to see suggested"
            " heading labels; check GM note detection"
        ),
    },
    8: {
        "name": "Heading Insertion",
        "changes": (
            "Replaces font signature markers with markdown"
            " headings (#, ##, ###) based on"
            " font-family-mapping.json labels; formats GM"
            " notes and read-aloud text as blockquotes;"
            " inserts image placeholders"
        ),
        "outputs": ("*-phase8.md (final output," " markers converted to headings)"),
        "compare": (
            "Final *-phase8.md should have proper markdown"
            " headings replacing \u00absigXXX:text\u00bb markers;"
            " compare structure with original PDF"
        ),
    },
    9: {
        "name": "Lint & Final Review",
        "changes": (
            "Runs markdown lint checks for common issues"
            " (spacing, blank lines, list consistency)"
        ),
        "outputs": "Lint report (in conversion-report.md)",
        "compare": ("Check conversion-report.md Warnings section" " for any lint violations"),
    },
    10: {
        "name": "Report Generation",
        "changes": (
            "Generates conversion-report.md, creates"
            " completion metadata, bundles diagnostics"
            " if enabled"
        ),
        "outputs": (
            "conversion-report.md, .completion.json," " diagnostic-bundle.zip (if enabled)"
        ),
        "compare": ("This report! Verify all sections are" " complete and accurate"),
    },
}


class Phase10(Phase):
    """Phase 10: Report Generation.

    Generates the final conversion report and diagnostic bundle.
    """

    @property
    def phase_num(self) -> int:
        return 10

    @property
    def has_agent_steps(self) -> bool:
        return True  # Steps 10.2-10.3: Quality ratings and issue documentation

    def execute(self, state: ConversionState) -> PhaseResult:
        """Execute report generation steps.

        Args:
            state: Current conversion state

        Returns:
            PhaseResult with generation results
        """
        result = self.create_result()
        output_dir = Path(state.output_dir)
        pdf_name = Path(state.pdf_path).stem

        try:
            # Step 10.1: Summarize pipeline outcomes
            metadata = load_metadata(output_dir)

            # Use separate typed variables for lists
            warnings_list: list[str] = []
            errors_list: list[str] = []

            # Collect warnings and errors from phase results
            for phase_result in state.phase_results:
                phase_num = phase_result.get("phase_num")
                warnings = phase_result.get("warnings", [])
                errors = phase_result.get("errors", [])

                for warning in warnings:
                    warnings_list.append(f"Phase {phase_num}: {warning}")

                for error in errors:
                    errors_list.append(f"Phase {phase_num}: {error}")

            result.add_step(
                StepResult(
                    step_id="10.1",
                    description="Summarize pipeline outcomes",
                    status=PhaseStatus.SUCCESS,
                    message=("Summarized " f"{len(state.completed_phases)} completed phases"),
                )
            )

            # Step 10.2: Quality ratings (AGENT - STUBBED)
            result.add_step(
                StepResult(
                    step_id="10.2",
                    description="Quality ratings (AGENT)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Agent step will be implemented in E4-07b",
                )
            )

            # Step 10.3: Document remaining issues (AGENT - STUBBED)
            result.add_step(
                StepResult(
                    step_id="10.3",
                    description="Document remaining issues (AGENT)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Agent step will be implemented in E4-07b",
                )
            )

            # Step 10.4: Generate conversion-report.md
            # Use the already-typed variables directly
            pdf_title_str = metadata.title if metadata else "Unknown"
            pdf_author_str = metadata.author if metadata else "Unknown"
            page_count_num = metadata.page_count if metadata else 0
            conversion_date_str = datetime.now().isoformat()[:10]
            completed_phases_list = state.completed_phases

            # Calculate performance metrics
            started_at = datetime.fromisoformat(state.started_at)
            completed_at = datetime.now()
            duration = completed_at - started_at
            duration_str = str(timedelta(seconds=int(duration.total_seconds())))

            report_lines = [
                "# PDF Conversion Report",
                "",
                f"**Source:** {pdf_title_str}",
                f"**Author:** {pdf_author_str}",
                f"**Pages:** {page_count_num}",
                f"**Converted:** {conversion_date_str}",
                "",
                "## Pipeline Summary",
                "",
                (
                    "Completed Phases: "
                    f"{', '.join(str(p) for p in sorted(completed_phases_list))}"
                ),
                "",
                "## Phase Summary",
                "",
                "| Phase | Name | Output Files |",
                "|-------|------|--------------|",
            ]

            # Add phase summary table (concise)
            for phase_num in sorted(completed_phases_list):
                details = PHASE_DETAILS.get(phase_num, {})
                phase_name = details.get("name", f"Phase {phase_num}")
                outputs = details.get("outputs", "N/A")
                report_lines.append(f"| {phase_num} | {phase_name} | {outputs} |")

            report_lines.extend(
                [
                    "",
                    "## Phase Details",
                    "",
                ]
            )

            # Add detailed breakdown for each phase
            for phase_num in sorted(completed_phases_list):
                details = PHASE_DETAILS.get(phase_num, {})
                phase_name = details.get("name", f"Phase {phase_num}")
                outputs = details.get("outputs", "N/A")
                changes = details.get("changes", "N/A")
                compare = details.get("compare", "N/A")

                report_lines.extend(
                    [
                        f"### Phase {phase_num}: {phase_name}",
                        "",
                        f"**Output Files:** {outputs}",
                        "",
                        "**Changes Made:**",
                        changes,
                        "",
                        "**What to Compare:**",
                        compare,
                        "",
                    ]
                )

            # Add performance section
            report_lines.extend(
                [
                    "## Performance",
                    "",
                    f"**Conversion Started:** {started_at.isoformat()}",
                    f"**Conversion Completed:** {completed_at.isoformat()}",
                    f"**Total Duration:** {duration_str}",
                    "",
                ]
            )

            if warnings_list:
                report_lines.extend(
                    [
                        "## Warnings",
                        "",
                    ]
                )
                for warning in warnings_list:
                    report_lines.append(f"- {warning}")
                report_lines.append("")

            if errors_list:
                report_lines.extend(
                    [
                        "## Errors",
                        "",
                    ]
                )
                for error in errors_list:
                    report_lines.append(f"- {error}")
                report_lines.append("")

            report_lines.extend(
                [
                    "## Output Files",
                    "",
                    (f"- `{pdf_name}-phase8.md`" " - Final converted markdown"),
                    ("- `font-family-mapping.json`" " - Font signature mapping"),
                    ("- `toc-extracted.txt`" " - Extracted table of contents"),
                    ("- `images/image-manifest.json`" " - Image positions"),
                    "",
                    "## License Notice",
                    "",
                    (
                        "Images extracted from this PDF are copyrighted"
                        " by the original publisher."
                    ),
                    (
                        "They are commented out by default. Uncommenting"
                        " for personal use at your table"
                    ),
                    (
                        "is generally acceptable, but do not redistribute"
                        " or publish without permission."
                    ),
                    "",
                ]
            )

            report_content = "\n".join(report_lines)
            report_path = output_dir / "conversion-report.md"

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            result.add_step(
                StepResult(
                    step_id="10.4",
                    description="Generate conversion-report.md",
                    status=PhaseStatus.SUCCESS,
                    message=f"Report saved to {report_path}",
                )
            )

            # Step 10.5: Write completion metadata
            completion_data = {
                "completed_at": datetime.now().isoformat(),
                "total_phases": len(completed_phases_list),
                "warnings_count": len(warnings_list),
                "errors_count": len(errors_list),
            }

            completion_path = output_dir / ".completion.json"
            with open(completion_path, "w", encoding="utf-8") as f:
                json.dump(completion_data, f, indent=2, sort_keys=True)

            result.add_step(
                StepResult(
                    step_id="10.5",
                    description="Write completion metadata",
                    status=PhaseStatus.SUCCESS,
                    message="Completion metadata saved",
                )
            )

            # Step 10.6: Create diagnostics bundle if enabled
            if state.diagnostics_enabled:
                # Bundle creation is handled by orchestrator
                result.add_step(
                    StepResult(
                        step_id="10.6",
                        description="Create diagnostics bundle",
                        status=PhaseStatus.SUCCESS,
                        message=("Diagnostics bundle will be" " created by orchestrator"),
                    )
                )
            else:
                result.add_step(
                    StepResult(
                        step_id="10.6",
                        description="Create diagnostics bundle",
                        status=PhaseStatus.SKIPPED,
                        message=("Diagnostics not enabled" " (--diagnostics flag not set)"),
                    )
                )

            result.output_file = str(report_path)

        except Exception as e:
            result.add_error(f"Report generation failed: {e}")

        result.complete()
        return result
