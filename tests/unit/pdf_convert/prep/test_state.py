import json
from pathlib import Path

from gm_kit.pdf_convert.prep.state import (
    PrepRunState,
    PrepStatus,
    load_prep_state,
    save_prep_state,
)


def test_save_prep_state__should_round_trip_status__when_state_is_written(
    tmp_path: Path,
) -> None:
    path = tmp_path / "prep-state.json"
    state = PrepRunState(
        status=PrepStatus.INITIALIZED,
        current_phase_key=None,
        completed_steps=[],
    )

    save_prep_state(path, state)
    loaded = load_prep_state(path)

    assert loaded is not None
    assert loaded.status == PrepStatus.INITIALIZED
    assert loaded.completed_steps == []
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "status": "initialized",
        "current_phase_key": None,
        "completed_steps": [],
    }


def test_load_prep_state__should_return_none__when_state_file_missing(tmp_path: Path) -> None:
    assert load_prep_state(tmp_path / "missing-prep-state.json") is None


def test_prep_run_state__should_reject_malformed_payload__when_completed_steps_is_not_list() -> None:
    payload: dict[str, object] = {
        "status": "running",
        "current_phase_key": "prep.initialize-workspace",
        "completed_steps": "prep.initialize-workspace.bootstrap",
    }

    try:
        PrepRunState.from_dict(payload)
    except ValueError as error:
        assert "completed_steps" in str(error)
    else:  # pragma: no cover - safety guard for test intent
        raise AssertionError("PrepRunState.from_dict() should reject malformed payloads")


def test_prep_run_state__should_reject_malformed_payload__when_current_phase_key_is_not_string_or_none() -> None:
    payload = {
        "status": "running",
        "current_phase_key": 123,
        "completed_steps": [],
    }

    try:
        PrepRunState.from_dict(payload)
    except ValueError as error:
        assert "current_phase_key" in str(error)
    else:  # pragma: no cover - safety guard for test intent
        raise AssertionError("PrepRunState.from_dict() should reject malformed payloads")


def test_prep_run_state__should_reject_malformed_payload__when_status_is_invalid() -> None:
    payload: dict[str, object] = {
        "status": "paused",
        "current_phase_key": "prep.initialize-workspace",
        "completed_steps": [],
    }

    try:
        PrepRunState.from_dict(payload)
    except ValueError as error:
        assert "paused" in str(error)
    else:  # pragma: no cover - safety guard for test intent
        raise AssertionError("PrepRunState.from_dict() should reject invalid status values")
