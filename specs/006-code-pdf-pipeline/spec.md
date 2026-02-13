# Feature Specification: PDF Code Pipeline

**Feature Branch**: `006-code-pdf-pipeline`
**Created**: 2026-02-06
**Status**: Draft
**Input**: User description: "refer to the E4-07a feature in BACKLOG.md for details and instructions for this feature"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Code-Driven Pipeline (Priority: P1)

As a GM-Kit operator, I want to run the code-driven PDF→Markdown pipeline end-to-end so I can produce a structured Markdown draft plus diagnostic artifacts.

**Why this priority**: This is the core value of E4-07a; without a working code pipeline, the overall conversion flow cannot run.

**Independent Test**: Can be fully tested by running the pipeline on a sample PDF and verifying the final Markdown and phase artifacts are produced.

**Acceptance Scenarios**:

1. **Given** a supported PDF and a working workspace, **When** the full code-driven pipeline is run, **Then** the pipeline completes and produces a Phase 8 markdown output (hierarchy applied) plus per-phase artifacts. Full validation requires E4-07b/c.
2. **Given** a supported PDF, **When** the pipeline encounters a known non-fatal anomaly, **Then** it records the anomaly in diagnostics and still produces the phase outputs for completed steps.
3. **Given** a PDF that triggers an error condition (corrupted, no extractable text), **When** the pipeline is run, **Then** it halts with a clear error message and does not produce incomplete outputs.

---

### User Story 2 - Run Individual Phases (Priority: P2)

As a GM-Kit operator, I want to run specific phases in isolation so I can debug or validate individual steps without re-running the entire pipeline.

**Why this priority**: Phase-level execution is essential for diagnostics and iterative refinement.

**Independent Test**: Can be tested by executing a single phase on a sample PDF and verifying only that phase’s outputs are produced.

**Acceptance Scenarios**:

1. **Given** a supported PDF and a selected phase, **When** the phase is run in isolation, **Then** the phase outputs are generated and the pipeline does not execute unrelated phases.

---

### User Story 3 - Accurate Heading Signatures (Priority: P3)

As a QA reviewer, I want heading inference to use a full font signature (family + size + weight + style) so headings that share a family but differ by style are classified correctly.

**Why this priority**: Heading accuracy is a primary quality signal for the Markdown output and prevents misclassified section levels.

**Independent Test**: Can be tested by using a PDF where headings share a family but differ in weight/style and verifying distinct signatures are recognized and used during inference.

**Acceptance Scenarios**:

1. **Given** a PDF with headings that share a font family but differ in weight/style, **When** signatures are extracted, **Then** the signatures are distinct and used for heading inference.

---

### Edge Cases

| Edge Case | Expected Behavior | Test Approach |
|-----------|-------------------|---------------|
| PDFs with no extractable text content | ERROR: halt with "scanned PDF detected" guidance | Unit test (mock) |
| Headings that share family and size but differ only by weight/style | Handled via full font signature differentiation | Integration (Homebrewery fixture) |
| PDFs with missing or incomplete TOC entries | WARNING: continue with font-based inference only | Integration (Homebrewery no-TOC fixture) |
| Corrupted or partially readable PDF files | ERROR: halt with diagnostic message | Unit test (mock) |
| Missing phase input file (e.g., `--phase 5` without Phase 4 output) | ERROR: "Phase input file not found - run previous phase first" | Unit test (mock missing file) |
| PDF contains HTML tags or markdown-sensitive characters in body text | Phase 5 MUST wrap HTML tags and markdown special characters in backticks to prevent markdown rendering issues | Integration (Homebrewery fixture with HTML content) |
| Callout config file is empty or contains `[]` | Pipeline proceeds with no callout detection from config; keyword-based detection still applies | Unit test |
| Callout config file has invalid JSON | WARNING: log parse error and continue without config-based callout detection | Unit test |
| Callout config `start_text`/`end_text` not found in PDF content | No callout regions matched; no error raised | Integration test |
| PDF contains tables | Table cell data extracted as flat text lines with no structural information; no table reconstruction attempted | Integration (Homebrewery fixture) |

### Deferred: Table Detection and Reconstruction

Table detection (step 7.7) and table conversion (step 8.7) are **deferred to E4-07b** (agent-driven pipeline). Investigation during E4-07a implementation confirmed that reconstructing table structure from PDF text extraction alone is not feasible without spatial analysis or multimodal OCR. PyMuPDF extracts table cells as individual text lines with no row/column information, producing a flat list of values.

