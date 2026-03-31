"""Rubric registry and evaluation utilities.

Provides centralized access to rubric definitions and evaluation helpers.
"""

from typing import Any

from .rubrics import StepRubric, get_all_rubrics, get_rubric


class RubricRegistry:
    """Registry for accessing and validating rubrics."""

    def __init__(self) -> None:
        """Initialize registry with all rubrics."""
        self._rubrics: dict[str, StepRubric] = get_all_rubrics()

    def get(self, step_id: str) -> StepRubric | None:
        """Get rubric for a step."""
        return self._rubrics.get(step_id)

    def all_rubrics(self) -> dict[str, StepRubric]:
        """Get all rubrics."""
        return self._rubrics.copy()

    def has_rubric(self, step_id: str) -> bool:
        """Check if step has a rubric."""
        return step_id in self._rubrics

    def get_dimension_names(self, step_id: str) -> list[str]:
        """Get dimension names for a step's rubric."""
        rubric = self._rubrics.get(step_id)
        if not rubric:
            return []
        return [d.name for d in rubric.dimensions]


class EvaluationResult:
    """Result of rubric evaluation."""

    def __init__(
        self,
        step_id: str,
        passed: bool,
        dimension_scores: dict[str, int],
        critical_failures: list[str],
        feedback: str | None = None,
    ):
        self.step_id = step_id
        self.passed = passed
        self.dimension_scores = dimension_scores
        self.critical_failures = critical_failures
        self.feedback = feedback or ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_id": self.step_id,
            "passed": self.passed,
            "dimension_scores": self.dimension_scores,
            "critical_failures": self.critical_failures,
            "feedback": self.feedback,
        }


def evaluate_step_output(
    step_id: str,
    rubric_scores: dict[str, int],
    critical_failures_found: list[str],
    feedback: str | None = None,
) -> EvaluationResult:
    """Evaluate agent output against rubric.

    Args:
        step_id: Step identifier
        rubric_scores: Dict mapping dimension names to scores (1-5)
        critical_failures_found: List of critical failures detected
        feedback: Optional feedback message

    Returns:
        EvaluationResult with pass/fail status
    """
    rubric = get_rubric(step_id)

    if not rubric:
        # No rubric for this step, auto-pass
        return EvaluationResult(
            step_id=step_id,
            passed=True,
            dimension_scores=rubric_scores,
            critical_failures=critical_failures_found,
            feedback=feedback or "No rubric defined for this step",
        )

    # Validate scores
    valid, errors = rubric.validate_scores(rubric_scores)

    # Check critical failures
    has_critical = len(critical_failures_found) > 0

    # Pass if: valid scores AND no critical failures AND all scores >= min
    passed = valid and not has_critical
    if valid:
        for score in rubric_scores.values():
            if score < rubric.min_score:
                passed = False
                break

    return EvaluationResult(
        step_id=step_id,
        passed=passed,
        dimension_scores=rubric_scores,
        critical_failures=critical_failures_found,
        feedback=feedback or "",
    )


def format_rubric_feedback(
    step_id: str, dimension_scores: dict[str, int], critical_failures: list[str]
) -> str:
    """Format rubric results as human-readable feedback.

    Args:
        step_id: Step identifier
        dimension_scores: Scores per dimension
        critical_failures: Any critical failures

    Returns:
        Formatted feedback string
    """
    lines = [f"Rubric Evaluation for Step {step_id}", "=" * 40]

    # Add dimension scores
    rubric = get_rubric(step_id)
    if rubric:
        lines.append("\nDimension Scores:")
        for dim in rubric.dimensions:
            score = dimension_scores.get(dim.name, 0)
            guide = dim.scoring_guide.get(score, "Unknown")
            lines.append(f"  {dim.name}: {score}/5 - {guide}")

    # Add critical failures
    if critical_failures:
        lines.append("\n⚠ Critical Failures:")
        for failure in critical_failures:
            lines.append(f"  - {failure}")

    # Calculate average
    if dimension_scores:
        avg = sum(dimension_scores.values()) / len(dimension_scores)
        lines.append(f"\nAverage Score: {avg:.1f}/5")

    return "\n".join(lines)


# Global registry instance
_registry: RubricRegistry | None = None


def get_registry() -> RubricRegistry:
    """Get global rubric registry."""
    global _registry
    if _registry is None:
        _registry = RubricRegistry()
    return _registry
