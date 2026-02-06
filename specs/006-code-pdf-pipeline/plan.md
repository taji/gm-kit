# Implementation Plan: PDF Code Pipeline

**Branch**: `006-code-pdf-pipeline` | **Date**: 2026-02-06 | **Spec**: /home/todd/Dev/gm-kit/specs/006-code-pdf-pipeline/spec.md
**Input**: Feature specification from `/specs/006-code-pdf-pipeline/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement the code-driven PDF→Markdown pipeline, replacing mock phases with real implementations. Phases 0–8 execute all Code-category steps with Phase 8 markdown as the primary deliverable. Phases 9–10 implement only their Code-category steps; Agent/User steps remain stubbed until E4-07b/c. Heading inference must use full font signatures (family + size + weight + style), with tests covering same-family/different-style headings.

## Technical Context

**Language/Version**: Python 3.13.7
**Primary Dependencies**: typer, rich, PyMuPDF (fitz), pymarkdownlnt
**Storage**: Files on local workspace (.state.json, per-phase artifacts, manifests)
**Testing**: pytest (unit + integration)
**Target Platform**: Cross-platform CLI (Linux/macOS/Windows)
**Project Type**: single
**Performance Goals**: Code-step phases (1-8): ~0.5s/page target; pre-flight ~0.2s/page (inherited from E4-07e)
**Constraints**: Local-only execution; no network required; deterministic outputs for code steps
**Scale/Scope**: Single-user CLI workflow per conversion

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Library-First**: PASS — code lives in `src/gm_kit/pdf_convert` as testable modules.
- **CLI Interface**: PASS — `gmkit pdf-convert` already exposes the pipeline.
- **Test-First**: PASS — plan includes unit + integration coverage per phase.
- **Integration Testing**: PASS — phase transitions and CLI flows covered in integration tests.
- **Observability/Versioning/Simplicity**: PASS — structured phase outputs and diagnostics, no new complexity.
- **AI Agent Integration**: PASS — agent steps are integration points only; prompts live in templates.
- **Interactive CLI Testing**: PASS — not applicable here (gmkit init only).
- **Cross-Platform Installation**: PASS — no install changes required.

## Project Structure

### Documentation (this feature)

```text
specs/006-code-pdf-pipeline/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
src/
└── gm_kit/
    └── pdf_convert/
        ├── orchestrator.py
        ├── preflight.py
        ├── metadata.py
        ├── state.py
        ├── constants.py
        └── phases/
            ├── base.py
            ├── stubs.py
            └── ... (real phase modules added here)

tests/
├── unit/
│   └── pdf_convert/
└── integration/
    └── pdf_convert/
```

**Structure Decision**: Single-project CLI; all pipeline code remains under `src/gm_kit/pdf_convert`, with tests under `tests/unit/pdf_convert` and `tests/integration/pdf_convert`.

## Complexity Tracking

No constitution violations requiring justification.
