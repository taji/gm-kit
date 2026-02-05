"""Mock phase implementations for testing.

Provides MockPhase class that simulates phase execution
with configurable behavior for testing different scenarios.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gm_kit.pdf_convert.constants import PHASE_MAX, PHASE_MIN
from gm_kit.pdf_convert.phases.base import Phase, PhaseResult, PhaseStatus, StepResult

if TYPE_CHECKING:
    from gm_kit.pdf_convert.state import ConversionState


@dataclass
class MockPhaseConfig:
    """Configuration for mock phase behavior.

    Attributes:
        status: Status to return (default: SUCCESS)
        delay_ms: Simulated execution delay in milliseconds
        error_message: Error message if status is ERROR
        warning_message: Warning message if status is WARNING
        output_file: Output file path to report
        step_count: Number of steps to simulate
        fail_at_step: Step number to fail at (0 = don't fail)
    """
    status: PhaseStatus = PhaseStatus.SUCCESS
    delay_ms: int = 0
    error_message: str | None = None
    warning_message: str | None = None
    output_file: str | None = None
    step_count: int = 3
    fail_at_step: int = 0


class MockPhase(Phase):
    """Mock implementation of a pipeline phase.

    Used for testing the orchestrator without real phase implementations.
    Behavior can be configured via MockPhaseConfig.
    """

    def __init__(
        self,
        phase_num: int,
        config: MockPhaseConfig | None = None,
    ) -> None:
        """Initialize mock phase.

        Args:
            phase_num: Phase number (0-10)
            config: Optional configuration for behavior
        """
        self._phase_num = phase_num
        self._config = config or MockPhaseConfig()

    @property
    def phase_num(self) -> int:
        return self._phase_num

    def execute(self, state: ConversionState) -> PhaseResult:
        """Execute the mock phase.

        Simulates phase execution based on configuration.
        Respects --yes flag in state.config for non-interactive mode.

        Args:
            state: Current conversion state

        Returns:
            PhaseResult with configured status
        """
        result = self.create_result(
            status=self._config.status,
            output_file=self._config.output_file,
        )

        # Simulate delay
        if self._config.delay_ms > 0:
            time.sleep(self._config.delay_ms / 1000.0)

        # Simulate steps
        for step_num in range(1, self._config.step_count + 1):
            step_id = f"{self.phase_num}.{step_num}"

            # Check if we should fail at this step
            if self._config.fail_at_step == step_num:
                step = StepResult(
                    step_id=step_id,
                    description=f"Step {step_num} (failed)",
                    status=PhaseStatus.ERROR,
                    message=self._config.error_message or f"Mock error at step {step_id}",
                )
                result.add_step(step)
                result.add_error(step.message or "")
                break

            # Normal step
            step = StepResult(
                step_id=step_id,
                description=f"Step {step_num}",
                status=PhaseStatus.SUCCESS,
                duration_ms=self._config.delay_ms // self._config.step_count,
            )
            result.add_step(step)

        # Add warning if configured
        if self._config.warning_message:
            result.add_warning(self._config.warning_message)

        # Add error if configured (for ERROR status without fail_at_step)
        if self._config.status == PhaseStatus.ERROR and not self._config.fail_at_step:
            result.add_error(self._config.error_message or "Mock phase error")

        result.complete()
        return result


class MockPhaseRegistry:
    """Registry of mock phases for the pipeline.

    Provides default SUCCESS phases for all 11 phases (0-10),
    with ability to configure specific phases for testing.
    """

    def __init__(self) -> None:
        self._configs: dict[int, MockPhaseConfig] = {}

    def configure(self, phase_num: int, config: MockPhaseConfig) -> None:
        """Configure behavior for a specific phase.

        Args:
            phase_num: Phase number to configure
            config: Configuration for the phase
        """
        self._configs[phase_num] = config

    def configure_error(
        self,
        phase_num: int,
        error_message: str,
        fail_at_step: int = 0,
    ) -> None:
        """Configure a phase to return ERROR status.

        Args:
            phase_num: Phase number to configure
            error_message: Error message to return
            fail_at_step: Step number to fail at (0 = fail immediately)
        """
        self._configs[phase_num] = MockPhaseConfig(
            status=PhaseStatus.ERROR,
            error_message=error_message,
            fail_at_step=fail_at_step,
        )

    def configure_warning(
        self,
        phase_num: int,
        warning_message: str,
    ) -> None:
        """Configure a phase to return WARNING status.

        Args:
            phase_num: Phase number to configure
            warning_message: Warning message to return
        """
        self._configs[phase_num] = MockPhaseConfig(
            status=PhaseStatus.WARNING,
            warning_message=warning_message,
        )

    def reset(self) -> None:
        """Reset all configurations to defaults."""
        self._configs.clear()

    def get_phase(self, phase_num: int) -> MockPhase:
        """Get a mock phase instance.

        Args:
            phase_num: Phase number (0-10)

        Returns:
            MockPhase configured for the phase
        """
        config = self._configs.get(phase_num, MockPhaseConfig())
        return MockPhase(phase_num, config)

    def get_all_phases(self) -> list[Phase]:
        """Get all 11 mock phases (0-10).

        Returns:
            List of Phase instances
        """
        return [self.get_phase(i) for i in range(PHASE_MIN, PHASE_MAX + 1)]


# Default registry instance for use by orchestrator
default_registry = MockPhaseRegistry()


def get_mock_phases() -> list[Phase]:
    """Get all mock phases using default registry.

    Returns:
        List of Phase instances (MockPhase)
    """
    return default_registry.get_all_phases()


def configure_mock_phase(phase_num: int, config: MockPhaseConfig) -> None:
    """Configure a mock phase in the default registry.

    Args:
        phase_num: Phase number to configure
        config: Configuration for the phase
    """
    default_registry.configure(phase_num, config)


def reset_mock_phases() -> None:
    """Reset all mock phase configurations to defaults."""
    default_registry.reset()
