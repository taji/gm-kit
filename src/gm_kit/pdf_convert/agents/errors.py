"""Error types for agent step execution."""


class AgentStepError(Exception):
    """Base exception for agent step failures.

    Attributes:
        step_id: The step that failed
        error: Description of what failed
        recovery: Actionable guidance to fix
    """

    def __init__(self, step_id: str, error: str, recovery: str = ""):
        self.step_id = step_id
        self.error = error
        self.recovery = recovery
        super().__init__(f"Step {step_id}: {error}")


class ContractViolation(Exception):
    """Exception raised when agent output violates contract schema."""

    def __init__(
        self,
        step_id: str,
        validation_errors: list[str],
        output: dict[str, object] | None = None,
    ):
        self.step_id = step_id
        self.validation_errors = validation_errors
        self.output = output or {}
        message = f"Step {step_id} output violates contract: {validation_errors}"
        super().__init__(message)


class RetryExhaustedError(AgentStepError):
    """Exception raised when max retries are exhausted."""

    def __init__(self, step_id: str, attempts: int, last_error: str):
        self.attempts = attempts
        super().__init__(
            step_id=step_id,
            error=f"Max retries ({attempts}) exhausted. Last error: {last_error}",
            recovery="Check agent output quality or escalate to manual review",
        )


class MissingInputError(AgentStepError):
    """Exception raised when required input artifact is missing."""

    def __init__(self, step_id: str, missing_artifact: str):
        super().__init__(
            step_id=step_id,
            error=f"Required input artifact missing: {missing_artifact}",
            recovery=f"Re-run previous phase to generate {missing_artifact}",
        )
