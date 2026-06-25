# E7-01 Key-Based Prep Registry Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a prep-only registry foundation that defines stable phase and step identities, validates them at startup, and exposes deterministic ordering plus presentation-only display aliases.

**Architecture:** Add a new `gm_kit.pdf_convert.prep` package that is separate from the existing numeric conversion pipeline. Keep definition types, sanitization/error helpers, and registry logic in focused files so later Epic 7 features can import the prep foundation without pulling in command wiring or conversion migration code.

**Tech Stack:** Python 3.13, standard library `dataclasses`, `enum`, `importlib`, `re`, existing pytest test suite, existing `just` quality commands.

---

## Planned File Structure

**Create**
- `src/gm_kit/pdf_convert/prep/__init__.py`
- `src/gm_kit/pdf_convert/prep/registry_types.py`
- `src/gm_kit/pdf_convert/prep/registry_errors.py`
- `src/gm_kit/pdf_convert/prep/registry.py`
- `tests/unit/pdf_convert/prep/__init__.py`
- `tests/unit/pdf_convert/prep/support.py`
- `tests/unit/pdf_convert/prep/test_registry_types.py`
- `tests/unit/pdf_convert/prep/test_registry_validation.py`
- `tests/unit/pdf_convert/prep/test_registry_runtime.py`

**Modify**
- `src/gm_kit/pdf_convert/__init__.py`
- `specs/e7-01-key-based-prep-registry/feature_journal.md`

**Do Not Modify In E7-01**
- `src/gm_kit/pdf_convert/orchestrator.py`
- `src/gm_kit/pdf_convert/state.py`
- `src/gm_kit/pdf_convert/phases/base.py`
- existing conversion-phase implementations

The new prep registry must be isolated from the current numeric `PhaseRegistry`. E7-01 establishes the foundation only; later features will decide where and how the prep command consumes it.

---

### Task 1: Add Prep Registry Type Models

**Files:**
- Create: `src/gm_kit/pdf_convert/prep/__init__.py`
- Create: `src/gm_kit/pdf_convert/prep/registry_types.py`
- Create: `tests/unit/pdf_convert/prep/__init__.py`
- Create: `tests/unit/pdf_convert/prep/test_registry_types.py`

- [ ] **Step 1: Write the failing type-model tests**

```python
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
```

Run: `pytest tests/unit/pdf_convert/prep/test_registry_types.py -v`
Expected: FAIL with import errors because the prep registry types do not exist yet.

