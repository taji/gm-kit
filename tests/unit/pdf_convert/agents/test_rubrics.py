"""Tests for rubric definitions and evaluation."""

from gm_kit.pdf_convert.agents.evaluator import (
    EvaluationResult,
    RubricRegistry,
    evaluate_step_output,
    format_rubric_feedback,
    get_registry,
)
from gm_kit.pdf_convert.agents.rubrics import (
    RUBRIC_3_2,
    RubricDimension,
    get_all_rubrics,
    get_rubric,
)


class TestRubricDimension:
    """Test RubricDimension class."""

    def test_create_dimension(self):
        """Should create dimension with scoring guide."""
        dim = RubricDimension(
            name="completeness",
            description="All items captured",
            scoring_guide={5: "Perfect", 3: "Good", 1: "Poor"},
            weight=1.0,
        )

        assert dim.name == "completeness"
        assert dim.weight == 1.0
        assert 5 in dim.scoring_guide


class TestStepRubric:
    """Test StepRubric class."""

    def test_validate_perfect_scores(self):
        """Should pass validation with perfect scores."""
        rubric = RUBRIC_3_2
        scores = {"completeness": 5, "level_accuracy": 5, "page_accuracy": 5, "output_format": 5}

        passed, errors = rubric.validate_scores(scores)

        assert passed is True
        assert len(errors) == 0

    def test_validate_missing_dimension(self):
        """Should fail if dimension missing."""
        rubric = RUBRIC_3_2
        scores = {"completeness": 5}  # Missing other dimensions

        passed, errors = rubric.validate_scores(scores)

        assert passed is False
        assert any("Missing score" in e for e in errors)

    def test_validate_below_minimum(self):
        """Should report error for scores below minimum."""
        rubric = RUBRIC_3_2
        scores = {"completeness": 2, "level_accuracy": 5, "page_accuracy": 5, "output_format": 5}

        passed, errors = rubric.validate_scores(scores)

        # Validation passes (structure OK) but score below min should be noted
        # Actually the current implementation reports it in errors
        assert any("below minimum" in e for e in errors)


class TestGetRubric:
    """Test get_rubric function."""

    def test_get_existing_rubric(self):
        """Should return rubric for valid step."""
        rubric = get_rubric("3.2")

        assert rubric is not None
        assert rubric.step_id == "3.2"
        assert len(rubric.dimensions) == 4

    def test_get_missing_rubric(self):
        """Should return None for invalid step."""
        rubric = get_rubric("99.99")

        assert rubric is None

    def test_all_rubrics_present(self):
        """Should have all 13 step rubrics."""
        all_rubrics = get_all_rubrics()

        assert len(all_rubrics) == 13

        # Check key steps
        assert "3.2" in all_rubrics
        assert "7.7" in all_rubrics
        assert "9.2" in all_rubrics
        assert "10.2" in all_rubrics


