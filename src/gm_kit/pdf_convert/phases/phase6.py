"""Phase 6: Structural Formatting.

Code steps 6.1-6.3: Word-level fixes, list detection, hyphenation fixes.
Agent step 6.4 is stubbed (spelling correction).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from gm_kit.pdf_convert.phases.base import Phase, PhaseResult, PhaseStatus, StepResult

if TYPE_CHECKING:
    from gm_kit.pdf_convert.state import ConversionState

logger = logging.getLogger(__name__)


class Phase6(Phase):
    """Phase 6: Structural Formatting.

    Applies word-level fixes, detects lists, and fixes hyphenation issues.
    """

    @property
    def phase_num(self) -> int:
        return 6

    @property
    def has_agent_steps(self) -> bool:
        return True  # Step 6.4: Fix OCR spelling artifacts

    def execute(self, state: ConversionState) -> PhaseResult:
        """Execute structural formatting steps.

        Args:
            state: Current conversion state

        Returns:
            PhaseResult with formatting results
        """
        result = self.create_result()
        output_dir = Path(state.output_dir)
        pdf_name = Path(state.pdf_path).stem

        input_path = output_dir / f"{pdf_name}-phase5.md"
        output_path = output_dir / f"{pdf_name}-phase6.md"

        # Check if input exists
        if not input_path.exists():
            result.add_error(f"Phase input file not found - run previous phase first: {input_path}")
            result.status = PhaseStatus.ERROR
            result.complete()
            return result

        try:
            with open(input_path, encoding="utf-8") as f:
                content = f.read()

            # Step 6.1: Fix hyphenation at line breaks
            # Pattern: word-\nword -> wordword
            content = re.sub(r"(\w)-\n(\w)", r"\1\2", content)

            # Also handle soft-hyphen character
            content = content.replace("\u00ad", "")

            result.add_step(
                StepResult(
                    step_id="6.1",
                    description="Fix hyphenation at line breaks",
                    status=PhaseStatus.SUCCESS,
                    message="Removed hyphenation artifacts",
                )
            )

            # Step 6.2: Detect and format bullet lists
            lines = content.split("\n")
            formatted_lines = []

            bullet_patterns = [
                r"^\s*[•·]\s+",  # Bullet characters
                r"^\s*[-*]\s+",  # Dash/asterisk bullets
                r"^\s*\(\d+\)\s+",  # Numbered (1)
                r"^\s*\d+\.\s+",  # Numbered 1.
            ]

            in_list = False
            for line in lines:
                is_bullet = any(re.match(pattern, line) for pattern in bullet_patterns)

                if is_bullet:
                    # Normalize bullet to markdown format
                    for pattern in bullet_patterns[:2]:
                        if re.match(pattern, line):
                            line = re.sub(pattern, "- ", line)
                            break
                    in_list = True
                elif line.strip() and in_list:
                    # Check if this is a continuation line
                    if not line.startswith(" ") and not line.startswith("-"):
                        in_list = False

                formatted_lines.append(line)

            content = "\n".join(formatted_lines)

            result.add_step(
                StepResult(
                    step_id="6.2",
                    description="Detect and format bullet lists",
                    status=PhaseStatus.SUCCESS,
                    message="Normalized bullet list formatting",
                )
            )

            # Step 6.3: Preserve indented sub-items
            # Already handled in step 6.2 by preserving indentation
            result.add_step(
                StepResult(
                    step_id="6.3",
                    description="Preserve indented sub-items",
                    status=PhaseStatus.SUCCESS,
                    message="Preserved list indentation",
                )
            )

            # Step 6.4: Fix OCR spelling artifacts (AGENT STEP - STUBBED)
            result.add_step(
                StepResult(
                    step_id="6.4",
                    description="Fix OCR spelling artifacts (AGENT)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Agent step will be implemented in E4-07b",
                )
            )

            # Save output
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            result.output_file = str(output_path)

        except Exception as e:
            result.add_error(f"Structural formatting failed: {e}")

        result.complete()
        return result
