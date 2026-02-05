# QA Release Gate Checklist: PDF to Markdown Command Orchestration

**Purpose**: Formal release gate validation - "Unit Tests for Requirements" to ensure acceptance criteria are testable and complete
**Created**: 2026-01-29
**Feature**: [spec.md](../spec.md)
**Audience**: QA / Test Design
**Depth**: Comprehensive (Formal Release Gate)

---

## CLI Interface & Arguments

### Requirement Completeness

- [x] CHK001 - Are all CLI flags documented with their expected argument types and defaults? [Completeness, Spec §FR-004 to FR-010] ✓ CLI Argument Specification table added
- [x] CHK002 - Is the behavior specified when mutually exclusive flags are provided together (e.g., `--resume` with `--phase`)? [Gap, Edge Case] ✓ CLI Flag Constraints section added
- [x] CHK003 - Are help text requirements specified for the `--help` flag output? [Gap] ✓ Help Text Requirements section with example format
- [x] CHK004 - Is the behavior defined when `--output` directory path contains spaces or special characters? [Gap, Edge Case] ✓ Edge case added
- [x] CHK005 - Are requirements specified for handling relative vs absolute paths in `<pdf-path>` and `--output`? [Gap] ✓ Edge case added
- [x] CHK006 - Is the behavior defined when `--phase N` receives an invalid phase number (e.g., 11, -1, "abc")? [Gap, Edge Case] ✓ Edge case added
- [x] CHK007 - Is the behavior defined when `--from-step N.N` receives an invalid step format (e.g., "5", "5.3.1", "abc")? [Gap, Edge Case] ✓ Edge case added

### Requirement Clarity

- [x] CHK008 - Is "full pipeline execution" in FR-005 quantified with specific phases/steps that run? [Clarity, Spec §FR-005] ✓ FR-005 updated: "Phase 0 pre-flight through Phase 10, all 11 phases"
- [x] CHK009 - Can "user is warned and prompted to confirm overwrite" be objectively tested? [Measurability, User Story 2 Scenario 3] ✓ Exact prompt format specified
- [x] CHK010 - Is the exact warning message format specified for existing `.state.json` detection? [Clarity, User Story 2 Scenario 3] ✓ Exact message specified in US2 Scenario 3
- [x] CHK011 - Is the exact output format of `--status` specified (JSON, table, prose)? [Clarity, Spec §FR-009] ✓ FR-009a specifies table format with example

### Acceptance Criteria Quality

- [x] CHK012 - Can "CLI is invoked with the PDF path" be objectively verified in automated tests? [Measurability, User Story 1 Scenario 1] ✓ Testing note added to US1 Scenario 1
- [x] CHK013 - Is "working directory is created" specific about expected folder structure? [Clarity, User Story 1 Scenario 1] ✓ FR-021 specifies complete folder structure
- [x] CHK014 - Are timing expectations for "pre-flight analysis begins" testable? [Measurability, User Story 2 Scenario 1] ✓ SC-001 specifies 2s for 2-page PDF

---

## State Management & Resume

### Requirement Completeness

- [x] CHK015 - Are all fields required in `.state.json` documented with types and constraints? [Completeness, Spec §FR-017, FR-018] ✓ FR-018 refs contracts/state-schema.json; Integration Contracts section
- [x] CHK016 - Is the state file schema version migration strategy defined for future changes? [Gap] ✓ Edge case added: version field, migration strategy
- [x] CHK017 - Is the behavior specified when `.state.json` has an unknown/future schema version? [Gap, Edge Case] ✓ Edge case: error message for newer version
- [x] CHK018 - Is the atomic write requirement specified to prevent corruption on interruption? [Gap, Reliability] ✓ FR-019a specifies atomic writes (temp+rename)
- [x] CHK019 - Are file locking requirements specified for concurrent access attempts? [Gap, Edge Case] ✓ Edge case: exclusive lock, 5-second timeout
- [x] CHK020 - Is the behavior defined when state file indicates "in_progress" but process is no longer running? [Gap, Recovery Flow] ✓ Edge case: stale lock detection
- [x] CHK021 - Are timestamp format requirements (ISO8601) explicitly specified in FR-018? [Clarity, Spec §FR-018] ✓ FR-018 specifies ISO8601

