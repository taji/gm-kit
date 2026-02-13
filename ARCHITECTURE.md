# Architecture

This document captures the canonical design decisions for GM-Kit. Feature-specific plans and research are merged here after specification work completes.

## CI Pipeline (Walking Skeleton)

### Scope
- Linux-only CI pipeline for PRs to `master`.
- Windows validation is deferred to a future CD feature.

### Workflow
- CI runs on pull requests to `master`.
- Quality gates are executed via `just` tasks.
- Parity checks compare bash vs PowerShell-generated outputs on Linux; CI fails if PowerShell cannot be installed.

### Quality Gates
- `just lint`
- `just typecheck`
- `just test-unit`
- `just test-integration`
- `just test-parity`
- `just bandit`
- `just audit` (pip-audit via `uv tool run`)

### Parity Strategy
- Compare generated hello-gmkit outputs produced by bash and PowerShell scripts.
- PowerShell is installed on the Linux runner if missing; parity failure blocks the PR.

### Constraints
- CI must fail if PowerShell install fails.
- No CD or published-package validation in CI.

### Data Model Notes
- CI artifacts are ephemeral; no persistent data model is introduced.

---

## PDF Pipeline Architecture (E4-07a)

### Overview

For detailed step-by-step specifications, see `specs/004-pdf-research/pdf-conversion-architecture.md`. This document summarizes the canonical decisions and highlights cross-cutting rules.

The PDF-to-Markdown conversion pipeline consists of **11 phases (0-10)** with **70 total steps**, categorized by execution type:

| Category | Count | Description |
|----------|-------|-------------|
| **Code** | 49 | Deterministic automation via Python/PyMuPDF |
| **Agent** | 15 | Judgment calls requiring AI analysis |
| **User** | 5 | Confirmation steps requiring human decision |

### Design Principles

1. **Category Pyramid**: Maximize Code (reliable automation), then Agent (judgment calls), then User (only when needed)
2. **Generate Early, Confirm Late**: Create artifacts (JSON, detection data) early in the pipeline; defer user review until all analysis is complete
3. **Primary Audience: The Agent**: Prefer consistency over aesthetics for AI consumption
4. **Font Signature Preservation**: Use markers to track font information through the pipeline: `«sig001:The Homebrewery V3»`

### Operational Patterns

#### Error Conditions (Selected)

| Phase | Condition | Message | Action |
|-------|-----------|---------|--------|
| 0 | PDF file missing/unreadable | `ERROR: Cannot open PDF - file not found or corrupted` | Verify path and PDF integrity |
| 0 | Scanned PDF (low extractable text) | `ERROR: Scanned PDF detected - very little extractable text` | Run external OCR (out of scope) |
| 0 | User cancels | `ABORT: User cancelled after pre-flight report` | No action |
| 3 | No TOC found | `WARNING: No TOC found - hierarchy may be incomplete` | Continue with font-based detection |
| 4 | No text extracted | `ERROR: No text extracted from PDF` | Verify PDF has selectable text |
| 5-6 | Missing phase input | `ERROR: Phase input file not found - run previous phase first` | Resume from prior phase |
| 7 | Font mapping missing/invalid | `ERROR: font-family-mapping.json not found or malformed` | Re-run Phase 3 |
| 8 | No heading sources | `WARNING: No heading sources available - flat document structure` | Continue without hierarchy |
| 9 | Lint violations exceed threshold | `WARNING: Many lint violations - document may need significant cleanup` | User reviews issues |
| 10 | Diagnostic bundle fails | `WARNING: Failed to create zip bundle - files saved individually` | Check disk space |

#### Retry Logic (Agent Steps)

- Max attempts: 3 per Agent step
- Validation: output must pass step contract before acceptance
- On failure: log error, then skip or halt based on criticality

Criticality guidance:
- High: halt and require user input
- Medium: flag for user and continue
- Low: skip with warning

#### User Interaction Format (Summary)

User prompts use fixed-width, plain-text layouts with lettered choices for broad CLI compatibility. Step-specific templates exist for:
- 0.6 pre-flight confirmation
- 7.10 label review
- 9.9 header/footer review
- 9.10–9.11 final issue review

### Phase Summary