**Investigation findings:**
- Table headers and data cells appear as a flat sequence with no structural cues
- Reconstructing row/column relationships requires spatial coordinate analysis (cell bounding boxes) or visual/multimodal OCR
- This is inherently a judgment task better suited to agent steps than deterministic code

**E4-07a behavior:** Tables pass through the pipeline as flat text. No placeholder insertion or structural markers are added. Phase 8 outputs table content as plain paragraphs.

**Future options (for E4-07b or later):**
- Agent step 7.7: Detect table regions using spatial analysis or multimodal prompts
- Agent step 8.7: Convert detected tables to markdown table syntax
- Multimodal OCR: Use page images + AI vision to reconstruct table structure (see `specs/004-pdf-research/pdf-conversion-architecture.md` for architecture discussion)

### Terminology: Non-Fatal Anomalies

**Non-fatal anomalies** are conditions that trigger a WARNING status (as defined in the architecture's Error Conditions table) rather than an ERROR. The pipeline continues execution and records the anomaly in phase results. Examples: missing TOC, lint violations exceeding threshold. See `specs/004-pdf-research/pdf-conversion-architecture.md` §Error Conditions for the complete list.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run the full code-driven PDF→Markdown pipeline and produce a final Markdown output.
- **FR-002**: System MUST support executing individual phases independently for diagnostic workflows.
- **FR-003**: System MUST generate and preserve per-phase outputs for inspection and troubleshooting.
- **FR-004**: System MUST extract and persist font signatures using family, size, weight, and style.
- **FR-005**: System MUST use the full font signature (family + size + weight + style) during heading inference.
- **FR-006**: System MUST update any persisted/exchanged font-signature schema to include the full signature fields.
- **FR-007**: System MUST replace the existing E4-07e stub phases with real implementations while preserving the current orchestration surface.
- **FR-008**: System MUST include unit tests for individual modules and integration tests that validate intermediate phase outputs (phase4.md through phase8.md) for correctness and phase-to-phase compatibility, including same-family-different-style heading scenarios.
- **FR-009**: System MUST add regression tests when integration anomalies require code changes.
- **FR-010**: System MUST support a `callout_config.json` file that allows users to define custom callout boundaries (start/end text fragments) for GM callout detection. If no config file is provided via `--gm-callout-config-file`, the system creates an empty default in the output directory during pre-flight (Phase 0).
- **FR-011**: System MUST use callout definitions from `callout_config.json` during Phase 7 (structural detection) to identify font signatures associated with callout regions, and apply blockquote formatting to those signatures during Phase 8 (heading insertion).

### Deliverable Scope

E4-07a delivers through Phase 8 with stub integration points for Agent/User steps. Phase 9/10 execute with stub results until E4-07b/c are implemented. The Phase 8 markdown output (hierarchy applied) is the primary deliverable for this feature.

### Pipeline Outputs (Reference)

The following artifacts are produced during pipeline execution. Full details in `specs/004-pdf-research/pdf-conversion-architecture.md`.

| Phase | Key Outputs | E4-07a Status |
|-------|-------------|---------------|
| 0 | `metadata.json`, `callout_config.json` (default if not provided), pre-flight report (console) | Complete |
| 1 | `images/` folder, `images/image-manifest.json` | Complete |
| 2 | `preprocessed/<filename>-no-images.pdf` | Complete |
| 3 | `toc-extracted.txt`, `font-family-mapping.json` | Complete (agent step 3.2 stubbed) |
| 4 | `<filename>-phase4.md` | Complete (agent step 4.6 stubbed) |
| 5 | `<filename>-phase5.md` | Complete |
| 6 | `<filename>-phase6.md` | Complete (agent step 6.4 stubbed) |
| 7 | Updated `font-family-mapping.json` (with callout labels from config) | Complete (agent/user steps stubbed) |
| 8 | `<filename>-phase8.md` | Complete (agent steps stubbed) |
| 9 | Validated markdown | Partial (agent/user steps stubbed) |
| 10 | `conversion-report.md`, `diagnostic-bundle.zip` | Partial (agent steps stubbed) |

**Enhanced Conversion Report (Phase 10)**:
The conversion report includes detailed tracking and performance metrics:

- **Phase Details Table**: Lists each completed phase with three columns:
  - **Phase**: Phase number and name
  - **Changes Made**: Summary of transformations applied in that phase
  - **What to Compare**: Guidance on what to look for when reviewing phase outputs against input documents

- **Performance Section**: Timing metrics including:
  - **Conversion Started**: ISO8601 timestamp when pipeline began
  - **Conversion Completed**: ISO8601 timestamp when pipeline finished
  - **Total Duration**: Elapsed time in HH:MM:SS format

This allows operators to track how phase documents are changing from input to final output and monitor conversion performance.

### Font Signature Marker Workflow

The pipeline uses a marker-based approach to connect font analysis (Phase 3) with heading application (Phase 8):

**Marker Format**: `«sigXXX:text»`
- Example: `«sig001:The Homebrewery V3»`

**Workflow**:
1. **Phase 3** generates `font-family-mapping.json` with unique signature IDs (sig001, sig002, etc.) and heading labels (H1, H2, H3)
2. **Phase 4** extracts text and wraps consecutive spans with the same font signature: `«sig001:The Homebrewery V3»`
3. **Phase 5** performs character-level cleanup (icon font removal, footer stripping) while **preserving markers**
4. **Phase 6** performs word/token-level cleanup (hyphenation fixes, bullet normalization) while **preserving markers**
5. **Phase 7** loads `callout_config.json` and matches start/end text boundaries against extracted content. Font signatures whose content falls within a callout region are labeled (e.g., `callout_gm`, `callout_sidebar`) in `font-family-mapping.json`.
6. **Phase 8** reads `*-phase6.md` (not `*-phase4.md`!), parses markers, looks up the signature ID in the JSON, and replaces with markdown: `# The Homebrewery V3` for headings, or `> text` for callout-labeled signatures. Multi-line callout blocks continue blockquote formatting across normal lines and empty lines. A callout block ends only when a heading is encountered, a different callout label begins, a non-callout marker line is encountered, a configured `end_text` marker is detected for that callout label, or EOF is reached.

**Important**: Phase 8's input is `*-phase6.md`, not `*-phase4.md`. Phases 5 and 6 perform essential cleanup on the text while preserving the font signature markers. The marker-preserving cleanup ensures Phase 8 receives cleaned text without losing font identity information needed for heading/callout detection.

**Collision Handling**:
- Existing « and » characters in PDF text are escaped as `\«` and `\»` during Phase 4
- Pattern matching in Phase 8 uses strict regex: `«(sig[a-z0-9]+):([^»]+)»`
- Escaped characters are restored after marker processing

**Full pipeline**: All outputs above, with Phase 8 markdown as the primary deliverable for E4-07a.

**Phase-only run**: Only the outputs for the specified phase are generated/updated.

### Stub Replacement Scope (Planning Input)

The current pipeline uses mock phases as placeholders. These must be replaced with real phase implementations during this feature.

- **Stub entrypoints**: `get_mock_phases()` and the mock phase registry in `src/gm_kit/pdf_convert/phases/stubs.py`
- **Orchestration hook**: the orchestrator currently loads mock phases via `get_mock_phases()` in `src/gm_kit/pdf_convert/orchestrator.py`
- **Phases to replace**: phases 0–10 must be backed by real orchestration phases that implement the code-category steps and invoke agent/user steps as integration points (agent/user logic is implemented in E4-07b/E4-07c)
- **Implementation depth**: Real phase classes replace `MockPhase` for all phases. Phases 0–8 have full Code-step implementations with stub handlers for Agent/User steps. Phases 9–10 implement only their Code-category steps (9.6 linting, 10.1/10.4-10.6 report generation); remaining Agent/User steps return placeholder results until E4-07b/c.
- **Phase/step mapping**: the detailed mapping from architecture steps to concrete phase implementations is defined during planning (using `specs/004-pdf-research/pdf-conversion-architecture.md` as the source)

### Plan Inputs from Architecture

The plan MUST reference the following sections in `specs/004-pdf-research/pdf-conversion-architecture.md` to derive tasks and sequencing:

- **Phase Summary + Detailed Phase Specifications**: authoritative step lists and Code/Agent/User ownership.
- **Label Inference Logic (Step 3.6)**: includes multi-span TOC matching and fallback heuristics.
- **Decision Log items**: sequencing constraints (e.g., 5.2 before 5.3, 7.9 before 7.10, 8.1 first, 8.10 single-H1 logic).
- **Error Conditions + Retry Logic**: required for user-visible error handling and tests.
- **Prior Art (POC Scripts)**: reference-only guidance for implementation; do not copy verbatim. They can be used as a starting point for fresh implementations, especially Phase 2 image removal and Phase 3 font sampling.

### Key Entities *(include if feature involves data)*

- **Font Signature**: A heading-identifying record containing font family, size, weight, and style.
- **Callout Config**: A JSON file (`callout_config.json`) defining custom callout boundaries via start/end text fragments. Used during Phase 7 to identify callout regions and label matching font signatures.
- **Phase Output**: Diagnostic artifact produced by a single pipeline phase.
- **Conversion Report**: Summary of pipeline outcomes, anomalies, and completion status.
- **Phase Result**: Structured status and metadata for a phase execution.

## Assumptions & Dependencies

### Assumptions

- Target PDFs are text-extractable (scanned/OCR-only PDFs are out of scope for this feature).
- A small set of representative PDFs is available for automated tests.

### Dependencies

- Existing orchestration surface (CLI, orchestrator, state, preflight) is already in place from E4-07e.
- E4-07a replaces stubs but does not redefine user-facing command structure.

**Inherited Modules from E4-07e:**

| Module | Purpose |
|--------|---------|
| `cli.py` | `gmkit pdf-convert` command with resume/phase/status flags |
| `orchestrator.py` | Pipeline execution, phase sequencing, state updates |
| `state.py` | `ConversionState` persistence (`.state.json`) |
| `preflight.py` | Pre-flight analysis (metadata, TOC detection, text extractability) |
| `metadata.py` | PDF metadata extraction dataclass |
| `phases/base.py` | `Phase` ABC, `PhaseResult`, `StepResult` types |
| `phases/stubs.py` | Mock phase implementations (to be replaced) |

### Phase Interface Contract

Real phase implementations must extend `Phase` (from `phases/base.py`) and implement:

```python
class Phase(ABC):
    @property
    def phase_num(self) -> int: ...      # Phase number 0-10

    def execute(self, state: ConversionState) -> PhaseResult: ...
```

- **Input**: `ConversionState` with pdf_path, output_dir, and prior phase results
- **Output**: `PhaseResult` containing status, step results, output file path, warnings/errors
- **Registration**: Phases are registered via a phase registry (replacing `get_mock_phases()`)
- **Orchestrator contract**: Orchestrator calls `phase.execute(state)` and updates state based on result

### Test Fixtures

PDF fixtures for integration testing are located in `tests/fixtures/pdf_convert/`.

| Fixture | Characteristics | Edge Cases Covered |
|---------|-----------------|-------------------|
| `The Homebrewery - NaturalCrit.pdf` | No embedded TOC, same-family headings with different weight/style | Missing TOC, font signature differentiation |
| `The Homebrewery - NaturalCrit (with TOC).pdf` | Embedded TOC version (TOC covers only first page) | Happy path, TOC extraction (presence/format only) |

**Unit test mocks** (no fixture needed):
- Corrupted/unreadable PDF → mock PyMuPDF to raise exception
- No extractable text (scanned PDF) → mock text extraction to return < 100 chars

**Fixture gaps** (create if integration coverage needed):
- Complex layout PDF → for advanced spatial analysis tests (if needed in future)
- Large PDF (50+ pages) → for chunking/performance tests

### Non-Functional Requirements

**Performance (inherited from E4-07e)**:
- Pre-flight (Phase 0): ~0.2s/page baseline (2s for 2-page reference PDF)
- No hard timeouts enforced; user can interrupt via Ctrl+C

**Performance (E4-07a additions)**:
- Code-step phases (1-8): Target ~0.5s/page total for all Code steps on reference PDF
- Benchmark during implementation; adjust threshold based on CI results

**Determinism**:
- Code-step outputs MUST be deterministic for the same input PDF
- No timestamps or random values in phase output files (except `.state.json` metadata)
- Repeat runs on identical input produce byte-identical markdown outputs

**Resource Limits**:
- Disk: Working directory may use up to 10x source PDF size (extracted images, per-phase outputs, preprocessed PDF)
- Memory: Not gated; typical RPG PDFs are under 100MB and PyMuPDF handles efficiently. Large PDFs (500+ pages) may require chunking per architecture.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running the code-driven pipeline on each supported sample PDF completes and produces a Phase 8 markdown output (hierarchy applied) plus per-phase artifacts.
- **SC-002**: For a PDF with same-family headings that differ by weight/style, heading inference differentiates them using full signatures in tests.
- **SC-003**: All unit and integration tests for code-driven phases pass for the feature branch.
- **SC-004**: Any code change triggered by an integration test anomaly includes a corresponding unit test that reproduces the issue.
