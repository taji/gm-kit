from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from gm_kit.pdf_convert.prep.contracts import AnnotationProposal

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[4]
    / "devtools"
    / "scripts"
    / "prep_mock_agent_handoff.py"
)

spec = importlib.util.spec_from_file_location("prep_mock_agent_handoff", _SCRIPT_PATH)
assert spec and spec.loader, "Could not locate prep_mock_agent_handoff.py"
prep_mock_agent_handoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep_mock_agent_handoff)


def test_load_crop_entries__should_reconstruct_entries__when_manifest_contains_items(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "annotation-refinement-inputs.json"
    crop_path = tmp_path / "crops" / "callout-ap-test_p001.png"
    crop_path.parent.mkdir(parents=True, exist_ok=True)
    crop_path.write_bytes(b"png")
    manifest_path.write_text(
        json.dumps(
            {
                "source_pdf_path": "source.pdf",
                "candidate_count": 1,
                "crops_dir": str(crop_path.parent),
                "items": [
                    {
                        "proposal_id": "ap-test",
                        "page": 1,
                        "bbox": [10.0, 20.0, 30.0, 40.0],
                        "anchor_phrase": "gm note",
                        "anchor_text": "GM Note",
                        "issue": "expanded_across_multiple_text_blocks",
                        "collected_block_count": 3,
                        "image_path": str(crop_path),
                        "source_pdf_path": "source.pdf",
                        "crop_rect": [8.0, 18.0, 32.0, 42.0],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    entries = prep_mock_agent_handoff._load_crop_entries(manifest_path)

    assert len(entries) == 1
    assert entries[0].proposal_id == "ap-test"
    assert entries[0].crop_rect == [8.0, 18.0, 32.0, 42.0]


def test_load_proposals__should_reconstruct_annotation_proposals__when_json_contains_array(
    tmp_path: Path,
) -> None:
    proposals_path = tmp_path / "annotation-proposals.json"
    proposals_path.write_text(
        json.dumps(
            [
                {
                    "proposal_id": "ap-test",
                    "label": "callout",
                    "page": 1,
                    "bbox": [10.0, 20.0, 30.0, 40.0],
                    "confidence": 0.9,
                    "metadata": {"source": "code"},
                }
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    proposals = prep_mock_agent_handoff._load_proposals(proposals_path)

    assert len(proposals) == 1
    assert proposals[0] == AnnotationProposal(
        proposal_id="ap-test",
        label="callout",
        page=1,
        bbox=[10.0, 20.0, 30.0, 40.0],
        confidence=0.9,
        metadata={"source": "code"},
    )
