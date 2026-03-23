"""Workspace handoff I/O helpers for agent steps."""

import json
from pathlib import Path
from typing import Any

from .base import AgentStepOutputEnvelope
from .errors import AgentStepError


def write_agent_inputs(
    step_id: str, workspace: str, inputs: dict[str, Any], attempt: int = 1
) -> Path:
    """Write step input files to workspace for agent execution.

    Creates step-input.json and step-instructions.md in the workspace's
    agent_steps/{step_id}/ directory.

    Args:
        step_id: Step identifier (e.g., '3.2')
        workspace: Path to conversion workspace
        inputs: Dictionary of input data and artifacts
        attempt: Attempt number (1-3)

    Returns:
        Path to the step directory

    Raises:
        MissingInputError: If required inputs are missing
    """
    workspace_path = Path(workspace)
    step_dir = workspace_path / "agent_steps" / f"step_{step_id.replace('.', '_')}"
    step_dir.mkdir(parents=True, exist_ok=True)

    # Write step-input.json
    input_file = step_dir / "step-input.json"
    input_payload = {"step_id": step_id, "attempt": attempt, **inputs}

    with open(input_file, "w") as f:
        json.dump(input_payload, f, indent=2)

    # Load and render instruction template
    template = _load_instruction_template(step_id)
    instructions = _render_template(template, inputs)

    # Write step-instructions.md
    instruction_file = step_dir / "step-instructions.md"
    with open(instruction_file, "w") as f:
        f.write(instructions)

    # Clear stale output from prior invocations of the same step id.
    output_file = step_dir / "step-output.json"
    if output_file.exists():
        output_file.unlink()

    return step_dir


def read_agent_output(
    step_id: str, workspace: str, validate: bool = True
) -> AgentStepOutputEnvelope:
    """Read agent output from workspace.

    Args:
        step_id: Step identifier
        workspace: Path to conversion workspace
        validate: Whether to validate against contract schema

    Returns:
        AgentStepOutputEnvelope with output data

    Raises:
        AgentStepError: If output file not found or invalid
        ContractViolation: If validation fails and validate=True
    """
    workspace_path = Path(workspace)
    step_dir = workspace_path / "agent_steps" / f"step_{step_id.replace('.', '_')}"
    output_file = step_dir / "step-output.json"

    if not output_file.exists():
        raise AgentStepError(
            step_id=step_id,
            error=f"Output file not found: {output_file}",
            recovery="Agent must write step-output.json before resuming",
        )

    with open(output_file) as f:
        output_data = json.load(f)

    # TODO: Validate against contract schema if validate=True

    return AgentStepOutputEnvelope(
        step_id=output_data.get("step_id", step_id),
        status=output_data.get("status", "unknown"),
        data=output_data.get("data", {}),
        warnings=output_data.get("warnings", []),
        notes=output_data.get("notes"),
        rubric_scores=output_data.get("rubric_scores"),
        critical_failures=output_data.get("critical_failures"),
    )


def _load_instruction_template(step_id: str) -> str:
    """Load instruction template for a step."""
    # TODO: Load from instructions/ directory
    template_path = Path(__file__).parent / "instructions" / f"step_{step_id.replace('.', '_')}.md"

    if template_path.exists():
        with open(template_path) as f:
            return f.read()

    # Return default template if specific one doesn't exist
    return f"""# Step {step_id}

Complete the task described in the input file and write output to step-output.json.
"""


def _render_template(template: str, inputs: dict[str, Any]) -> str:
    """Render template with variable substitution."""
    # Simple variable substitution: {variable_name}
    result = template
    for key, value in inputs.items():
        placeholder = f"{{{key}}}"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    return result
