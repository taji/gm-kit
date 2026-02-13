"""Phase 9: Lint & Final Review.

Code step 9.6: Markdown linting using pymarkdownlnt.
Agent steps 9.1-9.5, 9.7-9.8: Quality checks and reviews.
User steps 9.9-9.11: Issue resolution.
"""

from __future__ import annotations

import json
import logging
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from gm_kit.pdf_convert.phases.base import Phase, PhaseResult, PhaseStatus, StepResult

if TYPE_CHECKING:
    from gm_kit.pdf_convert.state import ConversionState

logger = logging.getLogger(__name__)

# Thresholds for lint violation reporting
LINT_WARNING_THRESHOLD = 20
LINT_SUMMARY_DISPLAY_LIMIT = 3
COMMAND_NOT_FOUND_EXIT_CODE = 127


class Phase9(Phase):
    """Phase 9: Lint & Final Review.

    Performs quality checks and markdown linting.
    """

    @property
    def phase_num(self) -> int:
        return 9

    @property
    def has_agent_steps(self) -> bool:
        return True  # Steps 9.1-9.5, 9.7-9.8: Quality assessments and reviews

    @property
    def has_user_steps(self) -> bool:
        return True  # Steps 9.9-9.11: Issue resolution

    def execute(self, state: ConversionState) -> PhaseResult:  # noqa: PLR0912
        """Execute lint and review steps.

        Args:
            state: Current conversion state

        Returns:
            PhaseResult with review results
        """
        result = self.create_result()
        output_dir = Path(state.output_dir)
        pdf_name = Path(state.pdf_path).stem

        input_path = output_dir / f"{pdf_name}-phase8.md"

        # Check if input exists
        if not input_path.exists():
            result.add_error(f"Phase input file not found - run previous phase first: {input_path}")
            result.status = PhaseStatus.ERROR
            result.complete()
            return result

        try:
            input_path.read_text(encoding="utf-8")

            # Step 9.1: Completeness check (AGENT - STUBBED)
            result.add_step(
                StepResult(
                    step_id="9.1",
                    description="Completeness check (AGENT)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Agent step will be implemented in E4-07b",
                )
            )

            # Step 9.2: Structure validation (AGENT - STUBBED)
            result.add_step(
                StepResult(
                    step_id="9.2",
                    description="Structure validation (AGENT)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Agent step will be implemented in E4-07b",
                )
            )

            # Step 9.3: Reading flow check (AGENT - STUBBED)
            result.add_step(
                StepResult(
                    step_id="9.3",
                    description="Reading flow check (AGENT)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Agent step will be implemented in E4-07b",
                )
            )

            # Step 9.4: Table formatting check (AGENT - STUBBED)
            result.add_step(
                StepResult(
                    step_id="9.4",
                    description="Table formatting check (AGENT)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Agent step will be implemented in E4-07b",
                )
            )

            # Step 9.5: Callout formatting check (AGENT - STUBBED)
            result.add_step(
                StepResult(
                    step_id="9.5",
                    description="Callout formatting check (AGENT)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Agent step will be implemented in E4-07b",
                )
            )

            # Step 9.6: Run markdown lint using pymarkdownlnt
            lint_violations: list[str] = []
            lint_skipped_reason: str | None = None

            try:
                # Run pymarkdownlnt with JSON output
                cmd = [
                    sys.executable,
                    "-m",
                    "pymarkdown",
                    "scan",
                    "--json",
                    str(input_path),
                ]
                proc = subprocess.run(  # nosec B603
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )

                # Parse JSON output if available
                if proc.stdout:
                    try:
                        violations_data = json.loads(proc.stdout)
                        # Extract unique violation types
                        seen_rules = set()
                        for violation in violations_data:
                            rule_id = violation.get("rule_id", "")
                            if rule_id and rule_id not in seen_rules:
                                seen_rules.add(rule_id)
                                lint_violations.append(rule_id)
                    except json.JSONDecodeError:
                        # If JSON parsing fails, check if there were any violations
                        if proc.returncode != 0:
                            lint_violations.append("Markdown lint violations detected")

                # If pymarkdownlnt is not installed, gracefully skip lint details.
                if (
                    proc.returncode == COMMAND_NOT_FOUND_EXIT_CODE
                    or "No module named" in proc.stderr
                ):
                    logger.warning("pymarkdownlnt not available, skipping detailed lint")
                    lint_violations = []
                    lint_skipped_reason = "pymarkdownlnt not available"

            except subprocess.TimeoutExpired:
                logger.warning("pymarkdownlnt timed out, skipping lint")
                lint_violations = []
                lint_skipped_reason = "pymarkdownlnt timed out"
            except FileNotFoundError:
                logger.warning("pymarkdownlnt not found, skipping lint")
                lint_violations = []
                lint_skipped_reason = "pymarkdownlnt not found"
            except Exception as e:
                logger.warning(f"pymarkdownlnt failed: {e}, skipping lint")
                lint_violations = []
                lint_skipped_reason = "pymarkdownlnt execution failed"

            status = PhaseStatus.SUCCESS
            if lint_skipped_reason:
                status = PhaseStatus.WARNING
                message = f"Lint check skipped: {lint_skipped_reason}"
                result.add_warning(message)
            elif lint_violations:
                status = (
                    PhaseStatus.WARNING
                    if len(lint_violations) > LINT_WARNING_THRESHOLD
                    else PhaseStatus.SUCCESS
                )
                message = (
                    f"Found {len(lint_violations)} lint issues: "
                    f"{', '.join(lint_violations[:LINT_SUMMARY_DISPLAY_LIMIT])}"
                )
                if len(lint_violations) > LINT_SUMMARY_DISPLAY_LIMIT:
                    remaining = len(lint_violations) - LINT_SUMMARY_DISPLAY_LIMIT
                    message += f" and {remaining} more"
                if len(lint_violations) > LINT_WARNING_THRESHOLD:
                    result.add_warning(
                        "Many lint violations - document may need significant cleanup"
                    )
            else:
                message = "No lint violations found"

            result.add_step(
                StepResult(
                    step_id="9.6",
                    description="Run markdown lint",
                    status=status,
                    message=message,
                )
            )

            # Step 9.7: Review TOC validation issues (AGENT - STUBBED)
            result.add_step(
                StepResult(
                    step_id="9.7",
                    description="Review TOC validation issues (AGENT)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Agent step will be implemented in E4-07b",
                )
            )

            # Step 9.8: Review two-column reading order (AGENT - STUBBED)
            result.add_step(
                StepResult(
                    step_id="9.8",
                    description="Review two-column reading order (AGENT)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: Agent step will be implemented in E4-07b",
                )
            )

            # Step 9.9: Present issues to user (USER - STUBBED)
            result.add_step(
                StepResult(
                    step_id="9.9",
                    description="Present issues to user (USER)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: User step will be implemented in E4-07c",
                )
            )

            # Step 9.10: Capture user feedback (USER - STUBBED)
            result.add_step(
                StepResult(
                    step_id="9.10",
                    description="Capture user feedback (USER)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: User step will be implemented in E4-07c",
                )
            )

            # Step 9.11: Apply corrections (USER - STUBBED)
            result.add_step(
                StepResult(
                    step_id="9.11",
                    description="Apply corrections (USER)",
                    status=PhaseStatus.SUCCESS,
                    message="Stub: User step will be implemented in E4-07c",
                )
            )

        except Exception as e:
            result.add_error(f"Lint and review failed: {e}")

        result.complete()
        return result
