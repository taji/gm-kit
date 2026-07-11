from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from numbers import Real
from pathlib import Path

PREP_CONTRACT_VERSION = "1"
BOUNDING_BOX_COORDINATE_COUNT = 4
ANNOTATION_PROPOSAL_LABELS = {"table", "callout", "skip"}
ANNOTATION_PROPOSAL_SOURCES = {"code", "ai", "hybrid"}
ANNOTATION_REVIEW_MODES = {"interactive", "auto_accept", "bypass"}
ANNOTATION_REVIEW_STATUSES = {"pending", "accepted", "revised", "auto_accepted"}
ANNOTATION_REVIEW_DECISIONS = {"accept", "reject", "edit"}
CALLOUT_REGION_LABELS = {"callout_gm", "callout_read_aloud"}


@dataclass(frozen=True)
class PrepPaths:
    root: Path
    manifest: Path
    state: Path
    complete: Path
    log: Path


@dataclass(frozen=True)
class PrepArtifactEntry:
    name: str
    status: str

    def validate(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("PrepArtifactEntry.name must be a non-empty string")
        if not isinstance(self.status, str) or not self.status:
            raise ValueError("PrepArtifactEntry.status must be a non-empty string")

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PrepArtifactEntry:
        entry = cls(name=_require_str(data, "name"), status=_require_str(data, "status"))
        entry.validate()
        return entry


@dataclass(frozen=True)
class PrepCommandMetadata:
    command_name: str
    resume_requested: bool = False

    def validate(self) -> None:
        if not isinstance(self.command_name, str) or not self.command_name:
            raise ValueError("PrepCommandMetadata.command_name must be a non-empty string")
        if not isinstance(self.resume_requested, bool):
            raise ValueError("PrepCommandMetadata.resume_requested must be a boolean")

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PrepCommandMetadata:
        metadata = cls(
            command_name=_require_str(data, "command_name"),
            resume_requested=_require_bool(data, "resume_requested", default=False),
        )
        metadata.validate()
        return metadata


@dataclass(frozen=True)
class PrepManifest:
    contract_version: str
    pdf_path: str
    workspace_path: str
    command_metadata: PrepCommandMetadata
    artifacts: list[PrepArtifactEntry]
    phase_keys: list[str]
    step_keys: list[str]
    completed: bool
    failure_phase_key: str | None = None
    failure_step_key: str | None = None
    failure_message: str | None = None

    def validate(self) -> None:
        if self.contract_version != PREP_CONTRACT_VERSION:
            raise ValueError(
                f"PrepManifest.contract_version must be {PREP_CONTRACT_VERSION}"
            )
        if not isinstance(self.pdf_path, str) or not self.pdf_path:
            raise ValueError("PrepManifest.pdf_path must be a non-empty string")
        if not isinstance(self.workspace_path, str) or not self.workspace_path:
            raise ValueError("PrepManifest.workspace_path must be a non-empty string")
        if not isinstance(self.completed, bool):
            raise ValueError("PrepManifest.completed must be a boolean")
        for field_name, field_value in (
            ("failure_phase_key", self.failure_phase_key),
            ("failure_step_key", self.failure_step_key),
            ("failure_message", self.failure_message),
        ):
            if field_value is not None and not isinstance(field_value, str):
                raise ValueError(f"PrepManifest.{field_name} must be a string or None")
        if self.completed and any(
            field_value is not None
            for field_value in (
                self.failure_phase_key,
                self.failure_step_key,
                self.failure_message,
            )
        ):
            raise ValueError("PrepManifest failure fields must be empty when completed")
        if not isinstance(self.command_metadata, PrepCommandMetadata):
            raise ValueError("PrepManifest.command_metadata must be PrepCommandMetadata")
        self.command_metadata.validate()
        if not isinstance(self.artifacts, list):
            raise ValueError("PrepManifest.artifacts must be a list")
        for artifact in self.artifacts:
            if not isinstance(artifact, PrepArtifactEntry):
                raise ValueError("PrepManifest.artifacts entries must be PrepArtifactEntry")
            artifact.validate()
        _validate_str_list(self.phase_keys, "phase_keys")
        _validate_str_list(self.step_keys, "step_keys")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PrepManifest:
        required_fields = [
            "contract_version",
            "pdf_path",
            "workspace_path",
            "command_metadata",
            "artifacts",
            "phase_keys",
            "step_keys",
            "completed",
        ]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"PrepManifest missing required fields: {missing_fields}")

        command_metadata_data = data["command_metadata"]
        if not isinstance(command_metadata_data, dict):
            raise ValueError("PrepManifest.command_metadata must be a mapping")

        artifacts_data = data["artifacts"]
        if not isinstance(artifacts_data, list):
            raise ValueError("PrepManifest.artifacts must be a list")

        manifest = cls(
            contract_version=_require_str(data, "contract_version"),
            pdf_path=_require_str(data, "pdf_path"),
            workspace_path=_require_str(data, "workspace_path"),
            command_metadata=PrepCommandMetadata.from_dict(command_metadata_data),
            artifacts=[
                PrepArtifactEntry.from_dict(artifact)
                for artifact in artifacts_data
                if isinstance(artifact, dict)
            ],
            phase_keys=_require_str_list(data, "phase_keys"),
            step_keys=_require_str_list(data, "step_keys"),
            completed=_require_bool(data, "completed"),
            failure_phase_key=_require_optional_str(data, "failure_phase_key"),
            failure_step_key=_require_optional_str(data, "failure_step_key"),
            failure_message=_require_optional_str(data, "failure_message"),
        )
        if len(manifest.artifacts) != len(artifacts_data):
            raise ValueError("PrepManifest.artifacts entries must be mappings")
        manifest.validate()
        return manifest


