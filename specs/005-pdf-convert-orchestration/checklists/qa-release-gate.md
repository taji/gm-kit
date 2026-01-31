# QA Release Gate Checklist: PDF to Markdown Command Orchestration

**Purpose**: Formal release gate validation - "Unit Tests for Requirements" to ensure acceptance criteria are testable and complete
**Created**: 2026-01-29
**Feature**: [spec.md](../spec.md)
**Audience**: QA / Test Design
**Depth**: Comprehensive (Formal Release Gate)

---

## CLI Interface & Arguments

### Requirement Completeness

- [ ] CHK001 - Are all CLI flags documented with their expected argument types and defaults? [Completeness, Spec §FR-004 to FR-010]
- [ ] CHK002 - Is the behavior specified when mutually exclusive flags are provided together (e.g., `--resume` with `--phase`)? [Gap, Edge Case]
- [ ] CHK003 - Are help text requirements specified for the `--help` flag output? [Gap]
- [ ] CHK004 - Is the behavior defined when `--output` directory path contains spaces or special characters? [Gap, Edge Case]
- [ ] CHK005 - Are requirements specified for handling relative vs absolute paths in `<pdf-path>` and `--output`? [Gap]
- [ ] CHK006 - Is the behavior defined when `--phase N` receives an invalid phase number (e.g., 11, -1, "abc")? [Gap, Edge Case]
- [ ] CHK007 - Is the behavior defined when `--from-step N.N` receives an invalid step format (e.g., "5", "5.3.1", "abc")? [Gap, Edge Case]

### Requirement Clarity

- [ ] CHK008 - Is "full pipeline execution" in FR-005 quantified with specific phases/steps that run? [Clarity, Spec §FR-005]
- [ ] CHK009 - Can "user is warned and prompted to confirm overwrite" be objectively tested? [Measurability, User Story 2 Scenario 3]
- [ ] CHK010 - Is the exact warning message format specified for existing `.state.json` detection? [Clarity, User Story 2 Scenario 3]
- [ ] CHK011 - Is the exact output format of `--status` specified (JSON, table, prose)? [Clarity, Spec §FR-009]

### Acceptance Criteria Quality

- [ ] CHK012 - Can "CLI is invoked with the PDF path" be objectively verified in automated tests? [Measurability, User Story 1 Scenario 1]
- [ ] CHK013 - Is "working directory is created" specific about expected folder structure? [Clarity, User Story 1 Scenario 1]
- [ ] CHK014 - Are timing expectations for "pre-flight analysis begins" testable? [Measurability, User Story 2 Scenario 1]

---

## State Management & Resume

### Requirement Completeness

- [ ] CHK015 - Are all fields required in `.state.json` documented with types and constraints? [Completeness, Spec §FR-017, FR-018]
- [ ] CHK016 - Is the state file schema version migration strategy defined for future changes? [Gap]
- [ ] CHK017 - Is the behavior specified when `.state.json` has an unknown/future schema version? [Gap, Edge Case]
- [ ] CHK018 - Is the atomic write requirement specified to prevent corruption on interruption? [Gap, Reliability]
- [ ] CHK019 - Are file locking requirements specified for concurrent access attempts? [Gap, Edge Case]
- [ ] CHK020 - Is the behavior defined when state file indicates "in_progress" but process is no longer running? [Gap, Recovery Flow]
- [ ] CHK021 - Are timestamp format requirements (ISO8601) explicitly specified in FR-018? [Clarity, Spec §FR-018]

### Requirement Clarity

- [ ] CHK022 - Is "validate state file integrity" in FR-020 quantified with specific validation rules? [Clarity, Spec §FR-020]
- [ ] CHK023 - Is "corrupted" state file defined with detectable corruption patterns? [Clarity, User Story 3 Scenario 3]
- [ ] CHK024 - Can "state file accurately reflects conversion progress" be objectively measured? [Measurability, Spec §SC-005]
- [ ] CHK025 - Is "updated after each step completion" specific about synchronous vs asynchronous writes? [Clarity, Spec §FR-019]

