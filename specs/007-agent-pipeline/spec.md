# Feature Specification: PDF→Markdown Agent-Driven Pipeline

**Feature Branch**: `007-agent-pipeline`
**Created**: 2026-02-06
**Updated**: 2026-02-15
**Status**: Draft
**Input**: User description: "Implement the Agent-category steps (13 of 77 total) from the PDF conversion architecture. This includes prompt templates and contracts for visual TOC parsing, sentence boundary resolution, spelling correction, table detection, table conversion, quality assessments, and two-column reading order validation."
**Architecture Reference**: `specs/004-pdf-research/pdf-conversion-architecture.md` (v11)

## Clarifications

### Session 2026-02-06

- Q: Reference test corpus for agent-step validation → A: Homebrewery (with TOC), Homebrewery (without TOC), and Call of Cthulhu.
- Q: Pass/Fail threshold for rubric scoring → A: Per-step minimum score plus no critical failures.
- Q: Output format for agent-step contracts → A: JSON schema per step.
- Q: Handling missing or incomplete agent-step inputs → A: Fail step with structured error + recovery guidance.

### Session 2026-02-14 (Architecture Alignment)

- E4-07a implementation (merged 2026-02-13) changed step numbering and agent step composition.
- Step 4.6 renumbered to 4.5 (two-column detection step removed).
- Step 8.6 (quote formatting) removed — author quotes render as plain text.
- Step 8.7 (callout formatting) integrated into Code step 8.2.
- Step 8.8 (figure placeholders) became Code step 8.9.
- Only 8.7 (table conversion) remains as Phase 8 agent step.
- Step 6.4 mitigation: err on the side of flagging rather than auto-fixing uncertain OCR corrections, especially near table-like content.
- Agent step count updated from 15 to 14.

### Session 2026-02-16 (Clarify)

- Rubric evaluation mechanism: LLM-based (Option A). Agent scores outputs against rubric criteria using temperature=0 and structured output. SC-003 "deterministic" means consistent/reproducible, not bit-identical.

### Steps Covered (Agent) (13 steps)

| Step | Phase | Description | Criticality |
|------|-------|-------------|-------------|
| 3.2 | TOC & Font Extraction | If no embedded TOC, parse visual TOC page | Medium |
| 4.5 | Text Extraction & Merge | Resolve split sentences at chunk boundaries | Low |
| 6.4 | Word/Token-Level Fixes | Fix spelling errors (OCR artifacts: rn→m, l→1, O→0) | Low |
| 7.7 | Structural Detection | Detect table structures | Medium |
| 8.7 | Hierarchy Application | Convert detected tables to markdown format | Medium |
| 9.2 | Quality & Review | Structural clarity assessment | High |
| 9.3 | Quality & Review | Text flow / readability assessment | High |
| 9.4 | Quality & Review | Table integrity check | High |
| 9.5 | Quality & Review | Callout formatting check | High |
| 9.7 | Quality & Review | Review TOC validation issues (gaps, duplicates) | Medium |
| 9.8 | Quality & Review | Review two-column reading order issues | Medium |
| 10.2 | Report & Diagnostics | Include quality ratings (1-5 scale) | Low |
| 10.3 | Report & Diagnostics | Document up to 3 remaining issues with examples | Low |

### Step Groupings

Steps fall into four functional groups:

1. **Content Repair** (3.2, 4.5, 6.4): Fill gaps the Code pipeline cannot handle deterministically — TOC parsing, sentence rejoining, OCR correction.
2. **Table Processing** (7.7, 8.7): Detect and convert table structures that PyMuPDF extracts as flat text.
3. **Quality Assessment** (9.2-9.5, 9.7-9.8): Evaluate the converted document across multiple quality dimensions.
4. **Reporting** (10.2-10.3): Produce quality ratings and document remaining issues.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Produce reliable agent-step outputs (Priority: P1)

As a conversion operator, I want the agent-driven steps to produce consistent, well-formed outputs for each step so the pipeline can proceed without manual rework.

**Why this priority**: The agent outputs are upstream dependencies for multiple later phases; unstable outputs block the entire pipeline.

**Independent Test**: Provide the standard test inputs for each agent step and confirm outputs match their contracts and pass rubric thresholds.

**Acceptance Scenarios**:

1. **Given** a standard input artifact for an agent step, **When** the step prompt is executed, **Then** the output conforms to the step's contract and passes the rubric criteria.
2. **Given** an input artifact with minor formatting anomalies, **When** the step prompt is executed, **Then** the output still meets the contract with clearly reported anomalies.
3. **Given** a missing or incomplete input artifact, **When** the step is invoked, **Then** the step fails with a structured error containing the step ID, a description of what is missing, and recovery guidance (e.g., "Re-run Phase 3 to generate toc-extracted.txt").

---

### User Story 2 - Validate agent outputs consistently (Priority: P2)

As a reviewer, I want evaluation rubrics that make the quality of agent outputs measurable and repeatable.

**Why this priority**: Without consistent evaluation, the pipeline can regress without clear signal.

**Independent Test**: Apply rubrics to a fixed test corpus and verify scoring is deterministic and thresholds are explicit.