@dataclass(frozen=True)
class AnnotationProposal:
    proposal_id: str
    label: str
    page: int
    bbox: list[float]
    confidence: float
    metadata: dict[str, object]

    def validate(self) -> None:
        if not isinstance(self.proposal_id, str) or not self.proposal_id:
            raise ValueError("AnnotationProposal.proposal_id must be a non-empty string")
        if self.label not in ANNOTATION_PROPOSAL_LABELS:
            raise ValueError(
                "AnnotationProposal.label must be one of table, callout, skip"
            )
        if not isinstance(self.page, int) or isinstance(self.page, bool) or self.page < 1:
            raise ValueError("AnnotationProposal.page must be an integer >= 1")
        _validate_bbox(self.bbox, "AnnotationProposal.bbox")
        if (
            not isinstance(self.confidence, Real)
            or isinstance(self.confidence, bool)
            or not 0.0 <= float(self.confidence) <= 1.0
        ):
            raise ValueError(
                "AnnotationProposal.confidence must be a number between 0.0 and 1.0"
            )
        _validate_annotation_metadata(
            self.metadata,
            "AnnotationProposal.metadata",
        )

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "proposal_id": self.proposal_id,
            "label": self.label,
            "page": self.page,
            "bbox": [float(value) for value in self.bbox],
            "confidence": float(self.confidence),
            "metadata": _normalize_json_mapping(
                self.metadata,
                "AnnotationProposal.metadata",
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AnnotationProposal:
        proposal = cls(
            proposal_id=_require_non_empty_str(data, "proposal_id", "AnnotationProposal"),
            label=_require_non_empty_str(data, "label", "AnnotationProposal"),
            page=_require_positive_int(data, "page", "AnnotationProposal"),
            bbox=_require_bbox(data, "bbox", "AnnotationProposal"),
            confidence=_require_bounded_float(data, "confidence", "AnnotationProposal"),
            metadata=_require_annotation_metadata(
                data,
                "metadata",
                "AnnotationProposal",
            ),
        )
        proposal.validate()
        return proposal


@dataclass(frozen=True)
class PrepGuidanceInput:
    prefer_detect_tables: bool = True
    prefer_detect_callouts: bool = True
    prefer_skip_full_page_artifacts: bool = True
    review_requested: bool = True
    auto_accept_annotations: bool = False
    capture_skip_intent: bool = True
    callout_anchor_phrases: list[str] = field(
        default_factory=lambda: _default_callout_anchor_phrases()
    )
    callout_bbox_padding: dict[str, float] = field(
        default_factory=lambda: _default_callout_bbox_padding()
    )
    callout_max_vertical_gap: float = 18.0

    def validate(self) -> None:
        for field_name, field_value in (
            ("prefer_detect_tables", self.prefer_detect_tables),
            ("prefer_detect_callouts", self.prefer_detect_callouts),
            ("prefer_skip_full_page_artifacts", self.prefer_skip_full_page_artifacts),
            ("review_requested", self.review_requested),
            ("auto_accept_annotations", self.auto_accept_annotations),
            ("capture_skip_intent", self.capture_skip_intent),
        ):
            if not isinstance(field_value, bool):
                raise ValueError(f"PrepGuidanceInput.{field_name} must be a boolean")
        _validate_callout_anchor_phrases(
            self.callout_anchor_phrases,
            "PrepGuidanceInput.callout_anchor_phrases",
        )
        _validate_callout_bbox_padding(
            self.callout_bbox_padding,
            "PrepGuidanceInput.callout_bbox_padding",
        )
        if (
            not isinstance(self.callout_max_vertical_gap, Real)
            or isinstance(self.callout_max_vertical_gap, bool)
            or self.callout_max_vertical_gap <= 0
        ):
            raise ValueError(
                "PrepGuidanceInput.callout_max_vertical_gap must be a number greater than 0"
            )

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PrepGuidanceInput:
        guidance = cls(
            prefer_detect_tables=_require_bool_value(
                data,
                "prefer_detect_tables",
                "PrepGuidanceInput",
                default=True,
            ),
            prefer_detect_callouts=_require_bool_value(
                data,
                "prefer_detect_callouts",
                "PrepGuidanceInput",
                default=True,
            ),
            prefer_skip_full_page_artifacts=_require_bool_value(
                data,
                "prefer_skip_full_page_artifacts",
                "PrepGuidanceInput",
                default=True,
            ),
            review_requested=_require_bool_value(
                data,
                "review_requested",
                "PrepGuidanceInput",
                default=True,
            ),
            auto_accept_annotations=_require_bool_value(
                data,
                "auto_accept_annotations",
                "PrepGuidanceInput",
                default=False,
            ),
            capture_skip_intent=_require_bool_value(
                data,
                "capture_skip_intent",
                "PrepGuidanceInput",
                default=True,
            ),
            callout_anchor_phrases=_require_string_list_value(
                data,
                "callout_anchor_phrases",
                "PrepGuidanceInput",
                default=_default_callout_anchor_phrases(),
            ),
            callout_bbox_padding=_require_bbox_padding_value(
                data,
                "callout_bbox_padding",
                "PrepGuidanceInput",
                default=_default_callout_bbox_padding(),
            ),
            callout_max_vertical_gap=_require_real_value(
                data,
                "callout_max_vertical_gap",
                "PrepGuidanceInput",
                default=18.0,
            ),
        )
        guidance.validate()
        return guidance


@dataclass(frozen=True)
class AnnotationReviewEdits:
    review_mode: str
    review_status: str
    skip_ranges_input: str
    skip_pages_explicit: list[int]
    proposal_decisions: dict[str, str]
    updated_regions: dict[str, dict[str, object]]
    notes: str = ""

    def validate(self) -> None:
        _validate_choice(
            self.review_mode,
            "AnnotationReviewEdits.review_mode",
            ANNOTATION_REVIEW_MODES,
        )
        _validate_choice(
            self.review_status,
            "AnnotationReviewEdits.review_status",
            ANNOTATION_REVIEW_STATUSES,
        )
        if not isinstance(self.skip_ranges_input, str):
            raise ValueError("AnnotationReviewEdits.skip_ranges_input must be a string")
        _validate_page_list(
            self.skip_pages_explicit,
            "AnnotationReviewEdits.skip_pages_explicit",
        )
        _validate_proposal_decisions(
            self.proposal_decisions,
            "AnnotationReviewEdits.proposal_decisions",
        )
        _validate_updated_regions(
            self.updated_regions,
            "AnnotationReviewEdits.updated_regions",
        )
        if not isinstance(self.notes, str):
            raise ValueError("AnnotationReviewEdits.notes must be a string")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "review_mode": self.review_mode,
            "review_status": self.review_status,
            "skip_ranges_input": self.skip_ranges_input,
            "skip_pages_explicit": list(self.skip_pages_explicit),
            "proposal_decisions": dict(self.proposal_decisions),
            "updated_regions": {
                proposal_id: _serialize_review_region(region, proposal_id)
                for proposal_id, region in self.updated_regions.items()
            },
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AnnotationReviewEdits:
        edits = cls(
            review_mode=_require_non_empty_str(
                data,
                "review_mode",
                "AnnotationReviewEdits",
            ),
            review_status=_require_non_empty_str(
                data,
                "review_status",
                "AnnotationReviewEdits",
            ),
            skip_ranges_input=_require_str_value(
                data,
                "skip_ranges_input",
                "AnnotationReviewEdits",
                default="",
            ),
            skip_pages_explicit=_require_page_list(
                data,
                "skip_pages_explicit",
                "AnnotationReviewEdits",
            ),
            proposal_decisions=_require_decision_mapping(
                data,
                "proposal_decisions",
                "AnnotationReviewEdits",
            ),
            updated_regions=_require_updated_regions(
                data,
                "updated_regions",
                "AnnotationReviewEdits",
            ),
            notes=_require_str_value(
                data,
                "notes",
                "AnnotationReviewEdits",
                default="",
            ),
        )
        edits.validate()
        return edits


@dataclass(frozen=True)
class PrepGuidanceResolved:
    skip_pages: list[int]
    skip_regions: list[dict[str, object]]
    table_regions: list[dict[str, object]]
    callout_regions: list[dict[str, object]]

    def validate(self) -> None:
        _validate_page_list(self.skip_pages, "PrepGuidanceResolved.skip_pages")
        _validate_region_list(self.skip_regions, "PrepGuidanceResolved.skip_regions")
        _validate_region_list(self.table_regions, "PrepGuidanceResolved.table_regions")
        _validate_region_list(
            self.callout_regions,
            "PrepGuidanceResolved.callout_regions",
            require_label=True,
            label_choices=CALLOUT_REGION_LABELS,
        )

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "skip_pages": list(self.skip_pages),
            "skip_regions": [_serialize_region(region) for region in self.skip_regions],
            "table_regions": [_serialize_region(region) for region in self.table_regions],
            "callout_regions": [
                _serialize_region(
                    region,
                    require_label=True,
                    label_choices=CALLOUT_REGION_LABELS,
                )
                for region in self.callout_regions
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PrepGuidanceResolved:
        resolved = cls(
            skip_pages=_require_page_list(data, "skip_pages", "PrepGuidanceResolved"),
            skip_regions=_require_region_list(data, "skip_regions", "PrepGuidanceResolved"),
            table_regions=_require_region_list(data, "table_regions", "PrepGuidanceResolved"),
            callout_regions=_require_region_list(
                data,
                "callout_regions",
                "PrepGuidanceResolved",
                require_label=True,
                label_choices=CALLOUT_REGION_LABELS,
            ),
        )
        resolved.validate()
        return resolved


def build_prep_paths(workspace_dir: Path) -> PrepPaths:
    prep_root = workspace_dir / "prep"
    return PrepPaths(
        root=prep_root,
        manifest=prep_root / "prep-manifest.json",
        state=prep_root / "prep-state.json",
        complete=prep_root / "prep-complete.json",
        log=prep_root / "logs" / "prep.log",
    )


def _require_str(data: dict[str, object], key: str) -> str:
    value = data[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"PrepManifest.{key} must be a non-empty string")
    return value


def _require_bool(data: dict[str, object], key: str, default: bool | None = None) -> bool:
    if key not in data:
        if default is not None:
            return default
        raise ValueError(f"PrepManifest.{key} is required")
    value = data[key]
    if not isinstance(value, bool):
        raise ValueError(f"PrepManifest.{key} must be a boolean")
    return value


def _require_str_list(data: dict[str, object], key: str) -> list[str]:
    value = data[key]
    if not isinstance(value, list):
        raise ValueError(f"PrepManifest.{key} must be a list")
    return _validate_str_list(value, key)


def _require_optional_str(data: dict[str, object], key: str) -> str | None:
    if key not in data or data[key] is None:
        return None
    value = data[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"PrepManifest.{key} must be a string or None")
    return value


def _validate_str_list(values: Sequence[object], key: str) -> list[str]:
    if not isinstance(values, list):
        raise ValueError(f"PrepManifest.{key} must be a list")
    validated: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"PrepManifest.{key} entries must be strings")
        validated.append(value)
    return validated


def _require_non_empty_str(data: dict[str, object], key: str, owner: str) -> str:
    if key not in data:
        raise ValueError(f"{owner}.{key} is required")
    value = data[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"{owner}.{key} must be a non-empty string")
    return value


def _require_bool_value(
    data: dict[str, object],
    key: str,
    owner: str,
    default: bool | None = None,
) -> bool:
    if key not in data:
        if default is not None:
            return default
        raise ValueError(f"{owner}.{key} is required")
    value = data[key]
    if not isinstance(value, bool):
        raise ValueError(f"{owner}.{key} must be a boolean")
    return value


def _require_real_value(
    data: dict[str, object],
    key: str,
    owner: str,
    default: float | None = None,
) -> float:
    if key not in data:
        if default is not None:
            return float(default)
        raise ValueError(f"{owner}.{key} is required")
    value = data[key]
    if not isinstance(value, Real) or isinstance(value, bool):
        raise ValueError(f"{owner}.{key} must be a number")
    return float(value)


def _require_string_list_value(
    data: dict[str, object],
    key: str,
    owner: str,
    default: list[str] | None = None,
) -> list[str]:
    if key not in data:
        return list(default or [])
    value = data[key]
    if not isinstance(value, list):
        raise ValueError(f"{owner}.{key} must be a list")
    validated: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{owner}.{key} entries must be non-empty strings")
        validated.append(item)
    return validated


def _require_bbox_padding_value(
    data: dict[str, object],
    key: str,
    owner: str,
    default: dict[str, float] | None = None,
) -> dict[str, float]:
    if key not in data:
        return dict(default or {})
    value = data[key]
    if not isinstance(value, dict):
        raise ValueError(f"{owner}.{key} must be a mapping")
    padding: dict[str, float] = {}
    for side in ("top", "right", "bottom", "left"):
        if side not in value:
            raise ValueError(f"{owner}.{key} must define {side}")
        side_value = value[side]
        if not isinstance(side_value, Real) or isinstance(side_value, bool) or side_value < 0:
            raise ValueError(f"{owner}.{key}.{side} must be a number greater than or equal to 0")
        padding[side] = float(side_value)
    for extra_key, extra_value in value.items():
        if extra_key not in padding:
            if (
                not isinstance(extra_value, Real)
                or isinstance(extra_value, bool)
                or extra_value < 0
            ):
                raise ValueError(
                    f"{owner}.{key}.{extra_key} must be a number greater than or equal to 0"
                )
            padding[extra_key] = float(extra_value)
    return padding


def _require_str_value(
    data: dict[str, object],
    key: str,
    owner: str,
    default: str | None = None,
) -> str:
    if key not in data:
        if default is not None:
            return default
        raise ValueError(f"{owner}.{key} is required")
    value = data[key]
    if not isinstance(value, str):
        raise ValueError(f"{owner}.{key} must be a string")
    return value


def _default_callout_anchor_phrases() -> list[str]:
    return [
        "GM Note",
        "Gamemaster Note",
        "Gamemaster's Note",
        "DM Note",
        "Dungeonmaster Note",
        "Dungeonmaster's Note",
        "Keeper's Note",
    ]


def _default_callout_bbox_padding() -> dict[str, float]:
    return {
        "top": 4.0,
        "right": 6.0,
        "bottom": 6.0,
        "left": 6.0,
    }


def _validate_callout_anchor_phrases(values: Sequence[object], field_name: str) -> list[str]:
    validated: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} entries must be non-empty strings")
        validated.append(value)
    return validated