### Scenario Coverage

- [ ] CHK026 - Are requirements defined for resume when last completed phase output file is missing? [Gap, Exception Flow]
- [ ] CHK027 - Are requirements defined for resume when disk space is exhausted mid-conversion? [Gap, Exception Flow]
- [ ] CHK028 - Are requirements defined for state transitions (in_progress → completed, in_progress → failed)? [Gap, State Machine]
- [ ] CHK029 - Is recovery behavior specified when resume fails partway through a phase? [Gap, Recovery Flow]

---

## Pre-flight Analysis

### Requirement Completeness

- [ ] CHK030 - Are all metadata fields to extract specified with their data types? [Completeness, Spec §FR-011]
- [ ] CHK031 - Is the behavior defined when PDF metadata fields are empty or malformed? [Gap, Edge Case]
- [ ] CHK032 - Is the "<100 extractable characters" threshold explicitly documented in spec? [Clarity, Spec §FR-014]
- [ ] CHK033 - Are complexity thresholds (low/moderate/high) quantified with specific criteria? [Gap, Spec §FR-015]
- [ ] CHK034 - Is font family counting method specified (unique names, unique name+size, etc.)? [Clarity, Spec §FR-015]
- [ ] CHK035 - Is the `metadata.json` schema specified with required vs optional fields? [Completeness, Spec §FR-016]

### Requirement Clarity

- [ ] CHK036 - Can "detect embedded TOC presence" result be objectively tested (true/false, count)? [Measurability, Spec §FR-013]
- [ ] CHK037 - Is "estimate complexity" specific about the algorithm/heuristics used? [Clarity, Spec §FR-015]
- [ ] CHK038 - Is the pre-flight report output format specified (rich terminal, JSON, both)? [Gap]

### Acceptance Criteria Quality

- [ ] CHK039 - Can "within 10 seconds for PDFs under 50 pages" be automated in CI without flakiness? [Measurability, Spec §SC-001]
- [ ] CHK040 - Are test PDF characteristics specified (page count, image count, complexity) for SC-001 validation? [Gap, Test Data]
- [ ] CHK041 - Is "displays file metrics, complexity assessment, and user involvement notice" specific about exact content? [Clarity, User Story 1 Scenario 2]

---

## Error Handling

### Requirement Completeness

- [ ] CHK042 - Are all error conditions from architecture document mapped to specific error messages? [Completeness, Spec §FR-029 to FR-031]
- [ ] CHK043 - Is exit code behavior specified for each error type (e.g., 1 for user abort, 2 for file not found)? [Gap]
- [ ] CHK044 - Are error message requirements specified for stderr vs stdout routing? [Gap]
- [ ] CHK045 - Is the behavior defined for permission denied errors on PDF read? [Gap, Edge Case]
- [ ] CHK046 - Is the behavior defined for encrypted/password-protected PDFs? [Gap, Edge Case]
- [ ] CHK047 - Are requirements specified for partial failure cleanup (what gets deleted on abort)? [Gap, Recovery Flow]

### Requirement Clarity

- [ ] CHK048 - Is "actionable error messages" quantified with specific content requirements? [Clarity, Spec §SC-004]
- [ ] CHK049 - Can "100% of error conditions produce actionable error messages" be verified without exhaustive manual testing? [Measurability, Spec §SC-004]
- [ ] CHK050 - Is "not stack traces" specific about what should be shown instead (error code, help URL, etc.)? [Clarity, Spec §SC-004]

### Scenario Coverage

- [ ] CHK051 - Are requirements defined for handling keyboard interrupt (Ctrl+C) during conversion? [Gap, Exception Flow]
- [ ] CHK052 - Are requirements defined for SIGTERM/SIGKILL signal handling? [Gap, Exception Flow]
- [ ] CHK053 - Are requirements defined for graceful degradation when PyMuPDF fails to load? [Gap, Dependency Failure]

