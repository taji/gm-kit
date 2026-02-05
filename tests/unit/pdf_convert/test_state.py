"""Unit tests for state management (T019)."""

import json
from pathlib import Path

import pytest

from gm_kit.pdf_convert.constants import PHASE_MAX, PHASE_MIN
from gm_kit.pdf_convert.state import (
    ConversionState,
    ConversionStatus,
    ErrorInfo,
    SCHEMA_VERSION,
    save_state,
    load_state,
    validate_state_for_resume,
    _acquire_lock,
    _release_lock,
)


class TestErrorInfo:
    """Tests for ErrorInfo dataclass."""

    def test_error_info__should_create_valid_instance__when_valid_fields(self):
        """ErrorInfo can be created with all fields."""
        error = ErrorInfo(
            phase=5,
            step="5.3",
            code="PDF_ERROR",
            message="Failed to extract text",
            recoverable=True,
            suggestion="Try re-running phase 5",
        )
        assert error.phase == 5
        assert error.step == "5.3"
        assert error.code == "PDF_ERROR"

    def test_error_info__should_roundtrip__when_converted_to_dict_and_back(self):
        """ErrorInfo can roundtrip through dictionary."""
        original = ErrorInfo(
            phase=3,
            step="3.1",
            code="STATE_ERROR",
            message="State corrupted",
            recoverable=False,
            suggestion="Delete state and restart",
        )
        data = original.to_dict()
        restored = ErrorInfo.from_dict(data)

        assert restored.phase == original.phase
        assert restored.step == original.step
        assert restored.code == original.code
        assert restored.recoverable == original.recoverable


class TestConversionState:
    """Tests for ConversionState dataclass."""

    def test_conversion_state__should_create_initial_state__when_valid_paths(self, tmp_path):
        """ConversionState can be created with minimal fields."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
        )

        assert state.version == SCHEMA_VERSION
        assert state.current_phase == 0
        assert state.current_step == "0.1"
        assert state.status == ConversionStatus.IN_PROGRESS
        assert state.completed_phases == []
        assert state.error is None

    def test_conversion_state__should_convert_to_absolute__when_relative_paths(self, tmp_path):
        """ConversionState converts paths to absolute."""
        # Use relative-looking path (though in tmp_path)
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )

        assert Path(state.pdf_path).is_absolute()
        assert Path(state.output_dir).is_absolute()

    def test_conversion_state__should_accept_status__when_string_or_enum(self, tmp_path):
        """ConversionState accepts string or enum for status."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
            status="completed",  # string
        )
        assert state.status == ConversionStatus.COMPLETED

    def test_conversion_state__should_update_phase__when_set_current_phase_called(self, tmp_path):
        """set_current_phase updates phase and step."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )

        state.set_current_phase(5, "5.3")
        assert state.current_phase == 5
        assert state.current_step == "5.3"

    def test_conversion_state__should_raise_error__when_phase_out_of_range(self, tmp_path):
        """set_current_phase rejects invalid phase numbers."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )

        with pytest.raises(ValueError, match=f"Phase must be {PHASE_MIN}-{PHASE_MAX}"):
            state.set_current_phase(-1)

        with pytest.raises(ValueError, match=f"Phase must be {PHASE_MIN}-{PHASE_MAX}"):
            state.set_current_phase(11)

    def test_conversion_state__should_add_to_completed__when_phase_marked_completed(self, tmp_path):
        """mark_phase_completed adds to completed list."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )

        result = {"phase_num": 0, "status": "SUCCESS"}
        state.mark_phase_completed(0, result)

        assert 0 in state.completed_phases
        assert result in state.phase_results

    def test_conversion_state__should_sort_completed_phases__when_added_out_of_order(self, tmp_path):
        """mark_phase_completed keeps completed_phases sorted."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )

        state.mark_phase_completed(2, {"phase_num": 2})
        state.mark_phase_completed(0, {"phase_num": 0})
        state.mark_phase_completed(1, {"phase_num": 1})

        assert state.completed_phases == [0, 1, 2]

    def test_conversion_state__should_set_status_and_error__when_set_failed_called(self, tmp_path):
        """set_failed sets status and error."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )

        error = ErrorInfo(
            phase=3, step="3.1", code="ERR",
            message="Failed", recoverable=True, suggestion="Retry"
        )
        state.set_failed(error)

        assert state.status == ConversionStatus.FAILED
        assert state.error == error

    def test_conversion_state__should_set_completed_status__when_set_completed_called(self, tmp_path):
        """set_completed sets status."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )

        state.set_completed()
        assert state.status == ConversionStatus.COMPLETED

    def test_conversion_state__should_set_cancelled_status__when_set_cancelled_called(self, tmp_path):
        """set_cancelled sets status."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )

        state.set_cancelled()
        assert state.status == ConversionStatus.CANCELLED

    def test_conversion_state__should_roundtrip__when_converted_to_dict_and_back(self, tmp_path):
        """ConversionState can roundtrip through dictionary."""
        original = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
            current_phase=5,
            current_step="5.3",
            completed_phases=[0, 1, 2, 3, 4],
            diagnostics_enabled=True,
            config={"key": "value"},
        )

        data = original.to_dict()
        restored = ConversionState.from_dict(data)

        assert restored.version == original.version
        assert restored.pdf_path == original.pdf_path
        assert restored.current_phase == original.current_phase
        assert restored.completed_phases == original.completed_phases
        assert restored.diagnostics_enabled == original.diagnostics_enabled
        assert restored.config == original.config

    def test_conversion_state__should_include_error_in_dict__when_error_present(self, tmp_path):
        """to_dict includes error when present."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )
        error = ErrorInfo(
            phase=1, step="1.1", code="ERR",
            message="Msg", recoverable=True, suggestion="Fix"
        )
        state.set_failed(error)

        data = state.to_dict()
        assert data["error"] is not None
        assert data["error"]["code"] == "ERR"