def _validate_callout_bbox_padding(
    values: dict[str, float],
    field_name: str,
) -> dict[str, float]:
    if not isinstance(values, dict):
        raise ValueError(f"{field_name} must be a mapping")
    for side in ("top", "right", "bottom", "left"):
        if side not in values:
            raise ValueError(f"{field_name} must define {side}")
        side_value = values[side]
        if not isinstance(side_value, Real) or isinstance(side_value, bool) or side_value < 0:
            raise ValueError(
                f"{field_name}.{side} must be a number greater than or equal to 0"
            )
    return {key: float(value) for key, value in values.items() if isinstance(value, Real)}


def _require_positive_int(data: dict[str, object], key: str, owner: str) -> int:
    if key not in data:
        raise ValueError(f"{owner}.{key} is required")
    value = data[key]
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{owner}.{key} must be an integer >= 1")
    return value


def _require_bbox(data: dict[str, object], key: str, owner: str) -> list[float]:
    if key not in data:
        raise ValueError(f"{owner}.{key} is required")
    return _validate_bbox(data[key], f"{owner}.{key}")


def _require_bounded_float(data: dict[str, object], key: str, owner: str) -> float:
    if key not in data:
        raise ValueError(f"{owner}.{key} is required")
    value = data[key]
    if (
        not isinstance(value, Real)
        or isinstance(value, bool)
        or not 0.0 <= float(value) <= 1.0
    ):
        raise ValueError(f"{owner}.{key} must be a number between 0.0 and 1.0")
    return float(value)


