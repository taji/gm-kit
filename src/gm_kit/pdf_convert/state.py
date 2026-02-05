"""State management for PDF conversion pipeline.

Provides ConversionState for tracking progress and ErrorInfo for error details.
Handles atomic writes and file locking for concurrent access protection.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from gm_kit.pdf_convert.constants import PHASE_MAX, PHASE_MIN

logger = logging.getLogger(__name__)

# File lock timeout in seconds
LOCK_TIMEOUT_SECONDS = 5
LOCK_RETRY_DELAY = 1.0
LOCK_MAX_RETRIES = 3

# Current schema version
SCHEMA_VERSION = "1.0"


class ConversionStatus(str, Enum):
    """Status of the overall conversion process."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ErrorInfo:
    """Error details for failed conversions.

    Attributes:
        phase: Phase number where error occurred (0-10)
        step: Step identifier where error occurred (e.g., "5.3")
        code: Error code for programmatic handling
        message: Human-readable error message
        recoverable: Whether resume might succeed
        suggestion: Suggested action for user
    """

    phase: int
    step: str
    code: str
    message: str
    recoverable: bool
    suggestion: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ErrorInfo:
        """Create ErrorInfo from dictionary."""
        return cls(
            phase=data["phase"],
            step=data["step"],
            code=data["code"],
            message=data["message"],
            recoverable=data["recoverable"],
            suggestion=data["suggestion"],
        )


@dataclass
class ConversionState:
    """Tracks progress through the PDF conversion pipeline.

    Persisted to .state.json in the output directory.

    Attributes:
        version: Schema version for compatibility (e.g., "1.0")
        pdf_path: Absolute path to source PDF
        output_dir: Absolute path to output directory
        started_at: Conversion start timestamp (ISO8601)
        updated_at: Last state update timestamp (ISO8601)
        current_phase: Phase currently executing (0-10)
        current_step: Step currently executing (e.g., "5.3")
        completed_phases: List of completed phase numbers
        phase_results: Results for each completed phase
        status: Current conversion status
        error: Error details if status is FAILED
        diagnostics_enabled: Whether --diagnostics flag was set
        config: Additional CLI configuration options
    """

    pdf_path: str
    output_dir: str
    version: str = SCHEMA_VERSION
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    current_phase: int = 0
    current_step: str = "0.1"
    completed_phases: list[int] = field(default_factory=list)
    phase_results: list[dict[str, Any]] = field(default_factory=list)
    status: ConversionStatus = ConversionStatus.IN_PROGRESS
    error: ErrorInfo | None = None
    diagnostics_enabled: bool = False
    config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure paths are absolute."""
        self.pdf_path = str(Path(self.pdf_path).resolve())
        self.output_dir = str(Path(self.output_dir).resolve())
        # Convert string status to enum if needed
        if isinstance(self.status, str):
            self.status = ConversionStatus(self.status)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to now."""
        self.updated_at = datetime.now().isoformat()

    def set_current_phase(self, phase: int, step: str = "0.1") -> None:
        """Set the current phase and step being executed.

        Args:
            phase: Phase number (0-10)
            step: Step identifier within the phase
        """
        if not PHASE_MIN <= phase <= PHASE_MAX:
            raise ValueError(f"Phase must be {PHASE_MIN}-{PHASE_MAX}, got {phase}")
        self.current_phase = phase
        self.current_step = step
        self.update_timestamp()

    def mark_phase_completed(self, phase: int, result: dict[str, Any]) -> None:
        """Mark a phase as completed and record its result.

        Args:
            phase: Phase number that completed
            result: PhaseResult as dictionary
        """
        if phase not in self.completed_phases:
            self.completed_phases.append(phase)
            self.completed_phases.sort()
        self.phase_results.append(result)
        self.update_timestamp()

    def set_failed(self, error: ErrorInfo) -> None:
        """Mark conversion as failed with error details."""
        self.status = ConversionStatus.FAILED
        self.error = error
        self.update_timestamp()

    def set_completed(self) -> None:
        """Mark conversion as successfully completed."""
        self.status = ConversionStatus.COMPLETED
        self.update_timestamp()

    def set_cancelled(self) -> None:
        """Mark conversion as cancelled by user."""
        self.status = ConversionStatus.CANCELLED
        self.update_timestamp()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "pdf_path": self.pdf_path,
            "output_dir": self.output_dir,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "current_phase": self.current_phase,
            "current_step": self.current_step,
            "completed_phases": self.completed_phases,
            "phase_results": self.phase_results,
            "status": self.status.value,
            "error": self.error.to_dict() if self.error else None,
            "diagnostics_enabled": self.diagnostics_enabled,
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConversionState:
        """Create ConversionState from dictionary."""
        error = None
        if data.get("error"):
            error = ErrorInfo.from_dict(data["error"])

        return cls(
            version=data["version"],
            pdf_path=data["pdf_path"],
            output_dir=data["output_dir"],
            started_at=data["started_at"],
            updated_at=data["updated_at"],
            current_phase=data["current_phase"],
            current_step=data["current_step"],
            completed_phases=data.get("completed_phases", []),
            phase_results=data.get("phase_results", []),
            status=ConversionStatus(data["status"]),
            error=error,
            diagnostics_enabled=data.get("diagnostics_enabled", False),
            config=data.get("config", {}),
        )

    @property
    def state_file_path(self) -> Path:
        """Get the path to the state file."""
        return Path(self.output_dir) / ".state.json"

    @property
    def lock_file_path(self) -> Path:
        """Get the path to the lock file."""
        return Path(self.output_dir) / ".state.lock"


