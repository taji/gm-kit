from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HandlerPolicy(str, Enum):  # noqa: UP042
    REQUIRED = "required"
    OPTIONAL = "optional"


class HandlerStatus(str, Enum):  # noqa: UP042
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
    ) -> PrepStepDefinition:
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
