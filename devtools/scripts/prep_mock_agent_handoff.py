#!/usr/bin/env python3
"""Prep-specific mock-agent handoff for callout refinement.

This runs `gmkit analyze-and-prep-pdf` in handoff mode, applies the local mock
refinement adapter directly to the paused callout crops, writes
`annotation-refined-proposals.json`, and resumes prep.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from gm_kit.pdf_convert.prep.analysis_artifacts import build_analysis_artifact_paths
from gm_kit.pdf_convert.prep.contracts import AnnotationProposal
from gm_kit.pdf_convert.prep.refinement import (
    CalloutRefinementCropEntry,
    MockCalloutRefinementAgent,
    refine_callout_proposals,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the prep analyze flow with a direct mock refinement handoff."
    )
    parser.add_argument("--pdf", required=True, help="Source PDF path for prep.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Prep workspace/output directory.",
    )
    parser.add_argument(
        "--python-version",
        default=None,
        help="Optional pinned Python version; defaults to repository .python-version.",
    )
    parser.add_argument(
        "--log-output",
        action="store_true",
        default=True,
        help="Forward prep progress to the console.",
    )
    return parser.parse_args()


def _workspace_root() -> Path:
    return Path.cwd().resolve()


def _python_version(workspace_root: Path, override: str | None) -> str:
    if override:
        return override
    for candidate_root in (workspace_root, *workspace_root.parents):
        candidate = candidate_root / ".python-version"
        if candidate.exists():
            return candidate.read_text(encoding="utf-8").strip()
    raise FileNotFoundError("Could not locate .python-version")


def _run_gmkit_analyze(
    *,
    workspace_root: Path,
    python_version: str,
    pdf_path: str,
    output_dir: str,
    log_output: bool,
) -> None:
    env = os.environ.copy()
    env["GMKIT_CALL_OUT_REFINEMENT_MODE"] = "handoff"
    cmd = [
        "uv",
        "run",
        "--python",
        python_version,
        "--extra",
        "dev",
        "--editable",
        "--",
        "gmkit",
        "analyze-and-prep-pdf",
        pdf_path,
        "--output",
        output_dir,
        "--yes",
    ]
    if log_output:
        cmd.append("--log-output")
    subprocess.run(cmd, cwd=str(workspace_root), env=env, check=True)


def _load_crop_entries(path: Path) -> list[CalloutRefinementCropEntry]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise ValueError(f"{path.name} must contain an items array")
    return [CalloutRefinementCropEntry(**item) for item in items if isinstance(item, dict)]


def _load_proposals(path: Path) -> list[AnnotationProposal]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path.name} must contain a JSON array")
    proposals: list[AnnotationProposal] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} entries must be JSON objects")
        proposals.append(AnnotationProposal.from_dict(item))
    return proposals


def _run_mock_refinement(output_dir: Path) -> None:
    analysis_paths = build_analysis_artifact_paths(output_dir)
    request_path = analysis_paths.annotation_refinement_request
    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    if not isinstance(request_payload, dict):
        raise ValueError("annotation-refinement-request.json must contain a JSON object")

    proposal_path = analysis_paths.annotation_proposals
    if not proposal_path.exists():
        raise FileNotFoundError(proposal_path)

    crop_manifest = analysis_paths.annotation_refinement_manifest
    if not crop_manifest.exists():
        raise FileNotFoundError(crop_manifest)

    proposals = _load_proposals(proposal_path)
    crop_entries = _load_crop_entries(crop_manifest)
    refined_proposals, decisions = refine_callout_proposals(
        proposals=proposals,
        crop_entries=crop_entries,
        agent=MockCalloutRefinementAgent(),
    )

    analysis_paths.annotation_refined_proposals.write_text(
        json.dumps([proposal.to_dict() for proposal in refined_proposals], indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Mock refinement complete: {len(decisions)} proposal(s) refined "
        f"from {len(crop_entries)} crop(s)."
    )


def _resume_gmkit(
    *,
    workspace_root: Path,
    python_version: str,
    output_dir: str,
) -> None:
    cmd = [
        "uv",
        "run",
        "--python",
        python_version,
        "--extra",
        "dev",
        "--editable",
        "--",
        "gmkit",
        "analyze-and-prep-pdf",
        "--resume",
        output_dir,
        "--yes",
    ]
    subprocess.run(cmd, cwd=str(workspace_root), check=True)


def main() -> int:
    args = parse_args()
    workspace_root = _workspace_root()
    python_version = _python_version(workspace_root, args.python_version)
    output_dir = Path(args.output_dir).resolve()

    _run_gmkit_analyze(
        workspace_root=workspace_root,
        python_version=python_version,
        pdf_path=args.pdf,
        output_dir=str(output_dir),
        log_output=args.log_output,
    )
    _run_mock_refinement(output_dir)
    _resume_gmkit(
        workspace_root=workspace_root,
        python_version=python_version,
        output_dir=str(output_dir),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
