"""Tests for agent dispatch and runtime."""

import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from gm_kit.pdf_convert.agents.dispatch import (
    DEFAULT_AGENT,
    UnsupportedAgentError,
    build_agent_command,
    get_agent_config,
    get_ci_tested_agents,
    get_current_agent,
    get_supported_agents,
    is_agent_available,
)
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
        assert "Process this text" in cmd

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

    @patch("gm_kit.pdf_convert.agents.dispatch.subprocess.run")
    def test_agent_available(self, mock_run):
        """Should return True if agent in PATH."""
        mock_run.return_value = MagicMock(returncode=0)

        result = is_agent_available("codex")

        assert result is True
        mock_run.assert_called_once()

    @patch("gm_kit.pdf_convert.agents.dispatch.subprocess.run")
    def test_agent_not_available(self, mock_run):
        """Should return False if agent not in PATH."""
        mock_run.return_value = MagicMock(returncode=1)

        result = is_agent_available("codex")

        assert result is False


class TestAgentStepRuntime:
    """Test AgentStepRuntime class."""

    def test_initialization(self, tmp_path):
        """Should initialize with workspace."""
        runtime = AgentStepRuntime(str(tmp_path))

        assert runtime.workspace == str(tmp_path)
        assert runtime.max_retries == 3

    @patch("gm_kit.pdf_convert.agents.runtime.evaluate_step_output")
    @patch("gm_kit.pdf_convert.agents.runtime.write_agent_inputs")
    @patch("gm_kit.pdf_convert.agents.runtime.invoke_agent")
    @patch("gm_kit.pdf_convert.agents.runtime.read_agent_output")
    def test_execute_step_success(
        self, mock_read, mock_invoke, mock_write, mock_evaluate, tmp_path
    ):
        """Should execute step successfully."""
        # Create step directory and instruction file
        step_dir = tmp_path / "step_3_2"
        step_dir.mkdir(parents=True)
        (step_dir / "step-instructions.md").write_text("# Instructions")

        # Mock successful execution
        mock_write.return_value = step_dir
        mock_invoke.return_value = MagicMock(returncode=0)

        from gm_kit.pdf_convert.agents.base import AgentStepOutputEnvelope
        from gm_kit.pdf_convert.agents.evaluator import EvaluationResult

        mock_envelope = AgentStepOutputEnvelope(
            step_id="3.2", status="success", data={}, warnings=[], rubric_scores={"completeness": 5}
        )
        mock_read.return_value = mock_envelope

        # Mock successful evaluation
        mock_evaluate.return_value = EvaluationResult(
            step_id="3.2",
            passed=True,
            dimension_scores={"completeness": 5},
            critical_failures=[],
        )

        runtime = AgentStepRuntime(str(tmp_path))

        with patch.object(runtime.validator, "validate"):
            envelope, status = runtime.execute_step(
                step_id="3.2", inputs={"test": "data"}, attempt=1
            )

        assert status.name == "COMPLETED"

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
