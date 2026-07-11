from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gm_kit.pdf_convert.prep.chunking import CHUNK_PAGE_BUDGET
from gm_kit.pdf_convert.prep.contracts import build_prep_paths


@dataclass(frozen=True)
class PrepAnalysisArtifactPaths:
    metadata: Path
    preflight_report: Path
    images_dir: Path
    image_manifest: Path
    preprocessed_dir: Path
    no_images_pdf: Path
    toc: Path
    chapter_index: Path
    chunk_plan: Path
    guidance_defaults: Path
    annotation_proposals: Path
    annotation_refinement_hints: Path
    annotation_review_edits: Path
    guidance_resolved: Path
    reviewed_guidance: Path
    annotated_pdf: Path


def build_analysis_artifact_paths(
    workspace_dir: Path,
    pdf_stem: str | None = None,
) -> PrepAnalysisArtifactPaths:
    prep_root = build_prep_paths(workspace_dir).root
    resolved_pdf_stem = _validate_pdf_stem(pdf_stem)
    images_dir = prep_root / "images"
    preprocessed_dir = prep_root / "preprocessed"
    return PrepAnalysisArtifactPaths(
        metadata=prep_root / "metadata.json",
        preflight_report=prep_root / "preflight-report.json",
        images_dir=images_dir,
        image_manifest=images_dir / "image-manifest.json",
        preprocessed_dir=preprocessed_dir,
        no_images_pdf=preprocessed_dir / f"{resolved_pdf_stem}-no-images.pdf",
        toc=prep_root / "toc-extracted.txt",
        chapter_index=prep_root / "chapter-index.json",
        chunk_plan=prep_root / "chunk-plan.json",
        guidance_defaults=prep_root / "prep-guidance.defaults.yml",
        annotation_proposals=prep_root / "annotation-proposals.json",
        annotation_refinement_hints=prep_root / "annotation-refinement-hints.json",
        annotation_review_edits=prep_root / "annotation-review.edits.json",
        guidance_resolved=prep_root / "prep-guidance.resolved.json",
        reviewed_guidance=prep_root / "prep-guidance.reviewed.json",
        annotated_pdf=prep_root / "annotated-prep.pdf",
    )


def _validate_pdf_stem(pdf_stem: str | None) -> str:
    if pdf_stem is None:
        resolved_pdf_stem = "source"
    elif pdf_stem == "":
        raise ValueError("pdf_stem must be filename-safe")
    else:
        resolved_pdf_stem = pdf_stem
    candidate = Path(resolved_pdf_stem)

    if candidate.is_absolute():
        raise ValueError("pdf_stem must be filename-safe")
    if candidate.name != resolved_pdf_stem:
        raise ValueError("pdf_stem must be filename-safe")
    if ".." in candidate.parts:
        raise ValueError("pdf_stem must be filename-safe")
    if "\\" in resolved_pdf_stem:
        raise ValueError("pdf_stem must be filename-safe")

    return resolved_pdf_stem


def requires_chunk_plan(page_count: int) -> bool:
    return page_count > CHUNK_PAGE_BUDGET
