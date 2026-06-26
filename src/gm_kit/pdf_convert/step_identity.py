from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StepIdentity:
    step_key: str
    display_id: str
    display_name: str
    phase: int

    def __post_init__(self) -> None:
        if not self.step_key.strip():
            raise ValueError("step_key must not be empty")
        if not self.display_id.strip():
            raise ValueError("display_id must not be empty")
        if not self.display_name.strip():
            raise ValueError("display_name must not be empty")
        if self.phase < 0:
            raise ValueError("phase must be non-negative")

    @property
    def workspace_slug(self) -> str:
        return self.step_key

    @property
    def display_label(self) -> str:
        return self.display_id

    def workspace_path(self, output_dir: Path) -> Path:
        return Path(output_dir) / "agent_steps" / f"phase_{self.phase}" / self.workspace_slug
