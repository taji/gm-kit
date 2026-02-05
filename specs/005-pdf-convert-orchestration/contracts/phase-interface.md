# Phase Interface Contract

**Version**: 1.0
**Feature**: 005-pdf-convert-orchestration

## Overview

This document defines the interface contract that all pipeline phases must implement. E4-07a (Code), E4-07b (Agent), E4-07c (User), and E4-07d (Image Link) components will implement phases conforming to this interface.

## Phase Interface

### Abstract Base Class

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

class PhaseStatus(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"

@dataclass
class StepResult:
    step_id: str           # e.g., "0.1", "5.3"
    description: str       # Human-readable step description
    status: PhaseStatus
    duration_ms: int
    output_file: Optional[Path] = None
    message: Optional[str] = None

@dataclass
class PhaseResult:
    phase_num: int
    name: str
    status: PhaseStatus
    started_at: str        # ISO8601
    completed_at: str      # ISO8601
    steps: List[StepResult]
    output_file: Optional[Path] = None
    warnings: List[str] = None
    errors: List[str] = None

class Phase(ABC):
    """Interface for pipeline phases."""

    @property
    @abstractmethod
    def phase_num(self) -> int:
        """Return phase number (0-10)."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return human-readable phase name."""
        pass

    @property
    @abstractmethod
    def steps(self) -> List[str]:
        """Return list of step IDs in execution order."""
        pass

    @abstractmethod
    def execute(self, context: "ConversionContext") -> PhaseResult:
        """
        Execute this phase.

        Args:
            context: Conversion context with paths, state, and config

        Returns:
            PhaseResult with step-level details

        Raises:
            PhaseError: On unrecoverable errors
        """
        pass

    def can_resume_from(self, step_id: str) -> bool:
        """
        Check if phase supports resuming from a specific step.

        Default: True (phases support step-level resume)
        """
        return step_id in self.steps
```

### Conversion Context

```python
@dataclass
class ConversionContext:
    """Context passed to each phase during execution."""

    # Paths
    pdf_path: Path              # Source PDF
    output_dir: Path            # Working directory

    # State
    state: "ConversionState"    # Current state (mutable)
    metadata: "PDFMetadata"     # Extracted PDF metadata

    # Configuration
    diagnostics_enabled: bool   # --diagnostics flag
    resume_from_step: Optional[str] = None  # For --from-step

    # Phase dependencies (outputs from previous phases)
    phase_outputs: dict[int, Path] = None  # {phase_num: output_file}

    # User interaction callback (provided by E4-07c)
    user_interaction: "UserInteraction" = None
```

## Contract Requirements

### 1. Phase Registration

Each phase must be registered with the orchestrator:

```python
# orchestrator.py
PHASES: dict[int, type[Phase]] = {
    0: PreflightPhase,     # E4-07e (this feature)
    1: ImageExtractionPhase,  # E4-07a
    2: ImageRemovalPhase,     # E4-07a
    # ... etc
}
```

### 2. Step Execution Order

- Steps within a phase MUST execute in `steps` property order
- Each step MUST update state after completion
- Partial completion MUST be resumable

### 3. Error Handling

- Recoverable errors: Return `PhaseResult` with `status=ERROR`
- Unrecoverable errors: Raise `PhaseError`
- All errors MUST include actionable message

```python
class PhaseError(Exception):
    """Raised for unrecoverable phase errors."""

    def __init__(
        self,
        phase: int,
        step: str,
        code: str,
        message: str,
        recoverable: bool = False,
        suggestion: str = ""
    ):
        self.phase = phase
        self.step = step
        self.code = code
        self.message = message
        self.recoverable = recoverable
        self.suggestion = suggestion
        super().__init__(message)
```

### 4. Output File Conventions

| Phase | Primary Output |
|-------|---------------|
| 0 | `metadata.json` |
| 1 | `images/image-manifest.json` |
| 2 | `preprocessed/<name>-no-images.pdf` |
| 3 | `toc-extracted.txt`, `font-family-mapping.json` |
| 4 | `<name>-phase4.md` |
| 5 | `<name>-phase5.md` |
| 6 | `<name>-phase6.md` |
| 7 | `font-family-mapping.json` (updated) |
| 8 | `<name>-phase8.md` |
| 9 | `<name>-final.md` |
| 10 | `conversion-report.md`, `diagnostic-bundle.zip` (optional) |

### 5. User Interaction Contract

Phases requiring user input MUST use the `UserInteraction` interface:

```python
class UserInteraction(ABC):
    """Interface for user prompts (implemented by E4-07c)."""

    @abstractmethod
    def confirm(self, prompt: str, default: bool = True) -> bool:
        """Yes/no confirmation."""
        pass

    @abstractmethod
    def choose(
        self,
        prompt: str,
        options: List[str],
        default: int = 0
    ) -> int:
        """Multiple choice selection."""
        pass

    @abstractmethod
    def input(self, prompt: str, default: str = "") -> str:
        """Free-form text input."""
        pass
```

## Mock Implementation

For E4-07e, all phases (1-10) use mock implementations:

```python
class MockPhase(Phase):
    """Mock phase for E4-07e integration testing."""

    def __init__(self, phase_num: int, name: str, steps: List[str]):
        self._phase_num = phase_num
        self._name = name
        self._steps = steps

    @property
    def phase_num(self) -> int:
        return self._phase_num

    @property
    def name(self) -> str:
        return self._name

    @property
    def steps(self) -> List[str]:
        return self._steps

    def execute(self, context: ConversionContext) -> PhaseResult:
        # Create mock output file
        output_file = context.output_dir / f"mock-phase{self._phase_num}.md"
        output_file.write_text(f"# Mock output for Phase {self._phase_num}\n")

        return PhaseResult(
            phase_num=self._phase_num,
            name=self._name,
            status=PhaseStatus.SUCCESS,
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            steps=[
                StepResult(
                    step_id=step_id,
                    description=f"Mock step {step_id}",
                    status=PhaseStatus.SUCCESS,
                    duration_ms=10
                )
                for step_id in self._steps
            ],
            output_file=output_file
        )
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial contract definition |