### Requirement Clarity

- [x] CHK022 - Is "validate state file integrity" in FR-020 quantified with specific validation rules? [Clarity, Spec §FR-020] ✓ FR-020 lists 5 specific validation rules
- [x] CHK023 - Is "corrupted" state file defined with detectable corruption patterns? [Clarity, User Story 3 Scenario 3] ✓ US3 Scenario 3: "fails FR-020 validation"
- [x] CHK024 - Can "state file accurately reflects conversion progress" be objectively measured? [Measurability, Spec §SC-005] ✓ SC-005 specifies 3 measurable criteria
- [x] CHK025 - Is "updated after each step completion" specific about synchronous vs asynchronous writes? [Clarity, Spec §FR-019] ✓ FR-019 specifies synchronous writes

### Scenario Coverage

- [x] CHK026 - Are requirements defined for resume when last completed phase output file is missing? [Gap, Exception Flow] ✓ Edge case added with error message
- [x] CHK027 - Are requirements defined for resume when disk space is exhausted mid-conversion? [Gap, Exception Flow] ✓ Edge case added with error message
- [x] CHK028 - Are requirements defined for state transitions (in_progress → completed, in_progress → failed)? [Gap, State Machine] ✓ FR-019b specifies state machine
- [x] CHK029 - Is recovery behavior specified when resume fails partway through a phase? [Gap, Recovery Flow] ✓ Edge case added: state updated, retry from step

---

## Pre-flight Analysis

### Requirement Completeness

- [x] CHK030 - Are all metadata fields to extract specified with their data types? [Completeness, Spec §FR-011] ✓ FR-011 lists all fields with types
- [x] CHK031 - Is the behavior defined when PDF metadata fields are empty or malformed? [Gap, Edge Case] ✓ Edge case added: empty→"", malformed→null, invalid encoding→U+FFFD
- [x] CHK032 - Is the "<100 extractable characters" threshold explicitly documented in spec? [Clarity, Spec §FR-014] ✓ FR-014 specifies <100 chars
- [x] CHK033 - Are complexity thresholds (low/moderate/high) quantified with specific criteria? [Gap, Spec §FR-015] ✓ FR-015 specifies Low/Moderate/High thresholds
- [x] CHK034 - Is font family counting method specified (unique names, unique name+size, etc.)? [Clarity, Spec §FR-015] ✓ FR-015: base font name only, with note about variants
- [x] CHK035 - Is the `metadata.json` schema specified with required vs optional fields? [Completeness, Spec §FR-016] ✓ FR-016 specifies required/optional fields

### Requirement Clarity

- [x] CHK036 - Can "detect embedded TOC presence" result be objectively tested (true/false, count)? [Measurability, Spec §FR-013] ✓ FR-013: has_toc, toc_entries, toc_max_depth
- [x] CHK037 - Is "estimate complexity" specific about the algorithm/heuristics used? [Clarity, Spec §FR-015] ✓ FR-015 specifies criteria for low/moderate/high
- [x] CHK038 - Is the pre-flight report output format specified (rich terminal, JSON, both)? [Gap] ✓ FR-016a specifies exact terminal format with example

### Acceptance Criteria Quality

- [x] CHK039 - Can "within 10 seconds for PDFs under 50 pages" be automated in CI without flakiness? [Measurability, Spec §SC-001] ✓ SC-001 updated: 2s for 2-page PDF, ~0.2s/page, note about CI adjustment
- [x] CHK040 - Are test PDF characteristics specified (page count, image count, complexity) for SC-001 validation? [Gap, Test Data] ✓ Test Data section added with reference PDF specs
- [x] CHK041 - Is "displays file metrics, complexity assessment, and user involvement notice" specific about exact content? [Clarity, User Story 1 Scenario 2] ✓ FR-016a specifies exact content format

---

## Error Handling

### Requirement Completeness

