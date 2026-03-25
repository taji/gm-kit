"""Runtime adapter for agent step execution.

Provides high-level functions for executing agent steps from phase files,
including pause/resume behavior and state management.
"""

import json
from pathlib import Path
from typing import Any

from .agent_step import read_agent_output, write_agent_inputs
from .base import AgentStepOutputEnvelope, Criticality, StepStatus
from .contracts import ContractValidator
from .errors import AgentStepError, AgentStepPause, ContractViolation, RetryExhaustedError
from .evaluator import evaluate_step_output
from .registry import get_registry


class AgentStepRuntime:
    """Runtime for executing agent steps with retry and resume support."""

    def __init__(
        self,
        workspace: str,
        max_retries: int = 3,
        validator: ContractValidator | None = None,
        agent_debug: bool | None = None,
    ):
        """Initialize runtime.

        Args:
            workspace: Conversion workspace directory
            max_retries: Maximum retry attempts (default 3)
            validator: Contract validator (created if None)
        """
        self.workspace = workspace
        self.max_retries = max_retries
        self.validator = validator or ContractValidator()
        self.registry = get_registry()
        self.agent_debug = (
            self._load_agent_debug_from_state() if agent_debug is None else bool(agent_debug)
        )

    def execute_step(
        self, step_id: str, inputs: dict[str, Any], attempt: int = 1
    ) -> tuple[AgentStepOutputEnvelope | None, StepStatus]:
        """Execute an agent step with full lifecycle.

        This is the main entry point for agent step execution from phase files.
        It handles:
        1. Writing input files to workspace
        2. Pausing (CLI exits, agent runs)
        3. Resuming and reading output
        4. Contract validation
        5. Rubric evaluation
        6. Retry if needed

        Args:
            step_id: Step identifier (e.g., '3.2')
            inputs: Input data for the step
            attempt: Current attempt number (1-based)

        Returns:
            Tuple of (output_envelope, status)

        Raises:
            RetryExhaustedError: If max retries exceeded
            AgentStepError: If step execution fails
        """
        # Get step definition
        # Handle dynamic step IDs for multi-page steps (e.g., 7.7_p1, 7.7_p2 map to 7.7)
        registry_step_id = step_id
        if step_id.startswith("7.7_p"):
            registry_step_id = "7.7"

        step_def = self.registry.get(registry_step_id)
        if not step_def:
            raise AgentStepError(
                step_id=step_id, error=f"Unknown step: {step_id}", recovery="Check step_id is valid"
            )

        # Resume path: if this step is already awaiting output and output exists,
        # consume it instead of re-writing handoff artifacts.
        if self._has_pending_output(step_id, inputs):
            current_attempt = self._get_attempt_from_state(default=attempt)
            try:
                envelope = read_agent_output(
                    step_id=step_id,
                    workspace=self.workspace,
                    validate=False,
                )
            except AgentStepError as e:
                return self._handle_failure(step_id, str(e), current_attempt, retryable=True)

            return self._finalize_step(step_id, envelope, current_attempt)

        # Initial handoff path: write step artifacts and pause for external agent.
        step_dir = write_agent_inputs(
            step_id=step_id, workspace=self.workspace, inputs=inputs, attempt=attempt
        )

        # Update state to AWAITING_AGENT and hand control back to caller.
        self._update_state(step_id, StepStatus.AWAITING_AGENT, attempt)

        raise AgentStepPause(
            step_id=step_id,
            step_dir=str(step_dir),
            recovery=(
                "Write step-output.json in the step directory, then run "
                f'gmkit pdf-convert --resume "{self.workspace}"'
            ),
        )

    def resume_step(self, step_id: str) -> tuple[AgentStepOutputEnvelope | None, StepStatus]:
        """Resume a step from AWAITING_AGENT state.

        Called when --resume flag is used. Reads existing output and validates.

        Args:
            step_id: Step to resume

        Returns:
            Tuple of (output_envelope, status)
        """
        # Try to read existing output
        try:
            envelope = read_agent_output(step_id=step_id, workspace=self.workspace, validate=False)
            current_attempt = self._get_attempt_from_state(default=1)
            return self._finalize_step(step_id, envelope, current_attempt)

        except Exception as e:
            # No valid output yet - still waiting
            raise AgentStepError(
                step_id=step_id,
                error=f"Step not complete: {e}",
                recovery="Agent must write step-output.json before resuming",
            ) from e

    def _handle_failure(
        self, step_id: str, error: str, attempt: int, retryable: bool
    ) -> tuple[AgentStepOutputEnvelope | None, StepStatus]:
        """Handle step failure with retry logic.

        Args:
            step_id: Failed step
            error: Error message
            attempt: Current attempt
            retryable: Whether failure is retryable

        Returns:
            Tuple of (envelope or None, status)

        Raises:
            RetryExhaustedError: If max retries exceeded
        """
        step_def = self.registry.get(step_id)

        if retryable and attempt < self.max_retries:
            # Write retry instructions
            step_dir = Path(self.workspace) / "agent_steps" / f"step_{step_id.replace('.', '_')}"
            step_dir.mkdir(parents=True, exist_ok=True)
            retry_file = step_dir / "retry-instructions.md"

            retry_file.write_text(
                f"# Retry Attempt {attempt + 1}/{self.max_retries}\n\n"
                f"Previous attempt failed: {error}\n\n"
                f"Please fix the issues and rewrite step-output.json.\n"
            )

            self._update_state(step_id, StepStatus.RETRY_REQUEST_WRITTEN, attempt + 1)

            # Re-raise for caller to handle retry
            raise AgentStepError(
                step_id=step_id,
                error=f"Attempt {attempt} failed: {error}. Retry prepared.",
                recovery="Check retry-instructions.md and run --resume",
            )

        # Max retries exceeded - escalate based on criticality
        self._update_state(step_id, StepStatus.ESCALATED)

        if step_def and step_def.criticality == Criticality.HIGH:
            raise RetryExhaustedError(step_id=step_id, attempts=attempt, last_error=error)
        elif step_def and step_def.criticality == Criticality.MEDIUM:
            # Flag and continue
            self._update_state(step_id, StepStatus.FLAGGED)
            return None, StepStatus.FLAGGED
        else:
            # Skip
            self._update_state(step_id, StepStatus.SKIPPED)
            return None, StepStatus.SKIPPED

    def _update_state(self, step_id: str, status: StepStatus, attempt: int | None = None) -> None:
        """Update state file with current step status.

        Args:
            step_id: Current step
            status: New status
            attempt: Attempt number (optional)
        """
        state_file = Path(self.workspace) / ".state.json"

        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
        else:
            state = {}

        state["current_step"] = step_id
        # Keep conversion lifecycle status (in_progress/completed/failed) intact.
        # Agent-step lifecycle is tracked separately to avoid corrupting ConversionStatus.
        state["agent_step_status"] = status.name
        if attempt:
            state["attempt"] = attempt

        # Atomic write
        temp_file = state_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(state, f, indent=2)
        temp_file.rename(state_file)

    def _envelope_to_dict(self, envelope: AgentStepOutputEnvelope) -> dict:
        """Convert envelope to dict for validation.

        Args:
            envelope: Output envelope

        Returns:
            Dictionary representation
        """
        payload = {
            "step_id": envelope.step_id,
            "status": envelope.status,
            "data": envelope.data,
            "warnings": envelope.warnings,
        }
        if envelope.notes is not None:
            payload["notes"] = envelope.notes
        if envelope.rubric_scores is not None:
            payload["rubric_scores"] = envelope.rubric_scores
        if envelope.critical_failures is not None:
            payload["critical_failures"] = envelope.critical_failures
        return payload

    def _load_agent_debug_from_state(self) -> bool:
        """Load agent-debug flag from conversion state when available."""
        state_file = Path(self.workspace) / ".state.json"
        if not state_file.exists():
            return False
        try:
            with open(state_file) as f:
                state = json.load(f)
        except Exception:
            return False
        config = state.get("config", {})
        return bool(config.get("agent_debug", False))

    def _normalize_rubric_scores(self, step_id: str, envelope: AgentStepOutputEnvelope) -> None:
        """Normalize known rubric edge cases before evaluation."""
        if step_id != "7.7" or not envelope.rubric_scores:
            return

        if "boundary_accuracy" in envelope.rubric_scores:
            return

        if self._step_7_7_requires_boundary_score(envelope):
            return

        envelope.rubric_scores = {
            **envelope.rubric_scores,
            "boundary_accuracy": 5,
        }

    def _step_7_7_requires_boundary_score(self, envelope: AgentStepOutputEnvelope) -> bool:
        """Return True when step 7.7 output includes concrete table boundaries."""
        data = envelope.data or {}
        tables = data.get("tables")
        has_table_bboxes = isinstance(tables, list) and any(
            isinstance(table, dict)
            and isinstance(table.get("bbox_pixels"), dict)
            and bool(table.get("bbox_pixels"))
            for table in tables
        )
        has_top_level_bbox = isinstance(data.get("bbox_pixels"), dict) and bool(
            data.get("bbox_pixels")
        )
        return (
            data.get("tables_detected") is True
            or data.get("phase") == "vision_confirmation"
            or has_top_level_bbox
            or has_table_bboxes
        )

    def _has_pending_output(self, step_id: str, inputs: dict[str, Any]) -> bool:
        """Return True when this step already has output to finalize.

        We intentionally do not gate on current agent-step status because phase-level
        resume currently re-enters earlier agent steps (e.g. 9.2 before 9.3). In that
        flow, a completed prior step may update state status and otherwise prevent
        consuming already-written output for the next paused step.
        """
        output_file = self._step_dir(step_id) / "step-output.json"
        if not output_file.exists():
            return False

        input_file = self._step_dir(step_id) / "step-input.json"
        if not input_file.exists():
            return True

        try:
            with open(input_file) as f:
                persisted_input = json.load(f)
        except Exception:
            return True

        if persisted_input.get("step_id") != step_id:
            return False

        # Compare all input keys except "step_id": the method argument `step_id` is
        # already the authoritative identifier. For multi-page steps (e.g. 7.7_p1),
        # the inputs dict carries the canonical step type id ("7.7") while the persisted
        # file stores the page-specific id ("7.7_p1"), so comparing that key would
        # always produce a false mismatch and cause an infinite re-pause loop.
        return all(
            persisted_input.get(key) == value for key, value in inputs.items() if key != "step_id"
        )

    def _load_state(self) -> dict[str, Any]:
        """Load state from workspace when present."""
        state_file = Path(self.workspace) / ".state.json"
        if not state_file.exists():
            return {}

        try:
            with open(state_file) as f:
                loaded = json.load(f)
                return loaded if isinstance(loaded, dict) else {}
        except Exception:
            return {}

    def _get_attempt_from_state(self, default: int) -> int:
        """Read current step attempt from state with sane fallback."""
        state = self._load_state()
        attempt_value = state.get("attempt", default)
        try:
            attempt_int = int(attempt_value)
        except (TypeError, ValueError):
            return default
        return attempt_int if attempt_int >= 1 else default

    def _step_dir(self, step_id: str) -> Path:
        """Return workspace step directory path."""
        return Path(self.workspace) / "agent_steps" / f"step_{step_id.replace('.', '_')}"

    def _finalize_step(
        self, step_id: str, envelope: AgentStepOutputEnvelope, attempt: int
    ) -> tuple[AgentStepOutputEnvelope | None, StepStatus]:
        """Validate, score, and finalize an agent step output."""
        try:
            self.validator.validate(step_id=step_id, output=self._envelope_to_dict(envelope))
        except ContractViolation as e:
            return self._handle_failure(
                step_id, f"Contract violation: {e.validation_errors}", attempt, retryable=True
            )

        if envelope.rubric_scores:
            self._normalize_rubric_scores(step_id, envelope)
            eval_result = evaluate_step_output(
                step_id=step_id,
                rubric_scores=envelope.rubric_scores,
                critical_failures_found=envelope.critical_failures or [],
                feedback=envelope.notes,
            )

            if not eval_result.passed:
                return self._handle_failure(
                    step_id,
                    f"Rubric evaluation failed: {eval_result.critical_failures}",
                    attempt,
                    retryable=True,
                )

        self._update_state(step_id, StepStatus.COMPLETED, attempt)
        return envelope, StepStatus.COMPLETED


def run_agent_step(
    step_id: str, workspace: str, inputs: dict[str, Any], max_retries: int = 3
) -> AgentStepOutputEnvelope | None:
    """Convenience function to run an agent step.

    Args:
        step_id: Step to execute
        workspace: Workspace directory
        inputs: Step inputs
        max_retries: Max retry attempts

    Returns:
        Output envelope or None if step was flagged/skipped

    Raises:
        AgentStepError: If execution fails
    """
    runtime = AgentStepRuntime(workspace, max_retries)
    envelope, status = runtime.execute_step(step_id, inputs)
    return envelope