def _require_mapping(data: dict[str, object], key: str, owner: str) -> dict[str, object]:
    if key not in data:
        raise ValueError(f"{owner}.{key} is required")
    value = data[key]
    if not isinstance(value, dict):
        raise ValueError(f"{owner}.{key} must be a mapping")
    return dict(value)


def _require_annotation_metadata(
    data: dict[str, object],
    key: str,
    owner: str,
) -> dict[str, object]:
    metadata = _require_mapping(data, key, owner)
    return _validate_annotation_metadata(metadata, f"{owner}.{key}")


def _require_page_list(data: dict[str, object], key: str, owner: str) -> list[int]:
    if key not in data:
        raise ValueError(f"{owner}.{key} is required")
    return _validate_page_list(data[key], f"{owner}.{key}")


def _require_region_list(
    data: dict[str, object],
    key: str,
    owner: str,
    *,
    require_label: bool = False,
    label_choices: set[str] | None = None,
) -> list[dict[str, object]]:
    if key not in data:
        raise ValueError(f"{owner}.{key} is required")
    return _validate_region_list(
        data[key],
        f"{owner}.{key}",
        require_label=require_label,
        label_choices=label_choices,
    )


def _require_decision_mapping(
    data: dict[str, object],
    key: str,
    owner: str,
) -> dict[str, str]:
    mapping = _require_mapping(data, key, owner)
    return _validate_proposal_decisions(mapping, f"{owner}.{key}")


