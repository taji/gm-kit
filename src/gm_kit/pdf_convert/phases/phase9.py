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

    @staticmethod
    def _build_structured_error(step_id: str, error: str, recovery: str) -> str:
        """Create FR-008 structured error message payload."""
        return json.dumps({"step_id": step_id, "error": error, "recovery": recovery})

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

            # Step 9.1: Dropped - Phase 4 guarantees all page markers
            # No agent step needed for completeness check

            # Execute all quality assessment agent steps (9.2-9.5, 9.7-9.8)
            output_dir = Path(state.output_dir)
            self._execute_quality_assessment(result, output_dir, input_path)

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

    def _execute_quality_assessment(  # noqa: PLR0912
        self,
        result: PhaseResult,
        output_dir: Path,
        input_path: Path,
    ) -> None:
        """Execute quality assessment agent steps (9.2, 9.3, 9.4, 9.5, 9.7, 9.8).

        Args:
            result: Phase result for adding steps
            output_dir: Output directory
            input_path: Path to input markdown file
        """
        try:
            from gm_kit.pdf_convert.agents import AgentStepRuntime
            from gm_kit.pdf_convert.agents.errors import MissingInputError
            from gm_kit.pdf_convert.agents.step_builders import (
                build_callout_formatting_payload,
                build_reading_order_payload,
                build_structural_clarity_payload,
                build_table_integrity_payload,
                build_text_flow_payload,
                build_toc_validation_payload,
            )

            runtime = AgentStepRuntime(str(output_dir))

            steps_to_execute = [
                ("9.2", "Structural clarity assessment"),
                ("9.3", "Text flow assessment"),
                ("9.4", "Table integrity check"),
                ("9.5", "Callout formatting check"),
                ("9.7", "TOC validation"),
                ("9.8", "Reading order review"),
            ]

            for step_id, description in steps_to_execute:
                try:
                    # Load TOC file for relevant steps
                    toc_file = output_dir / "toc-extracted.txt"
                    font_mapping = output_dir / "font-family-mapping.json"
                    tables_manifest = output_dir / "tables-manifest.json"
                    gm_callout_config = output_dir / "gm-callout-config.json"

                    if step_id == "9.2":
                        inputs = build_structural_clarity_payload(
                            phase8_file=str(input_path),
                            toc_file=str(toc_file) if toc_file.exists() else "",
                            workspace=str(output_dir),
                        )
                    elif step_id == "9.3":
                        # Text flow assessment just needs the phase8 file
                        inputs = build_text_flow_payload(
                            phase8_file=str(input_path),
                            workspace=str(output_dir),
                        )
                    elif step_id == "9.4" and tables_manifest.exists():
                        # Table integrity check needs tables manifest
                        inputs = build_table_integrity_payload(
                            phase8_file=str(input_path),
                            tables_manifest=str(tables_manifest),
                            workspace=str(output_dir),
                        )
                    elif step_id == "9.4":
                        raise MissingInputError(
                            step_id="9.4",
                            missing_artifact="tables-manifest.json",
                        )
                    elif step_id == "9.5" and gm_callout_config.exists():
                        # Callout formatting check needs callout config
                        inputs = build_callout_formatting_payload(
                            phase8_file=str(input_path),
                            gm_callout_config=str(gm_callout_config),
                            workspace=str(output_dir),
                        )
                    elif step_id == "9.5":
                        raise MissingInputError(
                            step_id="9.5",
                            missing_artifact="gm-callout-config.json",
                        )
                    elif step_id == "9.7" and font_mapping.exists():
                        inputs = build_toc_validation_payload(
                            phase8_file=str(input_path),
                            toc_file=str(toc_file) if toc_file.exists() else "",
                            font_family_mapping=str(font_mapping),
                            workspace=str(output_dir),
                        )
                    elif step_id == "9.7":
                        result.add_step(
                            StepResult(
                                step_id=step_id,
                                description=f"{description} (AGENT)",
                                status=PhaseStatus.WARNING,
                                message=(
                                    "Skipped with flag: required artifact "
                                    "font-family-mapping.json not available"
                                ),
                            )
                        )
                        continue
                    elif step_id == "9.8":
                        # Reading order review just needs the phase8 file
                        inputs = build_reading_order_payload(
                            phase8_file=str(input_path),
                            pdf_metadata=None,
                            workspace=str(output_dir),
                        )
                    else:
                        continue

                    envelope, status = runtime.execute_step(step_id, inputs)

                    if envelope and isinstance(envelope.data, dict):
                        result.add_step(
                            StepResult(
                                step_id=step_id,
                                description=f"{description} (AGENT)",
                                status=PhaseStatus.SUCCESS,
                                message=f"Score: {envelope.data.get('score', 0)}/5",
                            )
                        )
                    else:
                        status_hint = f"Agent step status: {status.name}" if status else ""
                        result.add_step(
                            StepResult(
                                step_id=step_id,
                                description=f"{description} (AGENT)",
                                status=PhaseStatus.WARNING,
                                message=f"Agent step returned no envelope. {status_hint}".strip(),
                            )
                        )
                except MissingInputError as e:
                    message = self._build_structured_error(
                        step_id=step_id,
                        error=e.error,
                        recovery=e.recovery,
                    )
                    result.add_step(
                        StepResult(
                            step_id=step_id,
                            description=f"{description} (AGENT)",
                            status=PhaseStatus.ERROR,
                            message=message,
                        )
                    )
                    result.add_error(f"Step {step_id} failed due to missing required input")
                    raise
                except Exception as e:
                    high_critical_steps = {"9.2", "9.3", "9.4", "9.5"}
                    if step_id in high_critical_steps:
                        message = self._build_structured_error(
                            step_id=step_id,
                            error=str(e),
                            recovery="Fix the step input/output issues and re-run Phase 9",
                        )
                        result.add_step(
                            StepResult(
                                step_id=step_id,
                                description=f"{description} (AGENT)",
                                status=PhaseStatus.ERROR,
                                message=message,
                            )
                        )
                        result.add_error(f"High-criticality step {step_id} failed")
                        raise
                    result.add_step(
                        StepResult(
                            step_id=step_id,
                            description=f"{description} (AGENT)",
                            status=PhaseStatus.WARNING,
                            message=f"Agent step failed: {e}",
                        )
                    )

        except Exception as e:
            logger.warning(f"Quality assessment failed: {e}")