---

## Integration Contracts (E4-07a/b/c/d)

### Requirement Completeness

- [ ] CHK054 - Is the Phase interface contract testable without real E4-07a/b/c/d implementations? [Completeness, Contract]
- [ ] CHK055 - Are mock behavior requirements specified for each phase (what mocks return)? [Gap, Test Design]
- [ ] CHK056 - Is the boundary between orchestrator and phase implementation clearly defined? [Clarity, Contract]
- [ ] CHK057 - Are phase registration requirements specified (how phases are discovered/loaded)? [Clarity, Contract §1]
- [ ] CHK058 - Is the UserInteraction interface contract testable with pexpect mocks? [Completeness, Contract §5]

### Requirement Clarity

- [ ] CHK059 - Is "calling into E4-07a/b/c/d components" specific about invocation mechanism? [Clarity, Spec §FR-024]
- [ ] CHK060 - Can PhaseResult status enum values be mapped to specific CLI exit behaviors? [Measurability, Contract]
- [ ] CHK061 - Is step-level resume contract clear about which phases support it vs which don't? [Clarity, Contract §2]

### Scenario Coverage

- [ ] CHK062 - Are requirements defined for when a mock phase unexpectedly returns ERROR status? [Gap, Exception Flow]
- [ ] CHK063 - Are requirements defined for timeout behavior when a phase hangs? [Gap, Non-Functional]
- [ ] CHK064 - Are requirements specified for phase output file naming when filename contains special characters? [Gap, Edge Case]

---

## Cross-Platform Parity

### Requirement Completeness

- [ ] CHK065 - Are Bash script requirements specified with minimum bash version? [Gap, Spec §FR-022]
- [ ] CHK066 - Are PowerShell script requirements specified with minimum PS version? [Gap, Spec §FR-023]
- [ ] CHK067 - Is path separator handling specified (forward slash vs backslash)? [Gap]
- [ ] CHK068 - Are line ending requirements specified for generated scripts (LF vs CRLF)? [Gap]
- [ ] CHK069 - Is parity testing requirement specified between bash and PowerShell outputs? [Gap, Test Design]

### Requirement Clarity

- [ ] CHK070 - Can "generate Bash script template" be verified with specific expected content? [Measurability, Spec §FR-022]
- [ ] CHK071 - Is "folder setup" specific about which folders are created and their permissions? [Clarity, Spec §FR-021]

### Scenario Coverage

- [ ] CHK072 - Are requirements defined for WSL (Windows Subsystem for Linux) behavior? [Gap, Edge Case]
- [ ] CHK073 - Are requirements defined for macOS vs Linux behavioral differences? [Gap, Edge Case]

---

## Slash Command (Agent Integration)

### Requirement Completeness

- [ ] CHK074 - Are prompt file content requirements specified for all 4 supported agents? [Completeness, Spec §FR-001, FR-002]
- [ ] CHK075 - Is the prompt file installation path specified for each agent type? [Completeness, Spec §FR-002]
- [ ] CHK076 - Is argument parsing/passthrough behavior specified for quoted paths with spaces? [Gap, Edge Case]
- [ ] CHK077 - Are requirements specified for what happens if `gmkit init` hasn't been run? [Gap, Exception Flow]

### Requirement Clarity

- [ ] CHK078 - Can "works identically across all supported agents" be objectively tested? [Measurability, Spec §SC-006]
- [ ] CHK079 - Is "identical" specific about which behaviors must match (output format, timing, errors)? [Clarity, Spec §SC-006]
- [ ] CHK080 - Is the prompt file format specified (markdown structure, required sections)? [Gap]

### Scenario Coverage

- [ ] CHK081 - Are requirements defined for agent-specific error handling differences? [Gap, Edge Case]
- [ ] CHK082 - Are requirements defined for when agent cannot execute CLI (permissions, path issues)? [Gap, Exception Flow]

