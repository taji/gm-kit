from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path


class PrepStatus(str, Enum):
    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class PrepRunState:
    status: PrepStatus
    current_phase_key: str | None
    completed_steps: list[str]

    def validate(self) -> None:
        if not isinstance(self.status, PrepStatus):
            raise ValueError("PrepRunState.status must be PrepStatus")
        if self.current_phase_key is not None and not isinstance(self.current_phase_key, str):
            raise ValueError("PrepRunState.current_phase_key must be a string or None")
        if not isinstance(self.completed_steps, list):
            raise ValueError("PrepRunState.completed_steps must be a list")
        for step in self.completed_steps:
            if not isinstance(step, str):
                raise ValueError("PrepRunState.completed_steps entries must be strings")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PrepRunState:
        if "status" not in data:
            raise ValueError("PrepRunState.status is required")
        if "completed_steps" not in data:
            raise ValueError("PrepRunState.completed_steps is required")

        current_phase_key = data.get("current_phase_key")
        if current_phase_key is not None and not isinstance(current_phase_key, str):
            raise ValueError("PrepRunState.current_phase_key must be a string or None")

        completed_steps = data["completed_steps"]
        if not isinstance(completed_steps, list):
            raise ValueError("PrepRunState.completed_steps must be a list")
        if not all(isinstance(step, str) for step in completed_steps):
            raise ValueError("PrepRunState.completed_steps entries must be strings")

        state = cls(
            status=PrepStatus(str(data["status"])),
            current_phase_key=current_phase_key,
            completed_steps=completed_steps,
        )
        state.validate()
        return state


def save_prep_state(path: Path, state: PrepRunState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8")


def load_prep_state(path: Path) -> PrepRunState | None:
    if not path.exists():
        return None

    data = json.loads(path.read_text(encoding="utf-8"))
    return PrepRunState.from_dict(data)