- [x] CHK042 - Are all error conditions from architecture document mapped to specific error messages? [Completeness, Spec §FR-029 to FR-031] ✓ FR-029 through FR-041 specify all error messages
- [x] CHK043 - Is exit code behavior specified for each error type (e.g., 1 for user abort, 2 for file not found)? [Gap] ✓ FR-044 through FR-048a specify exit codes 0-5
- [x] CHK044 - Are error message requirements specified for stderr vs stdout routing? [Gap] ✓ FR-041a specifies ERROR/ABORT→stderr, WARNING→stdout
- [x] CHK045 - Is the behavior defined for permission denied errors on PDF read? [Gap, Edge Case] ✓ Edge case added: error message, exit code 2
- [x] CHK046 - Is the behavior defined for encrypted/password-protected PDFs? [Gap, Edge Case] ✓ Edge case added: error message, exit code 3
- [x] CHK047 - Are requirements specified for partial failure cleanup (what gets deleted on abort)? [Gap, Recovery Flow] ✓ Edge case: all files preserved, no auto-cleanup

### Requirement Clarity

- [x] CHK048 - Is "actionable error messages" quantified with specific content requirements? [Clarity, Spec §SC-004] ✓ FR-041b specifies required content
- [x] CHK049 - Can "100% of error conditions produce actionable error messages" be verified without exhaustive manual testing? [Measurability, Spec §SC-004] ✓ SC-004 specifies unit test verification method
- [x] CHK050 - Is "not stack traces" specific about what should be shown instead (error code, help URL, etc.)? [Clarity, Spec §SC-004] ✓ FR-041b specifies: type prefix, description, suggestion, context

### Scenario Coverage

- [x] CHK051 - Are requirements defined for handling keyboard interrupt (Ctrl+C) during conversion? [Gap, Exception Flow] ✓ Edge case: state preserved via synchronous writes
- [x] CHK052 - Are requirements defined for SIGTERM/SIGKILL signal handling? [Gap, Exception Flow] ✓ Edge case: combined into interruption handling (no special signal handling)
- [x] CHK053 - Are requirements defined for graceful degradation when PyMuPDF fails to load? [Gap, Dependency Failure] ✓ Edge case: error message, exit code 5

---

## Integration Contracts (E4-07a/b/c/d)

### Requirement Completeness

- [x] CHK054 - Is the Phase interface contract testable without real E4-07a/b/c/d implementations? [Completeness, Contract] ✓ Phase Interface section: execute() signature, PhaseResult
- [x] CHK055 - Are mock behavior requirements specified for each phase (what mocks return)? [Gap, Test Design] ✓ Mock Phase Behavior section specifies return values
- [x] CHK056 - Is the boundary between orchestrator and phase implementation clearly defined? [Clarity, Contract] ✓ Orchestrator Responsibilities vs Phase Responsibilities sections
- [x] CHK057 - Are phase registration requirements specified (how phases are discovered/loaded)? [Clarity, Contract §1] ✓ Phase Registration section: static list, module mapping
- [x] CHK058 - Is the UserInteraction interface contract testable with pexpect mocks? [Completeness, Contract §5] ✓ UserInteraction Interface section specifies testability

### Requirement Clarity

- [x] CHK059 - Is "calling into E4-07a/b/c/d components" specific about invocation mechanism? [Clarity, Spec §FR-024] ✓ Phase Interface: execute(state) method
- [x] CHK060 - Can PhaseResult status enum values be mapped to specific CLI exit behaviors? [Measurability, Contract] ✓ PhaseResult to Exit Code Mapping section
- [x] CHK061 - Is step-level resume contract clear about which phases support it vs which don't? [Clarity, Contract §2] ✓ Step-Level Resume Support: all phases support it

### Scenario Coverage

- [x] CHK062 - Are requirements defined for when a mock phase unexpectedly returns ERROR status? [Gap, Exception Flow] ✓ Mock Phase Behavior: orchestrator handles identically to real phase
- [x] CHK063 - Are requirements defined for timeout behavior when a phase hangs? [Gap, Non-Functional] ✓ Phase Timeout section: no timeout, user can Ctrl+C
- [x] CHK064 - Are requirements specified for phase output file naming when filename contains special characters? [Gap, Edge Case] ✓ Edge case: Windows-incompatible chars replaced with underscore

---

## Cross-Platform Parity

### Requirement Completeness

