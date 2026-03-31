"""Workspace handoff I/O helpers for agent steps."""

import importlib.util
import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any

from .base import AgentStepOutputEnvelope
from .errors import AgentStepError

logger = logging.getLogger(__name__)


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
    # IMPORTANT: step_id and attempt must be last so they override any same-named
    # keys inside `inputs`. For multi-page steps the inputs dict carries the
    # canonical step-type id (e.g. "7.7") while the caller passes the page-
    # specific id (e.g. "7.7_p1") as `step_id`. The file must record "7.7_p1"
    # so that _has_pending_output can match it correctly on resume.
    input_file = step_dir / "step-input.json"
    input_payload = {**inputs, "step_id": step_id, "attempt": attempt}
    _ensure_workspace_schema_for_step(step_id=step_id, workspace_path=workspace_path, payload=input_payload)

    with open(input_file, "w") as f:
        json.dump(input_payload, f, indent=2)

    # Load and render instruction template (pass inputs so dynamic .py builders
    # can select the right prompt variant, e.g. text_scan vs vision_confirmation).
    template = _load_instruction_template(step_id, inputs)
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


def _ensure_workspace_schema_for_step(step_id: str, workspace_path: Path, payload: dict[str, Any]) -> None:
    """Copy step schema into workspace/schemas and ensure output_contract path.

    Agents receive `output_contract: schemas/<file>` in step-input.json. Keeping
    that schema file present in each workspace prevents repeated "file not found"
    fallback searches during live handoff runs.
    """
    base_step_id = re.sub(r"_p\d+(?:_t\d+)?$", "", step_id)
    schema_file = f"step_{base_step_id.replace('.', '_')}.schema.json"
    schema_src = Path(__file__).parent / "schemas" / schema_file
    if not schema_src.exists():
        return

    schema_dir = workspace_path / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    schema_dest = schema_dir / schema_file
    shutil.copy2(schema_src, schema_dest)

    if "output_contract" not in payload:
        logger.warning(
            "Missing output_contract in step payload for %s; defaulting to schemas/%s",
            step_id,
            schema_file,
        )
        payload["output_contract"] = f"schemas/{schema_file}"


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


def _load_instruction_template(step_id: str, inputs: dict[str, Any] | None = None) -> str:
    """Load instruction template for a step.

    Handles three cases:
    1. Static .md template (e.g. step_6_4.md) — loaded and returned directly.
    2. Dynamic .py template (e.g. step_7_7.py) — module imported and appropriate
       builder called based on ``inputs["phase"]``.
    3. No template found — generic fallback placeholder returned.

    For multi-page step IDs (e.g. "7.7_p1", "7.7_p2") the ``_p<N>`` suffix is
    stripped before looking up the file, since all pages share one template.
    """
    instructions_dir = Path(__file__).parent / "instructions"

    # Strip page/part suffix: "7.7_p1" -> "7.7", "7.7_p2" -> "7.7"
    base_step_id = re.sub(r"_p\d+$", "", step_id)
    file_stem = f"step_{base_step_id.replace('.', '_')}"

    # 1. Try static .md template first.
    md_path = instructions_dir / f"{file_stem}.md"
    if md_path.exists():
        return md_path.read_text(encoding="utf-8")

    # 2. Try dynamic .py module.
    py_path = instructions_dir / f"{file_stem}.py"
    if py_path.exists():
        spec = importlib.util.spec_from_file_location(file_stem, py_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[arg-type]

            phase = (inputs or {}).get("phase", "")

            # Dispatch to the right builder based on the declared phase.
            if phase == "text_scan" and hasattr(module, "build_text_scan_prompt"):
                extracted_text = (inputs or {}).get("extracted_text", "")
                page_num = int((inputs or {}).get("page_number_1based", 1))
                return module.build_text_scan_prompt(extracted_text, page_num)

            if phase == "vision_confirmation" and hasattr(module, "build_vision_prompt"):
                page_image = (inputs or {}).get("page_image", "")
                text_context = (inputs or {}).get("text_context", "")
                return module.build_vision_prompt(page_image, text_context)

            # Generic fallback: call the first callable that looks like a builder.
            for attr in dir(module):
                if attr.startswith("build_") and callable(getattr(module, attr)):
                    try:
                        return getattr(module, attr)()
                    except TypeError:
                        pass

    # 3. Generic fallback.
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
