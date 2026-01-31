# Feature Specification: PDF to Markdown Command Orchestration

**Feature Branch**: `005-pdf-convert-orchestration`
**Created**: 2026-01-29
**Status**: Draft
**Input**: User description: "E4-07e from BACKLOG.md - Implement the `/gmkit.pdf-to-markdown` slash command and `gmkit pdf-convert` CLI that orchestrates the entire PDF conversion pipeline"

**Architecture Reference**: `specs/004-pdf-research/pdf-conversion-architecture.md` (v10)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Convert PDF via Slash Command (Priority: P1)

A game master wants to convert a PDF rulebook to Markdown for easier reference during sessions. They open their AI coding agent (Claude, Codex, Gemini, or Qwen) in their project folder and invoke the `/gmkit.pdf-to-markdown` slash command with the path to their PDF file.

**Why this priority**: This is the primary entry point for the feature. The slash command is how most users will interact with the conversion pipeline through their preferred AI agent.

**Independent Test**: Can be fully tested by invoking the slash command with a test PDF and verifying the CLI is called with correct arguments and the conversion process initiates.

**Acceptance Scenarios**:

1. **Given** a project initialized with `gmkit init`, **When** user invokes `/gmkit.pdf-to-markdown "path/to/module.pdf"`, **Then** the prompt file instructs the agent to execute `gmkit pdf-convert "path/to/module.pdf"` and the output directory is created with a `.state.json` file.

   *Testing note: Slash command invocation is verified through manual/exploratory testing. Automated tests verify: (1) prompt file installation, (2) prompt file content contains correct CLI syntax, (3) CLI execution via pexpect.*

2. **Given** a valid PDF path, **When** the slash command is invoked, **Then** the pre-flight analysis runs and displays file metrics, complexity assessment, and user involvement notice.

3. **Given** a PDF that cannot be found, **When** the slash command is invoked, **Then** an actionable error message is displayed: "ERROR: Cannot open PDF - file not found or corrupted".

---

### User Story 2 - Convert PDF via CLI (Priority: P1)

A user wants to convert a PDF directly from the terminal without using an AI agent. They run `gmkit pdf-convert <pdf-path> --output <dir>` to start the conversion.

**Why this priority**: The CLI is the underlying mechanism that powers the slash command and provides direct access for automation, scripting, and advanced users.

**Independent Test**: Can be fully tested by running the CLI with a test PDF and verifying output folder structure and state file creation.

**Acceptance Scenarios**:

1. **Given** a valid PDF path and output directory, **When** `gmkit pdf-convert module.pdf --output ./converted/` is run, **Then** the working folder structure is created and pre-flight analysis completes, displaying the pre-flight report (per SC-001: within 2 seconds for 2-page reference PDF).

2. **Given** the `--diagnostics` flag is provided, **When** conversion completes, **Then** a diagnostic bundle (zip) is created containing phase-by-phase markdown iterations.

3. **Given** an output directory that already exists with a `.state.json`, **When** CLI is run without `--resume`, **Then** CLI displays "WARNING: Existing conversion found in <dir>. Last activity: <timestamp>." followed by prompt "Options: [O]verwrite and start fresh, [R]esume from checkpoint, [A]bort? " and waits for user input.

---

### User Story 3 - Resume Interrupted Conversion (Priority: P2)

A user's conversion was interrupted (closed terminal, network issue, etc.) and they want to resume from where it left off rather than starting over.

**Why this priority**: Long PDFs may take significant time to convert. Resume capability prevents wasted effort and improves user experience.

**Independent Test**: Can be tested by running a conversion, simulating interruption at a specific phase, then verifying `--resume` continues from the checkpoint.

**Acceptance Scenarios**:

1. **Given** a conversion that completed Phase 3 before interruption, **When** user runs `gmkit pdf-convert --resume ./converted/`, **Then** conversion resumes from Phase 4.

2. **Given** a `.state.json` file exists with phase progress, **When** `--resume` is used, **Then** the system reads the state and skips completed phases.

3. **Given** a corrupted (fails FR-020 validation) or missing `.state.json`, **When** `--resume` is attempted, **Then** CLI displays "ERROR: Cannot resume - state file missing or corrupt. Use 'gmkit pdf-convert <pdf-path>' to start fresh."

---

### User Story 4 - Re-run Specific Phase or Step (Priority: P2)

A user notices an issue with a specific phase's output and wants to re-run just that phase (or from a specific step) without restarting the entire conversion.

**Why this priority**: Allows targeted fixes without re-processing the entire document, especially valuable when debugging or refining output.

**Independent Test**: Can be tested by completing a conversion, modifying intermediate output, then verifying `--phase N` or `--from-step N.N` re-processes only the specified portion.

**Acceptance Scenarios**:

1. **Given** a completed conversion, **When** user runs `gmkit pdf-convert --phase 5 ./converted/`, **Then** only Phase 5 (Character-Level Fixes) is re-run using existing Phase 4 output.

2. **Given** a completed conversion, **When** user runs `gmkit pdf-convert --from-step 5.3 ./converted/`, **Then** Phase 5 resumes from step 5.3 (Normalize line breaks) onward.