**Acceptance Scenarios**:

1. **Given** a fixed set of step outputs, **When** rubrics are applied, **Then** the same scores and pass/fail results are produced across runs.
2. **Given** step outputs that are syntactically valid but contain quality issues (e.g., out-of-order headings, missed OCR errors), **When** rubrics are applied, **Then** the issues are reflected in reduced scores and the step fails if scores fall below the per-step minimum.

---

### User Story 3 - Integrate agent steps with the code pipeline (Priority: P3)

As a developer, I want the agent-step prompts, contracts, and rubrics aligned with the code pipeline so implementation can replace stubs with real agent calls without changing pipeline behavior.

**Why this priority**: E4-07a is already complete with stubs for each agent step. Integration alignment ensures stubs can be swapped without rework.

**Independent Test**: Verify that each agent step's contract inputs/outputs match the data flow in the E4-07a code pipeline stubs.

**Acceptance Scenarios**:

1. **Given** the code pipeline's stub interfaces for agent steps, **When** the agent-step artifacts are reviewed, **Then** each step has a matching prompt, contract, and rubric with compatible inputs/outputs.
2. **Given** a completed agent step replacing its stub, **When** the pipeline is executed end-to-end, **Then** downstream phases receive the expected data format and the pipeline completes without errors.

---

### Edge Cases

| Edge Case | Expected Behavior | Test Approach |
|-----------|-------------------|---------------|
| Agent step input artifact is missing or incomplete | Fail with structured error and recovery guidance | Provide deliberately incomplete inputs; verify error message and recovery steps |
| Agent output is syntactically valid but semantically inconsistent (e.g., out-of-order headings in TOC) | Rubric detects the inconsistency and fails the step | Create golden files with known semantic errors; verify rubric catches them |
| Multi-column content cannot be confidently resolved into a single reading order (step 9.8) | Flag as pervasive (>15%) for user review rather than attempting auto-fix | Provide two-column PDF excerpt; verify flagging vs fix threshold |
| Step 6.4 encounters abbreviations in table-like content (e.g., "ST", "DX", "HP") | Preserve abbreviations; flag uncertain corrections rather than auto-fixing | Provide input with TTRPG stat block; verify no false corrections |
| Step 3.2 receives a PDF with no TOC at all (neither embedded nor visual) | Return empty TOC result; pipeline continues with font-based hierarchy only | Provide PDF with no TOC page; verify graceful degradation |
| Agent produces malformed output after max retries (3 attempts) | Follow criticality-based escalation: High → halt, Medium → flag for user, Low → skip | Mock repeated failures per criticality level; verify correct escalation |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a distinct prompt template for each of the 13 agent-category steps listed in the architecture reference (v11).
- **FR-002**: Each prompt template MUST define the step's task, input format, expected output format, and edge-case handling (e.g., "Task: resolve split sentences; Input: chunk boundary text with markers; Output: corrected text; Edge case: no split sentences found → return input unchanged").
- **FR-003**: The system MUST define a contract per agent step expressed as a JSON schema specifying required fields and structural constraints for outputs.
- **FR-004**: The system MUST define a rubric for each agent step that makes output quality measurable and includes pass/fail criteria: a per-step minimum score of 3 out of 5 on each rubric dimension, plus zero critical failures. A **critical failure** is any output defect that would cause downstream pipeline steps to fail or produce corrupt results (e.g., malformed JSON, missing required fields, truncated content, wrong output format).
- **FR-005**: The system MUST map each agent step to its integration point in the E4-07a code pipeline with explicit expected inputs and outputs matching the stub interfaces.
- **FR-006**: The system MUST include test artifacts that allow contract testing, rubric evaluation, golden-file comparison, and structural validation for each agent step using the reference corpus.
- **FR-007**: The reference test corpus MUST include The Homebrewery (with TOC), The Homebrewery (without TOC), and Call of Cthulhu.
- **FR-008**: Missing or incomplete step inputs MUST fail the step with a structured error in the format: `{"step_id": "X.Y", "error": "description of what is missing", "recovery": "actionable guidance to fix"}` (e.g., `{"step_id": "3.2", "error": "toc-extracted.txt not found", "recovery": "Re-run Phase 3 to generate TOC extraction output"}`).
- **FR-009**: Agent step outputs MUST be validated against their contract before acceptance; invalid outputs trigger retry (max 3 attempts) with the validation error appended to the retry prompt.
- **FR-010**: After max retries, the system MUST follow criticality-based escalation: High criticality steps halt the pipeline; Medium steps flag for user or skip with degraded output; Low steps skip silently.
- **FR-011**: The agent-step scope MUST cover exactly 13 steps: 3.2, 4.5, 6.4, 7.7, 8.7, 9.2-9.5, 9.7-9.8, and 10.2-10.3. Step 9.1 (completeness check) was dropped — Phase 4 already guarantees all page markers are present by iterating every page explicitly; a code-level word-count check is sufficient and does not require agent judgment.
- **FR-012**: Step 3.2 (visual TOC parsing) MUST produce output in the same indented text format as the embedded TOC extractor (step 3.1): each entry on its own line, indented with 2 spaces per heading level (level 1 = no indent, level 2 = 2 spaces, etc.), with page number in `(page N)` notation (e.g., `Chapter One: The Village of Barovia (page 4)` / `  Section 1.1: Something (page 5)`). Output is written to `toc-extracted.txt` so downstream phases consume it identically regardless of which step produced it.
- **FR-013**: Step 6.4 (OCR spelling correction) addresses OCR artifacts in two scenarios: (1) PDFs that were scanned and OCR-processed before creation, leaving character substitution errors in the embedded text layer; (2) agent-driven OCR workflows where an AI agent with native OCR capability processes a scanned PDF externally and feeds the resulting text into the pipeline via the resume-from-phase feature. The pipeline itself does not perform OCR — step 6.4 is the cleanup and correction layer for either input path. Step 6.4 MUST preserve domain-specific TTRPG terminology (capitalized words, repeated terms, TOC/heading terms) and MUST err on the side of flagging rather than auto-fixing uncertain corrections, especially near table-like content with abbreviations.
- **FR-016**: Step 9.7 (TOC validation) MUST receive `font-family-mapping.json` as an additional input alongside `toc-extracted.txt` and the phase 8 markdown. The font mapping distinguishes headings sourced from the TOC from headings inferred by Phase 7 font analysis (ALL CAPS, Title Case detection). The LLM MUST apply appropriate skepticism to font-inferred headings when evaluating TOC gaps — a heading detected by font analysis but absent from the TOC may be a legitimate structural heading OR a misidentified decorative element (pull quote, table header, flavor text label). Uncertain cases MUST be flagged rather than reported as definitive gaps.

