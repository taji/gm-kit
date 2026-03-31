# Implementation Plan: PDF→Markdown Agent-Driven Pipeline

**Branch**: `007-agent-pipeline` | **Date**: 2026-02-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-agent-pipeline/spec.md`
**Architecture Sync**: Synced to `ARCHITECTURE.md` on 2026-03-31

## Summary

Implement the 13 Agent-category steps from the PDF conversion architecture (v11) using an agent-orchestrated model (confirmed viable by E2-09 audit). The running agent controls pipeline flow: Code steps run as `gmkit pdf-convert` CLI invocations; Agent steps are performed by the agent itself by reading workspace input files and writing workspace output files. Python code handles workspace I/O, contract validation, and CLI orchestration — no Python SDK calls for LLM inference. Supported agents: Claude Code, Codex CLI, OpenCode, Gemini CLI, Qwen (CI/CD automated testing covers Claude Code, Codex CLI, and OpenCode only — confirmed viable by E2-09; Gemini and Qwen are supported but not CI-tested). Steps are grouped into Content Repair (3.2, 4.5, 6.4), Table Processing (7.7, 8.7), Quality Assessment (9.2-9.5, 9.7-9.8), and Reporting (10.2-10.3).

## Technical Context

- **Language/Version**: Python 3.8+ (constitution mandate), running on 3.13.7
- **Primary Dependencies**: typer, rich, PyMuPDF/fitz, jsonschema (contract validation), Pillow (image cropping for table region extraction in steps 7.7/8.7)
- **Agent Integration**: Agent-orchestrated execution (E2-09 confirmed viable); running agent performs agent steps by reading workspace input files and writing workspace output files; no Python SDK calls for LLM inference; supported agents: Claude Code (`--print --dangerously-skip-permissions`), Codex CLI (`exec --full-auto -s workspace-write`), OpenCode (`run`), Gemini CLI, Qwen; CI/CD automated testing covers Claude Code, Codex CLI, and OpenCode only (E2-09 confirmed); Gemini and Qwen supported but not CI-tested
- **Storage**: Local files in conversion workspace (JSON contracts, markdown artifacts, prompt templates as Python modules)
- **Testing**: pytest (unit in tests/unit/, integration in tests/integration/, contract in tests/contract/)
- **Target Platform**: Linux/cross-platform CLI
- **Performance Goals**: N/A — LLM-bound, not latency-sensitive; focus on correctness and reproducibility
- **Constraints**: SC-003 requires consistent/reproducible rubric evaluations (temperature=0, structured output)
- **Scale/Scope**: 13 agent steps × 3 corpus PDFs = 39 step executions for validation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Library-First | PASS | Agent steps are a self-contained library under `src/gm_kit/pdf_convert/agents/` |
| II. CLI Interface | PASS | Integrates with existing `pdf-convert` CLI; agent steps are internal to pipeline |
| III. Test-First (NON-NEGOTIABLE) | PASS | TDD: contracts → unit tests → rubric tests → integration tests |
| IV. Integration Testing | PASS | Contract tests per step, end-to-end pipeline tests on reference corpus |
| V. Observability & Simplicity | PASS | Structured JSON errors (FR-008), evaluation results logged; YAGNI approach |
| VI. AI Agent Integration | PASS | Agent-orchestrated model (E2-09 confirmed); the running agent IS the provider — no separate SDK/API calls; file-based handoff (input/instruction files in, output file out) is the interface between Code steps and Agent steps; supported agents documented in E2-09 findings |
| VII. Interactive CLI Testing | N/A | No interactive prompts in agent steps |
| VIII. Cross-Platform Installation | N/A | No new installation requirements |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/007-agent-pipeline/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research decisions
├── data-model.md        # Phase 1 entity definitions
├── quickstart.md        # Phase 1 validation quickstart
├── contracts/           # Phase 1 contract overview
│   └── agent-steps.md   # Contract summary + per-step schema references
├── checklists/
│   └── requirements.md  # Spec quality checklist (see file for current item count/status)
└── feature_journal.md
```

### Source Code (repository root)