3. **Given** a phase number higher than the last completed phase, **When** `--phase N` is used, **Then** an error indicates the prerequisite phases haven't completed.

---

### User Story 5 - Check Conversion Status (Priority: P3)

A user wants to check the progress of an in-progress or completed conversion without running any additional processing.

**Why this priority**: Provides visibility into conversion state, useful for monitoring long-running conversions or understanding where a previous conversion stopped.

**Independent Test**: Can be tested by creating a `.state.json` at various stages and verifying `--status` output accurately reflects the state.

**Acceptance Scenarios**:

1. **Given** an in-progress conversion at Phase 6, **When** user runs `gmkit pdf-convert --status ./converted/`, **Then** a summary shows completed phases (1-5), current phase (6), and pending phases (7-10).

2. **Given** a completed conversion, **When** `--status` is run, **Then** summary shows all phases complete with final quality rating and any flagged issues.

3. **Given** no `.state.json` exists in the directory, **When** `--status` is run, **Then** message indicates no conversion in progress.

---

### Edge Cases

- What happens when the PDF is a scanned document with no extractable text?
  - Pre-flight detects <100 characters extracted, displays "ERROR: Scanned PDF detected - very little extractable text" with recommendation to use external OCR.

- What happens when the PDF file is very large (>50MB)?
  - Pre-flight warns "Very large file - may require extended processing" but proceeds if user confirms.

- What happens when output directory has insufficient permissions?
  - Phase 1 fails with "ERROR: Cannot create output directory - check permissions".

- What happens when conversion is interrupted during an Agent step?
  - State tracks step-level progress; resume continues from the failed step with retry logic.

- What happens when a phase depends on output from a skipped phase?
  - Error message indicates "Phase input file not found - run previous phase first" with suggestion to use `--from-step`.

- What happens when paths contain spaces or special characters?
  - CLI MUST accept paths with spaces when properly quoted (e.g., `"My Documents/rulebook.pdf"`).
  - CLI MUST handle Unicode characters in paths on systems that support them.
  - Generated shell scripts MUST properly escape paths in variable assignments.

- What happens with relative vs absolute paths?
  - CLI MUST accept both relative and absolute paths for `<pdf-path>` and `--output`.
  - Relative paths MUST be resolved relative to current working directory at invocation time.
  - State file (`.state.json`) MUST store absolute paths to ensure resume works from any directory.

- What happens when `--phase` receives an invalid value?
  - Non-integer values (e.g., "abc", "5.5"): Display "ERROR: --phase requires an integer between 0 and 10".
  - Out-of-range integers (e.g., -1, 11): Display "ERROR: Phase number must be between 0 and 10, got: N".
  - CLI MUST exit with non-zero status code on validation errors.

- What happens when `--from-step` receives an invalid format?
  - Invalid format (e.g., "5", "5.3.1", "abc"): Display "ERROR: --from-step requires format N.N (e.g., 5.3), got: X".
  - Valid format but non-existent step (e.g., "5.99"): Display "ERROR: Step 5.99 does not exist in Phase 5. Valid steps: 5.1, 5.2, 5.3".
  - CLI MUST exit with non-zero status code on validation errors.

- What happens when state schema changes in future versions?
  - State file includes `version` field (e.g., "1.0") for compatibility detection.
  - CLI MUST check version on load. If version is older than current, CLI attempts automatic migration.
  - If version is newer than CLI supports: Display "ERROR: State file version X.Y requires gmkit version N or later. Please upgrade."
  - Migration strategy: Additive changes (new optional fields) require no migration. Breaking changes increment major version and require explicit migration code.

- What happens if two processes attempt to use the same output directory?
  - CLI MUST acquire an exclusive lock on `.state.json` at startup.
  - If lock cannot be acquired within 5 seconds: Display "ERROR: Another conversion is in progress in <dir>. Wait for it to complete or use a different output directory."
  - Lock is released on process exit (normal or abnormal).

- What happens when state shows "in_progress" but no process is running?
  - When `--resume` is used and state shows "in_progress", CLI checks if the lock file is stale (no process holding lock).
  - If lock is stale: Display "WARNING: Previous conversion appears to have been interrupted. Resuming from last completed step."
  - State is updated to reflect actual completion status before resuming.

- What happens when resuming but a completed phase's output file is missing?
  - On resume, CLI verifies all completed phases have their output files present.
  - If output file missing: Display "ERROR: Phase N output file missing (<filename>). Re-run from Phase N with: gmkit pdf-convert --phase N <dir>"
  - State is NOT automatically corrected (user must explicitly re-run the phase).

- What happens when disk space is exhausted during conversion?
  - If write fails due to disk full: Display "ERROR: Disk full - cannot write output file. Free up space and resume with: gmkit pdf-convert --resume <dir>"
  - State file is written BEFORE phase output files, so resumability is preserved.
  - CLI exits with non-zero status code.