- **FR-015**: Agent steps that send large markdown inputs to the LLM MUST perform a preflight token estimate before the LLM call. If the estimated token count exceeds a configurable threshold (default: 100,000 tokens): in interactive mode (no `--yes` flag), the user is warned and prompted to continue or skip the step; in non-interactive mode (`--yes` flag), a warning is emitted and the step proceeds automatically. A skipped step due to size produces WARNING status (not ERROR) and the pipeline continues. This constraint applies particularly to step 9.3 (text flow assessment) where the full markdown is assessed as prose and chunking would miss cross-boundary flow issues.

- **FR-014**: Steps 7.7 and 8.7 (table detection and conversion) MUST use a two-pass multimodal approach: (1) Step 7.7 receives all pages' extracted text, identifies which pages likely contain tables from text signals alone, then renders those pages as images on-demand via PyMuPDF and sends them to the vision LLM to confirm table presence and extract bounding boxes in pixel coordinates; the rendered page images are saved to the output directory as intermediate artifacts. (2) Step 8.7 loads the already-saved page images from step 7.7 (no re-rendering), crops each image to the table's bounding box using standard Python image operations, and sends each cropped image alongside the garbled flat text to the vision LLM to produce properly structured markdown tables. Page images are NOT pre-rendered — rendering happens on-demand only for pages flagged in step 7.7, and intermediate page image artifacts may be discarded after step 8.7 completes.

### Key Entities *(include if feature involves data)*

- **Agent Step Prompt**: A single-step prompt template defining task, inputs, outputs, and edge cases. One per agent step (13 total).
- **Step Contract**: A JSON schema defining required fields and structural constraints for a step's output. One per agent step.
- **Step Rubric**: The evaluation criteria used to score and accept step outputs. Includes per-step minimum score and critical failure definitions. One per agent step.
- **Evaluation Result**: The pass/fail outcome and scoring summary for a step output, including individual criterion scores and any flagged issues.
- **Test Artifact**: A set of input/output pairs from the reference corpus used for contract testing, rubric evaluation, and golden-file comparison.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 13 agent steps have a prompt template, contract (JSON schema), and rubric defined and linked to their E4-07a pipeline integration points (stub interfaces).
- **SC-002**: For the reference test corpus, at least 90% of individual step executions (across all steps and all corpus PDFs) meet contract requirements on the first pass.
- **SC-003**: Rubric evaluations produce consistent, reproducible pass/fail outcomes across repeated runs on identical inputs. Rubrics are evaluated by LLM (temperature=0, structured output); "deterministic" means consistent given explicit criteria, not bit-identical.
- **SC-004**: The agent-step artifacts replace the existing E4-07a stubs without changing the pipeline's expected inputs/outputs, verified by end-to-end pipeline execution on the reference corpus.
- **SC-005**: Step 6.4 produces zero false corrections on TTRPG domain terms (monster names, game abbreviations, location names) in the reference corpus.

## Assumptions

- The code pipeline (E4-07a) is complete and merged (commit 8c8ead9, 2026-02-13). Stub interfaces define the integration contracts.
- The orchestration stubs in `src/gm_kit/pdf_convert/phases/` will be replaced by real agent invocations using these prompts and contracts.
- The architecture reference (v11, 2026-02-14) is the source of truth for step ordering, naming, and criticality.
- Agent retry logic (max 3 attempts with validation error feedback) is implemented in the orchestrator; this feature defines the prompts and contracts that the retry mechanism uses.
- The reference test corpus PDFs are available in `tests/fixtures/pdf_convert/`.
