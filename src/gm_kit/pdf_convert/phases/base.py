"""Phase interface and result types for PDF conversion pipeline.

Defines the abstract Phase interface that all pipeline phases implement,
along with PhaseResult and StepResult for tracking execution results.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from gm_kit.pdf_convert.constants import PHASE_COUNT, PHASE_MAX, PHASE_MIN, PHASE_NAMES

if TYPE_CHECKING:
    from gm_kit.pdf_convert.state import ConversionState


class PhaseStatus(str, Enum):
    """Status of a phase or step execution."""

    SUCCESS = "success"  # Completed without issues
    WARNING = "warning"  # Completed with non-fatal warnings
    ERROR = "error"  # Failed, may be recoverable
    SKIPPED = "skipped"  # Intentionally skipped (e.g., resume)


@dataclass
class StepResult:
    """Result of executing a single step within a phase.

    Attributes:
        step_id: Step identifier (e.g., "0.1", "5.3")
        description: Human-readable step description
        status: Execution status
        duration_ms: Execution time in milliseconds
        output_file: Path to output file if applicable
        message: Additional info or error message
    """

    step_id: str
    description: str
    status: PhaseStatus
    duration_ms: int = 0
    output_file: str | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        """Convert string status to enum if needed."""
        if isinstance(self.status, str):
            self.status = PhaseStatus(self.status)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "step_id": self.step_id,
            "description": self.description,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "output_file": self.output_file,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StepResult:
        """Create StepResult from dictionary."""
        return cls(
            step_id=data["step_id"],
            description=data["description"],
            status=PhaseStatus(data["status"]),
            duration_ms=data.get("duration_ms", 0),
            output_file=data.get("output_file"),
            message=data.get("message"),
        )


@dataclass
class PhaseResult:
    """Result of executing a single phase.

    Attributes:
        phase_num: Phase number (0-10)
        name: Human-readable phase name
        status: Overall phase status
        started_at: Phase start time (ISO8601)
        completed_at: Phase end time (ISO8601)
        steps: Individual step results
        output_file: Primary output file path
        warnings: Non-fatal warning messages
        errors: Error messages if failed
    """

    phase_num: int
    name: str
    status: PhaseStatus
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    steps: list[StepResult] = field(default_factory=list)
    output_file: str | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Convert string status to enum if needed."""
        if isinstance(self.status, str):
            self.status = PhaseStatus(self.status)

    @property
    def is_success(self) -> bool:
        """Check if phase completed successfully (success or warning)."""
        return self.status in (PhaseStatus.SUCCESS, PhaseStatus.WARNING)

    @property
    def is_error(self) -> bool:
        """Check if phase failed."""
        return self.status == PhaseStatus.ERROR

    def add_step(self, step: StepResult) -> None:
        """Add a step result to this phase."""
        self.steps.append(step)
        # Update phase status based on step
        if step.status == PhaseStatus.ERROR:
            self.status = PhaseStatus.ERROR
        elif step.status == PhaseStatus.WARNING and self.status == PhaseStatus.SUCCESS:
            self.status = PhaseStatus.WARNING

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
        if self.status == PhaseStatus.SUCCESS:
            self.status = PhaseStatus.WARNING

    def add_error(self, message: str) -> None:
        """Add an error message and set status to ERROR."""
        self.errors.append(message)
        self.status = PhaseStatus.ERROR

    def complete(self) -> None:
        """Mark the phase as complete with current timestamp."""
        self.completed_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "phase_num": self.phase_num,
            "name": self.name,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "steps": [s.to_dict() for s in self.steps],
            "output_file": self.output_file,
            "warnings": self.warnings,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PhaseResult:
        """Create PhaseResult from dictionary."""
        steps = [StepResult.from_dict(s) for s in data.get("steps", [])]
        return cls(
            phase_num=data["phase_num"],
            name=data["name"],
            status=PhaseStatus(data["status"]),
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at", ""),
            steps=steps,
            output_file=data.get("output_file"),
            warnings=data.get("warnings", []),
            errors=data.get("errors", []),
        )


