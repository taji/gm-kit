from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from gm_kit.pdf_convert.errors import ExitCode, get_exit_code_for_error
from gm_kit.pdf_convert.orchestrator import create_output_directory
from gm_kit.pdf_convert.prep.analysis_artifacts import (
    PrepAnalysisArtifactPaths,
    build_analysis_artifact_paths,
)
from gm_kit.pdf_convert.prep.contracts import (
    PREP_CONTRACT_VERSION,
    PrepArtifactEntry,
    PrepCommandMetadata,
    PrepManifest,
    PrepPaths,
    build_prep_paths,
)
from gm_kit.pdf_convert.prep.refinement import PrepRefinementPause
from gm_kit.pdf_convert.prep.registry import PREP_PHASE_KEYS, PrepRegistry
from gm_kit.pdf_convert.prep.registry_errors import sanitize_for_log
from gm_kit.pdf_convert.prep.registry_types import (
    HandlerPolicy,
    PrepPhaseDefinition,
    PrepStepDefinition,
)
from gm_kit.pdf_convert.prep.state import (
    PrepRunState,
    PrepStatus,
    load_prep_state,
    save_prep_state,
)


class _PrepStepFailure(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        current_phase_key: str | None,
        current_step_key: str | None,
        completed_steps: list[str],
    ) -> None:
        super().__init__(message)
        self.current_phase_key = current_phase_key
        self.current_step_key = current_step_key
        self.completed_steps = completed_steps


@dataclass(frozen=True)
class _ManifestContext:
    prep_paths: PrepPaths
    pdf_path: Path
    workspace_dir: Path
    step_keys: list[str]
    phase_keys: list[str]
    analysis_paths: PrepAnalysisArtifactPaths
    failure_phase_key: str | None = None
    failure_step_key: str | None = None
    failure_message: str | None = None


@dataclass(frozen=True)
class _FailureManifestContext:
    phase_key: str | None
    step_key: str | None
    message: str | None