- [x] CHK065 - Are Bash script requirements specified with minimum bash version? [Gap, Spec §FR-022] ✓ N/A - FR-022 removed; Python handles folder creation directly
- [x] CHK066 - Are PowerShell script requirements specified with minimum PS version? [Gap, Spec §FR-023] ✓ N/A - FR-023 removed; Python handles folder creation directly
- [x] CHK067 - Is path separator handling specified (forward slash vs backslash)? [Gap] ✓ Edge case added: internal use /, user input accepts both, display uses native
- [x] CHK068 - Are line ending requirements specified for generated scripts (LF vs CRLF)? [Gap] ✓ Edge case added: .sh→LF, .ps1→CRLF, .md→LF, .json→LF
- [x] CHK069 - Is parity testing requirement specified between bash and PowerShell outputs? [Gap, Test Design] ✓ N/A - No bash/PS scripts; Python pathlib handles cross-platform

### Requirement Clarity

- [x] CHK070 - Can "generate Bash script template" be verified with specific expected content? [Measurability, Spec §FR-022] ✓ N/A - FR-022 removed from spec
- [x] CHK071 - Is "folder setup" specific about which folders are created and their permissions? [Clarity, Spec §FR-021] ✓ FR-021 specifies complete structure with permission notes

### Scenario Coverage

- [x] CHK072 - Are requirements defined for WSL (Windows Subsystem for Linux) behavior? [Gap, Edge Case] ✓ Edge case: WSL treated as Linux
- [x] CHK073 - Are requirements defined for macOS vs Linux behavioral differences? [Gap, Edge Case] ✓ Edge case: no functional differences

---

## Slash Command (Agent Integration)

### Requirement Completeness

- [x] CHK074 - Are prompt file content requirements specified for all 4 supported agents? [Completeness, Spec §FR-001, FR-002] ✓ FR-002a/b specifies content requirements
- [x] CHK075 - Is the prompt file installation path specified for each agent type? [Completeness, Spec §FR-002] ✓ FR-002 lists paths for Claude, Codex, Gemini, Qwen
- [x] CHK076 - Is argument parsing/passthrough behavior specified for quoted paths with spaces? [Gap, Edge Case] ✓ Edge case added: quoted paths, agent responsible for shell escaping
- [x] CHK077 - Are requirements specified for what happens if `gmkit init` hasn't been run? [Gap, Exception Flow] ✓ Edge case: slash command won't exist; CLI works without init

### Requirement Clarity

- [x] CHK078 - Can "works identically across all supported agents" be objectively tested? [Measurability, Spec §SC-006] ✓ SC-006 specifies verification methods
- [x] CHK079 - Is "identical" specific about which behaviors must match (output format, timing, errors)? [Clarity, Spec §SC-006] ✓ SC-006 specifies: same CLI command, same args, same output files
- [x] CHK080 - Is the prompt file format specified (markdown structure, required sections)? [Gap] ✓ FR-002b specifies markdown structure with sections

### Scenario Coverage

- [x] CHK081 - Are requirements defined for agent-specific error handling differences? [Gap, Edge Case] ✓ Edge case: CLI errors consistent, agents may display differently
- [x] CHK082 - Are requirements defined for when agent cannot execute CLI (permissions, path issues)? [Gap, Exception Flow] ✓ Edge case: agent reports shell error, prompt suggests verification

---

## Diagnostic Bundle

### Requirement Completeness

- [x] CHK083 - Is the diagnostic bundle contents specified (which files, folder structure)? [Completeness, Spec §FR-010] ✓ FR-010b specifies complete file list
- [x] CHK084 - Is the zip file naming convention specified? [Gap] ✓ FR-010c: diagnostic-bundle.zip
- [x] CHK085 - Is bundle creation timing specified (during conversion vs at end)? [Gap] ✓ FR-010d: created at end of Phase 10
- [x] CHK086 - Are requirements specified for bundle creation when disk space is low? [Gap, Edge Case] ✓ Edge case: warning, exit 0, files saved individually

### Requirement Clarity

- [x] CHK087 - Can "containing phase-by-phase markdown iterations" be verified programmatically? [Measurability, User Story 2 Scenario 2] ✓ FR-010b lists specific phase output files
- [x] CHK088 - Is "original prompt for traceability" specific about which prompt (slash command args, CLI args)? [Clarity] ✓ FR-010b: cli-args.txt contains CLI invocation arguments