class Phase(ABC):
    """Abstract base class for pipeline phases.

    Each phase implements the execute() method which performs
    the phase's work and returns a PhaseResult.
    """

    @property
    @abstractmethod
    def phase_num(self) -> int:
        """Return the phase number (0-10)."""
        ...

    @property
    def has_agent_steps(self) -> bool:
        """Return True if phase contains agent steps that need prompts."""
        return False

    @property
    def has_user_steps(self) -> bool:
        """Return True if phase contains user interaction steps."""
        return False

    @property
    def name(self) -> str:
        """Return the phase name."""
        return PHASE_NAMES.get(self.phase_num, f"Phase {self.phase_num}")

    @abstractmethod
    def execute(self, state: ConversionState) -> PhaseResult:
        """Execute the phase.

        Args:
            state: Current conversion state

        Returns:
            PhaseResult with execution status and results
        """
        ...

    def create_result(
        self,
        status: PhaseStatus = PhaseStatus.SUCCESS,
        output_file: str | None = None,
    ) -> PhaseResult:
        """Create a PhaseResult for this phase.

        Helper method for phase implementations.

        Args:
            status: Initial status
            output_file: Primary output file path

        Returns:
            New PhaseResult instance
        """
        return PhaseResult(
            phase_num=self.phase_num,
            name=self.name,
            status=status,
            output_file=output_file,
        )

    def create_step_result(  # noqa: PLR0913
        self,
        step_num: int,
        description: str,
        status: PhaseStatus = PhaseStatus.SUCCESS,
        duration_ms: int = 0,
        output_file: str | None = None,
        message: str | None = None,
    ) -> StepResult:
        """Create a StepResult for a step in this phase.

        Args:
            step_num: Step number within the phase
            description: Step description
            status: Step status
            duration_ms: Execution duration
            output_file: Output file if any
            message: Additional message

        Returns:
            New StepResult instance
        """
        return StepResult(
            step_id=f"{self.phase_num}.{step_num}",
            description=description,
            status=status,
            duration_ms=duration_ms,
            output_file=output_file,
            message=message,
        )


class PhaseRegistry:
    """Registry for pipeline phases.

    Provides a central registry for all phase implementations,
    replacing the mock phase registry for production use.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._phases: dict[int, Phase] = {}

    def register(self, phase: Phase) -> None:
        """Register a phase implementation.

        Args:
            phase: Phase instance to register

        Raises:
            ValueError: If phase number is invalid or already registered
        """
        if not PHASE_MIN <= phase.phase_num <= PHASE_MAX:
            raise ValueError(
                f"Phase number {phase.phase_num} out of range [{PHASE_MIN}, {PHASE_MAX}]"
            )
        if phase.phase_num in self._phases:
            raise ValueError(f"Phase {phase.phase_num} already registered")
        self._phases[phase.phase_num] = phase

    def get_phase(self, phase_num: int) -> Phase | None:
        """Get a phase by number.

        Args:
            phase_num: Phase number (0-10)

        Returns:
            Phase instance or None if not registered
        """
        return self._phases.get(phase_num)

    def get_all_phases(self) -> list[Phase]:
        """Get all registered phases in order.

        Returns:
            List of Phase instances sorted by phase number
        """
        return [self._phases[i] for i in sorted(self._phases.keys())]

    def is_complete(self) -> bool:
        """Check if all phases (0-10) are registered.

        Returns:
            True if all phases registered, False otherwise
        """
        return len(self._phases) == PHASE_COUNT


# Global registry instance
_phase_registry: PhaseRegistry | None = None


def get_phase_registry() -> PhaseRegistry:
    """Get the global phase registry.

    Creates and initializes the registry on first call.

    Returns:
        PhaseRegistry with all phases registered
    """
    global _phase_registry
    if _phase_registry is None:
        _phase_registry = _create_registry()
    return _phase_registry


def _create_registry() -> PhaseRegistry:
    """Create and populate the phase registry.

    Imports and registers all phase implementations.

    Returns:
        Populated PhaseRegistry
    """
    registry = PhaseRegistry()

    # Import phases here to avoid circular imports
    # Phases will be registered as they're implemented
    try:
        from gm_kit.pdf_convert.phases.phase0 import Phase0
        from gm_kit.pdf_convert.phases.phase1 import Phase1
        from gm_kit.pdf_convert.phases.phase2 import Phase2
        from gm_kit.pdf_convert.phases.phase3 import Phase3
        from gm_kit.pdf_convert.phases.phase4 import Phase4
        from gm_kit.pdf_convert.phases.phase5 import Phase5
        from gm_kit.pdf_convert.phases.phase6 import Phase6
        from gm_kit.pdf_convert.phases.phase7 import Phase7
        from gm_kit.pdf_convert.phases.phase8 import Phase8
        from gm_kit.pdf_convert.phases.phase9 import Phase9
        from gm_kit.pdf_convert.phases.phase10 import Phase10

        registry.register(Phase0())
        registry.register(Phase1())
        registry.register(Phase2())
        registry.register(Phase3())
        registry.register(Phase4())
        registry.register(Phase5())
        registry.register(Phase6())
        registry.register(Phase7())
        registry.register(Phase8())
        registry.register(Phase9())
        registry.register(Phase10())
    except ImportError:
        # During initial development, phases may not exist yet
        pass

    return registry
