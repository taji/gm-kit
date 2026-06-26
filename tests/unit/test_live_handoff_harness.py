"""Unit tests for live_handoff_harness helper functions."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Load the harness module without installing it as a package.
# ---------------------------------------------------------------------------
_HARNESS_PATH = (
    Path(__file__).resolve().parents[2] / "devtools" / "scripts" / "live_handoff_harness.py"
)


def _load_harness():
    spec = importlib.util.spec_from_file_location("live_handoff_harness", _HARNESS_PATH)
    assert spec and spec.loader, "Could not locate live_handoff_harness.py"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[arg-type]
    return mod


harness = _load_harness()


# ---------------------------------------------------------------------------
# _strip_ansi
# ---------------------------------------------------------------------------


class TestStripAnsi:
    def test_strip_ansi__should_remove_colour_codes__when_present(self):
        raw = "\x1b[91m\x1b[1mError: \x1b[0mSomething went wrong"
        assert harness._strip_ansi(raw) == "Error: Something went wrong"

    def test_strip_ansi__should_return_unchanged__when_no_escapes(self):
        plain = "Just plain text"
        assert harness._strip_ansi(plain) == plain

    def test_strip_ansi__should_remove_reset_code__when_standalone(self):
        assert harness._strip_ansi("\x1b[0m") == ""

    def test_strip_ansi__should_handle_empty_string(self):
        assert harness._strip_ansi("") == ""

    def test_strip_ansi__should_remove_multiple_sequences__when_mixed(self):
        raw = "\x1b[32m> build\x1b[0m · \x1b[90mgpt-5.1-codex\x1b[0m"
        assert harness._strip_ansi(raw) == "> build · gpt-5.1-codex"


# ---------------------------------------------------------------------------
# _prefix_lines
# ---------------------------------------------------------------------------


class TestPrefixLines:
    def test_prefix_lines__should_tag_content_lines__when_source_provided(self):
        text = "line one\nline two\n"
        result = harness._prefix_lines(text, "GMKIT")
        assert result == "[GMKIT] line one\n[GMKIT] line two\n"

    def test_prefix_lines__should_pass_through_blank_lines__when_empty(self):
        text = "line one\n\nline two\n"
        result = harness._prefix_lines(text, "AGENT")
        assert result == "[AGENT] line one\n\n[AGENT] line two\n"

    def test_prefix_lines__should_handle_empty_string(self):
        assert harness._prefix_lines("", "GMKIT") == ""

    def test_prefix_lines__should_use_agent_prefix__when_source_is_agent(self):
        result = harness._prefix_lines("hello\n", "AGENT")
        assert result.startswith("[AGENT]")

    def test_prefix_lines__should_use_harness_prefix__when_source_is_harness(self):
        result = harness._prefix_lines("msg\n", "HARNESS")
        assert result.startswith("[HARNESS]")


# ---------------------------------------------------------------------------
# emit_output
# ---------------------------------------------------------------------------


class TestEmitOutput:
    def test_emit_output__should_write_tagged_clean_content__when_source_gmkit(
        self, tmp_path, capsys
    ):
        log = tmp_path / "console.log"
        harness.emit_output("Phase 1/10: Image Extraction...\n", log, source="GMKIT")

        log_text = log.read_text(encoding="utf-8")
        assert "[GMKIT] Phase 1/10: Image Extraction..." in log_text
        # Terminal output is raw (no prefix)
        captured = capsys.readouterr()
        assert "Phase 1/10" in captured.out

    def test_emit_output__should_write_tagged_content__when_source_agent(self, tmp_path, capsys):
        log = tmp_path / "console.log"
        harness.emit_output("Generated step-output.json\n", log, source="AGENT")

        log_text = log.read_text(encoding="utf-8")
        assert "[AGENT] Generated step-output.json" in log_text

    def test_emit_output__should_strip_ansi_in_log__when_ansi_present(self, tmp_path, capsys):
        log = tmp_path / "console.log"
        harness.emit_output("\x1b[32mSuccess\x1b[0m\n", log, source="GMKIT")

        log_text = log.read_text(encoding="utf-8")
        # Log must be clean
        assert "\x1b" not in log_text
        assert "[GMKIT] Success" in log_text
        # Terminal gets the raw ANSI version
        captured = capsys.readouterr()
        assert "\x1b[32m" in captured.out

    def test_emit_output__should_preserve_blank_line_spacing__when_multi_line(self, tmp_path):
        log = tmp_path / "console.log"
        harness.emit_output("line one\n\nline two\n", log, source="GMKIT")

        log_text = log.read_text(encoding="utf-8")
        assert "[GMKIT] line one\n\n[GMKIT] line two\n" in log_text

    def test_emit_output__should_skip_file_write__when_no_log_file(self, capsys):
        # Should not raise even when console_log_file is None
        harness.emit_output("hello\n", None, source="GMKIT")
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_emit_output__should_do_nothing__when_text_empty(self, tmp_path):
        log = tmp_path / "console.log"
        harness.emit_output("", log, source="GMKIT")
        assert not log.exists()

    def test_emit_output__should_append__when_called_multiple_times(self, tmp_path):
        log = tmp_path / "console.log"
        harness.emit_output("first\n", log, source="GMKIT")
        harness.emit_output("second\n", log, source="AGENT")

        log_text = log.read_text(encoding="utf-8")
        assert "[GMKIT] first" in log_text
        assert "[AGENT] second" in log_text


# ---------------------------------------------------------------------------
# pause parsing / step validation
# ---------------------------------------------------------------------------


class TestPauseStepParsing:
    def test_parse_pause_step_dir__should_capture_key_based_workspace__when_present(self):
        combined = (
            "Paused for agent step 3.2 in "
            "`/tmp/run/agent_steps/phase_9/text-flow-assessment`.\n"
        )

        assert harness.parse_pause_step_dir(combined) == Path(
            "/tmp/run/agent_steps/phase_9/text-flow-assessment"
        )

    def test_step_id_from_dir__should_return_step_key__when_key_based_workspace(self):
        step_dir = Path("/tmp/run/agent_steps/phase_9/text-flow-assessment")

        assert harness.step_id_from_dir(step_dir) == "text-flow-assessment"


class TestValidateStepOutput:
    def test_validate_step_output__should_use_output_step_id__when_output_is_present(
        self, tmp_path
    ):
        step_dir = tmp_path / "agent_steps" / "phase_9" / "text-flow-assessment"
        step_dir.mkdir(parents=True)
        (step_dir / "step-output.json").write_text(
            json.dumps(
                {
                    "step_id": "9.3",
                    "status": "success",
                    "data": {"ok": True},
                    "warnings": [],
                }
            ),
            encoding="utf-8",
        )

        class Validator:
            def __init__(self) -> None:
                self.step_ids: list[str] = []

            def validate(self, *, step_id: str, output: dict[str, object]) -> None:
                self.step_ids.append(step_id)

        validator = Validator()

        valid, message = harness.validate_step_output(
            step_dir, "text-flow-assessment", validator, ValueError
        )

        assert valid is True
        assert message == "contract valid"
        assert validator.step_ids == ["9.3"]
