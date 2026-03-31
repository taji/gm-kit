"""Tests for token preflight utility."""

import os
from unittest.mock import patch

from gm_kit.pdf_convert.agents.token_preflight import (
    check_token_threshold,
    estimate_tokens,
    format_token_info,
)


class TestEstimateTokens:
    """Test token estimation."""

    def test_empty_string(self):
        """Should return 0 for empty string."""
        assert estimate_tokens("") == 0

    def test_simple_text(self):
        """Should estimate based on 4 chars per token."""
        text = "a" * 400  # 400 chars
        assert estimate_tokens(text) == 100  # 400 / 4 = 100

    def test_partial_token(self):
        """Should floor division (integer tokens)."""
        text = "a" * 10
        assert estimate_tokens(text) == 2  # 10 // 4 = 2


class TestCheckTokenThreshold:
    """Test token threshold checking."""

    def test_below_threshold(self):
        """Should not flag when below threshold."""
        text = "a" * 100  # 25 tokens
        result = check_token_threshold(text, threshold=1000)

        assert result["exceeds_threshold"] is False
        assert result["user_choice"] == "proceed"

    def test_above_threshold_interactive_proceed(self):
        """Should prompt and proceed on 'y'."""
        text = "a" * 4000  # 1000 tokens

        with patch("builtins.input", return_value="y"):
            result = check_token_threshold(text, threshold=500)

        assert result["exceeds_threshold"] is True
        assert result["user_choice"] == "proceed"
        assert "WARNING" in result["warning_message"]

    def test_above_threshold_interactive_skip(self):
        """Should prompt and skip on 'n'."""
        text = "a" * 4000

        with patch("builtins.input", return_value="n"):
            result = check_token_threshold(text, threshold=500)

        assert result["user_choice"] == "skip"

    def test_auto_proceed_mode(self):
        """Should auto-proceed when auto_proceed=True."""
        text = "a" * 4000
        result = check_token_threshold(text, threshold=500, auto_proceed=True)

        assert result["exceeds_threshold"] is True
        assert result["user_choice"] == "auto_proceed"

    def test_env_var_override(self):
        """Should use GM_TOKEN_THRESHOLD env var."""
        text = "a" * 2000  # 500 tokens

        with patch.dict(os.environ, {"GM_TOKEN_THRESHOLD": "400"}), patch(
            "builtins.input", return_value="y"
        ):
            result = check_token_threshold(text)

        assert result["threshold"] == 400
        assert result["exceeds_threshold"] is True


class TestFormatTokenInfo:
    """Test token info formatting."""

    def test_format(self):
        """Should format with commas and percentage."""
        info = format_token_info(50000, 100000)
        assert "50,000" in info
        assert "100,000" in info
        assert "50.0%" in info

    def test_over_threshold(self):
        """Should show >100% when over threshold."""
        info = format_token_info(150000, 100000)
        assert "150.0%" in info