def _acquire_lock(lock_path: Path, timeout: float = LOCK_TIMEOUT_SECONDS) -> bool:
    """Attempt to acquire an exclusive lock on the state file.

    Args:
        lock_path: Path to the lock file
        timeout: Maximum time to wait for lock

    Returns:
        True if lock acquired, False otherwise
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Create lock file exclusively
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            # Lock exists, check if stale
            try:
                with open(lock_path) as f:
                    pid = int(f.read().strip())
                # Check if process is still running (calling kill with signal 0 does not terminate)
                # Check if process is still running (calling kill with signal 0 does not terminate)
                try:
                    os.kill(pid, 0)
                    # Process exists, wait and retry
                    time.sleep(0.1)
                except OSError:
                    # Process doesn't exist, lock is stale
                    lock_path.unlink()
                    continue
            except (ValueError, FileNotFoundError):
                # Invalid or removed lock file
                with contextlib.suppress(FileNotFoundError):
                    lock_path.unlink()
                continue
    return False


def _release_lock(lock_path: Path) -> None:
    """Release the lock on the state file."""
    with contextlib.suppress(FileNotFoundError):
        lock_path.unlink()


def save_state(state: ConversionState) -> None:
    """Save state to file with atomic write.

    Uses temp file + rename pattern to prevent corruption.
    Acquires file lock before writing.

    Args:
        state: ConversionState to save

    Raises:
        IOError: If lock cannot be acquired or write fails
    """
    state_path = state.state_file_path
    lock_path = state.lock_file_path

    # Ensure output directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Retry logic for lock contention
    for attempt in range(LOCK_MAX_RETRIES):
        if _acquire_lock(lock_path):
            try:
                # Write to temp file first
                fd, temp_path = tempfile.mkstemp(
                    dir=state_path.parent, prefix=".state_", suffix=".tmp"
                )
                try:
                    with os.fdopen(fd, "w") as f:
                        json.dump(state.to_dict(), f, indent=2)
                    # Atomic rename
                    os.replace(temp_path, state_path)
                except Exception:
                    # Clean up temp file on error
                    with contextlib.suppress(FileNotFoundError):
                        os.unlink(temp_path)
                    raise
            finally:
                _release_lock(lock_path)
            return
        elif attempt < LOCK_MAX_RETRIES - 1:
            time.sleep(LOCK_RETRY_DELAY)

    raise OSError(
        f"Could not acquire lock on {lock_path} after {LOCK_MAX_RETRIES} attempts. "
        "Another conversion may be in progress."
    )


def load_state(output_dir: Path) -> ConversionState | None:
    """Load state from file.

    Args:
        output_dir: Directory containing the state file

    Returns:
        ConversionState if file exists and is valid, None otherwise

    Raises:
        ValueError: If state file exists but is invalid
    """
    state_path = output_dir / ".state.json"

    if not state_path.exists():
        return None

    try:
        with open(state_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"State file is not valid JSON: {e}") from e

    # Validate required fields
    required_fields = [
        "version",
        "pdf_path",
        "output_dir",
        "started_at",
        "updated_at",
        "current_phase",
        "current_step",
        "status",
    ]
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValueError(f"State file missing required fields: {missing}")

    # Check version compatibility
    file_version = data.get("version", "0.0")
    major_file = int(file_version.split(".")[0])
    major_current = int(SCHEMA_VERSION.split(".")[0])

    if major_file > major_current:
        raise ValueError(
            f"State file version {file_version} requires gmkit version "
            f"with schema {file_version} or later. Current schema: {SCHEMA_VERSION}"
        )

    return ConversionState.from_dict(data)


def validate_state_for_resume(state: ConversionState) -> list[str]:
    """Validate state file for resume operation.

    Args:
        state: ConversionState to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check PDF path exists
    if not Path(state.pdf_path).exists():
        errors.append(f"Source PDF not found: {state.pdf_path}")

    # Check output directory matches
    if not Path(state.output_dir).exists():
        errors.append(f"Output directory not found: {state.output_dir}")

    # Check phase is valid
    if not PHASE_MIN <= state.current_phase <= PHASE_MAX:
        errors.append(f"Invalid current_phase: {state.current_phase}")

    # Check step format
    import re

    if not re.match(r"^\d+\.\d+$", state.current_step):
        errors.append(f"Invalid current_step format: {state.current_step}")

    # Check completed phases are valid and sorted
    if state.completed_phases != sorted(state.completed_phases):
        errors.append("completed_phases is not sorted")

    for phase in state.completed_phases:
        if phase >= state.current_phase:
            errors.append(
                f"completed_phases contains {phase} >= current_phase {state.current_phase}"
            )

    return errors
