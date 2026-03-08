"""Tests for contract validation helpers."""


import pytest

# Skip tests if jsonschema not available
pytest.importorskip("jsonschema")

from gm_kit.pdf_convert.agents.contracts import ContractValidator
from gm_kit.pdf_convert.agents.errors import ContractViolation


class TestContractValidator:
    """Test ContractValidator class."""

    def test_load_schema(self, tmp_path):
        """Should load schema from file."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        schema_file = schema_dir / "step_3_2.schema.json"
        schema_file.write_text('{"type": "object", "required": ["step_id"]}')

        validator = ContractValidator(schema_dir)
        schema = validator.load_schema("3.2")

        assert schema["type"] == "object"
        assert "step_id" in schema["required"]

    def test_validate_valid_output(self, tmp_path):
        """Should pass validation for valid output."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        schema = {
            "type": "object",
            "required": ["step_id", "status"],
            "properties": {"step_id": {"type": "string"}, "status": {"type": "string"}},
        }
        schema_file = schema_dir / "step_3_2.schema.json"
        import json

        schema_file.write_text(json.dumps(schema))

        validator = ContractValidator(schema_dir)
        output = {"step_id": "3.2", "status": "success"}

        errors = validator.validate("3.2", output)
        assert errors == []

    def test_validate_invalid_output(self, tmp_path):
        """Should raise ContractViolation for invalid output."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        schema = {
            "type": "object",
            "required": ["step_id", "status"],
        }
        schema_file = schema_dir / "step_3_2.schema.json"
        import json

        schema_file.write_text(json.dumps(schema))

        validator = ContractValidator(schema_dir)
        output = {"step_id": "3.2"}  # Missing required 'status'

        with pytest.raises(ContractViolation) as exc_info:
            validator.validate("3.2", output)

        assert "3.2" in str(exc_info.value)

    def test_is_valid_returns_bool(self, tmp_path):
        """Should return boolean without raising."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        schema_file = schema_dir / "step_3_2.schema.json"
        import json

        schema_file.write_text(
            json.dumps(
                {
                    "type": "object",
                    "required": ["step_id"],
                }
            )
        )

        validator = ContractValidator(schema_dir)

        assert validator.is_valid("3.2", {"step_id": "3.2"}) is True
        assert validator.is_valid("3.2", {}) is False
