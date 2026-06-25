from __future__ import annotations

import re
from dataclasses import dataclass

_SECRET_PATTERNS = [
    re.compile(r"(?<![\w])((?:token)=)([^\s,.;:)\]]+)", re.IGNORECASE),
    re.compile(r"(?<![\w])((?:secret)=)([^\s,.;:)\]]+)", re.IGNORECASE),
    re.compile(r"(?<![\w])((?:password)=)([^\s,.;:)\]]+)", re.IGNORECASE),
    re.compile(r"(?<![\w])((?:api_key)=)([^\s,.;:)\]]+)", re.IGNORECASE),
    re.compile(r"(?<![\w])((?:credential)=)([^\s,.;:)\]]+)", re.IGNORECASE),
    re.compile(r"(?<![\w])((?:credentials)=)([^\s,.;:)\]]+)", re.IGNORECASE),
    re.compile(r"(?<![\w])((?:key)=)([^\s,.;:)\]]+)", re.IGNORECASE),
]
_ABSOLUTE_PATH_PATTERN = re.compile(r"(/[^\s]+)+")
_WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"[A-Za-z]:\\[^\s]+")


def sanitize_for_log(message: str) -> str:
    sanitized = message
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub(r"\1[REDACTED]", sanitized)
    sanitized = _ABSOLUTE_PATH_PATTERN.sub("[REDACTED_PATH]", sanitized)
    sanitized = _WINDOWS_ABSOLUTE_PATH_PATTERN.sub("[REDACTED_PATH]", sanitized)
    return sanitized


@dataclass(frozen=True)
class PrepRegistryValidationError(ValueError):
    key: str
    failure_class: str
    remediation_hint: str

    def __str__(self) -> str:
        raw = (
            f"Registry validation failed for '{self.key}' "
            f"({self.failure_class}). Remediation: {self.remediation_hint}"
        )
        return sanitize_for_log(raw)