```text
src/gm_kit/pdf_convert/
├── agents/                        # NEW: Agent step library
│   ├── __init__.py                # Public API: write_agent_inputs(), read_agent_output(), AgentStepError
│   ├── base.py                    # AgentStep abstract base, shared types
│   ├── contracts.py               # Contract loader + validator (jsonschema)
│   ├── errors.py                  # AgentStepError, ContractViolation
│   ├── agent_step.py               # Agent step I/O: write input/instruction files, read output files
│   ├── instructions/              # Instruction templates written to workspace per step
│   │   ├── step_3_2.md            # Visual TOC parsing — markdown template, {variable} slots
│   │   ├── step_4_5.md            # Sentence boundary resolution
│   │   ├── step_6_4.md            # OCR spelling correction
│   │   ├── step_7_7.py            # Table detection — Python only (two-pass: text_scan + vision)
│   │   ├── step_8_7.md            # Table-to-markdown conversion
│   │   ├── step_9_2.md            # Structural clarity
│   │   ├── step_9_3.md            # Text flow / readability
│   │   ├── step_9_4.md            # Table integrity
│   │   ├── step_9_5.md            # Callout formatting
│   │   ├── step_9_7.md            # TOC validation review
│   │   ├── step_9_8.md            # Two-column reading order
│   │   ├── step_10_2.md           # Quality ratings
│   │   └── step_10_3.md           # Remaining issues
│   └── schemas/                   # JSON Schema files per step
│       ├── step_3_2.schema.json
│       ├── step_4_5.schema.json
│       └── ...                    # 13 total
├── phases/                        # EXISTING: E4-07a phases (stubs get replaced)
│   ├── base.py                    # Phase, PhaseResult, StepResult (unchanged)
│   ├── phase3.py                  # Step 3.2 stub → calls agents.run_agent_step("3.2", ...)
│   ├── phase4.py                  # Step 4.5 stub → agents call
│   ├── phase6.py                  # Step 6.4 stub → agents call
│   ├── phase7.py                  # Step 7.7 stub → agents call
│   ├── phase8.py                  # Step 8.7 stub → agents call
│   ├── phase9.py                  # Steps 9.2-9.5, 9.7-9.8 stubs → agents calls (9.1 stub remains as no-op)
│   └── phase10.py                 # Steps 10.2-10.3 stubs → agents calls
└── ...                            # Existing files unchanged

tests/
├── unit/pdf_convert/agents/       # NEW: Unit tests for agent library
│   ├── test_base.py               # AgentStep base class tests
│   ├── test_contracts.py          # Contract validation tests
│   ├── test_agent_step.py          # Workspace I/O tests (write inputs, read output)
│   ├── test_instructions.py       # Instruction file generation tests
│   └── test_errors.py             # Error type tests
├── contract/pdf_convert/agents/   # NEW: Contract tests per step
│   ├── test_step_3_2.py           # Contract test for step 3.2
│   └── ...                        # 13 total
├── integration/pdf_convert/agents/# NEW: Integration tests
│   └── test_agent_pipeline.py     # End-to-end pipeline with agent steps
└── fixtures/pdf_convert/
    ├── agents/                    # NEW: Test artifacts per step
    │   ├── inputs/                # Step input fixtures
    │   │   ├── step_3_2/          # Per-step input samples from corpus
    │   │   └── ...
    │   └── golden/                # Golden output files per step
    │       ├── step_3_2/
    │       └── ...
    ├── The Homebrewery - NaturalCrit.pdf
    ├── The Homebrewery - NaturalCrit - Without TOC.pdf
    └── download_cofc_fixture.sh   # CofC fixture (needs download)

{workspace}/                       # RUNTIME: conversion workspace (per-run)
└── page_images/                   # ON-DEMAND: rendered by step 7.7, reused by step 8.7
    ├── page_001.png               # Named page_{n:03d}.png; 150 DPI PNG via PyMuPDF
    └── ...                        # Cleanup policy: deleted after pipeline completes
```

**Structure Decision**: Single project layout following existing `src/gm_kit/pdf_convert/` convention. The new `agents/` subpackage is a library-first module (Constitution I) that the existing phase files consume.

## Implementation Approach

### Step Execution Flow

Each agent step uses a file-based handoff between Code steps and Agent steps:

```
Phase.execute() → agents.write_agent_inputs(step_id, inputs, workspace)
  1. Load instruction template (instructions/step_X_Y.md or step_7_7.py)
  2. Substitute variables into template
  3. Append standard "after completing this step" footer to instructions:
       "Write your output to step-output.json in this directory, then
        resume the pipeline by running:
          gmkit pdf-convert --resume {workspace_path}"
  4. Write step-input.json + step-instructions.md to {workspace}/agent_steps/step_X_Y/
  5. Update state.json: current_step = "X.Y", status = AWAITING_AGENT
  6. CLI exits — control passes to the running agent

[Agent performs the step]:
  A. Agent reads {workspace}/agent_steps/step_X_Y/step-input.json
  B. Agent reads {workspace}/agent_steps/step_X_Y/step-instructions.md
  C. Agent processes and writes step-output.json to the same directory
     Note — steps 4.5, 6.4, 8.7 (markdown-modifying steps):
       Agent edits the phase file directly (path provided in step-input.json);
       step-output.json contains metadata only (status, changes_made, notes)
     Note — step 7.7 two-pass:
       i.  Agent reads extracted text → identifies likely table pages
       ii. PyMuPDF renders flagged pages on-demand as images (Code utility)
       iii.Agent reads page images → returns bounding boxes per table
  D. Agent calls: gmkit pdf-convert --resume {workspace_path}

[Pipeline resumes via --resume]:
  7. CLI reads state.json → finds current_step = "X.Y", status = AWAITING_AGENT
  8. agents.read_agent_output(step_id, workspace) reads step-output.json
  9. Validate output against contract (schemas/step_X_Y.schema.json)
  10. If invalid → re-write error + retry instructions to workspace; CLI exits;
      agent re-runs (up to 3x retry budget)
  11. If valid → update state.json; pipeline continues to next Code phase
  12. After max retries → criticality-based escalation

Note — restart resilience: if the agent is interrupted and restarted, it calls
  gmkit pdf-convert --resume {workspace_path}; the CLI re-writes the workspace
  files for the current step (state.json is authoritative for position) and the
  agent proceeds from there.
```

### Implementation Order

Work is organized in dependency order:

1. **Foundation** (agents base, workspace I/O, contracts, errors, token_preflight utility)
   - `agent_step.py`: write_agent_inputs() reads markdown template, substitutes variables, appends standard resume-instruction footer, writes step-input.json + step-instructions.md to workspace; read_agent_output() reads step-output.json; handles retry instruction writes
   - `token_preflight.py`: shared utility for FR-015; estimates token count (~4 chars/token), warns user if markdown exceeds ~100k tokens (~80-120 two-column pages); warning message explicitly calls out that heading hierarchy and TOC alignment quality may degrade for large documents as quality assessment steps receive the full document; interactive skip or `--yes` auto-proceed
2. **Content Repair steps** (3.2, 4.5, 6.4) — simplest, fewest dependencies
   - Step 3.2: prompt enforces indented-text output format per FR-012 (not pipe-delimited); contract schema validates indent structure
   - Step 6.4: prompt addresses both OCR scenarios per FR-013: (a) pre-baked text layer artifacts; (b) agent-driven OCR path with resume-from-phase guidance
3. **Table Processing steps** (7.7, 8.7) — most complex, multimodal
   - Step 7.7: `step_7_7.py` has two `build_prompt()` functions — `build_text_scan_prompt()` and `build_vision_prompt()`; page images saved to `{workspace}/page_images/page_{n}.png` on-demand; reused by step 8.7
   - Step 8.7: loads saved images from `{workspace}/page_images/`; crops bounding-box region with PIL/Pillow; does NOT re-render
4. **Quality Assessment steps** (9.2-9.5, 9.7-9.8) — share common rubric pattern
   - Step 9.7: receives `font-family-mapping.json` from workspace (written by Phase 7) alongside markdown input; prompt instructs skepticism for font-inferred headings per FR-016
   - All Quality Assessment + Reporting steps (9.2-9.5, 9.7-9.8, 10.2-10.3): call `token_preflight` before sending the full markdown to the LLM. Content Repair (3.2, 4.5, 6.4) and Table Processing (7.7, 8.7) steps operate on targeted excerpts only — no preflight needed.
   - Skipped steps return `StepStatus.SKIPPED` (not scored; not a rubric failure; pipeline continues to next step)
