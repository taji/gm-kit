"""Agent-driven pipeline step library for PDF conversion.

This package provides the infrastructure for agent-orchestrated PDF conversion steps,
including workspace I/O, contract validation, rubric evaluation, and step execution coordination.

Public API:
    - write_agent_inputs(): Prepare workspace files for agent step execution
    - read_agent_output(): Read and validate agent step output
    - AgentStepError: Base exception for agent step failures
    - ContractViolation: Exception for contract validation failures
    - StepRegistry: Access to step definitions and metadata
    - RubricRegistry: Access to rubric definitions
    - get_rubric(): Get rubric for a specific step
    - evaluate_step_output(): Evaluate agent output against rubric
    - AgentStepRuntime: Execute agent steps with retry/resume
    - run_agent_step(): Convenience function to run a step
    - dispatch: Agent CLI invocation utilities
"""

from . import dispatch
from .agent_step import read_agent_output, write_agent_inputs
from .errors import AgentStepError, ContractViolation
from .evaluator import (
    EvaluationResult,
    RubricRegistry,
    evaluate_step_output,
    format_rubric_feedback,
)
from .evaluator import get_registry as get_rubric_registry
from .registry import StepRegistry
from .registry import get_registry as get_step_registry
from .rubrics import RubricDimension, StepRubric, get_all_rubrics, get_rubric
from .runtime import AgentStepRuntime, run_agent_step

__all__ = [
    "write_agent_inputs",
    "read_agent_output",
    "AgentStepError",
    "ContractViolation",
    "StepRegistry",
    "get_step_registry",
    "RubricRegistry",
    "get_rubric",
    "get_all_rubrics",
    "StepRubric",
    "RubricDimension",
    "EvaluationResult",
    "evaluate_step_output",
    "format_rubric_feedback",
    "get_rubric_registry",
    "AgentStepRuntime",
    "run_agent_step",
    "dispatch",
]