class PrepOrchestrator:
    def __init__(self, registry: PrepRegistry | None = None) -> None:
        self._registry = registry or _build_default_registry()

    def run_new_prep(
        self,
        pdf_path: Path,
        output_dir: Path | None = None,
        auto_proceed: bool = False,
        skip_callout_refinement: bool = False,
        log_output: bool = False,
    ) -> ExitCode:
        resolved_pdf_path = Path(pdf_path).resolve()
        if not _is_readable_pdf_path(resolved_pdf_path):
            return ExitCode.FILE_ERROR

        try:
            workspace_dir = create_output_directory(pdf_path=pdf_path, output_dir=output_dir)
        except PermissionError:
            return ExitCode.FILE_ERROR

        prep_paths = build_prep_paths(workspace_dir)
        analysis_paths = build_analysis_artifact_paths(
            workspace_dir,
            pdf_stem=resolved_pdf_path.stem,
        )
        ordered_phases = self._registry.get_ordered_phases()
        current_phase_key = ordered_phases[0].phase_key if ordered_phases else None
        step_keys = _get_current_step_keys(self._registry)

        prep_paths.root.mkdir(parents=True, exist_ok=True)
        prep_paths.log.parent.mkdir(parents=True, exist_ok=True)

        running_state = PrepRunState(
            status=PrepStatus.RUNNING,
            current_phase_key=current_phase_key,
            completed_steps=[],
        )
        save_prep_state(prep_paths.state, running_state)

        manifest = _build_manifest(
            _ManifestContext(
                prep_paths=prep_paths,
                pdf_path=resolved_pdf_path,
                workspace_dir=workspace_dir,
                step_keys=step_keys,
                phase_keys=[phase.phase_key for phase in ordered_phases],
                analysis_paths=analysis_paths,
            )
        )
        _write_json(prep_paths.manifest, manifest.to_dict())

        log_lines = [
            "Prep started",
            f"Source PDF: {resolved_pdf_path}",
            f"Workspace: {workspace_dir.resolve()}",
        ]
        completed_steps: list[str] = []

        try:
            completed_steps = self._execute_registry_steps(
                pdf_path=resolved_pdf_path,
                workspace_dir=workspace_dir,
                prep_paths=prep_paths,
                analysis_paths=analysis_paths,
                log_lines=log_lines,
                auto_proceed=auto_proceed,
                skip_callout_refinement=skip_callout_refinement,
                callout_refinement_mode=os.environ.get("GMKIT_CALL_OUT_REFINEMENT_MODE"),
                log_output=log_output,
            )
        except _PrepStepFailure as error:
            log_lines.append(f"ERROR: {sanitize_for_log(str(error))}")
            prep_paths.log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
            _write_json(
                prep_paths.manifest,
                _finalize_failure_manifest_payload(
                    manifest,
                    prep_paths=prep_paths,
                    analysis_paths=analysis_paths,
                    failure=_FailureManifestContext(
                        phase_key=error.current_phase_key,
                        step_key=error.current_step_key,
                        message=sanitize_for_log(str(error)),
                    ),
                ),
            )
            save_prep_state(
                prep_paths.state,
                PrepRunState(
                    status=PrepStatus.FAILED,
                    current_phase_key=error.current_phase_key,
                    completed_steps=error.completed_steps,
                ),
            )
            return get_exit_code_for_error(
                (
                    "ERROR",
                    sanitize_for_log(str(error)),
                    None,
                )
            )
        except Exception as error:
            log_lines.append(f"ERROR: {sanitize_for_log(str(error))}")
            prep_paths.log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
            _write_json(
                prep_paths.manifest,
                _finalize_failure_manifest_payload(
                    manifest,
                    prep_paths=prep_paths,
                    analysis_paths=analysis_paths,
                    failure=_FailureManifestContext(
                        phase_key=_get_completed_phase_key(
                            registry=self._registry,
                            completed_steps=completed_steps,
                        ),
                        step_key=None,
                        message=sanitize_for_log(str(error)),
                    ),
                ),
            )
            save_prep_state(
                prep_paths.state,
                PrepRunState(
                    status=PrepStatus.FAILED,
                    current_phase_key=_get_completed_phase_key(
                        registry=self._registry,
                        completed_steps=completed_steps,
                    ),
                    completed_steps=completed_steps,
                ),
            )
            return get_exit_code_for_error(
                (
                    "ERROR",
                    sanitize_for_log(str(error)),
                    None,
                )
            )
        except PrepRefinementPause as pause:
            log_lines.append(f"PAUSED: {sanitize_for_log(str(pause))}")
            prep_paths.log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
            save_prep_state(
                prep_paths.state,
                PrepRunState(
                    status=PrepStatus.RUNNING,
                    current_phase_key=_get_completed_phase_key(
                        registry=self._registry,
                        completed_steps=completed_steps,
                    ),
                    completed_steps=completed_steps,
                ),
            )
            _write_json(
                prep_paths.manifest,
                _finalize_manifest_payload(
                    manifest,
                    prep_paths=prep_paths,
                    analysis_paths=analysis_paths,
                ),
            )
            return ExitCode.SUCCESS

        log_lines.append("Prep completed")
        prep_paths.log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

        save_prep_state(
            prep_paths.state,
            PrepRunState(
                status=PrepStatus.COMPLETED,
                current_phase_key=None,
                completed_steps=completed_steps,
            ),
        )
        _write_json(
            prep_paths.complete,
            {
                "status": PrepStatus.COMPLETED.value,
                "manifest_path": str(prep_paths.manifest),
            },
        )
        _write_json(
            prep_paths.manifest,
            _finalize_manifest_payload(
                manifest,
                prep_paths=prep_paths,
                analysis_paths=analysis_paths,
            ),
        )
        return ExitCode.SUCCESS

    def show_status(self, workspace: Path) -> ExitCode:
        prep_paths = build_prep_paths(Path(workspace))
        if load_prep_state(prep_paths.state) is None:
            return ExitCode.STATE_ERROR
        return ExitCode.SUCCESS

    def resume_prep(
        self,
        workspace: Path,
        auto_proceed: bool = False,
        log_output: bool = False,
    ) -> ExitCode:
        del log_output
        prep_paths = build_prep_paths(Path(workspace))
        if load_prep_state(prep_paths.state) is None:
            return ExitCode.STATE_ERROR
        if prep_paths.complete.exists():
            return ExitCode.SUCCESS
        analysis_paths = build_analysis_artifact_paths(Path(workspace))
        if not analysis_paths.annotation_refinement_request.exists():
            return ExitCode.STATE_ERROR
        if not analysis_paths.annotation_refined_proposals.exists():
            return ExitCode.STATE_ERROR
        try:
            from gm_kit.pdf_convert.prep.handlers import (
                handle_finalize_reviewed_guidance,
                handle_render_annotated_prep_pdf,
                handle_seed_annotation_review,
            )

            handle_seed_annotation_review(analysis_paths=analysis_paths, auto_proceed=auto_proceed)
            manifest_payload = json.loads(prep_paths.manifest.read_text(encoding="utf-8"))
            manifest = PrepManifest.from_dict(manifest_payload)
            pdf_path = Path(manifest.pdf_path)
            handle_render_annotated_prep_pdf(
                pdf_path=pdf_path,
                analysis_paths=analysis_paths,
            )
            handle_finalize_reviewed_guidance(analysis_paths=analysis_paths)
        except Exception:
            return ExitCode.FILE_ERROR

        _write_json(
            prep_paths.manifest,
            _finalize_manifest_payload(
                manifest,
                prep_paths=prep_paths,
                analysis_paths=analysis_paths,
            ),
        )
        _write_json(
            prep_paths.complete,
            {
                "status": PrepStatus.COMPLETED.value,
                "manifest_path": str(prep_paths.manifest),
            },
        )
        save_prep_state(
            prep_paths.state,
            PrepRunState(
                status=PrepStatus.COMPLETED,
                current_phase_key=None,
                completed_steps=load_prep_state(prep_paths.state).completed_steps,
            ),
        )
        return ExitCode.SUCCESS

    def revise_prep_guidance(self, workspace: Path) -> ExitCode:
        prep_paths = build_prep_paths(Path(workspace))
        analysis_paths = build_analysis_artifact_paths(Path(workspace))

        required_paths = [
            analysis_paths.metadata,
            analysis_paths.annotation_proposals,
            analysis_paths.annotation_review_edits,
            analysis_paths.guidance_resolved,
        ]
        if any(not path.exists() for path in required_paths):
            return ExitCode.STATE_ERROR

        from gm_kit.pdf_convert.prep.handlers import handle_finalize_reviewed_guidance

        try:
            handle_finalize_reviewed_guidance(analysis_paths=analysis_paths)
        except Exception:
            return ExitCode.FILE_ERROR

        if prep_paths.manifest.exists():
            manifest_payload = json.loads(prep_paths.manifest.read_text(encoding="utf-8"))
            manifest = PrepManifest.from_dict(manifest_payload)
            _write_json(
                prep_paths.manifest,
                _finalize_manifest_payload(
                    manifest,
                    prep_paths=prep_paths,
                    analysis_paths=analysis_paths,
                ),
            )
        return ExitCode.SUCCESS

    def _execute_registry_steps(  # noqa: PLR0913
        self,
        *,
        pdf_path: Path,
        workspace_dir: Path,
        prep_paths: PrepPaths,
        analysis_paths: PrepAnalysisArtifactPaths,
        log_lines: list[str],
        auto_proceed: bool,
        skip_callout_refinement: bool,
        callout_refinement_mode: str | None,
        log_output: bool,
    ) -> list[str]:
        completed_steps: list[str] = []
        current_phase_key: str | None = None

        for phase in self._registry.get_ordered_phases():
            current_phase_key = phase.phase_key
            phase_message = _format_phase_started(phase)
            log_lines.append(phase_message)
            if log_output:
                print(phase_message)

            for step in self._registry.get_ordered_steps(phase.phase_key):
                handler = self._registry.get_handler(step.step_key)
                if handler is None:
                    step_message = _format_step_skipped(
                        self._registry,
                        phase.phase_key,
                        step.step_key,
                    )
                    log_lines.append(step_message)
                    if log_output:
                        print(step_message)
                    continue

                step_started_message = _format_step_started(
                    self._registry,
                    phase.phase_key,
                    step.step_key,
                )
                log_lines.append(step_started_message)
                if log_output:
                    print(step_started_message)
                try:
                    handler(
                        pdf_path=pdf_path,
                        workspace_dir=workspace_dir,
                        prep_paths=prep_paths,
                        analysis_paths=analysis_paths,
                        auto_proceed=auto_proceed,
                        skip_callout_refinement=skip_callout_refinement,
                        callout_refinement_mode=callout_refinement_mode,
                    )
                except Exception as error:
                    raise _PrepStepFailure(
                        f"{step.step_key} failed: {error}",
                        current_phase_key=current_phase_key,
                        current_step_key=step.step_key,
                        completed_steps=completed_steps.copy(),
                    ) from error
                completed_steps.append(step.step_key)
                save_prep_state(
                    prep_paths.state,
                    PrepRunState(
                        status=PrepStatus.RUNNING,
                        current_phase_key=current_phase_key,
                        completed_steps=completed_steps.copy(),
                    ),
                )
                step_completed_message = _format_step_completed(
                    self._registry,
                    phase.phase_key,
                    step.step_key,
                )
                log_lines.append(step_completed_message)
                if log_output:
                    print(step_completed_message)

        return completed_steps