5. **Reporting steps** (10.2-10.3) — aggregate from quality assessments
6. **Integration wiring** — replace stubs in phase files, end-to-end testing

### Rubric Dimensions Per Step

Each step has tailored rubric dimensions scored 1-5 by LLM evaluator:

| Step | Dimensions | Critical Failures |
|------|-----------|-------------------|
| 3.2 | Completeness, Level accuracy, Page accuracy, Output format (indented text, not pipe-delimited per FR-012) | Missing sections present in PDF |
| 4.5 | Correct joins, No false joins, Readability | Sentences merged across unrelated paragraphs |
| 6.4 | Correction accuracy, False positive rate, Domain term preservation | Corrupting TTRPG terms |
| 7.7 | Detection recall, Detection precision, Boundary accuracy | Missing a table entirely |
| 8.7 | Row/column fidelity, Markdown validity, Content preservation | Truncated/lost cell data |
| ~~9.1~~ | ~~Dropped~~ — Phase 4 guarantees all page markers; code-level check sufficient | N/A |
| 9.2 | Heading hierarchy, Section coherence, Nesting correctness | Malformed assessment JSON |
| 9.3 | Reading order, Paragraph integrity, Flow continuity | Malformed assessment JSON |
| 9.4 | Cell accuracy, Structure preservation, Alignment check | Malformed assessment JSON |
| 9.5 | Detection accuracy, Format preservation, Boundary correctness | Malformed assessment JSON |
| 9.7 | Gap detection, Duplicate detection, Actionable suggestions, Font-source awareness (skepticism for font-inferred headings per FR-016) | Malformed assessment JSON |
| 9.8 | Order correctness, Confidence flagging, Threshold adherence | Malformed assessment JSON |
| 10.2 | Rating justification, Dimension coverage, Score consistency | Missing required dimensions |
| 10.3 | Issue clarity, Example quality, Actionable guidance | Truncated or empty report |

### Test Strategy

Following Constitution III (Test-First, NON-NEGOTIABLE):

1. **Unit tests** (tests/unit/): Test workspace I/O logic, instruction file generation, contract validation, error handling. No network calls, no agent invocations.
   - `agent_step.py` tests: use `tmp_path` fixtures; assert correct file paths and content written for each step; assert read_agent_output() parses correctly.
   - Instruction tests: assert markdown templates render correctly after variable substitution; assert generated step-instructions.md contains required fields for each step; parameterized with fixture inputs. step_7_7.py tested for correct template selection per pass.
   - Token preflight: test both branches — interactive skip (mock `input()` returning "s") and `--yes` auto-proceed; use short markdown strings to trigger threshold.
   - Multimodal steps (7.7, 8.7): stub PNG in test fixtures; tests validate instruction content references correct image paths, not image content.
2. **Contract tests** (tests/contract/): Validate that fixture agent outputs conform to each step's JSON Schema. Use pre-written fixture output files (not live agent calls) → validate against schema. One contract test file per step (13 total).
3. **Integration tests** (tests/integration/): Live agent invocation against reference corpus. Verify SC-002 (90% first-pass), SC-003 (reproducible scores), SC-005 (zero false TTRPG corrections).
   - Agent: use configured agent from `GM_AGENT` env var (default: `codex`); invoked via subprocess with appropriate flags per agent (dispatch table maps agent name → full CLI invocation, e.g. `codex` → `codex exec --full-auto -s workspace-write`).
   - CI: integration tests skipped by default (marked `pytest.mark.integration`); run manually or in dedicated CI job with `GM_AGENT` set.
4. **Golden files**: Generated from first successful corpus run, reviewed manually. Subsequent runs compared for regression.
   - Vision steps (7.7, 8.7): golden files include bounding-box JSON from step 7.7 and markdown table output from step 8.7; captured at 150 DPI; if DPI changes, golden files must be regenerated.
   - Golden files stored in `tests/fixtures/pdf_convert/agents/golden/step_7_7/` and `step_8_7/`.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Execution model | Agent-orchestrated (E2-09 confirmed) | Running agent controls pipeline; Code steps are CLI invocations; Agent steps performed by agent itself; no Python SDK for LLM inference; eliminates auth complexity and double-billing |
