from __future__ import annotations

import importlib
from collections import defaultdict
from collections.abc import Callable

from gm_kit.pdf_convert.prep.registry_errors import (
    PrepRegistryValidationError,
    sanitize_for_log,
)
from gm_kit.pdf_convert.prep.registry_types import (
    DisplaySequenceMapping,
    HandlerPolicy,
    HandlerStatus,
    PrepPhaseDefinition,
    PrepStepDefinition,
)

PREP_PHASE_KEYS = (
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


class PrepRegistry:
    def __init__(
        self,
        phases: list[PrepPhaseDefinition],
        steps: list[PrepStepDefinition],
    ) -> None:
        self._phase_key_set = set(PREP_PHASE_KEYS)
        self._phases = tuple(phases)
        self._steps = tuple(steps)

        self._phase_by_key: dict[str, PrepPhaseDefinition] = {}
        self._ordered_phases: tuple[PrepPhaseDefinition, ...] = ()
        self._steps_by_key: dict[str, PrepStepDefinition] = {}
        self._ordered_steps_by_phase: dict[str, tuple[PrepStepDefinition, ...]] = {}
        self._display_mapping_by_step_key: dict[str, DisplaySequenceMapping] = {}
        self._handler_by_step_key: dict[str, Callable[..., object]] = {}
        self._disabled_optional_steps: tuple[PrepStepDefinition, ...] = ()

        self._validate_phases()
        self._validate_steps()
        self._resolve_handlers()
        self._build_display_mappings()

    @property
    def disabled_optional_steps(self) -> tuple[PrepStepDefinition, ...]:
        return self._disabled_optional_steps

    def get_ordered_phases(self) -> list[PrepPhaseDefinition]:
        return list(self._ordered_phases)

    def get_ordered_steps(self, phase_key: str) -> list[PrepStepDefinition]:
        return list(self._ordered_steps_by_phase.get(phase_key, ()))

    def get_display_mapping(self, step: PrepStepDefinition) -> DisplaySequenceMapping:
        step_key = step.step_key
        if step_key not in self._display_mapping_by_step_key:
            raise PrepRegistryValidationError(
                key=step_key,
                failure_class="unknown_step_key",
                remediation_hint="Use a step returned by the registry.",
            )

        return self._display_mapping_by_step_key[step_key]

    def get_handler(self, step_key: str) -> Callable[..., object] | None:
        return self._handler_by_step_key.get(step_key)

    def _build_display_mappings(self) -> None:
        display_mapping_by_step_key: dict[str, DisplaySequenceMapping] = {}

        for phase in self._ordered_phases:
            for step in self._ordered_steps_by_phase.get(phase.phase_key, ()):
                display_mapping_by_step_key[step.step_key] = DisplaySequenceMapping(
                    phase_key=phase.phase_key,
                    step_key=step.step_key,
                    phase_order=phase.order,
                    step_order=step.order,
                )

        self._display_mapping_by_step_key = display_mapping_by_step_key

    def _validate_phases(self) -> None:
        phase_by_key: dict[str, PrepPhaseDefinition] = {}
        phase_order_to_key: dict[int, str] = {}

        for phase in self._phases:
            self._validate_order_value(
                key=phase.phase_key,
                order=phase.order,
                failure_class="invalid_phase_order",
            )

            if phase.phase_key not in self._phase_key_set:
                raise PrepRegistryValidationError(
                    key=phase.phase_key,
                    failure_class="unknown_phase_key",
                    remediation_hint="Use one of the canonical prep phase keys.",
                )

            if phase.phase_key in phase_by_key:
                raise PrepRegistryValidationError(
                    key=phase.phase_key,
                    failure_class="duplicate_phase_key",
                    remediation_hint="Register each prep phase key only once.",
                )

            if phase.order in phase_order_to_key:
                raise PrepRegistryValidationError(
                    key=phase.phase_key,
                    failure_class="duplicate_phase_order",
                    remediation_hint="Use a unique phase order value.",
                )

            phase_by_key[phase.phase_key] = phase
            phase_order_to_key[phase.order] = phase.phase_key

        self._phase_by_key = phase_by_key
        self._ordered_phases = tuple(
            sorted(phase_by_key.values(), key=lambda phase: (phase.order, phase.phase_key))
        )

    def _validate_steps(self) -> None:
        steps_by_key: dict[str, PrepStepDefinition] = {}
        phase_step_orders: dict[str, dict[int, str]] = defaultdict(dict)
        ordered_steps_by_phase: dict[str, list[PrepStepDefinition]] = defaultdict(list)

        for step in self._steps:
            self._validate_order_value(
                key=step.step_key,
                order=step.order,
                failure_class="invalid_step_order",
            )

            if step.phase_key not in self._phase_by_key:
                raise PrepRegistryValidationError(
                    key=step.step_key,
                    failure_class="missing_phase_reference",
                    remediation_hint="Register the owning phase before registering the step.",
                )

            if step.step_key in steps_by_key:
                raise PrepRegistryValidationError(
                    key=step.step_key,
                    failure_class="duplicate_step_key",
                    remediation_hint="Register each prep step key only once.",
                )

            if step.order in phase_step_orders[step.phase_key]:
                raise PrepRegistryValidationError(
                    key=step.step_key,
                    failure_class="duplicate_step_order",
                    remediation_hint="Use a unique step order within the phase.",
                )

            steps_by_key[step.step_key] = step
            phase_step_orders[step.phase_key][step.order] = step.step_key
            ordered_steps_by_phase[step.phase_key].append(step)

        self._steps_by_key = steps_by_key
        self._ordered_steps_by_phase = {
            phase_key: tuple(sorted(phase_steps, key=lambda step: (step.order, step.step_key)))
            for phase_key, phase_steps in ordered_steps_by_phase.items()
        }

    def _resolve_handlers(self) -> None:
        resolved_steps: dict[str, PrepStepDefinition] = {}
        ordered_steps_by_phase: dict[str, list[PrepStepDefinition]] = defaultdict(list)
        handler_by_step_key: dict[str, Callable[..., object]] = {}
        disabled_optional_steps: list[PrepStepDefinition] = []

        for phase in self._ordered_phases:
            for step in self._ordered_steps_by_phase.get(phase.phase_key, ()):
                bound_step, handler = self._resolve_handler(step)
                resolved_steps[bound_step.step_key] = bound_step
                ordered_steps_by_phase[bound_step.phase_key].append(bound_step)

                if bound_step.handler_status == HandlerStatus.DISABLED_OPTIONAL:
                    disabled_optional_steps.append(bound_step)
                    continue

                if handler is not None:
                    handler_by_step_key[bound_step.step_key] = handler

        self._steps_by_key = resolved_steps
        self._ordered_steps_by_phase = {
            phase_key: tuple(sorted(phase_steps, key=lambda step: (step.order, step.step_key)))
            for phase_key, phase_steps in ordered_steps_by_phase.items()
        }
        self._handler_by_step_key = handler_by_step_key
        self._disabled_optional_steps = tuple(disabled_optional_steps)

    def _resolve_handler(
        self,
        step: PrepStepDefinition,
    ) -> tuple[PrepStepDefinition, Callable[..., object] | None]:
        try:
            module_name, attribute_name = self._parse_handler_ref(step.handler_ref)
            module = importlib.import_module(module_name)
            handler = getattr(module, attribute_name)
            if not callable(handler):
                raise TypeError(
                    f"Handler '{step.handler_ref}' resolved to non-callable "
                    f"type '{type(handler).__name__}'."
                )
        except Exception as error:
            reason = sanitize_for_log(str(error))
            if step.handler_policy == HandlerPolicy.OPTIONAL:
                return (
                    step.with_handler_status(
                        handler_status=HandlerStatus.DISABLED_OPTIONAL,
                        disable_reason=reason,
                    ),
                    None,
                )

            raise PrepRegistryValidationError(
                key=step.step_key,
                failure_class="required_handler_unavailable",
                remediation_hint="Fix the handler_ref import path or mark the step optional.",
            ) from error

        return (
            step.with_handler_status(handler_status=HandlerStatus.AVAILABLE),
            handler,
        )

    def _parse_handler_ref(self, handler_ref: str) -> tuple[str, str]:
        module_name, separator, attribute_name = handler_ref.partition(":")
        if not separator or not module_name or not attribute_name:
            raise ValueError("Handler references must use the 'module.path:callable_name' format.")

        return module_name, attribute_name

    def _validate_order_value(self, key: str, order: object, failure_class: str) -> None:
        if isinstance(order, bool) or not isinstance(order, int):
            raise PrepRegistryValidationError(
                key=key,
                failure_class=failure_class,
                remediation_hint="Use an integer order value.",
            )