- What happens when a resumed phase fails partway through?
  - State file is updated to `failed` status with current step recorded (e.g., step 5.3).
  - Error message includes the failing step: "ERROR: Phase 5 failed at step 5.3: <error details>"
  - User can retry from the failed step with: `gmkit pdf-convert --from-step 5.3 <dir>`
  - Previously completed phases remain marked as `completed` (not rolled back).

- What happens when PDF metadata fields are empty or malformed?
  - Empty/missing string fields: Use empty string "" (not null).
  - Missing date fields: Use null.
  - Malformed date fields (unparseable): Use null and log warning to diagnostics.
  - Invalid encoding in string fields: Replace invalid characters with Unicode replacement character (U+FFFD) and log warning.
  - metadata.json is always written, even if all optional fields are empty/null.

- What happens when PDF file exists but cannot be read (permission denied)?
  - Display "ERROR: Cannot read PDF - permission denied on <path>"
  - Exit with code 2 (file/path error).

- What happens when PDF is encrypted or password-protected?
  - Display "ERROR: PDF is encrypted or password-protected. Please provide an unprotected PDF."
  - Exit with code 3 (PDF processing error).

- What happens to intermediate files when conversion fails or is aborted?
  - On user abort (Ctrl+C or "Abort" selection): All files are preserved for potential resume.
  - On error: All files are preserved; state file records error for debugging.
  - No automatic cleanup/deletion of partial output.
  - User can manually delete output directory to start fresh, or use overwrite option on re-run.

- What happens when conversion is interrupted (any cause: Ctrl+C, SIGTERM, agent termination, crash)?
  - State file is always written synchronously after each step (per FR-019), ensuring resumability.
  - Partial output from an interrupted step may be incomplete but previous steps remain valid.
  - On next invocation with --resume, CLI detects incomplete state and resumes from last completed step.
  - No special signal handling required; resumability is guaranteed by synchronous state writes.

- What happens when a required module (e.g., PyMuPDF) fails to import?
  - Display "ERROR: Installation appears corrupted - missing required module '<module>'. Reinstall with: uv pip install gmkit"
  - Exit with code 5 (dependency error).

