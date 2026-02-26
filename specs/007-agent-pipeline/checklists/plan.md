# Plan Quality Checklist: PDF->Markdown Agent-Driven Pipeline

**Purpose**: Validate implementation plan completeness and consistency against the current spec before generating tasks.
**Created**: 2026-02-25
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md)

**Note**: This checklist validates the quality of the planning document (not implementation behavior).

## Plan-Spec Consistency

- [x] CHK001 Does the plan consistently use the 13-step scope and exclude step 9.1 from agent implementation? [Consistency, Spec §FR-011, Plan §Summary/Implementation Order]
- [x] CHK002 Do the step groupings in the plan match the spec's step groupings (Content Repair, Table Processing, Quality Assessment, Reporting)? [Consistency, Spec §Step Groupings, Plan §Summary]
- [x] CHK003 Do plan references to E4-07a stub replacement align with the spec's integration requirements (FR-005, SC-004)? [Consistency, Spec §FR-005/SC-004, Plan §Project Structure/Implementation Approach]

## Execution Model Clarity

- [x] CHK004 Does the plan clearly define the agent-orchestrated file handoff (write inputs/instructions, CLI exit, agent writes output, resume)? [Clarity, Plan §Step Execution Flow]
- [x] CHK005 Are workspace artifacts and file names consistent across the plan (`step-input.json`, `step-instructions.md`, `step-output.json`)? [Consistency, Plan §Project Structure, §Step Execution Flow]
- [x] CHK006 Does the plan clearly distinguish Python responsibilities (I/O, validation, orchestration) from agent responsibilities (LLM processing/output writing)? [Clarity, Plan §Summary, §Step Execution Flow]
- [x] CHK007 Is restart resilience behavior documented well enough to implement resume safely? [Completeness, Plan §Step Execution Flow]

## FR Coverage in Plan

- [x] CHK008 Does the plan specify how FR-012 (step 3.2 indented TOC output compatibility) is enforced in prompt/schema/rubric design? [Coverage, Spec §FR-012, Plan §Implementation Order/§Rubric Dimensions]
- [x] CHK009 Does the plan address FR-013 (OCR cleanup scope + conservative corrections) in step 6.4 design notes? [Coverage, Spec §FR-013, Plan §Implementation Order]
- [x] CHK010 Does the plan address FR-014 (two-pass multimodal table detection/conversion) with on-demand rendering and image reuse? [Coverage, Spec §FR-014, Plan §Implementation Order/§Dependency Notes]
- [x] CHK011 Does the plan address FR-015 token preflight with threshold, skip/proceed behavior, and affected steps? [Coverage, Spec §FR-015, Plan §Implementation Order/§Dependency Notes]
- [x] CHK012 Does the plan address FR-016 by passing `font-family-mapping.json` into step 9.7 and requiring skepticism for font-inferred headings? [Coverage, Spec §FR-016, Plan §Implementation Order/§Rubric Dimensions]

## Test Strategy Quality

- [x] CHK013 Are unit, contract, and integration test layers clearly separated with responsibilities that match AGENTS test boundary rules? [Consistency, AGENTS.md §4.6, Plan §Test Strategy]
- [x] CHK014 Are multimodal table steps (7.7/8.7) test strategies specific enough for fixture/golden coverage and image artifacts? [Completeness, Plan §Test Strategy]
- [x] CHK015 Are token-preflight branches (interactive skip / `--yes` auto-proceed) explicitly covered in unit tests? [Coverage, Spec §FR-015, Plan §Test Strategy]
- [x] CHK016 Are integration tests framed around the agent-orchestrated workflow and `GM_AGENT` selection, not Python SDK mocks? [Consistency, Plan §Test Strategy]

## Dependency and Environment Specification

- [x] CHK017 Are the stated dependencies in the plan aligned with the design (PyMuPDF, jsonschema, Pillow) and free of stale provider-SDK requirements? [Consistency, Plan §Technical Context]
- [x] CHK018 Are supported agents and CI-tested agents clearly distinguished? [Clarity, Plan §Summary, §Technical Context, §Key Design Decisions]
- [x] CHK019 Are configurable runtime knobs documented where relevant (`GM_AGENT`, `GM_TOKEN_THRESHOLD`, `GM_PAGE_IMAGE_DPI`)? [Completeness, Plan §Test Strategy, §Key Design Decisions, §Dependency Notes]

## Project Structure and Data Flow

- [x] CHK020 Does the planned source tree align with the data model and spec (agents package, instructions, schemas, tests/fixtures layout)? [Consistency, Plan §Project Structure, data-model.md]
- [x] CHK021 Are markdown-modifying steps (4.5, 6.4, 8.7) explicitly documented as in-place file edits with metadata-only `step-output.json`? [Clarity, Plan §Step Execution Flow, §Key Design Decisions]
- [x] CHK022 Is the dropped 9.1 step handled consistently in phase9 references (stub remains as no-op, not part of E4-07b implementation)? [Consistency, Spec §FR-011, Plan §Project Structure/§Rubric Dimensions]

## Task Readiness

- [x] CHK023 Is the implementation order detailed enough to derive tasks without inventing missing design decisions? [Readiness, Plan §Implementation Order]
- [x] CHK024 Are major risks/tradeoffs recorded (vision dependency, large-doc QA limits, retry/escalation behavior) so tasks can include coverage for them? [Readiness, Plan §Key Design Decisions/§Dependency Notes]

## Notes

- Check items off as completed: `[x]`
- Add inline findings when an item reveals a gap
- Regenerate this checklist if the plan changes materially (execution model, step list, project structure, or test strategy)
