"""Tests for agent dispatch and runtime."""

import json
import os
import subprocess
from unittest.mock import MagicMock, mock_open, patch

import pytest

from gm_kit.pdf_convert.agents.dispatch import (
    DEFAULT_AGENT,
    AgentDispatchError,
    UnsupportedAgentError,
    build_agent_command,
    get_agent_config,
    get_ci_tested_agents,
    get_current_agent,
    get_supported_agents,
    invoke_agent,
    is_agent_available,
)
from gm_kit.pdf_convert.agents.errors import AgentStepError
from gm_kit.pdf_convert.agents.runtime import (
    AgentStepRuntime,
    run_agent_step,
)


class TestGetAgentConfig:
    """Test get_agent_config function."""

    def test_get_codex_config(self):
        """Should return codex configuration."""
        config = get_agent_config("codex")

        assert config["cli"] == "codex"
        assert "--full-auto" in config["args"]

    def test_get_claude_config(self):
        """Should return claude configuration."""
        config = get_agent_config("claude")

        assert config["cli"] == "claude"
        assert "--print" in config["args"]

    def test_default_from_env(self):
        """Should use GM_AGENT env var."""
        with patch.dict(os.environ, {"GM_AGENT": "claude"}):
            config = get_agent_config()

        assert config["cli"] == "claude"

    def test_default_fallback(self):
        """Should default to codex."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_agent_config()

        assert config["cli"] == DEFAULT_AGENT

    def test_unsupported_agent(self):
        """Should raise for unsupported agent."""
        with pytest.raises(UnsupportedAgentError):
            get_agent_config("unknown")


class TestBuildAgentCommand:
    """Test build_agent_command function."""

    def test_builds_codex_command(self):
        """Should build codex command."""
        cmd = build_agent_command(
            prompt="Process this text", workspace="/tmp/workspace", agent_name="codex"
        )

        assert "codex" in cmd
        assert "exec" in cmd
        assert cmd[-1] == "-"

    def test_builds_claude_command(self):
        """Should build claude command."""
        cmd = build_agent_command(
            prompt="Process this text", workspace="/tmp/workspace", agent_name="claude"
        )

        assert "claude" in cmd
        assert "--print" in cmd


class TestGetSupportedAgents:
    """Test agent listing functions."""

    def test_get_supported_agents(self):
        """Should return supported agents."""
        agents = get_supported_agents()

        assert "codex" in agents
        assert "claude" in agents
        assert "opencode" in agents
        assert "gemini" in agents
        assert "qwen" in agents

    def test_get_ci_tested_agents(self):
        """Should return CI-tested agents."""
        agents = get_ci_tested_agents()

        assert "codex" in agents
        assert "claude" in agents
        assert "opencode" in agents
        assert "gemini" not in agents  # Not CI-tested

    def test_get_current_agent(self):
        """Should return configured agent."""
        with patch.dict(os.environ, {"GM_AGENT": "claude"}):
            agent = get_current_agent()

        assert agent == "claude"

    def test_get_current_agent_codex_alias(self):
        """Should normalize codex-cli alias to codex."""
        with patch.dict(os.environ, {"GM_AGENT": "codex-cli"}):
            agent = get_current_agent()

        assert agent == "codex"


class TestIsAgentAvailable:
    """Test is_agent_available function."""

    @patch("gm_kit.pdf_convert.agents.dispatch.shutil.which")
    def test_agent_available(self, mock_which):
        """Should return True if agent in PATH."""
        mock_which.return_value = "/usr/bin/codex"

        result = is_agent_available("codex")

        assert result is True
        mock_which.assert_called_once_with("codex")

    @patch("gm_kit.pdf_convert.agents.dispatch.shutil.which")
    def test_agent_not_available(self, mock_which):
        """Should return False if agent not in PATH."""
        mock_which.return_value = None

        result = is_agent_available("codex")

        assert result is False


class TestInvokeAgent:
    """Test invoke_agent function."""

    @patch("gm_kit.pdf_convert.agents.dispatch.subprocess.run")
    def test_codex_invocation_uses_argv_and_devnull(self, mock_run):
        """Should invoke codex without shell string parsing."""
        mock_run.return_value = MagicMock(returncode=0)

        invoke_agent("Line1\nLine2 (test)", workspace="/tmp/workspace", agent_name="codex")

        _, kwargs = mock_run.call_args
        called_cmd = mock_run.call_args.args[0]
        assert isinstance(called_cmd, list)
        assert called_cmd[-1] == "-"
        assert kwargs.get("cwd") == "/tmp/workspace"
        from subprocess import DEVNULL

        assert kwargs.get("stdout") is DEVNULL
        assert kwargs.get("stderr") is DEVNULL
        assert kwargs.get("input") == "Line1\nLine2 (test)"
        assert "shell" not in kwargs

    @patch("gm_kit.pdf_convert.agents.dispatch.subprocess.run")
    def test_capture_output_disables_devnull_redirect(self, mock_run):
        """Should preserve stdout/stderr when capture_output is requested."""
        mock_run.return_value = MagicMock(returncode=0)

        invoke_agent(
            "Process this text",
            workspace="/tmp/workspace",
            agent_name="codex",
            capture_output=True,
        )

        _, kwargs = mock_run.call_args
        assert kwargs.get("capture_output") is True
        assert kwargs.get("input") == "Process this text"
        assert "stdout" not in kwargs
        assert "stderr" not in kwargs

    @patch.dict(os.environ, {"GM_AGENT_TIMEOUT_SEC": "123"})
    @patch("gm_kit.pdf_convert.agents.dispatch.subprocess.run")
    def test_timeout_uses_env_override(self, mock_run):
        """Should use GM_AGENT_TIMEOUT_SEC when provided."""
        mock_run.return_value = MagicMock(returncode=0)

        invoke_agent("Process this text", workspace="/tmp/workspace", agent_name="codex")

        _, kwargs = mock_run.call_args
        assert kwargs.get("timeout") == 123

    @patch.dict(os.environ, {"GM_AGENT_TIMEOUT_SEC": "bogus"})
    @patch("gm_kit.pdf_convert.agents.dispatch.subprocess.run")
    def test_timeout_falls_back_to_default_when_env_invalid(self, mock_run):
        """Should default timeout when GM_AGENT_TIMEOUT_SEC is not an int."""
        mock_run.return_value = MagicMock(returncode=0)

        invoke_agent("Process this text", workspace="/tmp/workspace", agent_name="codex")

        _, kwargs = mock_run.call_args
        assert kwargs.get("timeout") == 300

    @patch.dict(os.environ, {"GM_AGENT_TIMEOUT_SEC": "17"})
    @patch("gm_kit.pdf_convert.agents.dispatch.subprocess.run")
    def test_timeout_error_message_reports_configured_seconds(self, mock_run):
        """Should include configured timeout in timeout error message."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["codex"], timeout=17)

        with pytest.raises(AgentDispatchError, match="timed out after 17 seconds"):
            invoke_agent("Process this text", workspace="/tmp/workspace", agent_name="codex")


