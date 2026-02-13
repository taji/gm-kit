from __future__ import annotations

import json
from pathlib import Path

from gm_kit.pdf_convert.active_conversion import (
    ACTIVE_CONVERSION_FILENAME,
    _now_iso,
    resolve_active_candidates,
    update_active_conversion,
)


def test_update_active_conversion__should_write_state__when_called(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    update_active_conversion(tmp_path, output_dir)

    state_path = tmp_path / ".gmkit" / ACTIVE_CONVERSION_FILENAME
    assert state_path.exists()

    payload = json.loads(state_path.read_text())
    assert payload["active"]["path"] == str(output_dir)
    assert payload["history"][0]["path"] == str(output_dir)


def test_update_active_conversion__should_deduplicate_history__when_same_path_used(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    update_active_conversion(tmp_path, output_dir)
    update_active_conversion(tmp_path, output_dir)

    state_path = tmp_path / ".gmkit" / ACTIVE_CONVERSION_FILENAME
    payload = json.loads(state_path.read_text())
    assert len(payload["history"]) == 1
    assert payload["history"][0]["path"] == str(output_dir)


def test_resolve_active_candidates__should_return_existing_paths__when_state_present(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    update_active_conversion(tmp_path, output_dir)

    candidates = resolve_active_candidates(tmp_path)
    assert candidates == [output_dir.resolve()]


def test_now_iso__should_include_utc_offset__when_called() -> None:
    assert _now_iso().endswith("+00:00")
