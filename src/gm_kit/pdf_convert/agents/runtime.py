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
from .dispatch import AgentDispatchError, invoke_agent
from .errors import AgentStepError, ContractViolation, RetryExhaustedError
from .evaluator import evaluate_step_output
from .registry import get_registry


class AgentStepRuntime:
    """Runtime for executing agent steps with retry and resume support."""

    def __init__(
        self, workspace: str, max_retries: int = 3, validator: ContractValidator | None = None
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
        step_def = self.registry.get(step_id)
        if not step_def:
            raise AgentStepError(
                step_id=step_id, error=f"Unknown step: {step_id}", recovery="Check step_id is valid"
            )

        # Write inputs to workspace
        step_dir = write_agent_inputs(
            step_id=step_id, workspace=self.workspace, inputs=inputs, attempt=attempt
        )

        # Update state to AWAITING_AGENT
        self._update_state(step_id, StepStatus.AWAITING_AGENT, attempt)

        # Load instruction file for prompt
        instruction_file = step_dir / "step-instructions.md"
        prompt = instruction_file.read_text()

        # Invoke agent
        try:
            result = invoke_agent(prompt=prompt, workspace=self.workspace, capture_output=False)

            if result.returncode != 0:
                raise AgentDispatchError(f"Agent exited with code {result.returncode}")

        except AgentDispatchError as e:
            # Agent invocation failed - treat as retryable
            return self._handle_failure(step_id, str(e), attempt, retryable=True)

        # Read output
        try:
            envelope = read_agent_output(
                step_id=step_id,
                workspace=self.workspace,
                validate=False,  # We'll validate manually
            )
        except AgentStepError as e:
            return self._handle_failure(step_id, str(e), attempt, retryable=True)

        # Validate against contract
        try:
            self.validator.validate(step_id=step_id, output=self._envelope_to_dict(envelope))
        except ContractViolation as e:
            return self._handle_failure(
                step_id, f"Contract violation: {e.validation_errors}", attempt, retryable=True
            )

        # Evaluate against rubric
        if envelope.rubric_scores:
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

        # Success!
        self._update_state(step_id, StepStatus.COMPLETED, attempt)
        return envelope, StepStatus.COMPLETED

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
            envelope = read_agent_output(step_id=step_id, workspace=self.workspace, validate=True)

            self._update_state(step_id, StepStatus.COMPLETED)
            return envelope, StepStatus.COMPLETED

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

    def _update_state(
        self, step_id: str, status: StepStatus, attempt: int | None = None
    ) -> None:
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
        state["status"] = status.name
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
        return {
            "step_id": envelope.step_id,
            "status": envelope.status,
            "data": envelope.data,
            "warnings": envelope.warnings,
            "notes": envelope.notes,
            "rubric_scores": envelope.rubric_scores,
            "critical_failures": envelope.critical_failures,
        }


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