def _build_default_registry() -> PrepRegistry:
    return PrepRegistry(
        phases=[
            PrepPhaseDefinition(
                phase_key=phase_key,
                order=(index + 1) * 100,
                display_name=_display_name_for_phase_key(phase_key),
            )
            for index, phase_key in enumerate(PREP_PHASE_KEYS)
        ],
        steps=[
            PrepStepDefinition(
                step_key="prep.analyze-document.extract-metadata",
                phase_key="prep.analyze-document",
                order=100,
                handler_ref=(
                    "gm_kit.pdf_convert.prep.handlers:"
                    "handle_extract_metadata_and_preflight"
                ),
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Extract PDF Metadata And Preflight",
            ),
            PrepStepDefinition(
                step_key="prep.extract-assets.extract-images",
                phase_key="prep.extract-assets",
                order=100,
                handler_ref="gm_kit.pdf_convert.prep.handlers:handle_extract_images",
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Extract Images",
            ),
            PrepStepDefinition(
                step_key="prep.extract-assets.create-no-images-pdf",
                phase_key="prep.extract-assets",
                order=200,
                handler_ref="gm_kit.pdf_convert.prep.handlers:handle_create_no_images_pdf",
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Create No-Images PDF",
            ),
            PrepStepDefinition(
                step_key="prep.derive-structure.acquire-canonical-toc",
                phase_key="prep.derive-structure",
                order=100,
                handler_ref="gm_kit.pdf_convert.prep.handlers:handle_extract_canonical_toc",
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Acquire Canonical TOC",
            ),
            PrepStepDefinition(
                step_key="prep.plan-chunks.build-chunk-plan",
                phase_key="prep.plan-chunks",
                order=100,
                handler_ref="gm_kit.pdf_convert.prep.handlers:handle_plan_chunks",
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Build Chunk Plan",
            ),
            PrepStepDefinition(
                step_key="prep.prepare-guidance.write-guidance-defaults",
                phase_key="prep.prepare-guidance",
                order=100,
                handler_ref="gm_kit.pdf_convert.prep.handlers:handle_write_guidance_defaults",
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Write Guidance Defaults For Convert Command",
            ),
            PrepStepDefinition(
                step_key="prep.propose-annotations.generate-annotation-proposals",
                phase_key="prep.propose-annotations",
                order=100,
                handler_ref=(
                    "gm_kit.pdf_convert.prep.handlers:"
                    "handle_generate_annotation_proposals"
                ),
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Create Annotation Candidates",
            ),
            PrepStepDefinition(
                step_key="prep.review-annotations.seed-review-artifacts",
                phase_key="prep.review-annotations",
                order=100,
                handler_ref=(
                    "gm_kit.pdf_convert.prep.handlers:"
                    "handle_seed_annotation_review"
                ),
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Seed Review Artifacts",
            ),
            PrepStepDefinition(
                step_key="prep.review-annotations.render-annotated-pdf",
                phase_key="prep.review-annotations",
                order=200,
                handler_ref=(
                    "gm_kit.pdf_convert.prep.handlers:"
                    "handle_render_annotated_prep_pdf"
                ),
                handler_policy=HandlerPolicy.REQUIRED,
                display_name="Render Reviewable Annotation PDF",
            ),
        ],
    )