class TestStatePersistence:
    """Tests for save_state and load_state."""

    def test_save_state__should_create_file__when_valid_state(self, tmp_path):
        """save_state creates .state.json file."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )

        save_state(state)

        state_file = tmp_path / ".state.json"
        assert state_file.exists()

    def test_save_state__should_roundtrip__when_saved_and_loaded(self, tmp_path):
        """State can be saved and loaded."""
        original = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
            current_phase=3,
            current_step="3.2",
            completed_phases=[0, 1, 2],
        )

        save_state(original)
        loaded = load_state(tmp_path)

        assert loaded is not None
        assert loaded.current_phase == original.current_phase
        assert loaded.completed_phases == original.completed_phases

    def test_load_state__should_return_none__when_file_missing(self, tmp_path):
        """load_state returns None when file doesn't exist."""
        result = load_state(tmp_path)
        assert result is None

    def test_load_state__should_raise_error__when_invalid_json(self, tmp_path):
        """load_state raises ValueError for invalid JSON."""
        state_file = tmp_path / ".state.json"
        state_file.write_text("not valid json{")

        with pytest.raises(ValueError, match="not valid JSON"):
            load_state(tmp_path)

    def test_load_state__should_raise_error__when_missing_fields(self, tmp_path):
        """load_state raises ValueError for missing required fields."""
        state_file = tmp_path / ".state.json"
        state_file.write_text('{"version": "1.0"}')

        with pytest.raises(ValueError, match="missing required fields"):
            load_state(tmp_path)

    def test_load_state__should_raise_error__when_future_version(self, tmp_path):
        """load_state raises ValueError for incompatible future version."""
        state_file = tmp_path / ".state.json"
        data = {
            "version": "99.0",  # Future major version
            "pdf_path": str(tmp_path / "test.pdf"),
            "output_dir": str(tmp_path),
            "started_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "current_phase": 0,
            "current_step": "0.1",
            "status": "in_progress",
        }
        state_file.write_text(json.dumps(data))

        with pytest.raises(ValueError, match="requires gmkit version"):
            load_state(tmp_path)

    def test_save_state__should_create_directory__when_output_dir_missing(self, tmp_path):
        """save_state creates output directory if needed."""
        nested = tmp_path / "nested" / "path"
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(nested),
        )

        save_state(state)

        assert (nested / ".state.json").exists()

    def test_save_state__should_raise_error__when_lock_unavailable(self, tmp_path, monkeypatch):
        """save_state raises OSError when lock cannot be acquired."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )

        monkeypatch.setattr("gm_kit.pdf_convert.state._acquire_lock", lambda *_: False)
        monkeypatch.setattr("gm_kit.pdf_convert.state.time.sleep", lambda *_: None)

        with pytest.raises(OSError, match="Could not acquire lock"):
            save_state(state)


class TestAtomicWrite:
    """Tests for atomic write mechanism."""

    def test_save_state__should_write_complete_file__when_atomic_write(self, tmp_path):
        """Atomic write prevents partial state files."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
            completed_phases=[0, 1, 2],
        )
        save_state(state)

        # Read back and verify complete
        loaded = load_state(tmp_path)
        assert loaded.completed_phases == [0, 1, 2]


