"""Base types and abstract classes for agent steps."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class StepStatus(Enum):
    """Status of an agent step execution."""

    PENDING = auto()
    REQUEST_WRITTEN = auto()
    AWAITING_AGENT = auto()
    OUTPUT_READ = auto()
    CONTRACT_VALIDATING = auto()
    RUBRIC_EVALUATING = auto()
    COMPLETED = auto()
    RETRY_REQUEST_WRITTEN = auto()
    ESCALATED = auto()
    HALTED = auto()
    FLAGGED = auto()
    SKIPPED = auto()


class Criticality(Enum):
    """Criticality level for step failure escalation."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AgentStepDefinition:
    """Static definition for one agent step."""

    step_id: str
    phase: int
    description: str
    criticality: Criticality
    instruction_template: str
    contract_schema: str
    rubric_id: str | None = None


@dataclass
class AgentStepWorkspaceRequest:
    """Files and metadata prepared for agent execution."""

    step_id: str
    workspace_dir: str
    step_dir: str
    input_file: str
    instruction_file: str
    attempt_number: int
    resume_command: str


@dataclass
class AgentStepInputPayload:
    """Input payload written to step-input.json."""

    step_id: str
    input_artifacts: dict[str, str]
    optional_artifacts: dict[str, str]
    context: dict[str, Any]
    output_contract: str
    image_paths: dict[str, str] | None = None


@dataclass
class AgentStepOutputEnvelope:
    """Output envelope from agent step."""

    step_id: str
    status: str
    data: dict[str, Any]
    warnings: list[str]
    notes: str | None = None
    rubric_scores: dict[str, int] | None = None
    critical_failures: list[str] | None = None


@dataclass
class StepAttemptRecord:
    """Record of one execution attempt."""

    step_id: str
    attempt_number: int
    validation_passed: bool
    rubric_passed: bool | None = None
    failure_reason: str | None = None
    retry_prompt_appendix: str | None = None


class AgentStep(ABC):
    """Abstract base class for agent steps."""

    @property
    @abstractmethod
    def step_id(self) -> str:
        """Return the step identifier (e.g., '3.2')."""
        ...

    @property
    @abstractmethod
    def criticality(self) -> Criticality:
        """Return the step criticality level."""
        ...

    @abstractmethod
    def write_inputs(self, workspace: str, inputs: dict[str, Any]) -> None:
        """Write step-input.json and step-instructions.md to workspace."""
        ...

    @abstractmethod
    def read_output(self, workspace: str) -> AgentStepOutputEnvelope:
        """Read and return step-output.json from workspace."""
        ...
