from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ACTIVE_CONVERSION_FILENAME = "active-conversion.json"
MAX_HISTORY = 20


@dataclass(frozen=True)
class ActiveConversionEntry:
    path: str
    updated_at: str


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _find_workspace_root(start: Path) -> Path:
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".gmkit").exists():
            return parent
    return current


def _active_state_path(start: Path) -> Path:
    root = _find_workspace_root(start)
    return root / ".gmkit" / ACTIVE_CONVERSION_FILENAME


def load_active_state(start: Path) -> dict | None:
    state_path = _active_state_path(start)
    if not state_path.exists():
        return None
    try:
        return json.loads(state_path.read_text())
    except json.JSONDecodeError:
        return None


def update_active_conversion(start: Path, output_dir: Path) -> None:
    output_dir = output_dir.resolve()
    state_path = _active_state_path(start)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    entry = ActiveConversionEntry(path=str(output_dir), updated_at=_now_iso())
    existing = load_active_state(start) or {}
    history = existing.get("history", [])

    # Deduplicate any existing entries for this path.
    history = [item for item in history if item.get("path") != entry.path]
    history.insert(0, {"path": entry.path, "updated_at": entry.updated_at})
    history = history[:MAX_HISTORY]

    payload = {
        "version": 1,
        "active": {"path": entry.path, "updated_at": entry.updated_at},
        "history": history,
    }
    state_path.write_text(json.dumps(payload, indent=2))


def resolve_active_candidates(start: Path) -> list[Path]:
    state = load_active_state(start)
    if not state:
        return []

    candidates: list[Path] = []
    active = state.get("active")
    if active and active.get("path"):
        candidates.append(Path(active["path"]))

    for item in state.get("history", []):
        path_value = item.get("path")
        if not path_value:
            continue
        candidates.append(Path(path_value))

    # Preserve order (most recent first), remove duplicates.
    seen: set[Path] = set()
    ordered: list[Path] = []
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            ordered.append(resolved)

    return ordered