def _require_updated_regions(
    data: dict[str, object],
    key: str,
    owner: str,
) -> dict[str, dict[str, object]]:
    mapping = _require_mapping(data, key, owner)
    return _validate_updated_regions(mapping, f"{owner}.{key}")


def _validate_bbox(value: object, field_name: str) -> list[float]:
    if (
        not isinstance(value, list)
        or len(value) != BOUNDING_BOX_COORDINATE_COUNT
    ):
        raise ValueError(f"{field_name} must contain exactly four numeric values")
    bbox: list[float] = []
    for item in value:
        if not isinstance(item, Real) or isinstance(item, bool):
            raise ValueError(f"{field_name} must contain exactly four numeric values")
        bbox.append(float(item))
    return bbox


def _validate_choice(value: object, field_name: str, choices: set[str]) -> str:
    if not isinstance(value, str) or value not in choices:
        options = ", ".join(sorted(choices))
        raise ValueError(f"{field_name} must be one of {options}")
    return value


def _validate_page_list(value: object, field_name: str) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    pages: list[int] = []
    for item in value:
        if not isinstance(item, int) or isinstance(item, bool) or item < 1:
            raise ValueError(f"{field_name} entries must be integers >= 1")
        pages.append(item)
    return pages


def _validate_region_list(
    value: object,
    field_name: str,
    *,
    require_label: bool = False,
    label_choices: set[str] | None = None,
) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    regions: list[dict[str, object]] = []
    for entry in value:
        if not isinstance(entry, dict):
            raise ValueError(f"{field_name} entries must be mappings")
        required_keys = {"page", "bbox"}
        if require_label:
            required_keys.add("label")
        if any(required_key not in entry for required_key in required_keys):
            required_fields = "page, bbox, and label" if require_label else "page and bbox"
            raise ValueError(f"{field_name} entries must contain {required_fields}")
        region = {
            "page": _validate_page_value(entry["page"], f"{field_name}.page"),
            "bbox": _validate_bbox(entry["bbox"], f"{field_name}.bbox"),
        }
        if require_label:
            region["label"] = _validate_choice(
                entry["label"],
                f"{field_name}.label",
                label_choices or set(),
            )
        for extra_key, extra_value in entry.items():
            if extra_key not in region:
                region[extra_key] = _normalize_json_value(
                    extra_value,
                    f"{field_name}.{extra_key}",
                )
        regions.append(region)
    return regions


