"""Unit tests for Phase 0 preflight behavior."""

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase0 import Phase0
from gm_kit.pdf_convert.state import ConversionState


class _Report:
    """Minimal preflight report stub for tests."""

    def __init__(self, text_extractable: bool = True, image_count: int = 0):
        self.text_extractable = text_extractable
        self.image_count = image_count


def test_phase0__should_preserve_user_callout_config__when_provided(tmp_path, monkeypatch):
    """Phase 0 should not overwrite a provided gm_callout_config_file."""
    pdf_path = tmp_path / "input.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    provided_callout = tmp_path / "provided-callouts.json"
    provided_callout.write_text("[]", encoding="utf-8")

    state = ConversionState(
        pdf_path=str(pdf_path),
        output_dir=str(tmp_path),
        config={"gm_callout_config_file": str(provided_callout)},
    )

    monkeypatch.setattr(
        "gm_kit.pdf_convert.phases.phase0.extract_metadata",
        lambda *_a, **_k: type("M", (), {"title": "", "page_count": 1, "has_toc": False})(),
    )
    monkeypatch.setattr("gm_kit.pdf_convert.phases.phase0.save_metadata", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "gm_kit.pdf_convert.phases.phase0.analyze_pdf",
        lambda *_a, **_k: _Report(text_extractable=True, image_count=0),
    )

    phase = Phase0()
    result = phase.execute(state)

    assert result.status in (PhaseStatus.SUCCESS, PhaseStatus.WARNING)
    assert state.config["gm_callout_config_file"] == str(provided_callout)
    step = next(s for s in result.steps if s.step_id == "0.6")
    assert step.status == PhaseStatus.SKIPPED


def test_phase0__should_create_default_callout_config__when_not_provided(tmp_path, monkeypatch):
    """Phase 0 should create output default callout config when none provided."""
    pdf_path = tmp_path / "input.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    state = ConversionState(
        pdf_path=str(pdf_path),
        output_dir=str(output_dir),
        config={},
    )

    monkeypatch.setattr(
        "gm_kit.pdf_convert.phases.phase0.extract_metadata",
        lambda *_a, **_k: type("M", (), {"title": "", "page_count": 1, "has_toc": False})(),
    )
    monkeypatch.setattr("gm_kit.pdf_convert.phases.phase0.save_metadata", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "gm_kit.pdf_convert.phases.phase0.analyze_pdf",
        lambda *_a, **_k: _Report(text_extractable=True, image_count=0),
    )

    phase = Phase0()
    result = phase.execute(state)

    expected_path = output_dir / "callout_config.json"
    assert result.status in (PhaseStatus.SUCCESS, PhaseStatus.WARNING)
    assert expected_path.exists()
    assert state.config["gm_callout_config_file"] == str(expected_path)
