# /gmkit.pdf-to-markdown

## Purpose

Convert a PDF document to well-formatted Markdown for use during game sessions. This command orchestrates a multi-phase pipeline that extracts text, preserves structure, and produces a clean Markdown file suitable for reference.

## Usage

```
/gmkit.pdf-to-markdown "<path-to-pdf>"
```

**Example:**
```
/gmkit.pdf-to-markdown "Call of Cthulhu - Keeper Rulebook.pdf"
```

## Instructions

When this command is invoked:

1. **Execute the CLI command:**
   ```bash
   gmkit pdf-convert "<path-to-pdf>"
   ```

2. **Review the pre-flight report** - The CLI will display:
   - File metrics (pages, images, fonts)
   - Complexity assessment
   - TOC detection status
   - User involvement phases (7 and 9 require your input)

3. **Confirm to proceed** - When prompted, select:
   - `A` to proceed with conversion
   - `B` to abort

4. **Monitor phase execution** - The CLI runs 11 phases:
   - Phase 0: Pre-flight analysis
   - Phases 1-6: Automated extraction and formatting
   - Phase 7: Font label assignment (may need user input)
   - Phase 8: Heading insertion
   - Phase 9: Lint and final review (may need user input)
   - Phase 10: Report generation

5. **Review output files** in the output directory:
   - `<name>-final.md` - The converted document
   - `conversion-report.md` - Quality ratings and issues
   - `review-checklist.md` - Manual QA verification items

## Expected Output

**Files produced:**
- Final markdown document with copyright notice
- Conversion report with quality ratings per section
- Review checklist for manual verification

**Directory structure:**
```
<pdf-basename>/
├── .state.json           # Conversion state (for resume)
├── metadata.json         # Extracted PDF metadata
├── images/               # Extracted images
├── <name>-final.md       # Final output
├── conversion-report.md  # Quality report
└── review-checklist.md   # QA checklist
```

## Error Handling

**If file not found:**
- ERROR: Cannot open PDF - file not found or corrupted
- Action: Verify the file path and ensure the file exists

**If scanned PDF (no text):**
- ERROR: Scanned PDF detected - very little extractable text
- Action: Use external OCR tool first, then retry

**If encrypted PDF:**
- ERROR: PDF is encrypted or password-protected
- Action: Provide an unprotected PDF

**If permission denied:**
- ERROR: Cannot read PDF - permission denied
- Action: Check file permissions and try again

**If conversion interrupted:**
- Resume with: `gmkit pdf-convert --resume <output-dir>` or `gmkit pdf-convert --resume`
- When no directory is provided, gmkit uses `.gmkit/active-conversion.json`
- The pipeline saves progress after each step

**Retry guidance:**
- If a phase fails, retry up to 3 times before escalating
- Use `--phase N` to re-run a specific phase (uses active conversion if no path given)
- Use `--from-step N.N` to resume from a specific step (uses active conversion if no path given)

## Options

| Flag | Description |
|------|-------------|
| `--output <dir>` | Specify output directory |
| `--diagnostics` | Create diagnostic bundle for debugging |
| `--yes` | Non-interactive mode (skip prompts) |
| `--resume` | Resume interrupted conversion (uses active conversion if no path given) |
| `--status` | Check conversion progress (uses active conversion if no path given) |
| `--phase N` | Re-run specific phase |
| `--from-step N.N` | Resume from specific step |

## User Involvement

Phases 7 and 9 may require your input:

**Phase 7 (Font Label Assignment):**
- Review font-to-heading mappings
- Confirm or adjust assignments

**Phase 9 (Lint & Final Review):**
- Review flagged issues
- Approve or request fixes

Two interaction flows are supported for Phase 9:

1. **Interactive (default):** The agent presents each concern one at a time, collects your response, applies the revision, and moves to the next.
2. **Checklist batch:** The agent generates `review-checklist.md` with all concerns. You can annotate the file with approvals, corrections, and notes, then ask the agent to address all annotations at once.

When prompted, provide clear responses using the table-based format if options are presented.