def _build_artifacts(
    prep_paths: PrepPaths,
    analysis_paths: PrepAnalysisArtifactPaths | None = None,
) -> list[PrepArtifactEntry]:
    artifacts = [
        PrepArtifactEntry(name=prep_paths.manifest.name, status="ready"),
        PrepArtifactEntry(name=prep_paths.state.name, status="ready"),
        PrepArtifactEntry(name=prep_paths.complete.name, status="ready"),
        PrepArtifactEntry(
            name=prep_paths.log.relative_to(prep_paths.root).as_posix(),
            status="ready",
        ),
    ]
    if analysis_paths is None:
        return artifacts

    optional_paths = [
        analysis_paths.metadata,
        analysis_paths.preflight_report,
        analysis_paths.image_manifest,
        analysis_paths.no_images_pdf,
        analysis_paths.toc,
        analysis_paths.chapter_index,
        analysis_paths.chunk_plan,
        analysis_paths.guidance_defaults,
        analysis_paths.annotation_proposals,
        analysis_paths.annotation_refinement_hints,
        analysis_paths.annotation_refinement_request,
        analysis_paths.annotation_refinement_manifest,
        analysis_paths.annotation_table_refinement_request,
        analysis_paths.annotation_table_refinement_manifest,
        analysis_paths.annotation_refined_proposals,
        analysis_paths.annotation_review_edits,
        analysis_paths.guidance_resolved,
        analysis_paths.reviewed_guidance,
        analysis_paths.annotated_pdf,
    ]
    if analysis_paths.annotation_refinement_crops_dir.exists():
        for crop_path in sorted(analysis_paths.annotation_refinement_crops_dir.glob("*.png")):
            optional_paths.append(crop_path)
    for path in optional_paths:
        if path.exists():
            artifacts.append(
                PrepArtifactEntry(
                    name=path.relative_to(prep_paths.root).as_posix(),
                    status="ready",
                )
            )

    return artifacts