class TestRubricRegistry:
    """Test RubricRegistry class."""

    def test_registry_has_all_rubrics(self):
        """Should load all rubrics on init."""
        registry = RubricRegistry()

        assert len(registry.all_rubrics()) == 13

    def test_get_dimension_names(self):
        """Should return dimension names for step."""
        registry = RubricRegistry()
        names = registry.get_dimension_names("7.7")

        assert "detection_recall" in names
        assert "detection_precision" in names
        assert "boundary_accuracy" in names

    def test_has_rubric(self):
        """Should check if step has rubric."""
        registry = RubricRegistry()

        assert registry.has_rubric("3.2") is True
        assert registry.has_rubric("99.99") is False

    def test_registry_singleton(self):
        """Should return same instance."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2


class TestEvaluateStepOutput:
    """Test evaluate_step_output function."""

    def test_pass_with_perfect_scores(self):
        """Should pass with all scores at 5."""
        result = evaluate_step_output(
            step_id="3.2",
            rubric_scores={
                "completeness": 5,
                "level_accuracy": 5,
                "page_accuracy": 5,
                "output_format": 5,
            },
            critical_failures_found=[],
        )

        assert result.passed is True
        assert len(result.critical_failures) == 0

    def test_fail_with_critical_failure(self):
        """Should fail if critical failure present."""
        result = evaluate_step_output(
            step_id="3.2",
            rubric_scores={
                "completeness": 5,
                "level_accuracy": 5,
                "page_accuracy": 5,
                "output_format": 5,
            },
            critical_failures_found=["Missing sections present in PDF TOC"],
        )

        assert result.passed is False
        assert len(result.critical_failures) == 1

    def test_fail_with_low_score(self):
        """Should fail if any score below minimum."""
        result = evaluate_step_output(
            step_id="3.2",
            rubric_scores={
                "completeness": 2,
                "level_accuracy": 5,
                "page_accuracy": 5,
                "output_format": 5,
            },
            critical_failures_found=[],
        )

        assert result.passed is False

    def test_no_rubric_auto_pass(self):
        """Should pass if no rubric defined."""
        result = evaluate_step_output(
            step_id="99.99",
            rubric_scores={},
            critical_failures_found=[],
        )

        assert result.passed is True

    def test_result_to_dict(self):
        """Should serialize to dict."""
        result = EvaluationResult(
            step_id="3.2",
            passed=True,
            dimension_scores={"completeness": 5},
            critical_failures=[],
            feedback="Good job",
        )

        data = result.to_dict()

        assert data["step_id"] == "3.2"
        assert data["passed"] is True
        assert data["feedback"] == "Good job"


class TestFormatRubricFeedback:
    """Test format_rubric_feedback function."""

    def test_includes_dimensions(self):
        """Should include dimension scores."""
        feedback = format_rubric_feedback(
            step_id="7.7",
            dimension_scores={
                "detection_recall": 5,
                "detection_precision": 4,
                "boundary_accuracy": 5,
            },
            critical_failures=[],
        )

        assert "detection_recall" in feedback
        assert "5/5" in feedback
        assert "Average Score" in feedback

    def test_includes_critical_failures(self):
        """Should include critical failures."""
        feedback = format_rubric_feedback(
            step_id="7.7",
            dimension_scores={"detection_recall": 5},
            critical_failures=["Missing a table entirely"],
        )

        assert "⚠ Critical Failures" in feedback
        assert "Missing a table" in feedback

    def test_handles_no_rubric(self):
        """Should handle step without rubric."""
        feedback = format_rubric_feedback(
            step_id="99.99",
            dimension_scores={"some_dim": 5},
            critical_failures=[],
        )

        assert "Step 99.99" in feedback


class TestRubricContent:
    """Test specific rubric content."""

    def test_rubric_3_2_has_four_dimensions(self):
        """Step 3.2 should have 4 dimensions."""
        rubric = get_rubric("3.2")

        assert len(rubric.dimensions) == 4
        assert any(d.name == "completeness" for d in rubric.dimensions)
        assert any(d.name == "level_accuracy" for d in rubric.dimensions)

    def test_rubric_7_7_has_table_dimensions(self):
        """Step 7.7 should have table-specific dimensions."""
        rubric = get_rubric("7.7")

        assert any(d.name == "detection_recall" for d in rubric.dimensions)
        assert any(d.name == "detection_precision" for d in rubric.dimensions)

    def test_rubric_9_2_has_quality_dimensions(self):
        """Step 9.2 should have quality assessment dimensions."""
        rubric = get_rubric("9.2")

        assert any(d.name == "heading_hierarchy" for d in rubric.dimensions)
        assert any(d.name == "section_coherence" for d in rubric.dimensions)

    def test_critical_failures_defined(self):
        """Each rubric should have critical failures defined."""
        for step_id, rubric in get_all_rubrics().items():
            assert len(rubric.critical_failures) >= 1, f"Step {step_id} has no critical failures"

    def test_all_dimensions_have_scoring_guides(self):
        """Each dimension should have 1-5 scoring guide."""
        for step_id, rubric in get_all_rubrics().items():
            for dim in rubric.dimensions:
                for score in [1, 2, 3, 4, 5]:
                    assert score in dim.scoring_guide, (
                        f"Step {step_id} dimension {dim.name} missing score {score}"
                    )