def _validate_proposal_decisions(
    value: object,
    field_name: str,
) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    decisions: dict[str, str] = {}
    for proposal_id, decision in value.items():
        if not isinstance(proposal_id, str) or not proposal_id:
            raise ValueError(f"{field_name} keys must be non-empty strings")
        decisions[proposal_id] = _validate_choice(
            decision,
            f"{field_name}.{proposal_id}",
            ANNOTATION_REVIEW_DECISIONS,
        )
    return decisions


def _validate_updated_regions(
    value: object,
    field_name: str,
) -> dict[str, dict[str, object]]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    regions: dict[str, dict[str, object]] = {}
    for proposal_id, region in value.items():
        if not isinstance(proposal_id, str) or not proposal_id:
            raise ValueError(f"{field_name} keys must be non-empty strings")
        if not isinstance(region, dict):
            raise ValueError(f"{field_name}.{proposal_id} must be a mapping")
        if any(required_key not in region for required_key in ("page", "bbox", "label")):
            raise ValueError(
                f"{field_name}.{proposal_id} must contain page, bbox, and label"
            )
        normalized_region = {
            "page": _validate_page_value(region["page"], f"{field_name}.{proposal_id}.page"),
            "bbox": _validate_bbox(region["bbox"], f"{field_name}.{proposal_id}.bbox"),
            "label": _validate_choice(
                region["label"],
                f"{field_name}.{proposal_id}.label",
                ANNOTATION_PROPOSAL_LABELS,
            ),
        }
        for extra_key, extra_value in region.items():
            if extra_key not in normalized_region:
                normalized_region[extra_key] = _normalize_json_value(
                    extra_value,
                    f"{field_name}.{proposal_id}.{extra_key}",
                )
        regions[proposal_id] = normalized_region
    return regions


