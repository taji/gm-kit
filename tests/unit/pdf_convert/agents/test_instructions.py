"""Test instruction template rendering."""


from gm_kit.pdf_convert.agents.agent_step import _render_template


class TestTemplateRendering:
    """Test template variable substitution."""

    def test_simple_substitution(self):
        """Should substitute simple variables."""
        template = "Hello {name}!"
        result = _render_template(template, {"name": "World"})
        assert result == "Hello World!"

    def test_multiple_substitutions(self):
        """Should substitute multiple variables."""
        template = "{greeting} {name}, you have {count} messages."
        inputs = {"greeting": "Hi", "name": "Alice", "count": "5"}
        result = _render_template(template, inputs)
        assert result == "Hi Alice, you have 5 messages."

    def test_missing_variable_unchanged(self):
        """Should leave missing variables as placeholders."""
        template = "Hello {name}, from {place}"
        result = _render_template(template, {"name": "World"})
        assert "Hello World" in result
        assert "{place}" in result


class TestStep7_7PromptBuilding:
    """Test step 7.7 two-pass prompt building."""

    def test_build_text_scan_prompt(self):
        """Should build text scan prompt."""
        from gm_kit.pdf_convert.agents.instructions.step_7_7 import build_text_scan_prompt

        prompt = build_text_scan_prompt("Sample text content", 5)

        assert "Step 7.7" in prompt
        assert "5" in prompt  # Page number
        assert "Sample text" in prompt
        assert "step-output.json" in prompt

    def test_build_vision_prompt(self):
        """Should build vision prompt."""
        from gm_kit.pdf_convert.agents.instructions.step_7_7 import build_vision_prompt

        prompt = build_vision_prompt("tests/fixtures/page_5.png", "Some text context")

        assert "Step 7.7" in prompt
        assert "tests/fixtures/page_5.png" in prompt
        assert "bbox_pixels" in prompt