---

## Diagnostic Bundle

### Requirement Completeness

- [ ] CHK083 - Is the diagnostic bundle contents specified (which files, folder structure)? [Completeness, Spec §FR-010]
- [ ] CHK084 - Is the zip file naming convention specified? [Gap]
- [ ] CHK085 - Is bundle creation timing specified (during conversion vs at end)? [Gap]
- [ ] CHK086 - Are requirements specified for bundle creation when disk space is low? [Gap, Edge Case]

### Requirement Clarity

- [ ] CHK087 - Can "containing phase-by-phase markdown iterations" be verified programmatically? [Measurability, User Story 2 Scenario 2]
- [ ] CHK088 - Is "original prompt for traceability" specific about which prompt (slash command args, CLI args)? [Clarity]

---

## Copyright Notice

### Requirement Completeness

- [ ] CHK089 - Is copyright notice template specified with exact markdown format? [Completeness, Spec §FR-032, FR-033]
- [ ] CHK090 - Are fallback values specified when metadata fields are empty? [Gap, Edge Case]
- [ ] CHK091 - Is notice insertion position specified (before H1, after H1, specific line)? [Clarity, Spec §FR-032]

### Requirement Clarity

- [ ] CHK092 - Can "using metadata from step 0.1" be verified by checking specific field mapping? [Measurability, Spec §FR-032]
- [ ] CHK093 - Is "tool attribution" specific about exact text to include? [Clarity, Spec §FR-033]

---

## Dependencies & Assumptions

### Documented Validation

- [ ] CHK094 - Is the E2-02 dependency version/interface specified for prompt installation? [Completeness, Dependency]
- [ ] CHK095 - Is the PyMuPDF minimum version requirement documented? [Gap, Dependency]
- [ ] CHK096 - Is the assumption "pexpect available for testing" validated for Windows CI? [Assumption]
- [ ] CHK097 - Are mock replacement criteria specified for when E4-07a/b/c/d are implemented? [Gap, Assumption]

---

## Non-Functional Requirements

### Performance

- [ ] CHK098 - Is the 10-second pre-flight target specified with test conditions (CPU, disk speed)? [Clarity, Spec §SC-001]
- [ ] CHK099 - Are memory usage requirements specified for large PDFs? [Gap, Non-Functional]
- [ ] CHK100 - Is the "~500 pages" limit in plan documented in spec as a testable constraint? [Gap, Plan vs Spec]

### Observability

- [ ] CHK101 - Are logging requirements specified (log levels, log format, log location)? [Gap, Non-Functional]
- [ ] CHK102 - Are progress indicator requirements specified during long-running phases? [Gap, UX]

### Reliability

- [ ] CHK103 - Is idempotency specified for re-running phases (same input → same output)? [Gap, Reliability]
- [ ] CHK104 - Are retry requirements specified for transient failures (file lock, etc.)? [Gap, Reliability]

---

## Traceability Summary

| Marker | Count | Meaning |
|--------|-------|---------|
| `[Spec §X]` | 42 | Requirement exists, checking quality |
| `[Gap]` | 52 | Requirement missing, needs addition |
| `[Clarity]` | 15 | Requirement exists but vague |
| `[Measurability]` | 12 | Acceptance criteria hard to test |
| `[Edge Case]` | 18 | Boundary condition not specified |
| `[Exception Flow]` | 9 | Error/recovery path missing |
| `[Non-Functional]` | 5 | NFR not specified |
| `[Contract]` | 6 | Interface boundary unclear |

---

## Notes

- This checklist validates **requirements quality**, not implementation correctness
- Items marked `[Gap]` indicate missing requirements that should be added to spec.md before implementation
- Items marked `[Clarity]` indicate requirements that need quantification for testability
- Run `/speckit.clarify` to address high-priority gaps before `/speckit.tasks`
- Consider splitting gaps by priority: P1 (blocks testing) vs P2 (nice-to-have)
