# Implementation Plan: PDF→Markdown Agent-Driven Pipeline

**Branch**: `007-agent-pipeline` | **Date**: 2026-02-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-agent-pipeline/spec.md`

## Summary

Implement the 13 Agent-category steps from the PDF conversion architecture (v11) by creating prompt templates, JSON schema contracts, LLM-based rubrics, and integration wiring to replace the existing E4-07a stubs. Each agent step receives structured input from the code pipeline, calls an LLM (temperature=0, structured output), validates the response against its contract, and evaluates quality via a rubric. Steps are grouped into Content Repair (3.2, 4.5, 6.4), Table Processing (7.7, 8.7), Quality Assessment (9.2-9.5, 9.7-9.8), and Reporting (10.2-10.3).

## Technical Context

- **Language/Version**: Python 3.8+ (constitution mandate), running on 3.13.7
- **Primary Dependencies**: typer, rich, PyMuPDF/fitz, jsonschema (contract validation), Pillow (image cropping for table region extraction in steps 7.7/8.7)
- **LLM Integration**: Provider-agnostic via abstraction layer; supports Claude, Gemini, Qwen, and other agents per Constitution VI; temperature=0; structured JSON output
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
| VI. AI Agent Integration | PASS | This IS the agent integration; follows AGENTS.md coding standards; Constitution VI v1.4 mandates provider-agnostic abstraction — `client.py` abstracts Claude, Gemini, Qwen, etc. |
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
│   └── requirements.md  # Spec quality checklist (42/42 passing)
└── feature-implementation-journal.txt
```

### Source Code (repository root)

```text
src/gm_kit/pdf_convert/
├── agents/                        # NEW: Agent step library
│   ├── __init__.py                # Public API: run_agent_step(), AgentStepError
│   ├── base.py                    # AgentStep abstract base, shared types
│   ├── client.py                  # LLM client abstraction (provider-agnostic, temperature=0)
│   ├── contracts.py               # Contract loader + validator (jsonschema)
│   ├── evaluation.py              # LLM-based rubric evaluator
│   ├── errors.py                  # AgentStepError, ContractViolation, RubricFailure
│   ├── prompts/                   # Prompt templates per step
│   │   ├── __init__.py
│   │   ├── step_3_2.py            # Visual TOC parsing
│   │   ├── step_4_5.py            # Sentence boundary resolution
│   │   ├── step_6_4.py            # OCR spelling correction
│   │   ├── step_7_7.py            # Table detection (two prompt fns: text_scan + vision)
│   │   ├── step_8_7.py            # Table-to-markdown conversion
│   │   ├── step_9_2.py            # Structural clarity
│   │   ├── step_9_3.py            # Text flow / readability
│   │   ├── step_9_4.py            # Table integrity
│   │   ├── step_9_5.py            # Callout formatting
│   │   ├── step_9_7.py            # TOC validation review
│   │   ├── step_9_8.py            # Two-column reading order
│   │   ├── step_10_2.py           # Quality ratings
│   │   └── step_10_3.py           # Remaining issues
│   ├── rubrics/                   # Rubric definitions per step
│   │   ├── __init__.py
│   │   ├── base.py                # Rubric base class, scoring types
│   │   ├── step_3_2.py            # ... one per step (same layout as prompts/)
│   │   └── ...
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
│   ├── test_evaluation.py         # Rubric evaluator tests
│   ├── test_prompts.py            # Prompt template construction tests
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

Each agent step follows this execution pattern:

```
Phase.execute() → agents.run_agent_step(step_id, inputs)
  1. Load prompt template (prompts/step_X_Y.py)
  2. Build prompt with step inputs
  3. Call LLM (client.py: configured provider, temperature=0, structured output)
     Note — step 7.7 uses two LLM calls internally:
       3a. Text scan: send all pages' extracted text → LLM identifies likely table pages
       3b. Image render: PyMuPDF renders flagged pages on-demand as images
       3c. Vision call: send page images → LLM returns bounding boxes per table
  4. Validate response against contract (schemas/step_X_Y.schema.json)
  5. If invalid → retry (up to 3x, append validation error to prompt)
  6. If valid → evaluate via rubric (rubrics/step_X_Y.py + LLM evaluation)
  7. If rubric passes (≥3/5 per dimension, zero critical failures) → return result
  8. If rubric fails → retry (counts toward same 3x budget)
  9. After max retries → criticality-based escalation
