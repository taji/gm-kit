# Implementation Plan: PDF to Markdown Command Orchestration

**Branch**: `005-pdf-convert-orchestration` | **Date**: 2026-01-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-pdf-convert-orchestration/spec.md`

## Summary

Implement the `/gmkit.pdf-to-markdown` slash command and `gmkit pdf-convert` CLI that orchestrates the PDF conversion pipeline. The CLI provides pre-flight analysis (Phase 0 steps 0.1-0.5), state tracking for resumability, and orchestration of phases 1-10 (initially with mocks for E4-07a/b/c/d components). The slash command prompt file invokes the CLI, making the conversion available through supported AI coding agents.

## Technical Context

**Language/Version**: Python 3.8+ (per constitution)
**Primary Dependencies**: typer (CLI), rich (terminal output), PyMuPDF/fitz (PDF operations), pexpect (interactive testing)
**Storage**: JSON files (`.state.json`, `metadata.json`) in conversion output directory
**Testing**: pytest with pexpect for interactive CLI testing, mocks for E4-07a/b/c/d components
**Target Platform**: macOS/Linux (bash), Windows (PowerShell)
**Project Type**: Single project - extends existing gmkit CLI
**Performance Goals**: Pre-flight analysis completes in <10 seconds for PDFs under 50 pages
**Constraints**: No network access required after installation; all operations local
**Scale/Scope**: Single-user CLI tool; handles PDFs up to ~500 pages (with chunking)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Library-First | PASS | `pdf_convert` module is self-contained library with CLI exposure |
| II. CLI Interface | PASS | `gmkit pdf-convert` command with text I/O, JSON state files |
| III. Test-First | PASS | TDD approach with unit tests (mocked), integration tests (pexpect) |
| IV. Integration Testing | PASS | Contract tests for E4-07a/b/c/d interfaces, pexpect for user flows |
| V. Observability/Simplicity | PASS | State file provides debuggability; YAGNI - mocks now, real later |
| VI. AI Agent Integration | PASS | Prompt file for supported agents (claude, codex-cli, gemini, qwen) |
| VII. Interactive CLI Testing | PASS | pexpect for pre-flight confirmation and user prompts |
| VIII. Cross-Platform | PASS | Bash and PowerShell script templates |

**Gate Result**: PASS - No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/005-pdf-convert-orchestration/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── state-schema.json
│   ├── metadata-schema.json
│   └── phase-interface.md
├── checklists/
│   └── requirements.md  # Spec validation checklist
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/gmkit_cli/
├── __init__.py
├── cli.py                    # Existing CLI entry point
├── commands/
│   ├── __init__.py
│   ├── init.py               # Existing init command
│   └── pdf_convert.py        # NEW: pdf-convert subcommand
├── pdf_convert/              # NEW: PDF conversion library
│   ├── __init__.py
│   ├── orchestrator.py       # Pipeline orchestration
│   ├── preflight.py          # Phase 0 analysis (steps 0.1-0.5)
│   ├── state.py              # State tracking (.state.json)
│   ├── metadata.py           # PDF metadata extraction
│   └── phases/               # Phase stubs (mocked for now)
│       ├── __init__.py
│       ├── base.py           # Phase interface
│       └── stubs.py          # Mock implementations
└── templates/
    └── prompts/
        └── gmkit.pdf-to-markdown.md  # NEW: Slash command prompt

tests/
├── unit/
│   └── pdf_convert/
│       ├── test_orchestrator.py
│       ├── test_preflight.py
│       ├── test_state.py
│       └── test_metadata.py
├── integration/
│   └── pdf_convert/
│       ├── test_cli_full_pipeline.py  # pexpect tests
│       └── test_resume_workflow.py
└── contract/
    └── pdf_convert/
        ├── test_phase_interface.py
        └── test_state_schema.py

.gmkit/scripts/
├── bash/
│   └── pdf-convert-setup.sh    # NEW: Folder structure setup
└── ps/
    └── pdf-convert-setup.ps1   # NEW: PowerShell equivalent
```

**Structure Decision**: Extends existing single-project structure. New `pdf_convert/` subpackage follows library-first principle - self-contained with CLI exposure via `commands/pdf_convert.py`.

## Complexity Tracking

> No violations requiring justification - all gates pass.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