def _validate_page_value(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{field_name} must be an integer >= 1")
    return value


def _serialize_region(
    region: dict[str, object],
    *,
    require_label: bool = False,
    label_choices: set[str] | None = None,
) -> dict[str, object]:
    serialized = dict(region)
    serialized["page"] = _validate_page_value(region["page"], "region.page")
    serialized["bbox"] = _validate_bbox(region["bbox"], "region.bbox")
    if require_label:
        serialized["label"] = _validate_choice(
            region["label"],
            "region.label",
            label_choices or set(),
        )
    for key, value in list(serialized.items()):
        if key not in {"page", "bbox"} | ({"label"} if require_label else set()):
            serialized[key] = _normalize_json_value(value, f"region.{key}")
    return serialized


def _serialize_review_region(
    region: dict[str, object],
    proposal_id: str,
) -> dict[str, object]:
    serialized = dict(region)
    serialized["page"] = _validate_page_value(
        region["page"],
        f"AnnotationReviewEdits.updated_regions.{proposal_id}.page",
    )
    serialized["bbox"] = _validate_bbox(
        region["bbox"],
        f"AnnotationReviewEdits.updated_regions.{proposal_id}.bbox",
    )
    serialized["label"] = _validate_choice(
        region["label"],
        f"AnnotationReviewEdits.updated_regions.{proposal_id}.label",
        ANNOTATION_PROPOSAL_LABELS,
    )
    for key, value in list(serialized.items()):
        if key not in {"page", "bbox", "label"}:
            serialized[key] = _normalize_json_value(
                value,
                f"AnnotationReviewEdits.updated_regions.{proposal_id}.{key}",
            )
    return serialized


def _validate_annotation_metadata(
    value: object,
    field_name: str,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")

    metadata = _normalize_json_mapping(value, field_name)
    source = metadata.get("source")
    if not isinstance(source, str) or source not in ANNOTATION_PROPOSAL_SOURCES:
        raise ValueError(
            f"{field_name}.source must be one of ai, code, hybrid"
        )
    return metadata


def _normalize_json_mapping(
    value: dict[str, object],
    field_name: str,
) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"{field_name} keys must be non-empty strings")
        normalized[key] = _normalize_json_value(item, f"{field_name}.{key}")
    return normalized


def _normalize_json_value(value: object, field_name: str) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_normalize_json_value(item, field_name) for item in value]
    if isinstance(value, dict):
        return _normalize_json_mapping(value, field_name)
    raise ValueError(f"{field_name} must be JSON-serializable")