| Phase | Name | Key Output | Primary Function |
|-------|------|------------|------------------|
| 0 | Pre-flight Analysis | metadata.json | PDF validation, complexity assessment |
| 1 | Image Extraction | images/, image-manifest.json | Extract images with position tracking |
| 2 | Image Removal | preprocessed/*-no-images.pdf | Create text-only PDF for processing |
| 3 | TOC & Font Extraction | toc-extracted.txt, font-family-mapping.json | Extract TOC, sample fonts, detect patterns |
| 4 | Text Extraction | *-phase4.md | Extract text with font signature markers |
| 5 | Character-Level Fixes | *-phase5.md | Clean artifacts, remove icons/footers |
| 6 | Structural Formatting | *-phase6.md | Fix hyphenation, normalize lists |
| 7 | Font Label Assignment | Updated font-family-mapping.json | Detect headings, callouts, structure |
| 8 | Heading Insertion | *-phase8.md | Apply markdown formatting based on labels |
| 9 | Lint & Final Review | (quality report) | Markdown linting via pymarkdownlnt |
| 10 | Report Generation | conversion-report.md | Generate conversion summary |

### Core Components

#### 1. Phase System

All phases implement the `Phase` abstract base class:

```python
class Phase(ABC):
    @property
    @abstractmethod
    def phase_num(self) -> int: ...

    @property
    def has_agent_steps(self) -> bool: ...

    @property
    def has_user_steps(self) -> bool: ...

    @abstractmethod
    def execute(self, state: ConversionState) -> PhaseResult: ...
```

**PhaseResult** tracks:
- Phase number and name
- Status (SUCCESS, WARNING, ERROR, SKIPPED)
- Step-by-step results
- Output file paths
- Warnings and errors

#### 2. Font Signature System

**Problem**: PDF text extraction loses font information needed for structure detection.

**Solution**: Wrap text spans with font signature markers during Phase 4:

```
«sig001:The Homebrewery V3»
«sig002:A Web-based tool for making D&D...»
«sig003:Introduction»
```

**Marker Format**: `«{signature_id}:{text_content}»`

**Signature ID Generation** (Phase 3):
- Based on font family + size + weight + style
- Assigned sequential IDs: sig001, sig002, sig003...
- Stored in `font-family-mapping.json`

**Marker Flow**:
1. **Phase 3**: Assign signature IDs to font combinations
2. **Phase 4**: Wrap extracted text with markers
3. **Phase 5**: Clean artifacts while preserving markers
4. **Phase 7**: Analyze markers to detect headings, callouts
5. **Phase 8**: Replace markers with markdown formatting

#### 3. State Management

**ConversionState** (`.state.json`) persists:
- Source PDF path
- Output directory
- Current phase/step
- Completed phases
- Phase results
- Error information
- Configuration options

**Atomic Writes**: State uses temp file + rename for crash safety

**File Locking**: Prevents concurrent access during resume operations

**Resume Capability**: Pipeline can resume from any completed phase

#### 4. Configuration Files

**callout_config.json**: Defines GM callout boundaries by start/end text fragments
```json
[
  {
    "start_text": "Read Aloud:",
    "end_text": "End Read Aloud",
    "label": "callout_read_aloud"
  }
]
```

**font-family-mapping.json**: Maps signatures to labels
```json
{
  "signatures": [
    {
      "id": "sig001",
      "font_name": "Times-Bold",
      "size": 18,
      "label": "H1",
      "samples": ["The Homebrewery V3"]
    }
  ]
}
```

**footer_config.json**: Detected footer/watermark signatures
**icon_config.json**: Detected icon font signatures

### Data Flow

```
PDF Input
    ↓
Phase 0: Pre-flight (validate, analyze)
    ↓
Phase 1-2: Image handling (extract, remove)
    ↓
Phase 3: TOC & Font Extraction
    → toc-extracted.txt
    → font-family-mapping.json
    ↓
Phase 4: Text Extraction with markers
    → *-phase4.md (with «sigXXX:text» markers)
    ↓
Phase 5-6: Cleanup & Formatting
    → *-phase6.md (cleaned, markers preserved)
    ↓
Phase 7: Structural Detection
    → Updated font-family-mapping.json (with labels)
    ↓
Phase 8: Markdown Generation
    → *-phase8.md (final markdown)
    ↓
Phase 9: Quality Review
    ↓
Phase 10: Report
    → conversion-report.md
```

### Error Handling

**Exit Codes** (src/gm_kit/pdf_convert/errors.py):
- 0: Success
- 1: General error
- 2: Invalid arguments
- 3: File not found
- 4: Permission denied
- 5: Scanned PDF (needs OCR)
- 6: Resume failed
- 10+: Phase-specific errors

**Recovery Strategies**:
1. **Resume**: `--resume <dir>` continues from last successful phase
2. **Retry**: `--from-step <step>` re-runs specific step
3. **Skip**: Non-critical steps can be skipped on failure

**State Recovery**: On error, state file records:
- Failed phase/step
- Error code and message
- Whether error is recoverable
- Suggested user action

### Key Design Decisions

#### 1. Font Signature Markers
**Decision**: Use guillemet markers (`«»`) to preserve font info
**Rationale**:
- Unlikely to conflict with PDF content
- Can escape actual guillemets: `\«`, `\»`
- Human-readable for debugging
- Machine-parseable for automation

#### 2. PyMuPDF (fitz) as PDF Engine
**Decision**: Use PyMuPDF for all PDF operations
**Rationale**:
- Pure Python bindings (no external dependencies)
- Fast C++ backend
- Good text extraction quality
- Supports TOC, images, metadata

#### 3. Three-Step Category System
**Decision**: Categorize all 70 steps as Code, Agent, or User
**Rationale**:
- Maximizes automation where deterministic
- Reserves agent judgment for ambiguous cases
- Minimizes user involvement to only necessary decisions

#### 4. JSON-Based Configuration
**Decision**: Use JSON for all configuration artifacts
**Rationale**:
- Human-readable for debugging
- Machine-parseable for automation
- Version-control friendly
- Can be edited by users if needed

#### 5. Ruff for Complexity Tracking
**Decision**: Use Ruff's mccabe plugin (C90) for cyclomatic complexity
**Rationale**:
- Already integrated in lint workflow
- Supports `# noqa: C901` for exceptions
- Unified toolchain (no separate radon dependency)

### Data Models

#### ConversionState Schema
```python
@dataclass
class ConversionState:
    version: str = "1.0"  # Schema version
    pdf_path: str  # Absolute path to source
    output_dir: str  # Absolute path to output
    started_at: str  # ISO8601 timestamp
    updated_at: str  # ISO8601 timestamp
    current_phase: int  # 0-10
    current_step: str  # e.g., "5.3"
    completed_phases: list[int]
    phase_results: list[dict]
    status: ConversionStatus
    error: ErrorInfo | None
    diagnostics_enabled: bool
    config: dict
```

#### PhaseResult Schema
```python
@dataclass
class PhaseResult:
    phase_num: int
    name: str
    status: PhaseStatus
    started_at: str
    completed_at: str
    steps: list[StepResult]
    output_file: str | None
    warnings: list[str]
    errors: list[str]
```

#### StepResult Schema
```python
@dataclass
class StepResult:
    step_id: str  # e.g., "3.1"
    description: str
    status: PhaseStatus
    duration_ms: int
    output_file: str | None
    message: str | None
```

### Testing Strategy

**Unit Tests**: Each phase tested in isolation with mocked dependencies
**Integration Tests**: Full pipeline runs on sample PDFs
**Parity Tests**: Bash vs PowerShell script output comparison
**Regression Rule**: Any integration anomaly that requires a code change must add a unit test covering the anomaly.

**Coverage Requirements**:
- All Code-category steps must have unit tests
- Agent steps tested via contract/rubric validation
- User steps mocked in CI

---

## Implementation Notes

### Complexity Management

**Current High-Complexity Functions** (marked with `# noqa: C901`):
- `phase3.py:execute()` - 31 complexity
- `phase3.py:_analyze_footer_watermarks()` - 33 complexity
- `phase5.py:execute()` - 65 complexity
- `phase7.py:execute()` - 82 complexity
- `phase4.py:execute()` - 38 complexity

**Mitigation**: These are intentionally complex orchestration functions. Extract step methods where practical.

### Future Enhancements

1. **Multimodal Table Detection**: Use image-based OCR for complex tables
2. **Agent Step Implementation**: Enable AI judgment for steps 3.2, 4.6, etc.
3. **User Interaction**: Implement confirmation prompts for user steps
4. **Performance**: Parallelize independent phases (1 & 2)
5. **Auto-fix**: Integrate pymarkdownlnt --fix capability

---

## Label Inference Logic (Step 3.6)

Core rules:
- Single H1 rule: exactly one H1 (document title). TOC level 1 starts at H2.
- TOC matching: match TOC entries to font signatures (family + size + weight + style).
- Multi-span TOC: merge adjacent spans with identical font signature before matching.
- Fallbacks: largest fonts map to H2/H3; most frequent font maps to body; monospace maps to code; ALL CAPS or Title Case headings map by relative size.

## Feature Split (E4-07)

| Feature | Scope | Notes |
|---------|-------|-------|
| E4-07a | Code steps | Deterministic pipeline and outputs |
| E4-07b | Agent steps | Prompts + validation for judgment calls |
| E4-07c | User steps | Interactive confirmation workflows |
| E4-07d | Image link injection | Manifest + commented links |
| E4-07e | Orchestration | CLI, state, resume/retry, phase wiring |

## Key Decisions (Pipeline)

- Pre-flight analysis gates the pipeline.
- Step order constraints: 5.2 before 5.3; 7.9 before 7.10; 8.1 before 8.2.
- Two-column heuristic removed; use spatial x-coordinate analysis if needed.
- pymarkdownlnt is the linting tool for Phase 9.
- Single H1 rule enforced; TOC level 1 maps to H2.

---

*Last Updated: 2026-02-10*
*Status: E4-07a (Code-driven pipeline) complete, E4-07b (Agent steps) pending*
