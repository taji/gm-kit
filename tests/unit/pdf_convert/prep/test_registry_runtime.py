from __future__ import annotations

import importlib
import sys

import pytest

from gm_kit.pdf_convert.prep.registry import PREP_PHASE_KEYS, PrepRegistry
from gm_kit.pdf_convert.prep.registry_errors import PrepRegistryValidationError
from gm_kit.pdf_convert.prep.registry_types import (
    DisplaySequenceMapping,
    HandlerPolicy,
    HandlerStatus,
    PrepPhaseDefinition,
    PrepStepDefinition,
)

from . import support as prep_support

sys.modules.setdefault("tests.unit.pdf_convert.prep.support", prep_support)


CANONICAL_PHASES = [
    PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace"),
    PrepPhaseDefinition("prep.analyze-document", 200, "Analyze PDF Document"),
    PrepPhaseDefinition("prep.extract-assets", 300, "Extract Assets"),
]

FULL_CANONICAL_PHASES = [
    PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace"),
    PrepPhaseDefinition("prep.analyze-document", 200, "Analyze PDF Document"),
    PrepPhaseDefinition("prep.extract-assets", 300, "Extract Assets"),
    PrepPhaseDefinition("prep.derive-structure", 400, "Derive Structure"),
    PrepPhaseDefinition("prep.plan-chunks", 500, "Plan Chunks"),
    PrepPhaseDefinition("prep.prepare-guidance", 600, "Prepare Guidance For Convert Command"),
    PrepPhaseDefinition("prep.propose-annotations", 700, "Create Annotation Candidates"),
    PrepPhaseDefinition("prep.review-annotations", 800, "Prepare Review Artifacts"),
    PrepPhaseDefinition("prep.finalize-prep-artifacts", 900, "Finalize Review Artifacts"),
]


def test_prep_registry__should_expose_canonical_phase_keys__when_imported() -> None:
    assert PREP_PHASE_KEYS == (
        "prep.initialize-workspace",
        "prep.analyze-document",
        "prep.extract-assets",
        "prep.derive-structure",
        "prep.plan-chunks",
        "prep.prepare-guidance",
        "prep.propose-annotations",
        "prep.review-annotations",
        "prep.finalize-prep-artifacts",
    )


def test_prep_package__should_export_expected_symbols__when_imported() -> None:
    prep_package = importlib.import_module("gm_kit.pdf_convert.prep")
    expected_exports = [
        "DisplaySequenceMapping",
        "HandlerPolicy",
        "HandlerStatus",
        "PrepPhaseDefinition",
        "PrepRegistry",
        "PrepStepDefinition",
    ]

    assert type(prep_package.__all__) is list
    assert [
        export_name
        for export_name in prep_package.__all__
        if export_name in set(expected_exports)
    ] == expected_exports
    assert prep_package.PrepRegistry is PrepRegistry


def test_prep_registry__should_return_phases_in_order__when_registered() -> None:
    registry = PrepRegistry(
        phases=[
            PrepPhaseDefinition("prep.extract-assets", 300, "Extract Assets"),
            PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace"),
        ],
        steps=[],
    )

    ordered = registry.get_ordered_phases()

    assert [phase.phase_key for phase in ordered] == [
        "prep.initialize-workspace",
        "prep.extract-assets",
    ]


def test_prep_registry__should_accept_full_canonical_phase_set__when_registered() -> None:
    registry = PrepRegistry(phases=FULL_CANONICAL_PHASES, steps=[])

    assert [phase.phase_key for phase in registry.get_ordered_phases()] == list(PREP_PHASE_KEYS)


def test_prep_registry__should_fail_validation__when_unknown_phase_key_exists() -> None:
    with pytest.raises(PrepRegistryValidationError) as error_info:
        PrepRegistry(
            phases=[PrepPhaseDefinition("prep.unknown-phase", 100, "Unknown")],
            steps=[],
        )

    assert error_info.value.failure_class == "unknown_phase_key"


def test_prep_registry__should_fail_validation__when_duplicate_phase_order_exists() -> None:
    with pytest.raises(PrepRegistryValidationError) as error_info:
        PrepRegistry(
            phases=[
                PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace"),
                PrepPhaseDefinition("prep.analyze-document", 100, "Analyze PDF Document"),
            ],
            steps=[],
        )

    assert error_info.value.failure_class == "duplicate_phase_order"