class TestFileLocking:
    """Tests for file locking mechanism."""

    def test_lock__should_acquire_and_release__when_not_held(self, tmp_path):
        """Lock can be acquired and released."""
        lock_path = tmp_path / ".state.lock"

        # Acquire
        acquired = _acquire_lock(lock_path, timeout=1)
        assert acquired is True
        assert lock_path.exists()

        # Release
        _release_lock(lock_path)
        assert not lock_path.exists()

    def test_lock__should_fail_second_acquire__when_already_held(self, tmp_path):
        """Second acquire fails while lock held."""
        lock_path = tmp_path / ".state.lock"

        # First acquire
        acquired1 = _acquire_lock(lock_path, timeout=1)
        assert acquired1 is True

        # Second acquire should fail (with short timeout)
        acquired2 = _acquire_lock(lock_path, timeout=0.5)
        assert acquired2 is False

        # Clean up
        _release_lock(lock_path)

    def test_lock__should_acquire__when_stale_lock_from_dead_process(self, tmp_path):
        """Stale lock from dead process is cleaned up."""
        lock_path = tmp_path / ".state.lock"

        # Create fake stale lock with invalid PID
        with open(lock_path, 'w') as f:
            f.write("99999999")  # Very high PID unlikely to exist

        # Should be able to acquire (stale lock cleaned up)
        acquired = _acquire_lock(lock_path, timeout=2)
        assert acquired is True

        _release_lock(lock_path)

    def test_lock__should_acquire__when_lock_pid_invalid(self, tmp_path):
        """Invalid PID in lock file is cleaned up."""
        lock_path = tmp_path / ".state.lock"

        lock_path.write_text("not-a-pid")

        acquired = _acquire_lock(lock_path, timeout=2)
        assert acquired is True

        _release_lock(lock_path)


class TestValidateStateForResume:
    """Tests for validate_state_for_resume."""

    def test_validate_state__should_return_empty__when_valid(self, tmp_path):
        """Valid state returns empty error list."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=3,
            current_step="3.1",
            completed_phases=[0, 1, 2],
        )

        errors = validate_state_for_resume(state)
        assert errors == []

    def test_validate_state__should_return_error__when_pdf_missing(self, tmp_path):
        """Missing PDF file returns error."""
        state = ConversionState(
            pdf_path=str(tmp_path / "nonexistent.pdf"),
            output_dir=str(tmp_path),
        )

        errors = validate_state_for_resume(state)
        assert errors == [f"Source PDF not found: {tmp_path / 'nonexistent.pdf'}"]

    def test_validate_state__should_return_error__when_output_dir_missing(self, tmp_path):
        """Missing output directory returns error."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path / "nonexistent"),
        )

        errors = validate_state_for_resume(state)
        assert errors == [f"Output directory not found: {tmp_path / 'nonexistent'}"]

    def test_validate_state__should_return_error__when_invalid_step_format(self, tmp_path):
        """Invalid step format returns error."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_step="invalid",
        )

        errors = validate_state_for_resume(state)
        assert errors == ["Invalid current_step format: invalid"]

    def test_validate_state__should_return_error__when_completed_phases_unsorted(self, tmp_path):
        """Unsorted completed_phases returns error."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=3,
        )
        # Manually set unsorted list (bypassing mark_phase_completed)
        state.completed_phases = [2, 0, 1]

        errors = validate_state_for_resume(state)
        assert errors == ["completed_phases is not sorted"]

    def test_validate_state__should_return_error__when_completed_phase_exceeds_current(self, tmp_path):
        """Completed phase >= current_phase returns error."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=3,
        )
        state.completed_phases = [0, 1, 2, 3]  # 3 >= current_phase 3

        errors = validate_state_for_resume(state)
        assert errors == ["completed_phases contains 3 >= current_phase 3"]

    def test_validate_state__should_return_error__when_phase_out_of_range(self, tmp_path):
        """Invalid current_phase returns error."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=PHASE_MAX + 1,
        )

        errors = validate_state_for_resume(state)
        assert errors == [f"Invalid current_phase: {PHASE_MAX + 1}"]
