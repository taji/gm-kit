"""Contract loading and validation helpers."""

import json
import re
from pathlib import Path
from typing import Any, cast

try:
    from jsonschema import ValidationError

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    ValidationError = Exception

from .errors import ContractViolation


class ContractValidator:
    """Validator for agent step output contracts."""

    def __init__(self, schemas_dir: Path | None = None):
        """Initialize validator with schemas directory.

        Args:
            schemas_dir: Directory containing JSON schema files.
                        Defaults to package schemas directory.
        """
        if schemas_dir is None:
            schemas_dir = Path(__file__).parent / "schemas"
        self.schemas_dir = schemas_dir
        self._schema_cache: dict[str, dict[str, Any]] = {}

    def load_schema(self, step_id: str) -> dict[str, Any]:
        """Load JSON schema for a step.

        Args:
            step_id: Step identifier (e.g., '3.2')

        Returns:
            JSON schema as dictionary

        Raises:
            FileNotFoundError: If schema file doesn't exist
        """
        if step_id in self._schema_cache:
            return self._schema_cache[step_id]

        # Multi-page steps use a page/part suffix (e.g. "7.7_p1", "7.7_p2").
        # All pages of the same step share one schema, so strip the suffix before
        # resolving the filename (e.g. "7.7_p1" -> "step_7_7.schema.json").
        schema_step_id = re.sub(r"_p\d+$", "", step_id)
        schema_file = self.schemas_dir / f"step_{schema_step_id.replace('.', '_')}.schema.json"

        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        with open(schema_file) as f:
            schema = cast(dict[str, Any], json.load(f))

        self._schema_cache[step_id] = schema
        return schema

    def validate(self, step_id: str, output: dict[str, Any]) -> list[str]:
        """Validate agent output against contract schema.

        Args:
            step_id: Step identifier
            output: Agent output dictionary

        Returns:
            List of validation error messages (empty if valid)

        Raises:
            ContractViolation: If output violates contract
        """
        if not HAS_JSONSCHEMA:
            raise RuntimeError("jsonschema package required for validation")

        schema = self.load_schema(step_id)

        # Access jsonschema module directly since we checked HAS_JSONSCHEMA
        import jsonschema as js

        validator = js.Draft7Validator(schema)
        errors = list(validator.iter_errors(output))

        if errors:
            error_messages = [str(e.message) for e in errors]
            raise ContractViolation(step_id, error_messages, output)

        return []

    def is_valid(self, step_id: str, output: dict[str, Any]) -> bool:
        """Check if output is valid without raising.

        Args:
            step_id: Step identifier
            output: Agent output dictionary

        Returns:
            True if valid, False otherwise
        """
        try:
            self.validate(step_id, output)
            return True
        except ContractViolation:
            return False
