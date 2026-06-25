# Implementation Plan: E7-01 Key-Based Prep Registry Foundation

**Branch**: `010-key-based-prep-registry` | **Date**: 2026-04-03 | **Spec**: `/home/todd/Dev/gm-kit/specs/e7-01-key-based-prep-registry/spec.md`
**Input**: Feature specification from `/home/todd/Dev/gm-kit/specs/e7-01-key-based-prep-registry/spec.md`

## Summary

Implement a key-based prep registry foundation for `gmkit analyze-and-prep-pdf` orchestration that replaces numeric-coupled identity with stable `phase_key`/`step_key` identities. The implementation introduces deterministic two-level ordering (`phase.order`, `step.order`), strict startup validation for required handlers, optional-handler disable semantics, composite display numbering for logs, and sanitized diagnostics.

## Technical Context

**Language/Version**: Python 3.13.7  
**Primary Dependencies**: standard library (`dataclasses`, `typing`, `importlib`), existing gm-kit modules under `src/gm_kit/pdf_convert/`  
**Storage**: files (`.state.json` and local conversion workspace artifacts), no new database for E7-01  
**Testing**: pytest (unit-first), plus existing lint/typecheck/test pipeline via just/uv  
**Target Platform**: Local CLI on Linux/macOS/Windows environments supported by gmkit  
**Project Type**: Python CLI/library internal architecture refactor  
**Performance Goals**: Registry startup validation remains deterministic and fast (target: sub-second startup overhead for typical prep registry sizes)  
**Constraints**: Key identity is authoritative; numeric IDs are display-only; offline/local-first behavior; no backward compatibility requirement for pre-E4-08a artifacts  
**Scale/Scope**: E7-01 foundation only (registry model, ordering, validation, logging metadata), no full prep command implementation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Status: CONDITIONAL PASS

- `.specify/memory/constitution.md` currently contains template placeholders and does not define enforceable project-specific gates.
- For this feature, governance is taken from repository standards in `AGENTS.md` and existing project quality/security constraints.
- No direct violations identified against active repository conventions:
  - Python CLI conventions maintained
  - tests required for new behavior
  - lint/typecheck/test/security workflow preserved

Post-design re-check: PASS (no new conflicts introduced by Phase 0/1 artifacts).

## Project Structure

### Documentation (this feature)

```text
specs/e7-01-key-based-prep-registry/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── prep-registry-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
└── gm_kit/
    ├── cli.py
    ├── pdf_convert/
    │   ├── orchestrator.py
    │   ├── state.py
    │   ├── phases/
    │   │   ├── base.py
    │   │   ├── phase0.py
    │   │   ├── phase4.py
    │   │   ├── phase6.py
    │   │   └── phase8.py
    │   └── agents/
    └── init/

tests/
├── unit/
│   └── pdf_convert/
├── integration/
└── fixtures/
```

**Structure Decision**: Single-project Python CLI structure (existing repo layout). E7-01 implementation work will be concentrated under `src/gm_kit/pdf_convert/` with unit tests under `tests/unit/pdf_convert/`.

## Complexity Tracking

No constitution violations requiring complexity exceptions are currently identified.
