# Implementation Plan: GM-Kit README & Structure Audit

**Branch**: `001-readme-audit` | **Date**: 2025-11-24 | **Spec**: [specs/001-readme-audit/spec.md](../spec.md)  
**Input**: Feature specification from `/specs/001-readme-audit/spec.md`

## Summary

Update README to describe the Arcane Library mission and feature workflow, ensure `.gitignore` excludes `spec-kit/` and `temp-resources/`, and document a manual structure audit (snapshot + checklist) so maintainers can prove the repo is Python-ready before opening PRs.

## Technical Context

**Language/Version**: Python 3.11 (per project standard)  
**Primary Dependencies**: None beyond git + Markdown editing  
**Storage**: N/A (documentation + repo metadata)  
**Testing**: Manual verification via README audit steps  
**Target Platform**: Cross-platform dev environments (macOS/Linux/Windows shells)  
**Project Type**: CLI + documentation repo driven by Spec-Kit  
**Performance Goals**: Contributors should navigate README instructions and run audits in under 5 minutes  
**Constraints**: Solutions must remain tool-agnostic; use shell commands available by default (ls/tree)  
**Scale/Scope**: Single README, `.gitignore`, and supporting planning artifacts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`constitution.md` is currently a placeholder with no defined principles, so no gates can be evaluated. Proceeding under the assumption that documentation-only changes comply; once the constitution is authored, rerun this gate to ensure simplicity/workflow requirements are met.

## Project Structure

### Documentation (this feature)

```text
specs/001-readme-audit/
├── plan.md          # This file
├── research.md      # Phase 0 output
├── data-model.md    # Phase 1 output
├── quickstart.md    # Phase 1 output
├── contracts/       # Phase 1 output (textual contracts/checklists)
└── tasks.md         # Created during /speckit.tasks (phase 2)
```

### Source Code (repository root)

```text
./
├── planning/              # Project overview, prompts, journals
├── specs/                 # Feature specs/plans (grows with each feature)
├── src/                   # GM-Kit Python sources
├── README.md              # Updated in this feature
├── .gitignore             # Updated in this feature
├── pyproject.toml
├── uv.lock
├── .python-version
├── setup_dev.sh
├── startcode.sh
├── temp-resources/        # Ignored scratch directory
├── spec-kit/              # Ignored upstream checkout
└── .specify/              # Spec-Kit automation scripts/templates
```

**Structure Decision**: Single Python CLI project with planning + specs directories; this feature only adjusts documentation/ignore files and adds planning artifacts under `specs/001-readme-audit/`.

## Complexity Tracking

No violations recorded (pending real constitution content).

## Post-Design Constitution Check

- Constitution still unpopulated; no gates to re-evaluate. Flag for maintainers to populate `constitution.md` so future plans can enforce simplicity, workflow, and testing gates explicitly.