```

### Implementation Order

Work is organized in dependency order:

1. **Foundation** (agents base, client, contracts, errors, token_preflight utility)
   - `client.py`: provider-agnostic LLM interface; `complete(prompt, *, vision=False) -> str`; raises `ProviderError`, `VisionNotSupportedError`
   - `token_preflight.py`: shared utility for FR-015; estimates token count (~4 chars/token), warns user if markdown exceeds ~100k tokens; interactive skip or `--yes` auto-proceed
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

1. **Unit tests** (tests/unit/): Mock LLM client, test prompt construction, contract validation logic, rubric scoring logic, error handling. No network calls.
   - Multimodal steps (7.7, 8.7): pass `Path("fixtures/agents/images/stub_page.png")` as image arg to mock client; stub PNG included in test fixtures; tests validate prompt construction and image path plumbing, not image content.
   - Token preflight: test both branches — interactive skip (mock `input()` returning "s") and `--yes` auto-proceed; use short markdown strings to trigger threshold.
   - `client.py` unit tests: mock at the SDK level (`unittest.mock.patch` on the provider SDK client method, e.g. `anthropic_client.messages.create`); test `VisionNotSupportedError` raised correctly. No raw HTTP mocking — provider SDKs own HTTP internally.
2. **Contract tests** (tests/contract/): Validate that each step's output schema matches the expected shape. Use fixture inputs → mock LLM → validate against schema. One contract test file per step (13 total). Also includes `test_client_contract.py` validating the `client.py` interface contract across all provider adapters.
3. **Integration tests** (tests/integration/): Real LLM calls against reference corpus. Verify SC-002 (90% first-pass), SC-003 (reproducible scores), SC-005 (zero false TTRPG corrections).
   - Provider: use configured provider from `GM_LLM_PROVIDER` env var (default: whichever is set in CI); CI runs with `--yes` flag (no interactive prompts).
   - Credentials: provider API keys via env vars (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, etc.); integration tests skipped if no key present (marked `pytest.mark.integration`).
4. **Golden files**: Generated from first successful corpus run, then reviewed manually. Subsequent runs compared for regression.
   - Vision steps (7.7, 8.7): golden files include bounding-box JSON from step 7.7 and markdown table output from step 8.7; captured at 150 DPI; if DPI changes, golden files must be regenerated.
   - Golden files stored in `tests/fixtures/pdf_convert/agents/golden/step_7_7/` and `step_8_7/`.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM provider | Provider-agnostic abstraction | Constitution VI mandates support for multiple AI agents (Claude, Gemini, Qwen, etc.); client.py abstracts provider differences behind a common interface |
| Rubric evaluation | LLM-based (temperature=0) | Quality dimensions are semantic, not rule-checkable (SC-003 clarification); works with any supported provider |
| Contract format | JSON Schema Draft-07 | Python jsonschema library mature; deterministic validation |
| Prompt storage | Python modules (not text files) | Allows parameterization, type checking, test imports |
| Table detection | Two-pass multimodal (text scan → on-demand image render → vision) | Step 7.7 scans extracted text to flag likely table pages, renders only those pages as images on-demand via PyMuPDF, then uses vision LLM for bounding box extraction; step 8.7 crops flagged regions and uses vision LLM to reconstruct markdown. No pre-rendered page images — rendering is on-demand only (FR-014) |
| Step output format | JSON with shared metadata envelope | Consistent validation; envelope has step_id, warnings, errors |
| Agent step library | Subpackage under pdf_convert | Library-first (Constitution I); self-contained, independently testable |
| client.py interface | `complete(prompt: str, *, vision: bool = False, images: list[Path] = None) -> str` | Provider differences hidden behind one method; `vision=True` with `images` for multimodal steps; raises `VisionNotSupportedError` if provider lacks vision; caller handles as step failure (criticality-based escalation, same as other critical failures) |
| Vision capability | Validated at invocation, not startup | `VisionNotSupportedError` raised by `client.py` when `vision=True` but provider doesn't support it; step catches and escalates per FR-010; not a silent fallback — pipeline fails the step explicitly |
| Token heuristic | Configurable via env var `GM_TOKEN_THRESHOLD` (default 100000) | ~4 chars/token estimate; set lower for testing; threshold checked before any quality-assessment step LLM call |
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