---

## Copyright Notice

### Requirement Completeness

- [x] CHK089 - Is copyright notice template specified with exact markdown format? [Completeness, Spec §FR-032, FR-033] ✓ FR-050a specifies exact template
- [x] CHK090 - Are fallback values specified when metadata fields are empty? [Gap, Edge Case] ✓ FR-050a shows fallback values in template
- [x] CHK091 - Is notice insertion position specified (before H1, after H1, specific line)? [Clarity, Spec §FR-032] ✓ FR-049a: before H1, first content in file

### Requirement Clarity

- [x] CHK092 - Can "using metadata from step 0.1" be verified by checking specific field mapping? [Measurability, Spec §FR-032] ✓ FR-049/FR-050a show field mapping
- [x] CHK093 - Is "tool attribution" specific about exact text to include? [Clarity, Spec §FR-033] ✓ FR-050a: "Tool: GM-Kit pdf-convert"

---

## Dependencies & Assumptions

### Documented Validation

- [x] CHK094 - Is the E2-02 dependency version/interface specified for prompt installation? [Completeness, Dependency] ✓ Assumptions section covers E2-02, forward-compatible
- [x] CHK095 - Is the PyMuPDF minimum version requirement documented? [Gap, Dependency] ✓ Assumptions: PyMuPDF (fitz) >= 1.23.0
- [x] CHK096 - Is the assumption "pexpect available for testing" validated for Windows CI? [Assumption] ✓ Assumptions: wexpect on Windows, pytest.mark.skipif
- [x] CHK097 - Are mock replacement criteria specified for when E4-07a/b/c/d are implemented? [Gap, Assumption] ✓ Assumptions: 3 criteria for mock replacement

---

## Non-Functional Requirements

### Performance

- [x] CHK098 - Is the 10-second pre-flight target specified with test conditions (CPU, disk speed)? [Clarity, Spec §SC-001] ✓ SC-001: 2s for 2-page PDF, note about CI adjustment
- [x] CHK099 - Are memory usage requirements specified for large PDFs? [Gap, Non-Functional] ✓ Assumptions: <2GB RAM for 500 pages
- [x] CHK100 - Is the "~500 pages" limit in plan documented in spec as a testable constraint? [Gap, Plan vs Spec] ✓ Assumptions: 500 pages mentioned with memory note

### Observability

- [x] CHK101 - Are logging requirements specified (log levels, log format, log location)? [Gap, Non-Functional] ✓ Assumptions: Python logging, DEBUG/INFO/WARNING/ERROR, stderr
- [x] CHK102 - Are progress indicator requirements specified during long-running phases? [Gap, UX] ✓ Assumptions: Rich progress, format specified, TTY fallback

### Reliability

- [x] CHK103 - Is idempotency specified for re-running phases (same input → same output)? [Gap, Reliability] ✓ Assumptions: Code phases deterministic, Agent phases non-deterministic
- [x] CHK104 - Are retry requirements specified for transient failures (file lock, etc.)? [Gap, Reliability] ✓ Assumptions: file lock 3x retry, disk I/O no retry

---

## Traceability Summary

| Marker | Original | Resolved | Resolution |
|--------|----------|----------|------------|
| `[Spec §X]` | 42 | 42 | Requirements verified/enhanced |
| `[Gap]` | 52 | 52 | Added to spec.md |
| `[Clarity]` | 15 | 15 | Quantified in spec.md |
| `[Measurability]` | 12 | 12 | Made testable |
| `[Edge Case]` | 18 | 18 | Added to Edge Cases section |
| `[Exception Flow]` | 9 | 9 | Added to spec.md |
| `[Non-Functional]` | 5 | 5 | Added to Assumptions |
| `[Contract]` | 6 | 6 | Added to Integration Contracts |

**Status**: ✓ ALL 104 ITEMS RESOLVED (2026-01-31)

---

## Notes

- This checklist validates **requirements quality**, not implementation correctness
- All gaps were addressed by updating spec.md during QA review session
- Items marked N/A were for FR-022/FR-023 (bash/PS scripts) which were removed from spec
- Ready for `/speckit.implement`