def _build_manifest(context: _ManifestContext) -> PrepManifest:
    return PrepManifest(
        contract_version=PREP_CONTRACT_VERSION,
        pdf_path=str(context.pdf_path),
        workspace_path=str(context.workspace_dir.resolve()),
        command_metadata=PrepCommandMetadata(
            command_name="analyze-and-prep-pdf",
            resume_requested=False,
        ),
        artifacts=_build_artifacts(context.prep_paths, context.analysis_paths),
        phase_keys=context.phase_keys,
        step_keys=context.step_keys,
        completed=False,
        failure_phase_key=context.failure_phase_key,
        failure_step_key=context.failure_step_key,
        failure_message=context.failure_message,
    )


def _get_current_step_keys(registry: PrepRegistry) -> list[str]:
    return [
        step.step_key
        for phase in registry.get_ordered_phases()
        for step in registry.get_ordered_steps(phase.phase_key)
    ]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _display_name_for_phase_key(phase_key: str) -> str:
    display_name = phase_key.removeprefix("prep.").replace("-", " ").title()
    if phase_key == "prep.analyze-document":
        return "Analyze PDF Document"
    if phase_key == "prep.prepare-guidance":
        return "Prepare Guidance For Convert Command"
    if phase_key == "prep.propose-annotations":
        return "Create Annotation Candidates"
    if phase_key == "prep.review-annotations":
        return "Prepare Review Artifacts"
    if phase_key == "prep.finalize-prep-artifacts":
        return "Finalize Review Artifacts"
    return display_name


