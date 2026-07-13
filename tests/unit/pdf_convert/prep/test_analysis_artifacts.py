from pathlib import Path

import pytest

from gm_kit.pdf_convert.prep.analysis_artifacts import build_analysis_artifact_paths


def test_build_analysis_artifact_paths__should_return_expected_subtree__when_workspace_provided(
    tmp_path: Path,
) -> None:
    paths = build_analysis_artifact_paths(tmp_path / "workspace", pdf_stem="sample")

    assert paths.metadata == tmp_path / "workspace" / "prep" / "metadata.json"
    assert paths.preflight_report == tmp_path / "workspace" / "prep" / "preflight-report.json"
    assert paths.images_dir == tmp_path / "workspace" / "prep" / "images"
    assert paths.image_manifest == tmp_path / "workspace" / "prep" / "images" / "image-manifest.json"
    assert paths.preprocessed_dir == tmp_path / "workspace" / "prep" / "preprocessed"
    assert (
        paths.no_images_pdf
        == tmp_path / "workspace" / "prep" / "preprocessed" / "sample-no-images.pdf"
    )
    assert paths.toc == tmp_path / "workspace" / "prep" / "toc-extracted.txt"
    assert paths.chapter_index == tmp_path / "workspace" / "prep" / "chapter-index.json"
    assert paths.chunk_plan == tmp_path / "workspace" / "prep" / "chunk-plan.json"
    assert (
        paths.guidance_defaults
        == tmp_path / "workspace" / "prep" / "prep-guidance.defaults.yml"
    )
    assert (
        paths.annotation_proposals
        == tmp_path / "workspace" / "prep" / "annotation-proposals.json"
    )
    assert (
        paths.annotation_refinement_hints
        == tmp_path / "workspace" / "prep" / "annotation-refinement-hints.json"
    )
    assert paths.annotation_refinement_dir == tmp_path / "workspace" / "prep" / "annotation-refinement"
    assert (
        paths.annotation_refinement_request
        == tmp_path
        / "workspace"
        / "prep"
        / "annotation-refinement"
        / "annotation-refinement-request.json"
    )
    assert (
        paths.annotation_refinement_manifest
        == tmp_path
        / "workspace"
        / "prep"
        / "annotation-refinement"
        / "annotation-refinement-inputs.json"
    )
    assert (
        paths.annotation_refinement_crops_dir
        == tmp_path / "workspace" / "prep" / "annotation-refinement" / "crops"
    )
    assert (
        paths.annotation_refined_proposals
        == tmp_path / "workspace" / "prep" / "annotation-refined-proposals.json"
    )
    assert (
        paths.annotation_review_edits
        == tmp_path / "workspace" / "prep" / "annotation-review.edits.json"
    )
    assert (
        paths.guidance_resolved
        == tmp_path / "workspace" / "prep" / "prep-guidance.resolved.json"
    )
    assert (
        paths.reviewed_guidance
        == tmp_path / "workspace" / "prep" / "prep-guidance.reviewed.json"
    )
    assert paths.annotated_pdf == tmp_path / "workspace" / "prep" / "annotated-prep.pdf"


def test_build_analysis_artifact_paths__should_use_source_fallback__when_pdf_stem_not_provided(
    tmp_path: Path,
) -> None:
    paths = build_analysis_artifact_paths(tmp_path / "workspace")

    assert (
        paths.no_images_pdf
        == tmp_path / "workspace" / "prep" / "preprocessed" / "source-no-images.pdf"
    )


@pytest.mark.parametrize(
    "pdf_stem",
    ["", "/tmp/escape", "../escape", "nested/name", r"nested\\name"],
)
def test_build_analysis_artifact_paths__should_reject_unsafe_pdf_stem__when_input_can_escape_prep_root(
    tmp_path: Path,
    pdf_stem: str,
) -> None:
    with pytest.raises(ValueError) as error:
        build_analysis_artifact_paths(tmp_path / "workspace", pdf_stem=pdf_stem)
    assert str(error.value) == "pdf_stem must be filename-safe"