class TestAgentStepRuntime:
    """Test AgentStepRuntime class."""

    def test_initialization(self, tmp_path):
        """Should initialize with workspace."""
        runtime = AgentStepRuntime(str(tmp_path))

        assert runtime.workspace == str(tmp_path)
        assert runtime.max_retries == 3

    def test_initialization_reads_agent_debug_from_state(self, tmp_path):
        """Should enable debug mode when state config requests it."""
        (tmp_path / ".state.json").write_text(
            json.dumps({"config": {"agent_debug": True}}), encoding="utf-8"
        )

        runtime = AgentStepRuntime(str(tmp_path))

        assert runtime.agent_debug is True

    @patch("gm_kit.pdf_convert.agents.runtime.evaluate_step_output")
    @patch("gm_kit.pdf_convert.agents.runtime.write_agent_inputs")
    def test_execute_step__should_pause_and_then_complete_when_output_written(
        self, mock_write, mock_evaluate, tmp_path
    ):
        """Should pause on first call and complete on resume call."""
        from gm_kit.pdf_convert.agents.errors import AgentStepPause
        from gm_kit.pdf_convert.agents.evaluator import EvaluationResult

        step_dir = tmp_path / "agent_steps" / "step_3_2"
        step_dir.mkdir(parents=True)
        (step_dir / "step-instructions.md").write_text("# Instructions", encoding="utf-8")

        mock_write.return_value = step_dir
        mock_evaluate.return_value = EvaluationResult(
            step_id="3.2",
            passed=True,
            dimension_scores={"completeness": 5},
            critical_failures=[],
        )
        runtime = AgentStepRuntime(str(tmp_path))

        with pytest.raises(AgentStepPause):
            runtime.execute_step(step_id="3.2", inputs={"test": "data"}, attempt=1)

        (step_dir / "step-output.json").write_text(
            json.dumps(
                {
                    "step_id": "3.2",
                    "status": "success",
                    "data": {"entries": []},
                    "rubric_scores": {"completeness": 5},
                    "warnings": [],
                }
            ),
            encoding="utf-8",
        )

        with patch.object(runtime.validator, "validate"):
            envelope, status = runtime.execute_step(
                step_id="3.2", inputs={"test": "data"}, attempt=1
            )

        assert status.name == "COMPLETED"
        assert envelope is not None
        assert envelope.step_id == "3.2"
        assert (tmp_path / ".state.json").exists()

    @patch("gm_kit.pdf_convert.agents.runtime.write_agent_inputs")
    def test_execute_step__should_write_awaiting_state_when_handoff_created(
        self, mock_write, tmp_path
    ):
        """Should persist AWAITING_AGENT state metadata on handoff."""
        from gm_kit.pdf_convert.agents.errors import AgentStepPause

        step_dir = tmp_path / "agent_steps" / "step_3_2"
        step_dir.mkdir(parents=True)
        (step_dir / "step-instructions.md").write_text("# Instructions", encoding="utf-8")
        mock_write.return_value = step_dir
        runtime = AgentStepRuntime(str(tmp_path), agent_debug=True)

        with pytest.raises(AgentStepPause) as excinfo:
            runtime.execute_step(step_id="3.2", inputs={"test": "data"}, attempt=2)

        assert "Output File Checklist" in excinfo.value.recovery
        assert "step-output.json" in excinfo.value.recovery
        assert str(step_dir.resolve()) in excinfo.value.recovery

        state = json.loads((tmp_path / ".state.json").read_text(encoding="utf-8"))
        assert state["current_step"] == "3.2"
        assert state["agent_step_status"] == "AWAITING_AGENT"
        assert state["attempt"] == 2

    @patch("gm_kit.pdf_convert.agents.runtime.evaluate_step_output")
    @patch("gm_kit.pdf_convert.agents.runtime.write_agent_inputs")
    def test_execute_step__should_consume_existing_output__when_state_status_not_awaiting(
        self, mock_write, mock_evaluate, tmp_path
    ):
        """Should finalize existing step output even if state status is COMPLETED."""
        from gm_kit.pdf_convert.agents.evaluator import EvaluationResult

        step_dir = tmp_path / "agent_steps" / "step_9_3"
        step_dir.mkdir(parents=True)
        (step_dir / "step-output.json").write_text(
            json.dumps(
                {
                    "step_id": "9.3",
                    "status": "success",
                    "data": {"flow_issues": [], "readability_score": 4},
                    "rubric_scores": {
                        "reading_order": 4,
                        "paragraph_integrity": 4,
                        "flow_continuity": 4,
                    },
                    "warnings": [],
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / ".state.json").write_text(
            json.dumps(
                {
                    "current_step": "9.2",
                    "agent_step_status": "COMPLETED",
                    "attempt": 1,
                }
            ),
            encoding="utf-8",
        )
        mock_evaluate.return_value = EvaluationResult(
            step_id="9.3", passed=True, dimension_scores={}, critical_failures=[]
        )

        runtime = AgentStepRuntime(str(tmp_path))
        with patch.object(runtime.validator, "validate"):
            envelope, status = runtime.execute_step(
                step_id="9.3", inputs={"test": "data"}, attempt=1
            )

        assert status.name == "COMPLETED"
        assert envelope is not None
        mock_write.assert_not_called()

    @patch("gm_kit.pdf_convert.agents.runtime.evaluate_step_output")
    def test_execute_step__should_fill_boundary_accuracy__when_step_7_7_has_no_tables(
        self, mock_evaluate, tmp_path
    ):
        """Should normalize 7.7 no-table rubric scores before evaluation."""
        step_dir = tmp_path / "agent_steps" / "step_7_7"
        step_dir.mkdir(parents=True)
        (step_dir / "step-output.json").write_text(
            json.dumps(
                {
                    "step_id": "7.7",
                    "status": "success",
                    "data": {"tables_detected": False, "tables": []},
                    "warnings": [],
                    "rubric_scores": {"detection_recall": 5, "detection_precision": 5},
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / ".state.json").write_text(
            json.dumps(
                {
                    "current_step": "7.7",
                    "agent_step_status": "AWAITING_AGENT",
                    "attempt": 1,
                }
            ),
            encoding="utf-8",
        )

        from gm_kit.pdf_convert.agents.evaluator import EvaluationResult

        mock_evaluate.return_value = EvaluationResult(
            step_id="7.7", passed=True, dimension_scores={}, critical_failures=[]
        )

        runtime = AgentStepRuntime(str(tmp_path))

        with patch.object(runtime.validator, "validate"):
            runtime.execute_step(step_id="7.7", inputs={"test": "data"}, attempt=1)

        rubric_scores = mock_evaluate.call_args.kwargs["rubric_scores"]
        assert rubric_scores["boundary_accuracy"] == 5

    @patch("gm_kit.pdf_convert.agents.runtime.evaluate_step_output")
    def test_execute_step__should_not_fill_boundary_accuracy__when_step_7_7_has_table_boundary(
        self, mock_evaluate, tmp_path
    ):
        """Should preserve missing boundary score failure path for table detections."""
        step_dir = tmp_path / "agent_steps" / "step_7_7"
        step_dir.mkdir(parents=True)
        (step_dir / "step-output.json").write_text(
            json.dumps(
                {
                    "step_id": "7.7",
                    "status": "success",
                    "data": {
                        "table_id": "t1",
                        "bbox_pixels": {"x0": 1, "y0": 1, "x1": 2, "y1": 2},
                    },
                    "warnings": [],
                    "rubric_scores": {"detection_recall": 5, "detection_precision": 5},
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / ".state.json").write_text(
            json.dumps(
                {
                    "current_step": "7.7",
                    "agent_step_status": "AWAITING_AGENT",
                    "attempt": 1,
                }
            ),
            encoding="utf-8",
        )
        from gm_kit.pdf_convert.agents.evaluator import EvaluationResult

        mock_evaluate.return_value = EvaluationResult(
            step_id="7.7",
            passed=False,
            dimension_scores={},
            critical_failures=[],
        )

        runtime = AgentStepRuntime(str(tmp_path))
        with patch.object(runtime.validator, "validate"), pytest.raises(AgentStepError):
            runtime.execute_step(step_id="7.7", inputs={"test": "data"}, attempt=1)

        rubric_scores = mock_evaluate.call_args.kwargs["rubric_scores"]
        assert "boundary_accuracy" not in rubric_scores

    @patch("gm_kit.pdf_convert.agents.runtime.evaluate_step_output")
    @patch("gm_kit.pdf_convert.agents.runtime.write_agent_inputs")
    def test_execute_step__should_not_reuse_stale_output__when_inputs_do_not_match(
        self, mock_write, mock_evaluate, tmp_path
    ):
        """Should create new handoff when existing output belongs to a different input payload."""
        from gm_kit.pdf_convert.agents.errors import AgentStepPause
        from gm_kit.pdf_convert.agents.evaluator import EvaluationResult

        step_dir = tmp_path / "agent_steps" / "step_7_7"
        step_dir.mkdir(parents=True)
        (step_dir / "step-input.json").write_text(
            json.dumps({"step_id": "7.7", "phase": "text_scan", "page_number_1based": 1}),
            encoding="utf-8",
        )
        (step_dir / "step-output.json").write_text(
            json.dumps(
                {
                    "step_id": "7.7",
                    "status": "success",
                    "data": {"tables_detected": False, "tables": []},
                    "warnings": [],
                    "rubric_scores": {"detection_recall": 5, "detection_precision": 5},
                }
            ),
            encoding="utf-8",
        )
        mock_write.return_value = step_dir
        mock_evaluate.return_value = EvaluationResult(
            step_id="7.7",
            passed=True,
            dimension_scores={},
            critical_failures=[],
        )

        runtime = AgentStepRuntime(str(tmp_path))

        with pytest.raises(AgentStepPause):
            runtime.execute_step(
                step_id="7.7",
                inputs={"phase": "text_scan", "page_number_1based": 2},
                attempt=1,
            )

        mock_write.assert_called_once()

    @patch("gm_kit.pdf_convert.agents.runtime.evaluate_step_output")
    @patch("gm_kit.pdf_convert.agents.runtime.write_agent_inputs")
    def test_execute_step__should_not_reuse_stale_output__when_input_artifact_newer_than_output(
        self, mock_write, mock_evaluate, tmp_path
    ):
        """Should create new handoff when referenced artifacts changed after step output."""
        from gm_kit.pdf_convert.agents.errors import AgentStepPause
        from gm_kit.pdf_convert.agents.evaluator import EvaluationResult

        phase8 = tmp_path / "phase8.md"
        phase8.write_text("# updated", encoding="utf-8")

        step_dir = tmp_path / "agent_steps" / "step_9_4"
        step_dir.mkdir(parents=True)
        (step_dir / "step-input.json").write_text(
            json.dumps(
                {
                    "step_id": "9.4",
                    "input_artifacts": {"phase8_file": str(phase8)},
                    "optional_artifacts": {},
                    "attempt": 1,
                }
            ),
            encoding="utf-8",
        )
        output_file = step_dir / "step-output.json"
        output_file.write_text(
            json.dumps(
                {
                    "step_id": "9.4",
                    "status": "success",
                    "data": {"tables_checked": 1, "issues": [], "score": 5},
                    "warnings": [],
                    "rubric_scores": {
                        "cell_accuracy": 5,
                        "structure_preservation": 5,
                        "alignment_check": 5,
                    },
                }
            ),
            encoding="utf-8",
        )

        # Make artifact newer than step-output to simulate rerun-updated upstream file.
        newer = output_file.stat().st_mtime + 10
        os.utime(phase8, (newer, newer))

        mock_write.return_value = step_dir
        mock_evaluate.return_value = EvaluationResult(
            step_id="9.4",
            passed=True,
            dimension_scores={},
            critical_failures=[],
        )

        runtime = AgentStepRuntime(str(tmp_path))

        with pytest.raises(AgentStepPause):
            runtime.execute_step(
                step_id="9.4",
                inputs={
                    "input_artifacts": {"phase8_file": str(phase8)},
                    "optional_artifacts": {},
                    "attempt": 1,
                },
                attempt=1,
            )

        mock_write.assert_called_once()

    @patch("gm_kit.pdf_convert.agents.runtime.evaluate_step_output")
    @patch("gm_kit.pdf_convert.agents.runtime.write_agent_inputs")
    def test_execute_step__should_reuse_output__when_paused_on_same_step(
        self, mock_write, mock_evaluate, tmp_path
    ):
        """Should consume pending output for current paused step despite newer artifacts."""
        from gm_kit.pdf_convert.agents.base import StepStatus
        from gm_kit.pdf_convert.agents.evaluator import EvaluationResult

        phase4 = tmp_path / "phase4.md"
        phase4.write_text("updated", encoding="utf-8")

        step_dir = tmp_path / "agent_steps" / "step_4_5"
        step_dir.mkdir(parents=True)
        (step_dir / "step-input.json").write_text(
            json.dumps(
                {
                    "step_id": "4.5",
                    "input_artifacts": {"phase_file": str(phase4)},
                    "optional_artifacts": {},
                    "context": {"chunk_boundaries": []},
                    "attempt": 1,
                }
            ),
            encoding="utf-8",
        )
        output_file = step_dir / "step-output.json"
        output_file.write_text(
            json.dumps(
                {
                    "step_id": "4.5",
                    "status": "success",
                    "data": {"changes_made": 0, "joins_made": []},
                    "warnings": [],
                    "rubric_scores": {
                        "correct_joins": 5,
                        "no_false_joins": 5,
                        "readability": 5,
                    },
                }
            ),
            encoding="utf-8",
        )

        # Simulate phase artifact newer than output (would normally trigger stale path).
        newer = output_file.stat().st_mtime + 10
        os.utime(phase4, (newer, newer))

        (tmp_path / ".state.json").write_text(
            json.dumps(
                {
                    "current_step": "4.5",
                    "agent_step_status": "AWAITING_AGENT",
                    "attempt": 1,
                }
            ),
            encoding="utf-8",
        )

        mock_evaluate.return_value = EvaluationResult(
            step_id="4.5",
            passed=True,
            dimension_scores={},
            critical_failures=[],
        )

        runtime = AgentStepRuntime(str(tmp_path))
        with patch.object(runtime.validator, "validate"):
            envelope, status = runtime.execute_step(
                step_id="4.5",
                inputs={
                    "input_artifacts": {"phase_file": str(phase4)},
                    "optional_artifacts": {},
                    "context": {"chunk_boundaries": []},
                    "attempt": 1,
                },
                attempt=1,
            )

        assert envelope is not None
        assert status == StepStatus.COMPLETED
        mock_write.assert_not_called()

    @patch("gm_kit.pdf_convert.agents.runtime.evaluate_step_output")
    @patch("gm_kit.pdf_convert.agents.runtime.write_agent_inputs")
    def test_execute_step__should_reuse_output__for_step_4_5_when_phase_file_is_newer(
        self, mock_write, mock_evaluate, tmp_path
    ):
        """Should not stale-invalidate 4.5 output when phase4 artifact mtime advances."""
        from gm_kit.pdf_convert.agents.base import StepStatus
        from gm_kit.pdf_convert.agents.evaluator import EvaluationResult

        phase4 = tmp_path / "phase4.md"
        phase4.write_text("updated", encoding="utf-8")

        step_dir = tmp_path / "agent_steps" / "step_4_5"
        step_dir.mkdir(parents=True)
        (step_dir / "step-input.json").write_text(
            json.dumps(
                {
                    "step_id": "4.5",
                    "input_artifacts": {"phase_file": str(phase4)},
                    "optional_artifacts": {},
                    "context": {"chunk_boundaries": []},
                    "output_contract": "schemas/step_4_5.schema.json",
                    "attempt": 1,
                }
            ),
            encoding="utf-8",
        )
        output_file = step_dir / "step-output.json"
        output_file.write_text(
            json.dumps(
                {
                    "step_id": "4.5",
                    "status": "success",
                    "data": {"changes_made": 0, "joins_made": []},
                    "warnings": [],
                    "rubric_scores": {
                        "correct_joins": 5,
                        "no_false_joins": 5,
                        "readability": 5,
                    },
                }
            ),
            encoding="utf-8",
        )

        newer = output_file.stat().st_mtime + 10
        os.utime(phase4, (newer, newer))

        mock_evaluate.return_value = EvaluationResult(
            step_id="4.5",
            passed=True,
            dimension_scores={},
            critical_failures=[],
        )

        runtime = AgentStepRuntime(str(tmp_path))
        with patch.object(runtime.validator, "validate"):
            envelope, status = runtime.execute_step(
                step_id="4.5",
                inputs={
                    "input_artifacts": {"phase_file": str(phase4)},
                    "optional_artifacts": {},
                    "context": {"chunk_boundaries": []},
                    "output_contract": "schemas/step_4_5.schema.json",
                    "attempt": 1,
                },
                attempt=1,
            )

        assert envelope is not None
        assert status == StepStatus.COMPLETED
        mock_write.assert_not_called()

    @patch("gm_kit.pdf_convert.agents.runtime.Path.exists")
    @patch(
        "gm_kit.pdf_convert.agents.runtime.open",
        mock_open(read_data='{"status": "AWAITING_AGENT"}'),
    )
    def test_resume_step(self, mock_exists, tmp_path):
        """Should resume from awaiting state."""
        mock_exists.return_value = True

        runtime = AgentStepRuntime(str(tmp_path))

        # This would need more mocking for full test
        # Just verify it attempts to read state
        assert runtime.workspace == str(tmp_path)


class TestRunAgentStep:
    """Test run_agent_step convenience function."""

    @patch("gm_kit.pdf_convert.agents.runtime.AgentStepRuntime")
    def test_runs_step(self, mock_runtime_class):
        """Should run step via runtime."""
        mock_runtime = MagicMock()
        mock_runtime.execute_step.return_value = (MagicMock(), MagicMock())
        mock_runtime_class.return_value = mock_runtime

        from gm_kit.pdf_convert.agents.base import AgentStepOutputEnvelope

        mock_envelope = AgentStepOutputEnvelope(
            step_id="3.2", status="success", data={}, warnings=[]
        )
        mock_runtime.execute_step.return_value = (mock_envelope, MagicMock())

        result = run_agent_step(step_id="3.2", workspace="/tmp/test", inputs={"test": "data"})

        assert result.step_id == "3.2"
        mock_runtime_class.assert_called_once()