- [ ] **Step 2: Implement the new type module**

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HandlerPolicy(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"


class HandlerStatus(str, Enum):
    PENDING = "pending"
    AVAILABLE = "available"
    DISABLED_OPTIONAL = "disabled_optional"


@dataclass(frozen=True)
class PrepPhaseDefinition:
    phase_key: str
    order: int
    display_name: str


@dataclass(frozen=True)
class DisplaySequenceMapping:
    phase_key: str
    step_key: str
    phase_order: int
    step_order: int

    @property
    def phase_alias(self) -> str:
        return str(self.phase_order)

    @property
    def step_alias(self) -> str:
        return f"{self.phase_order}.{self.step_order}"


@dataclass(frozen=True)
class PrepStepDefinition:
    step_key: str
    phase_key: str
    order: int
    handler_ref: str
    handler_policy: HandlerPolicy
    display_name: str
    handler_status: HandlerStatus = HandlerStatus.PENDING
    disable_reason: str | None = None

    def with_handler_status(
        self,
        handler_status: HandlerStatus,
        disable_reason: str | None = None,
    ) -> "PrepStepDefinition":
        return PrepStepDefinition(
            step_key=self.step_key,
            phase_key=self.phase_key,
            order=self.order,
            handler_ref=self.handler_ref,
            handler_policy=self.handler_policy,
            display_name=self.display_name,
            handler_status=handler_status,
            disable_reason=disable_reason,
        )
```

Also add the package export:

```python
from gm_kit.pdf_convert.prep.registry import PrepRegistry
from gm_kit.pdf_convert.prep.registry_types import (
    DisplaySequenceMapping,
    HandlerPolicy,
    HandlerStatus,
    PrepPhaseDefinition,
    PrepStepDefinition,
)

__all__ = [
    "DisplaySequenceMapping",
    "HandlerPolicy",
    "HandlerStatus",
    "PrepPhaseDefinition",
    "PrepRegistry",
    "PrepStepDefinition",
]
```

- [ ] **Step 3: Run the focused type-model tests**

Run: `pytest tests/unit/pdf_convert/prep/test_registry_types.py -v`
Expected: PASS

- [ ] **Step 4: Commit the type-model foundation**

```bash
git add src/gm_kit/pdf_convert/prep/__init__.py \
  src/gm_kit/pdf_convert/prep/registry_types.py \
  tests/unit/pdf_convert/prep/__init__.py \
  tests/unit/pdf_convert/prep/test_registry_types.py
git commit -m "feat(prep): add key-based prep registry type models"
```

---

### Task 2: Add Sanitized Validation Errors

**Files:**
- Create: `src/gm_kit/pdf_convert/prep/registry_errors.py`
- Create: `tests/unit/pdf_convert/prep/test_registry_validation.py`

- [ ] **Step 1: Write the failing validation and sanitization tests**

```python
from gm_kit.pdf_convert.prep.registry_errors import (
    PrepRegistryValidationError,
    sanitize_for_log,
)


def test_sanitize_for_log__should_redact_token_values__when_message_contains_secrets() -> None:
    message = "token=abc123 secret=topsecret"

    sanitized = sanitize_for_log(message)

    assert "abc123" not in sanitized
    assert "topsecret" not in sanitized


def test_sanitize_for_log__should_hide_absolute_paths__when_message_contains_local_paths() -> None:
    message = "failed to load /home/todd/private/module.py"

    sanitized = sanitize_for_log(message)

    assert "/home/todd/private/module.py" not in sanitized


def test_prep_registry_validation_error__should_include_actionable_fields__when_created() -> None:
    error = PrepRegistryValidationError(
        key="prep.initialize-workspace",
        failure_class="duplicate_phase_order",
        remediation_hint="Use a unique phase order value.",
    )

    rendered = str(error)

    assert "prep.initialize-workspace" in rendered
    assert "duplicate_phase_order" in rendered
    assert "Use a unique phase order value." in rendered
```

Run: `pytest tests/unit/pdf_convert/prep/test_registry_validation.py -v`
Expected: FAIL because the new error helpers do not exist yet.

- [ ] **Step 2: Implement the validation error and sanitization helpers**

```python
from __future__ import annotations

import re
from dataclasses import dataclass

_SECRET_PATTERNS = [
    re.compile(r"(token=)([^\\s]+)", re.IGNORECASE),
    re.compile(r"(secret=)([^\\s]+)", re.IGNORECASE),
    re.compile(r"(password=)([^\\s]+)", re.IGNORECASE),
]
_ABSOLUTE_PATH_PATTERN = re.compile(r"(/[^\\s]+)+")


def sanitize_for_log(message: str) -> str:
    sanitized = message
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub(r"\\1[REDACTED]", sanitized)
    sanitized = _ABSOLUTE_PATH_PATTERN.sub("[REDACTED_PATH]", sanitized)
    return sanitized


@dataclass(frozen=True)
class PrepRegistryValidationError(ValueError):
    key: str
    failure_class: str
    remediation_hint: str

    def __str__(self) -> str:
        raw = (
            f"Registry validation failed for '{self.key}' "
            f"({self.failure_class}). Remediation: {self.remediation_hint}"
        )
        return sanitize_for_log(raw)
```

- [ ] **Step 3: Run the focused validation helper tests**

Run: `pytest tests/unit/pdf_convert/prep/test_registry_validation.py -v`
Expected: PASS

- [ ] **Step 4: Commit the validation helpers**

```bash
git add src/gm_kit/pdf_convert/prep/registry_errors.py \
  tests/unit/pdf_convert/prep/test_registry_validation.py
git commit -m "feat(prep): add registry validation errors and sanitization"
```

---

### Task 3: Implement Registry Validation, Ordering, and Handler Resolution

**Files:**
- Create: `src/gm_kit/pdf_convert/prep/registry.py`
- Modify: `src/gm_kit/pdf_convert/prep/__init__.py`
- Create: `tests/unit/pdf_convert/prep/test_registry_runtime.py`

- [ ] **Step 1: Write the failing registry runtime tests**

```python
from gm_kit.pdf_convert.prep.registry import PREP_PHASE_KEYS, PrepRegistry
from gm_kit.pdf_convert.prep.registry_errors import PrepRegistryValidationError
from gm_kit.pdf_convert.prep.registry_types import (
    HandlerPolicy,
    HandlerStatus,
    PrepPhaseDefinition,
    PrepStepDefinition,
)


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


def test_prep_registry__should_fail_validation__when_duplicate_phase_order_exists() -> None:
    try:
        PrepRegistry(
            phases=[
                PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace"),
                PrepPhaseDefinition("prep.analyze-document", 100, "Analyze Document"),
            ],
            steps=[],
        )
    except PrepRegistryValidationError as error:
        assert error.failure_class == "duplicate_phase_order"
    else:
        raise AssertionError("Expected duplicate phase order validation failure")


def test_prep_registry__should_fail_validation__when_step_references_missing_phase() -> None:
    try:
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
    except PrepRegistryValidationError as error:
        assert error.failure_class == "missing_phase_reference"
    else:
        raise AssertionError("Expected missing phase reference validation failure")


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
    try:
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
    except PrepRegistryValidationError as error:
        assert error.failure_class == "required_handler_unavailable"
    else:
        raise AssertionError("Expected required handler validation failure")


def test_prep_registry__should_keep_existing_keys_unchanged__when_new_step_is_inserted() -> None:
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

    assert [step.step_key for step in registry.get_ordered_steps("prep.initialize-workspace")] == [
        "prep.initialize-workspace.first",
        "prep.initialize-workspace.inserted",
        "prep.initialize-workspace.second",
    ]
```

Run: `pytest tests/unit/pdf_convert/prep/test_registry_runtime.py -v`
Expected: FAIL because the registry implementation does not exist yet.

- [ ] **Step 2: Implement `PrepRegistry`**

```python
from __future__ import annotations

import importlib
from collections import defaultdict
from typing import Callable

from gm_kit.pdf_convert.prep.registry_errors import PrepRegistryValidationError, sanitize_for_log
from gm_kit.pdf_convert.prep.registry_types import (
    DisplaySequenceMapping,
    HandlerPolicy,
    HandlerStatus,
    PrepPhaseDefinition,
    PrepStepDefinition,
)

PREP_PHASE_KEYS = {
    "prep.initialize-workspace",
    "prep.analyze-document",
    "prep.extract-assets",
    "prep.derive-structure",
    "prep.plan-chunks",
    "prep.prepare-guidance",
    "prep.propose-annotations",
    "prep.review-annotations",
    "prep.finalize-prep-artifacts",
}


class PrepRegistry:
    def __init__(
        self,
        phases: list[PrepPhaseDefinition],
        steps: list[PrepStepDefinition],
    ) -> None:
        self._phases = phases
        self._steps = steps
        self._validated_steps: list[PrepStepDefinition] = []
        self._validate_phases()
        self._validate_steps()
        self._validated_steps = [self._resolve_handler(step) for step in self._steps]

    def get_ordered_phases(self) -> list[PrepPhaseDefinition]:
        return sorted(self._phases, key=lambda phase: phase.order)

    def get_ordered_steps(self, phase_key: str) -> list[PrepStepDefinition]:
        return sorted(
            [step for step in self._validated_steps if step.phase_key == phase_key],
            key=lambda step: step.order,
        )

    def get_display_mapping(self, step: PrepStepDefinition) -> DisplaySequenceMapping:
        phase = next(phase for phase in self._phases if phase.phase_key == step.phase_key)
        return DisplaySequenceMapping(
            phase_key=step.phase_key,
            step_key=step.step_key,
            phase_order=phase.order,
            step_order=step.order,
        )

    def _validate_phases(self) -> None:
        seen_keys: set[str] = set()
        seen_orders: set[int] = set()
        for phase in self._phases:
            if phase.phase_key not in PREP_PHASE_KEYS:
                raise PrepRegistryValidationError(
                    key=phase.phase_key,
                    failure_class="unknown_phase_key",
                    remediation_hint="Use one of the canonical prep phase keys.",
                )
            if phase.phase_key in seen_keys:
                raise PrepRegistryValidationError(
                    key=phase.phase_key,
                    failure_class="duplicate_phase_key",
                    remediation_hint="Register each prep phase key only once.",
                )
            if phase.order in seen_orders:
                raise PrepRegistryValidationError(
                    key=phase.phase_key,
                    failure_class="duplicate_phase_order",
                    remediation_hint="Use a unique phase order value.",
                )
            seen_keys.add(phase.phase_key)
            seen_orders.add(phase.order)

    def _validate_steps(self) -> None:
        phase_keys = {phase.phase_key for phase in self._phases}
        seen_step_keys: set[str] = set()
        phase_orders: dict[str, set[int]] = defaultdict(set)
        for step in self._steps:
            if step.phase_key not in phase_keys:
                raise PrepRegistryValidationError(
                    key=step.step_key,
                    failure_class="missing_phase_reference",
                    remediation_hint="Register the owning phase before registering the step.",
                )
            if step.step_key in seen_step_keys:
                raise PrepRegistryValidationError(
                    key=step.step_key,
                    failure_class="duplicate_step_key",
                    remediation_hint="Register each prep step key only once.",
                )
            if step.order in phase_orders[step.phase_key]:
                raise PrepRegistryValidationError(
                    key=step.step_key,
                    failure_class="duplicate_step_order",
                    remediation_hint="Use a unique step order within the phase.",
                )
            seen_step_keys.add(step.step_key)
            phase_orders[step.phase_key].add(step.order)

    def _resolve_handler(self, step: PrepStepDefinition) -> PrepStepDefinition:
        try:
            module_name, attribute_name = step.handler_ref.split(":", maxsplit=1)
            module = importlib.import_module(module_name)
            getattr(module, attribute_name)
        except Exception as error:
            reason = sanitize_for_log(str(error))
            if step.handler_policy == HandlerPolicy.OPTIONAL:
                return step.with_handler_status(
                    handler_status=HandlerStatus.DISABLED_OPTIONAL,
                    disable_reason=reason,
                )
            raise PrepRegistryValidationError(
                key=step.step_key,
                failure_class="required_handler_unavailable",
                remediation_hint="Fix the handler_ref import path or mark the step optional.",
            ) from error

        return step.with_handler_status(handler_status=HandlerStatus.AVAILABLE)
```

- [ ] **Step 3: Add a local test support module for resolvable handlers**

Create `tests/unit/pdf_convert/prep/support.py`:

```python
def first_handler() -> None:
    return None


def inserted_handler() -> None:
    return None


def second_handler() -> None:
    return None


def extract_images() -> None:
    return None
```

- [ ] **Step 4: Run the prep registry test suite**

Run: `pytest tests/unit/pdf_convert/prep -v`
Expected: PASS

- [ ] **Step 5: Commit the registry runtime**

```bash
git add src/gm_kit/pdf_convert/prep/registry.py \
  src/gm_kit/pdf_convert/prep/__init__.py \
  tests/unit/pdf_convert/prep/test_registry_runtime.py \
  tests/unit/pdf_convert/prep/support.py
git commit -m "feat(prep): implement deterministic key-based prep registry"
```

---

### Task 4: Expose Package and Run Quality Gates

**Files:**
- Modify: `src/gm_kit/pdf_convert/__init__.py`
- Modify: `specs/e7-01-key-based-prep-registry/feature_journal.md`

- [ ] **Step 1: Export the prep package from `pdf_convert`**

Update:

```python
__all__ = [
    "state",
    "metadata",
    "preflight",
    "errors",
    "phases",
    "prep",
]
```

- [ ] **Step 2: Run focused unit tests**

Run: `pytest tests/unit/pdf_convert/prep -v`
Expected: PASS

- [ ] **Step 3: Run repository quality commands for the touched surface**

Run: `just format`
Expected: formatting completes without modifying unrelated files unexpectedly

Run: `just format-imports`
Expected: import ordering completes successfully

Run: `just lint`
Expected: PASS

Run: `just typecheck`
Expected: PASS

Run: `just test`
Expected: PASS

Run: `pytest --cov=src`
Expected: coverage does not regress for touched modules

- [ ] **Step 4: Record the implementation session in the feature journal**

Append a new entry to `specs/e7-01-key-based-prep-registry/feature_journal.md` documenting:
- modules added
- validation and ordering behaviors implemented
- tests added
- any follow-up issues for E7-02 or E7-03

- [ ] **Step 5: Commit the finished E7-01 foundation**

```bash
git add src/gm_kit/pdf_convert/__init__.py \
  specs/e7-01-key-based-prep-registry/feature_journal.md
git commit -m "feat(prep): complete E7-01 key-based prep registry foundation"
```

---

## Self-Review Notes

- Spec coverage is complete for the approved E7-01 design: typed definitions, canonical phases, deterministic ordering, insertion safety, startup validation, optional handler disable semantics, display alias generation, and sanitization are all implemented by the planned tasks.
- The plan deliberately does not touch CLI wiring, prep artifacts, or numeric conversion migration because those belong to E7-02, E7-03, and E7-09.
- The handler reference format is normalized to `module.path:callable_name` in this implementation so import/bind validation is deterministic and testable.