def _finalize_manifest_payload(
    manifest: PrepManifest,
    *,
    prep_paths: PrepPaths,
    analysis_paths: PrepAnalysisArtifactPaths | None = None,
) -> dict[str, object]:
    payload = manifest.to_dict()
    payload["artifacts"] = [
        {"name": artifact.name, "status": artifact.status}
        for artifact in _build_artifacts(prep_paths, analysis_paths)
    ]
    payload["completed"] = True
    payload["failure_phase_key"] = None
    payload["failure_step_key"] = None
    payload["failure_message"] = None
    return payload


def _finalize_failure_manifest_payload(
    manifest: PrepManifest,
    *,
    prep_paths: PrepPaths,
    analysis_paths: PrepAnalysisArtifactPaths | None = None,
    failure: _FailureManifestContext,
) -> dict[str, object]:
    payload = manifest.to_dict()
    payload["artifacts"] = [
        {"name": artifact.name, "status": artifact.status}
        for artifact in _build_artifacts(prep_paths, analysis_paths)
    ]
    payload["completed"] = False
    payload["failure_phase_key"] = failure.phase_key
    payload["failure_step_key"] = failure.step_key
    payload["failure_message"] = failure.message
    return payload


def _format_phase_started(phase: PrepPhaseDefinition) -> str:
    return f"Phase {phase.order}: {phase.display_name} ({phase.phase_key}) started"


def _format_step_started(
    registry: PrepRegistry,
    phase_key: str,
    step_key: str,
) -> str:
    step = _get_registry_step(registry, phase_key, step_key)
    mapping = registry.get_display_mapping(step)
    return f"Step {mapping.step_alias}: {step.display_name} ({step.step_key}) started"


def _format_step_completed(
    registry: PrepRegistry,
    phase_key: str,
    step_key: str,
) -> str:
    step = _get_registry_step(registry, phase_key, step_key)
    mapping = registry.get_display_mapping(step)
    return f"Step {mapping.step_alias}: {step.display_name} ({step.step_key}) completed"


def _format_step_skipped(
    registry: PrepRegistry,
    phase_key: str,
    step_key: str,
) -> str:
    step = _get_registry_step(registry, phase_key, step_key)
    mapping = registry.get_display_mapping(step)
    return f"Step {mapping.step_alias}: {step.display_name} ({step.step_key}) skipped"


def _get_completed_phase_key(
    *,
    registry: PrepRegistry,
    completed_steps: list[str],
) -> str | None:
    if not completed_steps:
        ordered_phases = registry.get_ordered_phases()
        return ordered_phases[0].phase_key if ordered_phases else None

    completed_step_key = completed_steps[-1]
    for phase in registry.get_ordered_phases():
        for step in registry.get_ordered_steps(phase.phase_key):
            if step.step_key == completed_step_key:
                return phase.phase_key
    return None


def _get_registry_step(registry: PrepRegistry, phase_key: str, step_key: str) -> PrepStepDefinition:
    for step in registry.get_ordered_steps(phase_key):
        if step.step_key == step_key:
            return step
    raise KeyError(f"Unknown registry step: {step_key}")


def _is_readable_pdf_path(pdf_path: Path) -> bool:
    if not pdf_path.is_file():
        return False

    try:
        with pdf_path.open("rb"):
            return True
    except OSError:
        return False