def test_prep_registry__should_fail_validation__when_duplicate_phase_key_exists() -> None:
    with pytest.raises(PrepRegistryValidationError) as error_info:
        PrepRegistry(
            phases=[
                PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace"),
                PrepPhaseDefinition("prep.initialize-workspace", 200, "Initialize Workspace Again"),
            ],
            steps=[],
        )

    assert error_info.value.failure_class == "duplicate_phase_key"


def test_prep_registry__should_fail_validation__when_phase_order_is_not_an_integer() -> None:
    with pytest.raises(PrepRegistryValidationError) as error_info:
        PrepRegistry(
            phases=[PrepPhaseDefinition("prep.initialize-workspace", "100", "Initialize Workspace")],  # type: ignore[arg-type]
            steps=[],
        )

    assert error_info.value.failure_class == "invalid_phase_order"


def test_prep_registry__should_fail_validation__when_step_references_missing_phase() -> None:
    with pytest.raises(PrepRegistryValidationError) as error_info:
        PrepRegistry(
            phases=[PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace")],
            steps=[
                PrepStepDefinition(
                    step_key="prep.extract-assets.extract-images",
                    phase_key="prep.extract-assets",
                    order=100,
                    handler_ref="tests.unit.pdf_convert.prep.support:extract_images",
                    handler_policy=HandlerPolicy.REQUIRED,
                    display_name="Extract Images",
                )
            ],
        )

    assert error_info.value.failure_class == "missing_phase_reference"


def test_prep_registry__should_fail_validation__when_duplicate_step_key_exists() -> None:
    with pytest.raises(PrepRegistryValidationError) as error_info:
        PrepRegistry(
            phases=[CANONICAL_PHASES[0]],
            steps=[
                PrepStepDefinition(
                    step_key="prep.initialize-workspace.validate-input-paths",
                    phase_key="prep.initialize-workspace",
                    order=100,
                    handler_ref="tests.unit.pdf_convert.prep.support:first_handler",
                    handler_policy=HandlerPolicy.REQUIRED,
                    display_name="Validate Input Paths",
                ),
                PrepStepDefinition(
                    step_key="prep.initialize-workspace.validate-input-paths",
                    phase_key="prep.initialize-workspace",
                    order=200,
                    handler_ref="tests.unit.pdf_convert.prep.support:second_handler",
                    handler_policy=HandlerPolicy.REQUIRED,
                    display_name="Validate Input Paths Duplicate",
                ),
            ],
        )

    assert error_info.value.failure_class == "duplicate_step_key"


def test_prep_registry__should_fail_validation__when_duplicate_step_order_exists_within_phase() -> None:
    with pytest.raises(PrepRegistryValidationError) as error_info:
        PrepRegistry(
            phases=CANONICAL_PHASES,
            steps=[
                PrepStepDefinition(
                    step_key="prep.initialize-workspace.first",
                    phase_key="prep.initialize-workspace",
                    order=100,
                    handler_ref="tests.unit.pdf_convert.prep.support:first_handler",
                    handler_policy=HandlerPolicy.REQUIRED,
                    display_name="First",
                ),
                PrepStepDefinition(
                    step_key="prep.initialize-workspace.second",
                    phase_key="prep.initialize-workspace",
                    order=100,
                    handler_ref="tests.unit.pdf_convert.prep.support:second_handler",
                    handler_policy=HandlerPolicy.REQUIRED,
                    display_name="Second",
                ),
            ],
        )

    assert error_info.value.failure_class == "duplicate_step_order"


def test_prep_registry__should_fail_validation__when_step_order_is_not_an_integer() -> None:
    with pytest.raises(PrepRegistryValidationError) as error_info:
        PrepRegistry(
            phases=CANONICAL_PHASES[:1],
            steps=[
                PrepStepDefinition(
                    step_key="prep.initialize-workspace.first",
                    phase_key="prep.initialize-workspace",
                    order="100",  # type: ignore[arg-type]
                    handler_ref="tests.unit.pdf_convert.prep.support:first_handler",
                    handler_policy=HandlerPolicy.REQUIRED,
                    display_name="First",
                )
            ],
        )

    assert error_info.value.failure_class == "invalid_step_order"


def test_prep_registry__should_allow_same_step_order_across_different_phases__when_registered() -> None:
    registry = PrepRegistry(
        phases=CANONICAL_PHASES[:2],
        steps=[
            PrepStepDefinition(
                step_key="prep.initialize-workspace.first",
                phase_key="prep.initialize-workspace",
                order=100,
                handler_ref="tests.unit.pdf_convert.prep.support:first_handler",
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="First",
            ),
            PrepStepDefinition(
                step_key="prep.analyze-document.second",
                phase_key="prep.analyze-document",
                order=100,
                handler_ref="tests.unit.pdf_convert.prep.support:second_handler",
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Second",
            ),
        ],
    )

    assert [step.step_key for step in registry.get_ordered_steps("prep.initialize-workspace")] == [
        "prep.initialize-workspace.first"
    ]
    assert [step.step_key for step in registry.get_ordered_steps("prep.analyze-document")] == [
        "prep.analyze-document.second"
    ]


def test_prep_registry__should_expose_disabled_optional_steps__when_optional_handler_cannot_bind() -> None:
    registry = PrepRegistry(
        phases=[PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace")],
        steps=[
            PrepStepDefinition(
                step_key="prep.initialize-workspace.optional-visual-pass",
                phase_key="prep.initialize-workspace",
                order=100,
                handler_ref="missing.module:missing_handler",
                handler_policy=HandlerPolicy.OPTIONAL,
                display_name="Optional Visual Pass",
            )
        ],
    )

    disabled_steps = registry.disabled_optional_steps

    assert len(disabled_steps) == 1
    assert disabled_steps[0].step_key == "prep.initialize-workspace.optional-visual-pass"
    assert disabled_steps[0].handler_status == HandlerStatus.DISABLED_OPTIONAL


def test_prep_registry__should_mark_optional_handler_disabled__when_handler_cannot_bind() -> None:
    registry = PrepRegistry(
        phases=[PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace")],
        steps=[
            PrepStepDefinition(
                step_key="prep.initialize-workspace.optional-visual-pass",
                phase_key="prep.initialize-workspace",
                order=100,
                handler_ref="missing.module:missing_handler",
                handler_policy=HandlerPolicy.OPTIONAL,
                display_name="Optional Visual Pass",
            )
        ],
    )

    ordered_steps = registry.get_ordered_steps("prep.initialize-workspace")

    assert ordered_steps[0].handler_status == HandlerStatus.DISABLED_OPTIONAL
    assert ordered_steps[0].disable_reason is not None


def test_prep_registry__should_fail_startup__when_required_handler_cannot_bind() -> None:
    with pytest.raises(PrepRegistryValidationError) as error_info:
        PrepRegistry(
            phases=[PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace")],
            steps=[
                PrepStepDefinition(
                    step_key="prep.initialize-workspace.validate-input-paths",
                    phase_key="prep.initialize-workspace",
                    order=100,
                    handler_ref="missing.module:missing_handler",
                    handler_policy=HandlerPolicy.REQUIRED,
                    display_name="Validate Input Paths",
                )
            ],
        )

    assert error_info.value.failure_class == "required_handler_unavailable"


def test_prep_registry__should_return_bound_handler__when_step_handler_is_available() -> None:
    registry = PrepRegistry(
        phases=[CANONICAL_PHASES[0]],
        steps=[
            PrepStepDefinition(
                step_key="prep.initialize-workspace.validate-input-paths",
                phase_key="prep.initialize-workspace",
                order=100,
                handler_ref="tests.unit.pdf_convert.prep.support:first_handler",
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Validate Input Paths",
            )
        ],
    )

    handler = registry.get_handler("prep.initialize-workspace.validate-input-paths")

    assert handler is prep_support.first_handler



def test_prep_registry__should_return_none_for_handler__when_optional_step_is_disabled() -> None:
    registry = PrepRegistry(
        phases=[CANONICAL_PHASES[0]],
        steps=[
            PrepStepDefinition(
                step_key="prep.initialize-workspace.optional-visual-pass",
                phase_key="prep.initialize-workspace",
                order=100,
                handler_ref="missing.module:missing_handler",
                handler_policy=HandlerPolicy.OPTIONAL,
                display_name="Optional Visual Pass",
            )
        ],
    )

    assert registry.get_handler("prep.initialize-workspace.optional-visual-pass") is None


def test_prep_registry__should_mark_required_handler_available__when_handler_binds() -> None:
    registry = PrepRegistry(
        phases=[CANONICAL_PHASES[0]],
        steps=[
            PrepStepDefinition(
                step_key="prep.initialize-workspace.validate-input-paths",
                phase_key="prep.initialize-workspace",
                order=100,
                handler_ref="tests.unit.pdf_convert.prep.support:first_handler",
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Validate Input Paths",
            )
        ],
    )

    ordered_steps = registry.get_ordered_steps("prep.initialize-workspace")

    assert ordered_steps[0].handler_status == HandlerStatus.AVAILABLE
    assert ordered_steps[0].disable_reason is None


def test_prep_registry__should_fail_startup__when_handler_ref_format_is_invalid_for_required_handler() -> None:
    with pytest.raises(PrepRegistryValidationError) as error_info:
        PrepRegistry(
            phases=[CANONICAL_PHASES[0]],
            steps=[
                PrepStepDefinition(
                    step_key="prep.initialize-workspace.validate-input-paths",
                    phase_key="prep.initialize-workspace",
                    order=100,
                    handler_ref="tests.unit.pdf_convert.prep.support.first_handler",
                    handler_policy=HandlerPolicy.REQUIRED,
                    display_name="Validate Input Paths",
                )
            ],
        )

    assert error_info.value.failure_class == "required_handler_unavailable"


def test_prep_registry__should_keep_display_aliases_stable_for_existing_steps__when_new_step_is_inserted() -> None:
    phases = [PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace")]
    steps = [
        PrepStepDefinition(
            step_key="prep.initialize-workspace.first",
            phase_key="prep.initialize-workspace",
            order=100,
            handler_ref="tests.unit.pdf_convert.prep.support:first_handler",
            handler_policy=HandlerPolicy.REQUIRED,
            display_name="First",
        ),
        PrepStepDefinition(
            step_key="prep.initialize-workspace.second",
            phase_key="prep.initialize-workspace",
            order=300,
            handler_ref="tests.unit.pdf_convert.prep.support:second_handler",
            handler_policy=HandlerPolicy.REQUIRED,
            display_name="Second",
        ),
        PrepStepDefinition(
            step_key="prep.initialize-workspace.inserted",
            phase_key="prep.initialize-workspace",
            order=200,
            handler_ref="tests.unit.pdf_convert.prep.support:inserted_handler",
            handler_policy=HandlerPolicy.REQUIRED,
            display_name="Inserted",
        ),
    ]

    registry = PrepRegistry(phases=phases, steps=steps)
    ordered_steps = registry.get_ordered_steps("prep.initialize-workspace")
    mappings = [registry.get_display_mapping(step) for step in ordered_steps]

    assert [step.step_key for step in ordered_steps] == [
        "prep.initialize-workspace.first",
        "prep.initialize-workspace.inserted",
        "prep.initialize-workspace.second",
    ]
    assert [mapping.step_key for mapping in mappings] == [
        "prep.initialize-workspace.first",
        "prep.initialize-workspace.inserted",
        "prep.initialize-workspace.second",
    ]
    assert [mapping.step_alias for mapping in mappings] == [
        "100.100",
        "100.200",
        "100.300",
    ]


def test_prep_registry__should_return_empty_ordered_steps__when_phase_has_no_steps() -> None:
    registry = PrepRegistry(phases=CANONICAL_PHASES[:1], steps=[])

    assert registry.get_ordered_steps("prep.initialize-workspace") == []


def test_prep_registry__should_return_display_mapping__when_step_is_registered() -> None:
    step = PrepStepDefinition(
        step_key="prep.initialize-workspace.validate-input-paths",
        phase_key="prep.initialize-workspace",
        order=120,
        handler_ref="tests.unit.pdf_convert.prep.support:first_handler",
        handler_policy=HandlerPolicy.REQUIRED,
        display_name="Validate Input Paths",
    )
    registry = PrepRegistry(
        phases=[PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace")],
        steps=[step],
    )

    mapping = registry.get_display_mapping(step)

    assert mapping == DisplaySequenceMapping(
        phase_key="prep.initialize-workspace",
        step_key="prep.initialize-workspace.validate-input-paths",
        phase_order=100,
        step_order=120,
    )
    assert mapping.phase_alias == "100"
    assert mapping.step_alias == "100.120"


def test_prep_registry__should_return_resolved_step_instance__when_getting_display_mapping() -> None:
    registry = PrepRegistry(
        phases=[CANONICAL_PHASES[0]],
        steps=[
            PrepStepDefinition(
                step_key="prep.initialize-workspace.validate-input-paths",
                phase_key="prep.initialize-workspace",
                order=100,
                handler_ref="tests.unit.pdf_convert.prep.support:first_handler",
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Validate Input Paths",
            )
        ],
    )

    resolved_step = registry.get_ordered_steps("prep.initialize-workspace")[0]

    assert registry.get_display_mapping(resolved_step).step_key == resolved_step.step_key
