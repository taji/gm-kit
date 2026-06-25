import importlib

from gm_kit.pdf_convert.prep.registry_types import (
    DisplaySequenceMapping,
    HandlerPolicy,
    HandlerStatus,
    PrepPhaseDefinition,
    PrepStepDefinition,
)


def test_prep_phase_definition__should_store_required_fields__when_constructed() -> None:
    phase = PrepPhaseDefinition(
        phase_key="prep.initialize-workspace",
        order=100,
        display_name="Initialize Workspace",
    )

    assert phase.phase_key == "prep.initialize-workspace"
    assert phase.order == 100
    assert phase.display_name == "Initialize Workspace"


def test_prep_step_definition__should_store_required_fields__when_constructed() -> None:
    step = PrepStepDefinition(
        step_key="prep.initialize-workspace.validate-input-paths",
        phase_key="prep.initialize-workspace",
        order=100,
        handler_ref="gm_kit.pdf_convert.prep.handlers:validate_input_paths",
        handler_policy=HandlerPolicy.REQUIRED,
        display_name="Validate Input Paths",
    )

    assert step.step_key == "prep.initialize-workspace.validate-input-paths"
    assert step.phase_key == "prep.initialize-workspace"
    assert step.handler_policy == HandlerPolicy.REQUIRED


def test_display_sequence_mapping__should_render_default_alias__when_orders_are_valid() -> None:
    mapping = DisplaySequenceMapping(
        phase_key="prep.initialize-workspace",
        step_key="prep.initialize-workspace.validate-input-paths",
        phase_order=100,
        step_order=300,
    )

    assert mapping.phase_alias == "100"
    assert mapping.step_alias == "100.300"


def test_prep_step_definition__should_default_to_pending_handler_status__when_constructed() -> None:
    step = PrepStepDefinition(
        step_key="prep.initialize-workspace.validate-input-paths",
        phase_key="prep.initialize-workspace",
        order=100,
        handler_ref="gm_kit.pdf_convert.prep.handlers:validate_input_paths",
        handler_policy=HandlerPolicy.REQUIRED,
        display_name="Validate Input Paths",
    )

    assert step.handler_status == HandlerStatus.PENDING
    assert step.disable_reason is None


def test_prep_package__should_export_only_resolvable_type_symbols__when_imported() -> None:
    prep_package = importlib.import_module("gm_kit.pdf_convert.prep")

    expected_exports = [
        "DisplaySequenceMapping",
        "HandlerPolicy",
        "HandlerStatus",
        "PrepPhaseDefinition",
        "PrepRegistry",
        "PrepStepDefinition",
    ]

    for export_name in expected_exports:
        assert export_name in prep_package.__all__

    for export_name in prep_package.__all__:
        assert hasattr(prep_package, export_name)


def test_prep_step_definition__should_return_updated_copy__when_with_handler_status_called() -> None:
    step = PrepStepDefinition(
        step_key="prep.initialize-workspace.validate-input-paths",
        phase_key="prep.initialize-workspace",
        order=100,
        handler_ref="gm_kit.pdf_convert.prep.handlers:validate_input_paths",
        handler_policy=HandlerPolicy.OPTIONAL,
        display_name="Validate Input Paths",
    )

    updated_step = step.with_handler_status(
        handler_status=HandlerStatus.DISABLED_OPTIONAL,
        disable_reason="optional handler unavailable",
    )

    assert updated_step is not step
    assert updated_step.handler_status == HandlerStatus.DISABLED_OPTIONAL
    assert updated_step.disable_reason == "optional handler unavailable"
    assert updated_step.step_key == step.step_key
    assert step.handler_status == HandlerStatus.PENDING
    assert step.disable_reason is None
