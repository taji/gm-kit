"""Tests for agent step error types."""

from gm_kit.pdf_convert.agents.errors import (
    AgentStepError,
    ContractViolation,
    MissingInputError,
    RetryExhaustedError,
)


class TestAgentStepError:
    """Test base AgentStepError."""

    def test_error_message(self):
        """Should format error message with step_id."""
        error = AgentStepError(step_id="3.2", error="Test failure", recovery="Re-run phase 2")
        assert "Step 3.2" in str(error)
        assert "Test failure" in str(error)
        assert error.recovery == "Re-run phase 2"

    def test_optional_recovery(self):
        """Should allow empty recovery."""
        error = AgentStepError(step_id="4.5", error="Simple error")
        assert error.recovery == ""


class TestContractViolation:
    """Test ContractViolation error."""

    def test_with_validation_errors(self):
        """Should store validation errors."""
        errors = ["Field 'data' is required", "Invalid type for 'status'"]
        violation = ContractViolation(
            step_id="3.2", validation_errors=errors, output={"step_id": "3.2"}
        )
        assert len(violation.validation_errors) == 2
        assert "Field 'data'" in violation.validation_errors[0]
        assert violation.output == {"step_id": "3.2"}


class TestMissingInputError:
    """Test MissingInputError."""

    def test_error_message(self):
        """Should indicate missing artifact."""
        error = MissingInputError(step_id="3.2", missing_artifact="toc-extracted.txt")
        assert "toc-extracted.txt" in str(error)
        assert "Re-run previous phase" in error.recovery


class TestRetryExhaustedError:
    """Test RetryExhaustedError."""

    def test_tracks_attempts(self):
        """Should track number of attempts."""
        error = RetryExhaustedError(
            step_id="7.7", attempts=3, last_error="Invalid bounding box format"
        )
        assert error.attempts == 3
        assert "Max retries (3)" in str(error)
        assert "Invalid bounding box" in str(error)
