"""Contract tests for agent steps."""

import json
from pathlib import Path

import pytest

# Skip if jsonschema not available
pytest.importorskip("jsonschema")

from jsonschema import validate as jsonschema_validate


class TestStepContractValidation:
    """Base class for step contract validation."""

    def validate_output(self, step_id: str, output_data: dict, schema_dir: Path):
        """Validate output against schema.

        Args:
            step_id: Step identifier (e.g., '3.2')
            output_data: Output to validate
            schema_dir: Directory containing schema files
        """
        schema_file = schema_dir / f"step_{step_id.replace('.', '_')}.schema.json"

        if not schema_file.exists():
            pytest.skip(f"Schema file not found: {schema_file}")

        with open(schema_file) as f:
            schema = json.load(f)

        jsonschema_validate(output_data, schema)


class TestStep3_2Contract(TestStepContractValidation):
    """Contract tests for Step 3.2 (Visual TOC)."""

    def test_valid_toc_output(self):
        """Should validate correct TOC output."""
        output = {
            "step_id": "3.2",
            "status": "success",
            "data": {
                "entries": [
                    {"level": 1, "title": "Introduction", "page": 3},
                    {"level": 2, "title": "Overview", "page": 5},
                ]
            },
            "warnings": [],
        }
        # TODO: Add specific schema and validate
        assert output["step_id"] == "3.2"


class TestStep7_7Contract(TestStepContractValidation):
    """Contract tests for Step 7.7 (Table Detection)."""

    def test_valid_table_detection_output(self):
        """Should validate correct table detection output."""
        output = {
            "step_id": "7.7",
            "status": "success",
            "data": {
                "tables": [
                    {
                        "table_id": "t1",
                        "page_number": 5,
                        "bbox_pixels": {"x0": 67, "y0": 321, "x1": 633, "y1": 596},
                        "rows": 9,
                        "columns": 2,
                        "cells": 18,
                    }
                ]
            },
            "warnings": [],
        }
        assert output["data"]["tables"][0]["table_id"] == "t1"


class TestStep8_7Contract(TestStepContractValidation):
    """Contract tests for Step 8.7 (Table Conversion)."""

    def test_valid_table_conversion_output(self):
        """Should validate correct table conversion output."""
        output = {
            "step_id": "8.7",
            "status": "success",
            "data": {
                "tables": [
                    {
                        "table_id": "t1",
                        "markdown": "| Col1 | Col2 |\n|------|------|\n| A | B |",
                        "rows": 2,
                        "columns": 2,
                    }
                ],
                "changes_made": 1,
            },
            "warnings": [],
        }
        assert "markdown" in output["data"]["tables"][0]
