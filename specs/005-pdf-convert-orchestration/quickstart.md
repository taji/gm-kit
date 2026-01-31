# Quickstart: PDF to Markdown Command Orchestration

**Feature**: 005-pdf-convert-orchestration
**Date**: 2026-01-29

## Prerequisites

- GM-Kit installed via `uv tool install gmkit-cli`
- Project initialized with `gmkit init`
- A PDF file to convert

## Quick Usage

### Via Slash Command (Recommended)

In your AI coding agent (Claude, Codex, Gemini, or Qwen):

```
/gmkit.pdf-to-markdown "path/to/your-module.pdf"
```

### Via CLI

```bash
# Full conversion
gmkit pdf-convert my-module.pdf --output ./converted/

# With diagnostic bundle
gmkit pdf-convert my-module.pdf --output ./converted/ --diagnostics

# Check status of existing conversion
gmkit pdf-convert --status ./converted/

# Resume interrupted conversion
gmkit pdf-convert --resume ./converted/

# Re-run specific phase
gmkit pdf-convert --phase 5 ./converted/

# Re-run from specific step
gmkit pdf-convert --from-step 5.3 ./converted/
```

## What Happens

1. **Pre-flight Analysis** (Phase 0)
   - Extracts PDF metadata (title, author, pages, images)
   - Checks text extractability (detects scanned PDFs)
   - Analyzes complexity (fonts, layout)
   - Shows report and asks for confirmation

2. **Conversion Pipeline** (Phases 1-10)
   - Phase 1-2: Image extraction and removal
   - Phase 3: TOC and font analysis
   - Phase 4-6: Text extraction and cleanup
   - Phase 7-8: Structure detection and hierarchy
   - Phase 9: Quality review (requires user input)
   - Phase 10: Report generation

3. **Output**
   - Final markdown: `<output-dir>/<filename>-final.md`
   - Conversion report: `<output-dir>/conversion-report.md`
   - Extracted images: `<output-dir>/images/`
   - State file: `<output-dir>/.state.json`

## User Involvement

You'll be prompted for input in:
- **Phase 0**: Confirm to proceed after pre-flight report
- **Phase 7**: Review/adjust font-family labels
- **Phase 9**: Confirm header/footer removal, review issues

## Example Session

```
$ gmkit pdf-convert "Call of Cthulhu Quick-Start.pdf" --output ./coc-converted/

══════════════════════════════════════════════════════════════
  Pre-flight Analysis Complete
══════════════════════════════════════════════════════════════

PDF: Call of Cthulhu Quick-Start.pdf (30.6 MB, 50 pages)

  Metric              Value              Note
  ─────────────────────────────────────────────────────────────
  Images              34                 Will be extracted to images/
  Text                extractable        Native text found
  TOC                 embedded           Will use PDF outline
  Fonts               8 families         Moderate complexity
  Complexity          moderate

User involvement required in: Phase 7 (font labels), Phase 9 (review)

Options:
  A) Proceed with conversion
  B) Abort

Your choice [A/B]: A

Starting conversion...
Phase 1: Image Extraction ✓
Phase 2: Image Removal ✓
Phase 3: TOC & Font Extraction ✓
...
```

## Troubleshooting

### "ERROR: Scanned PDF detected"
The PDF contains images of text, not selectable text. Use an OCR tool first (out of scope for GM-Kit).

### "ERROR: Cannot open PDF"
Verify the file path is correct and the PDF is not corrupted.

### Conversion interrupted
Use `--resume` to continue from where you left off:
```bash
gmkit pdf-convert --resume ./converted/
```

### Poor output quality
Re-run the quality review phase:
```bash
gmkit pdf-convert --phase 9 ./converted/
```

## For Developers

### Testing with Mocks

Integration tests use mocks for phases 1-10. To run:

```bash
pytest tests/integration/pdf_convert/ -v
```

### Adding Real Phase Implementations

When E4-07a/b/c/d are implemented, replace mock phases in:
- `src/gmkit_cli/pdf_convert/phases/stubs.py` → real implementations
- Update `PHASES` registry in `orchestrator.py`