- What happens when PDF filename contains special characters?
  - Windows-incompatible characters (< > : " | ? *) are replaced with underscore in output directory and file names.
  - All other characters (spaces, parentheses, brackets, etc.) are preserved.
  - Example: `My Module: Revised?.pdf` → `My Module_ Revised_/My Module_ Revised_-phase4.md`
  - Original PDF path is stored in state file for reference.

- How are path separators handled across platforms?
  - CLI internally uses forward slashes (/) for all paths (Python pathlib normalizes).
  - User input accepts both forward and backslashes; normalized internally.
  - Output/display uses platform-native separators (/ on macOS/Linux, \ on Windows).
  - State file stores paths with forward slashes for portability.

- What line endings are used for generated files?
  - Bash scripts (.sh): LF line endings (Unix style).
  - PowerShell scripts (.ps1): CRLF line endings (Windows style).
  - Markdown output files: LF line endings (cross-platform, Git-friendly).
  - State/JSON files: LF line endings.

- How does the CLI behave on WSL (Windows Subsystem for Linux)?
  - WSL is treated as Linux (uses forward slashes, LF line endings).
  - No special handling required; Python's pathlib handles WSL paths correctly.

- Are there behavioral differences between macOS and Linux?
  - No functional differences; both use forward slashes, LF line endings, and Unix-style permissions.
  - Python's cross-platform libraries (pathlib, os) handle any minor differences.
  - File system case sensitivity (macOS default is case-insensitive, Linux is case-sensitive) is not a concern as filenames are generated programmatically.

- How are paths with spaces handled in slash command arguments?
  - User provides quoted path: `/gmkit.pdf-to-markdown "My Module.pdf"`
  - Prompt file instructs agent to pass the path to CLI with proper quoting.
  - Agent is responsible for shell escaping when invoking CLI.
  - Example: `gmkit pdf-convert "My Module.pdf"` or `gmkit pdf-convert 'My Module.pdf'`

- What happens if user tries to use `/gmkit.pdf-to-markdown` before running `gmkit init`?
  - The slash command won't exist; agent will report "unknown command" or similar.
  - If user runs CLI directly (`gmkit pdf-convert`) without init, CLI works normally (init is only needed for slash command installation).

- How are agent-specific error handling differences managed?
  - The CLI produces consistent error messages regardless of which agent invokes it.
  - Agents may display CLI errors differently (formatting, colors) but content is identical.
  - Prompt file includes guidance for agent to relay CLI errors to user verbatim.

- What happens when agent cannot execute CLI (permissions, path issues)?
  - Agent reports shell error (e.g., "command not found", "permission denied").
  - Prompt file instructs agent to suggest: "Verify gmkit is installed with: `gmkit --help`"
  - If PATH issue: suggest adding UV tools directory to PATH.

- What happens if disk space is insufficient for diagnostic bundle creation?
  - Display "WARNING: Failed to create diagnostic bundle - insufficient disk space. Phase outputs saved individually."
  - Exit with code 0 (conversion succeeded; bundle is optional).
  - Individual phase files remain accessible in output directory.

## Requirements *(mandatory)*

### Functional Requirements

**Slash Command:**
- **FR-001**: System MUST provide a `/gmkit.pdf-to-markdown` prompt file that instructs the AI agent to invoke the CLI.
- **FR-002**: Prompt file MUST be installed to the agent-specific command location during `gmkit init`:
  - Claude: `.claude/commands/gmkit.pdf-to-markdown.md`
  - Codex: `.codex/prompts/gmkit.pdf-to-markdown.md`
  - Gemini: `.gemini/commands/gmkit.pdf-to-markdown.toml`
  - Qwen: `.qwen/commands/gmkit.pdf-to-markdown.toml`
- **FR-002a**: Prompt file MUST contain:
  - Command purpose description
  - Usage instructions with example invocation
  - Instructions for the agent to invoke `gmkit pdf-convert` CLI
  - Expected output description
  - Error handling guidance with explicit "If X: ERROR" patterns (learned from spec-kit)
  - Retry guidance: agent should retry failed steps up to 3 times before escalating (learned from spec-kit)
  - Reference to table-based user prompt format for structured options (learned from spec-kit)
- **FR-002b**: Prompt file markdown structure:
  ```markdown
  # /gmkit.pdf-to-markdown

  ## Purpose
  [Command description]

  ## Usage
  [Example invocation]

  ## Instructions
  [Step-by-step for agent to invoke CLI]

  ## Expected Output
  [Files produced: final markdown, conversion-report.md with quality ratings]
  [Reference to review-checklist.md for manual QA verification]

  ## Error Handling
  [How agent should handle errors, retry guidance]
  ```
- **FR-003**: Prompt file MUST accept a PDF path as argument and pass it to the CLI.

**CLI Interface:**
- **FR-004**: System MUST provide a `gmkit pdf-convert` CLI command.
- **FR-005**: CLI MUST accept `<pdf-path>` and `--output <dir>` for full pipeline execution (Phase 0 pre-flight through Phase 10 report generation, executing all 11 phases in sequence).
- **FR-006**: CLI MUST accept `--resume <dir>` to continue from last checkpoint.
- **FR-007**: CLI MUST accept `--phase N <dir>` to re-run a specific phase.
- **FR-008**: CLI MUST accept `--from-step N.N <dir>` to re-run from a specific step.
- **FR-009**: CLI MUST accept `--status <dir>` to display conversion progress.
- **FR-009a**: `--status` output MUST display a formatted table showing:
  - Source PDF path and file size
  - Overall status (in_progress, completed, failed, cancelled)
  - For each phase: phase number, name, status (pending/completed/failed), and completion timestamp
  - Current phase/step if in_progress
  - Error summary if failed
  - Example output:
    ```
    Conversion Status: ./converted/
    ─────────────────────────────────
    Source: my-module.pdf (15.2 MB)
    Status: in_progress
    Started: 2026-01-29 14:30:00

    Phase  Name                    Status     Completed
    ─────  ──────────────────────  ─────────  ─────────────────
    0      Pre-flight Analysis     completed  2026-01-29 14:30:05
    1      Image Extraction        completed  2026-01-29 14:30:12
    2      Image Removal           completed  2026-01-29 14:30:18
    3      TOC & Font Extraction   completed  2026-01-29 14:30:25
    4      Text Extraction         completed  2026-01-29 14:31:02
    5      Character-Level Fixes   completed  2026-01-29 14:31:15
    6      Structural Formatting   in_progress (step 6.2)
    7      Font Label Assignment   pending
    ...
    ```
- **FR-010**: CLI MUST accept `--diagnostics` flag to include diagnostic bundle in output.
- **FR-010a**: CLI MUST accept `--yes` flag for non-interactive mode that:
  - Automatically proceeds after pre-flight analysis (skips step 0.6 confirmation)
  - Accepts default values for all user prompts in Phases 7 and 9
  - Useful for CI/CD pipelines, scripting, and automated testing
- **FR-010b**: Diagnostic bundle MUST contain:
  - All phase output files (`<name>-phase4.md` through `<name>-phase8.md`)
  - State file (`.state.json`)
  - Metadata file (`metadata.json`)
  - Font mapping (`font-family-mapping.json`)
  - TOC extraction (`toc-extracted.txt`)
  - Image manifest (`images/image-manifest.json`)
  - Conversion report (`conversion-report.md`)
  - CLI invocation arguments (as `cli-args.txt`)
- **FR-010c**: Diagnostic bundle zip file MUST be named `diagnostic-bundle.zip` and placed in the output directory.
- **FR-010d**: Diagnostic bundle MUST be created at the end of Phase 10, after all other files are generated. Bundle is only created if `--diagnostics` flag was specified by the user.

**CLI Argument Specification:**

| Flag | Argument | Type | Required | Default | Description |
|------|----------|------|----------|---------|-------------|
| `<pdf-path>` | positional | Path | Yes* | - | Path to source PDF file |
| `--output`, `-o` | `<dir>` | Path | No | `./<pdf-basename>/` | Output directory |
| `--resume`, `-r` | `<dir>` | Path | No | - | Resume conversion in directory |
| `--phase` | `N` | Integer (0-10) | No | - | Re-run specific phase |
| `--from-step` | `N.N` | String | No | - | Re-run from specific step |
| `--status`, `-s` | `<dir>` | Path | No | - | Show conversion status |
| `--diagnostics` | - | Flag | No | `false` | Include diagnostic bundle |
| `--yes`, `-y` | - | Flag | No | `false` | Non-interactive mode (accept defaults) |
| `--help`, `-h` | - | Flag | No | - | Show help text |

*`<pdf-path>` is required for new conversions but not for `--resume`, `--phase`, `--from-step`, or `--status` operations.

**CLI Flag Constraints:**
- `--resume`, `--phase`, `--from-step`, and `--status` are mutually exclusive operations.
- If multiple operation flags are provided, CLI MUST display error: "ERROR: Cannot combine --resume, --phase, --from-step, or --status. Use only one operation mode."
- `--diagnostics` can be combined with any operation mode.
- `--yes` can be combined with any operation mode (enables non-interactive/scripted execution).
- `--output` is only valid with `<pdf-path>` (new conversion); ignored for other operations.

**Help Text Requirements:**
- `--help` MUST display: command synopsis, all flags with descriptions, and at least one usage example.
- Help text MUST include version information for debugging purposes.
- Example format:
  ```
  gmkit pdf-convert - Convert PDF to Markdown (v0.1.0)

  Usage: gmkit pdf-convert <pdf-path> [OPTIONS]
         gmkit pdf-convert --resume <dir>
         gmkit pdf-convert --status <dir>

  Arguments:
    <pdf-path>  Path to the PDF file to convert

  Options:
    -o, --output <dir>    Output directory [default: ./<pdf-basename>/]
    -r, --resume <dir>    Resume interrupted conversion
    --phase <N>           Re-run specific phase (0-10)
    --from-step <N.N>     Re-run from specific step
    -s, --status <dir>    Show conversion status
    --diagnostics         Include diagnostic bundle in output
    -h, --help            Show this help message

  Examples:
    gmkit pdf-convert my-module.pdf
    gmkit pdf-convert my-module.pdf --output ./converted/ --diagnostics
    gmkit pdf-convert --resume ./converted/
  ```

**Pre-flight Analysis (Phase 0, steps 0.1-0.5):**
- **FR-011**: System MUST extract PDF metadata:
  - `file_size`: Integer (bytes)
  - `page_count`: Integer
  - `title`: String (empty string if not present)
  - `author`: String (empty string if not present)
  - `creator`: String (empty string if not present)
  - `copyright`: String (empty string if not present)
  - `creation_date`: String ISO8601 (null if not present)
  - `modification_date`: String ISO8601 (null if not present)
- **FR-012**: System MUST count images across all pages.
- **FR-013**: System MUST detect embedded TOC presence and report:
  - `has_toc`: Boolean (true if PDF outline/bookmarks exist)
  - `toc_entries`: Integer (count of outline entries, 0 if none)
  - `toc_max_depth`: Integer (maximum nesting level, 1 = flat, 2+ = nested)
  - Nested entries are preserved in hierarchy for later TOC reconstruction.
- **FR-014**: System MUST check text extractability (detect scanned PDFs with <100 extractable characters).
- **FR-015**: System MUST analyze font families and estimate complexity:
  - **Low**: ≤3 unique font families, ≤10 images, no detected tables
  - **Moderate**: 4-8 unique font families, 11-50 images, or detected tables
  - **High**: >8 unique font families, >50 images, multi-column layout detected, or mathematical notation present
  - Font family uniqueness is determined by base font name only (e.g., "Arial", "Times New Roman"), ignoring size, weight, and style variants. *Note: Further testing may require considering size, weight, and style variants based on how fonts are used within the document (e.g., bold for headings vs regular for body text).*
- **FR-016**: System MUST save extracted metadata to `metadata.json` for use in copyright notices. Schema:
  - Required fields: `file_size` (Integer), `page_count` (Integer)
  - Optional fields: `title`, `author`, `creator`, `copyright` (String, default ""), `creation_date`, `modification_date` (String ISO8601 or null)
  - See `contracts/metadata-schema.json` for complete JSON Schema definition.
- **FR-016a**: Pre-flight analysis (Step 0.6) MUST display results in the following format:
  ```
  ══════════════════════════════════════════════════════════════
    Pre-flight Analysis Complete
  ══════════════════════════════════════════════════════════════

  PDF: <filename> (<size>, <pages> pages)

    Metric              Value              Note
    ─────────────────────────────────────────────────────────────
    Images              <count>            Will be extracted to images/
    Text                extractable/none   Native text found / Scanned PDF
    TOC                 embedded/visual/none   Will use PDF outline / Parse visual TOC
    Fonts               <count> families   Low/Moderate/High complexity
    Copyright           "<notice>"         Found in metadata (or "Not found")
    Complexity          low/moderate/high

  User involvement required in: <list of phases requiring user input>

  Options:
    A) Proceed with conversion
    B) Abort

  Your choice [A/B]: _
  ```

**State Tracking:**
- **FR-017**: System MUST create and maintain `.state.json` in the output directory.
- **FR-018**: State file MUST track: current phase, current step, completed phases, timestamps (ISO8601 format), and any errors. See `contracts/state-schema.json` for complete schema with types and constraints.
- **FR-019**: State file MUST be updated synchronously after each step completion (write must complete before next step begins to ensure resumability).
- **FR-019a**: State file writes MUST be atomic (write to temp file, then rename) to prevent corruption if process is interrupted mid-write.
- **FR-019b**: Phase/step status MUST follow this state machine:
  - `pending` → `in_progress` (when phase/step begins execution)
  - `in_progress` → `completed` (when phase/step finishes successfully)
  - `in_progress` → `failed` (when phase/step encounters unrecoverable error)
  - `failed` → `in_progress` (when phase/step is retried via --phase or --resume)
  - Invalid transitions (e.g., `pending` → `completed`) MUST NOT occur.
- **FR-020**: System MUST validate state file integrity before resume operations:
  - File must be valid JSON (parse without error)
  - File must conform to `contracts/state-schema.json` (all required fields present with correct types)
  - `pdf_path` must point to an existing file
  - `output_dir` must match the directory containing the state file
  - `version` must be supported by current CLI version
  - If validation fails: Display specific error (e.g., "ERROR: State file corrupt - missing required field 'current_phase'")

**Folder Structure:**
- **FR-021**: System MUST create working folder structure:
  ```
  <output-dir>/
  ├── .state.json           # Conversion state tracking
  ├── metadata.json         # Extracted PDF metadata
  ├── images/               # Extracted images (Phase 1)
  │   └── image-manifest.json
  ├── preprocessed/         # Intermediate PDF files
  │   └── <name>-no-images.pdf
  ├── <name>-phase4.md      # Phase outputs
  ├── <name>-phase5.md
  ├── <name>-phase6.md
  ├── <name>-phase8.md
  ├── <name>-final.md       # Final output (Phase 9)
  ├── font-family-mapping.json
  ├── toc-extracted.txt
  ├── conversion-report.md  # Phase 10 output
  └── diagnostic-bundle.zip # Optional (--diagnostics)
  ```
- Folders created with default OS permissions (typically 755 on Unix, inherited on Windows).
- Files created with default OS permissions (typically 644 on Unix, inherited on Windows).

**Orchestration:**
- **FR-024**: System MUST orchestrate phases 1-10 in sequence, calling into E4-07a/b/c/d components via the Phase Interface (see Integration Contracts).
- **FR-025**: System MUST call E4-07c for step 0.6 (pre-flight user confirmation) before proceeding.
- **FR-026**: System MUST display user involvement notice listing phases requiring input (Phase 7, Phase 9).
- **FR-027**: System MUST halt on critical errors with actionable error messages.
- **FR-028**: System MUST continue with warnings on non-critical issues.

**Error Handling:**
- **FR-029**: System MUST display "ERROR: Cannot open PDF - file not found or corrupted" for missing/unreadable PDFs.
- **FR-030**: System MUST display "ERROR: Scanned PDF detected - very little extractable text" for scanned PDFs.
- **FR-031**: System MUST display "ABORT: User cancelled after pre-flight report" when user declines to proceed.
- **FR-032**: System MUST display "ERROR: Cannot create output directory - check permissions" when directory creation fails.
- **FR-033**: System MUST display "ERROR: Failed to create text-only PDF" when image removal fails.
- **FR-034**: System MUST display "WARNING: No TOC found - hierarchy may be incomplete" when no TOC detected.
- **FR-035**: System MUST display "ERROR: No text extracted from PDF" when text extraction yields empty result.
- **FR-036**: System MUST display "WARNING: Pervasive two-column issues detected - expect manual review" when >50% pages affected.
- **FR-037**: System MUST display "ERROR: Phase input file not found - run previous phase first" when phase input missing.
- **FR-038**: System MUST display "ERROR: font-family-mapping.json not found or malformed" when font JSON invalid.
- **FR-039**: System MUST display "WARNING: No heading sources available - flat document structure" when no TOC or font labels.
- **FR-040**: System MUST display "WARNING: Many lint violations - document may need significant cleanup" when 20+ violations.
- **FR-041**: System MUST display "WARNING: Failed to create zip bundle - files saved individually" when bundle creation fails.
- **FR-041a**: ERROR and ABORT messages MUST be written to stderr. WARNING messages and normal output MUST be written to stdout.
- **FR-041b**: Actionable error messages MUST include:
  - Error type prefix (ERROR/WARNING/ABORT)
  - Brief description of what failed
  - Suggested action or next step (e.g., "check permissions", "run previous phase first")
  - Relevant context (file path, phase number) where applicable

**Exit Codes:**
- **FR-044**: CLI MUST return exit code 0 on successful completion.
- **FR-045**: CLI MUST return exit code 1 for user abort (ABORT messages).
- **FR-046**: CLI MUST return exit code 2 for file/path errors (file not found, permissions).
- **FR-047**: CLI MUST return exit code 3 for PDF processing errors (scanned PDF, extraction failure).
- **FR-048**: CLI MUST return exit code 4 for state/resume errors (corrupt state, missing phase input).
- **FR-048a**: CLI MUST return exit code 5 for dependency errors (corrupted installation, missing required modules).

**Copyright Notice:**
- **FR-049**: System MUST insert copyright notice block at top of final markdown output using metadata from step 0.1.
- **FR-049a**: Copyright notice MUST be inserted as the very first content in the file, before the H1 heading.
- **FR-050**: Copyright notice MUST include: title, author/publisher, copyright (if available), source filename, conversion date, and tool attribution.
- **FR-050a**: Copyright notice MUST use this exact format:
  ```markdown
  <!--
  COPYRIGHT NOTICE
  ================
  This markdown file was converted from a copyrighted PDF for personal game
  preparation use only. The text, structure, and content remain the intellectual
  property of the original publisher. Do not redistribute, publish, or share
  this file publicly. For official content, please purchase from the publisher.

  Title: [PDF title metadata or filename]
  Author/Publisher: [PDF author/creator metadata if available, or "Unknown"]
  Copyright: [PDF copyright metadata if available, or "See original publication"]
  Source file: [Original PDF filename]
  Converted: [ISO8601 date]
  Tool: GM-Kit pdf-convert
  -->
  ```

### Key Entities

- **Conversion State**: Tracks progress through the pipeline (current phase, step, timestamps, errors). Persisted in `.state.json`.
- **PDF Metadata**: Extracted properties (title, author, page count, copyright) used for pre-flight report and copyright notices. Persisted in `metadata.json`.
- **Phase Output**: Intermediate markdown files produced by each phase (e.g., `<filename>-phase4.md`).
- **Diagnostic Bundle**: Optional zip file containing all phase outputs and original prompt for debugging.

### Integration Contracts

**ConversionState:**
- `pdf_path`: Path to source PDF file
- `output_dir`: Path to working directory
- `current_phase`: Integer (0-10)
- `current_step`: String (e.g., "4.3")
- `completed_phases`: List of completed phase numbers
- `completed_steps`: List of completed step identifiers
- `phase_outputs`: Map of phase number to output file path
- `started_at`: ISO8601 timestamp
- `updated_at`: ISO8601 timestamp
- `errors`: List of error messages
- `config`: CLI configuration (diagnostics flag, yes flag, etc.)

**Phase Interface:**
- Each phase MUST implement: `execute(state: ConversionState) -> PhaseResult`
- `PhaseResult` MUST contain: `status` (SUCCESS/ERROR/WARNING), `output_files` (list), `errors` (list), `warnings` (list)
- Interface is testable via mock implementations that return predetermined PhaseResult values.

**Mock Phase Behavior:**
- Mock phases MUST return SUCCESS status with empty output_files for phases 0-10.
- Mock phases MUST simulate state transitions (update current_phase/step).
- Mock phases MUST respect --yes flag (skip user prompts in phases 0, 7, 9).
- For testing error paths, mocks MUST be configurable to return ERROR status with specific error messages.
- When mock returns ERROR, orchestrator MUST handle it identically to real phase ERROR:
  - Update state to failed
  - Display error message from PhaseResult.errors
  - Exit with appropriate code

**Orchestrator Responsibilities (Python CLI):**
- Parse CLI arguments and validate inputs
- Create/load ConversionState
- Call phases in sequence (0-10)
- Handle --resume, --phase, --from-step logic
- Write state file after each phase/step
- Handle exit codes based on PhaseResult status

**Phase Responsibilities:**
- Execute phase-specific logic
- Return PhaseResult with status and outputs
- NOT write state file (orchestrator's job)
- NOT handle CLI arguments (receive config via ConversionState)

**Phase Registration:**
- Phases are registered as a static list in the orchestrator (phases 0-10).
- No dynamic plugin discovery required.
- Each phase maps to a module: `gmkit.phases.phase_N` where N is 0-10.
- Mock implementations replace real modules during testing via dependency injection.

**UserInteraction Interface:**
- User prompts MUST be testable via pexpect (expect specific prompt text, send responses).
- Prompt text MUST be deterministic (no timestamps or random content in prompts).
- All prompts MUST end with a recognizable pattern (e.g., `: _` or `[A/B]: `).
- For --yes mode, prompts are skipped and default responses used (no pexpect needed).

**PhaseResult to Exit Code Mapping:**
- `SUCCESS` → Continue to next phase; exit 0 if final phase
- `WARNING` → Continue to next phase; exit 0 if final phase (warnings logged)
- `ERROR` → Stop execution; exit code based on error type (2-5 per FR-044 through FR-048a)

**Step-Level Resume Support:**
- All phases (0-10) MUST support step-level resume via `--from-step N.N`.
- Each phase MUST track completed steps in ConversionState.
- On resume from step N.M, phase N executes steps M through end, skipping earlier steps.
- Step outputs are idempotent - re-running a step overwrites previous output for that step.

**Phase Timeout:**
- No timeout enforced by orchestrator (phases may take arbitrarily long).
- User can interrupt via Ctrl+C; state is preserved per interruption handling.
- Rationale: Agent-driven phases have unpredictable duration; hard timeouts would cause false failures.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can invoke `/gmkit.pdf-to-markdown` and see pre-flight analysis within 2 seconds for the reference test PDF (`test-data/The Homebrewery - NaturalCrit.pdf`, 2 pages). Threshold scales linearly for larger documents (~0.2s/page baseline). *Note: Threshold may require adjustment based on real-world CI results.*
- **SC-002**: Users can resume an interrupted conversion and continue from the last completed step without re-processing earlier phases.
- **SC-003**: Users can re-run a specific phase and see updated output without affecting other phases' artifacts.
- **SC-004**: 100% of error conditions (FR-029 through FR-041) produce actionable error messages (not stack traces). Verified by unit tests that trigger each enumerated error condition and assert the expected message format per FR-041b.
- **SC-005**: State file accurately reflects conversion progress:
  - Every phase marked "completed" in state has its corresponding output file present on disk
  - Current phase/step in state matches the last successfully written output
  - `--status` output matches both state file and file system state
  - Verifiable via automated test that completes each phase and asserts state ↔ filesystem consistency
- **SC-006**: Slash command works identically across all supported agents (Claude, Codex, Gemini, Qwen). "Identical" means:
  - Same CLI command is invoked (`gmkit pdf-convert`)
  - Same arguments are passed to CLI
  - Same output files are produced for identical inputs
  - Verified by: (1) prompt file content review ensuring each agent's prompt invokes CLI identically, (2) CLI integration tests with consistent inputs/outputs. Optional: multi-agent invocation tests (see BACKLOG E2-08 for future CI feature).

## Test Data

Test input files are located in `specs/005-pdf-convert-orchestration/test_inputs/`:

| File | Pages | Images | Fonts | Complexity | Used For |
|------|-------|--------|-------|------------|----------|
| `The Homebrewery - NaturalCrit.pdf` | 2 | ~5 | 8+ families | High | Pre-flight timing (SC-001), font complexity, TOC detection |

## Assumptions

- E4-07a (Code pipeline), E4-07b (Agent pipeline), E4-07c (User interaction), and E4-07d (Image link injection) will be implemented after this feature, replacing mocks.
- Integration tests will use mocks for Code steps (Python functions), Agent steps (prompt responses), and User steps (pexpect for simulated input).
- pexpect is used for interactive testing on Linux/macOS. On Windows, tests use `wexpect` (Windows equivalent) or skip interactive tests with `pytest.mark.skipif`.
- Unit tests will retain mocks permanently for isolation and speed.
- Mocks are replaced with real implementations when: (1) the corresponding E4-07x feature is merged to master, (2) its integration tests pass, and (3) the interface contract is unchanged.
- The existing `gmkit init` command (from E2-02) will be extended to install the new prompt file. The prompt file format is forward-compatible; no version pinning required.
- PyMuPDF (fitz) >= 1.23.0 is required for PDF operations (text extraction, image extraction, TOC reading).
- Memory usage: CLI should process PDFs up to 500 pages without exceeding 2GB RAM. For larger files, user should expect higher memory usage proportional to page count.
- Logging: CLI uses Python's standard logging module with levels DEBUG, INFO, WARNING, ERROR.
  - Default level: INFO (shows progress and warnings)
  - `--verbose` flag (future): enables DEBUG level
  - Logs written to stderr; stdout reserved for command output
  - No persistent log files by default (logs are ephemeral)
- Progress indicators: CLI displays current phase/step during execution using Rich library.
  - Format: "Phase N/10: <phase name> (step N.N)"
  - Updates in-place on terminals that support it
  - Falls back to line-by-line output on non-TTY (CI, piped output)
- Idempotency:
  - Code phases (deterministic): Re-running with identical input produces identical output.
  - Agent phases (non-deterministic): Output may vary between runs due to LLM behavior; however, output must still conform to the defined contracts/schema.
  - Timestamps in state file are exempt from idempotency (updated on each run).
- Transient failure retries:
  - File lock contention: Retry up to 3 times with 1-second delay before failing.
  - Disk I/O errors: No automatic retry; fail immediately with actionable error message.
  - Network errors (if any future feature requires): Retry up to 3 times with exponential backoff.

## Dependencies

- **E2-02 (Installer Skeleton)**: Provides `gmkit init` infrastructure for installing prompt files.
- **E4-07c**: Provides step 0.6 (pre-flight user confirmation) - will be mocked initially.
- **E4-07a/b/d**: Provide phase implementations - will be mocked initially.

## Out of Scope

- Actual implementation of phases 1-10 logic (covered by E4-07a/b/c/d).
- OCR for scanned PDFs (users directed to external tools).
- Automatic retry of failed agent steps (implemented in E4-07b).
- User interaction prompts beyond pre-flight confirmation (implemented in E4-07c).