| Workspace artifact protocol | step-input.json + step-instructions.md → step-output.json | Standard file contract per step in {workspace}/agent_steps/step_X_Y/; agent reads inputs, writes output; Python validates output against JSON Schema |
| Markdown modification (steps 4.5, 6.4, 8.7) | Agent edits phase file directly; step-output.json carries metadata only | These 3 steps modify the phase markdown in place — agent receives phase file path in step-input.json and edits it directly; step-output.json contains status/change count/notes only (not content); phase files remain clean, human-readable diff artifacts |
| Agent invocation | Agent-dependent CLI flags | Codex (default): `exec --full-auto -s workspace-write`; Claude Code: `--print --dangerously-skip-permissions`; OpenCode: `run`; all confirmed by E2-09. Gemini CLI and Qwen also supported; not CI-tested (E2-09 Phase 2 deferred). Agent selected via `GM_AGENT` env var; dispatch table maps name → full invocation |
| Instruction storage | Markdown templates (Python for step 7.7 only) | instructions/step_X_Y.md: human-readable, {variable} slots substituted by agent_step.py before writing to workspace; step_7_7.py is Python-only due to two-pass logic (text_scan + vision template selection) |
| Contract format | JSON Schema Draft-07 | Python jsonschema library mature; deterministic validation |
| Table detection | Two-pass multimodal (text scan → on-demand image render → vision) | Step 7.7: agent reads extracted text to identify likely table pages; PyMuPDF Code utility renders those pages as images on-demand; agent reads images and returns bounding boxes; step 8.7 crops and reconstructs markdown. No pre-rendered page images — rendering is on-demand only (FR-014) |
| Step 8.7 image path format | Relative to project root | Fixtures use paths like `tests/fixtures/pdf_convert/agents/inputs/table_pages/page_005.png` |
| Corpus test justfile commands | `test-corpus-homebrewery`, `test-corpus-b2`, `test-corpus-coc` | Enables parallel CI jobs per PDF |
| Image retention | Keep after pipeline | Remind user of workspace size; offer cleanup helper |
| Agent step library | Subpackage under pdf_convert | Library-first (Constitution I); self-contained, independently testable |
| Token heuristic | Configurable via env var `GM_TOKEN_THRESHOLD` (default 100000) | ~4 chars/token estimate (~80-120 two-column pages); threshold checked before quality-assessment steps (9.2-9.5, 9.7-9.8, 10.2-10.3) which receive the full document; warning explicitly flags heading hierarchy and TOC alignment as the most likely accuracy casualties for large documents; user may proceed or skip |
| Page image DPI | 150 DPI (configurable via `GM_PAGE_IMAGE_DPI`) | Balances file size vs. table text legibility; 150 DPI sufficient for vision LLM recognition; override for high-density tables |

## Dependency Notes

### PyMuPDF Page Rendering (step 7.7)

On-demand page rendering uses `fitz.Document.load_page(n).get_pixmap(dpi=150)`. Output written as PNG: `pixmap.save(str(page_images_dir / f"page_{n:03d}.png"))`. DPI configurable via `GM_PAGE_IMAGE_DPI` env var (default 150).

### Pillow Image Cropping (step 8.7)

Bounding box from step 7.7 is in page coordinates (points). Crop formula: `scale = dpi / 72; box = (x0*scale, y0*scale, x1*scale, y1*scale); img.crop(box)`. Precision note: PyMuPDF point coords are at 72 dpi baseline; multiply by `dpi/72` before PIL crop. This avoids sub-pixel misalignment on high-DPI renders.

### Token Estimation (FR-015)

Heuristic: `estimated_tokens = len(markdown_text) / 4`. Configurable threshold via `GM_TOKEN_THRESHOLD` (default 100000). This is a rough estimate sufficient for a preflight warning; not used for billing.

## Phase 2: Task Breakdown

*Generated by `/speckit.tasks` command — not created by `/speckit.plan`.*

See `tasks.md` once generated.
