# Keep on the Borderlands (pages 1–10) Findings

## Metadata
- PDF title: Dungeon Module B2, The Keep on the Borderlands
- Source file: `temp-resources/chunks/keep-on-the-borderlands/keep-01-10.pdf`
- Chunk(s) tested: 1–10
- Conversion approach: AI-only + Codex MCP text extraction experiments
- Agent/tool: Claude Code (Opus) vs Gemini 2.5 vs Qwen (hybrid via `pdftotext`) vs Codex + pdf-reader MCP (https://github.com/SylphxAI/pdf-reader-mcp)
- Commands used: Claude Code PDF read (native multimodal), Gemini OCR conversion (per user report), Qwen `pdftotext` extraction + Markdown formatting, Codex MCP `read_pdf` with page ranges
- Output location:
  - `temp-resources/chunks/keep-on-the-borderlands/keep-01-10-claude.md`
  - `temp-resources/chunks/keep-on-the-borderlands/keep-01-10-gemini.md`
  - `temp-resources/chunks/keep-on-the-borderlands/keep-01-10-qwen.md`
  - `temp-resources/chunks/keep-on-the-borderlands/keep-01-10-codex.md`
- Date: 2026-01-26
- Verification: PDF text extraction via `pdftotext -layout` (pages 1–10)
  - Column-crop artifacts for Codex test: `temp-resources/chunks/keep-on-the-borderlands/codex-crops/`

## Checklist Summary
- Checklist file: `specs/004-pdf-research/findings/review-checklist.md`
- Overall pass/fail: Partial pass (Claude strongest; Gemini close; Qwen fails due to missing content)

## Results
- Structural accuracy: Claude more consistent heading hierarchy; Gemini closer to original flow and pagination; Qwen loses order/content in two-column layout.
- Callouts & special blocks: Claude more descriptive for figures/legends; Gemini briefer.
- Text quality & cleanup: Claude/Gemini accurate; Qwen truncates sections and misplaces content.
- Tables: Claude preserved tables in Markdown; Gemini converted at least one table (Movement in Combat) to bullets; Qwen corrupts Armor Class table values.
- OCR quality: Gemini used OCR (per user report); Claude used native PDF read (per Claude summary); Qwen relied on `pdftotext` (no OCR).
- Image handling: Claude attempted symbols with Unicode; Gemini misread a map symbol as “H”; Qwen used a single generic figure placeholder.
- Codex MCP text extraction: Raw text stream with column merges and heavy character spacing artifacts on cropped columns; not suitable for direct Markdown conversion without extensive cleanup.

## Issues & Fixes
- Issue: Duplicate title pages in the PDF were consolidated by Claude but preserved by Gemini.
  - Impact: Claude improves readability but diverges from strict fidelity; Gemini preserves duplicates.
  - Fix/workaround: Decide policy for duplicate pages (dedupe vs preserve) in E4-07 guidance.
  - Notes: PDF text extraction shows duplicate title text; Gemini mirrors it, Claude merges.
- Issue: Qwen output missing large sections (Background, Start, Rumor Table, Areas of the Keep).
  - Impact: ~60% content loss makes Qwen output unusable for this PDF.
  - Fix/workaround: Avoid `pdftotext`-only extraction for dense two-column PDFs; prefer OCR or multimodal read.
  - Notes: Qwen truncated sections and dropped multi-column content.
- Issue: Armor Class table corrupted in Qwen output.
  - Impact: Incorrect rules data; breaks fidelity.
  - Fix/workaround: Use OCR/multimodal extraction or validate tables against source.
  - Notes: Values shifted (e.g., Shield-only mapped to AC 9 instead of 8).
- Issue: Map/ballista symbol rendering incorrect in both outputs.
  - Impact: Loss of fidelity for map legend.
  - Fix/workaround: Standardize placeholder text for symbols (e.g., [SYMBOL: ballista]).
  - Notes: Claude attempted ⊣; Gemini produced “H”.
- Issue: Codex pdf-reader MCP output unusable for clean conversion.
  - Impact: Severe spacing artifacts (e.g., “a c te rs a re…”) and dropped characters even after column cropping.
  - Fix/workaround: Prefer OCR/multimodal extraction for this PDF; do not rely on MCP text extraction for scanned or complex layouts.
  - Notes: Column-split PDFs (`keep-01-10-left.pdf`, `keep-01-10-right.pdf`, `keep-01-10-columns-ordered.pdf`) still produced degraded text.

## Observations
- What worked well: Claude’s headings/tables; Gemini’s strict adherence to original flow and page duplication.
- What broke: Symbol fidelity; Gemini table formatting for at least one table; Qwen dropped major sections and corrupted tables; Codex MCP extraction produced unusable spacing artifacts even with column crops.
- Surprises: Claude introduced new subheadings not explicitly present in PDF and added semantic formatting (bolding key terms) plus extra structuring (abbreviations list, movement table) that improved readability.
- Heuristic: If selecting text in a PDF column also highlights text in other columns, the PDF’s internal text order is interleaved and text extraction is likely unreliable. Prefer OCR/multimodal extraction for those files.
- pdftotext note: `pdftotext` (plain) preserved the most readable raw text of the CLI extracts, but it strips structural cues (headings/tables/callouts) and introduces column/spacing/hyphenation artifacts that are difficult to reliably reconstruct into Markdown.
- PyMuPDF/pdfplumber note: Both tools preserve core section text (e.g., BACKGROUND, START, RUMOR TABLE), but output contains heavy “spaced letters” artifacts and loses original structure. PyMuPDF’s “markdown” output does not emit heading markers (#, ##, etc.) and reads like plain text with page breaks. It remains more readable than pdfplumber/pdftotext for some lines, yet still requires substantial cleanup to rebuild headings/tables/callouts.
- PyMuPDF image extraction note: Extracted 19 images from `keep-01-10.pdf` into `temp-resources/chunks/keep-on-the-borderlands/images/`. No image references were inserted into Markdown; placement must be done manually if required. Image placement policy TBD (inline vs appendix, naming, and reference style).
- Claude image extraction note: Claude used `pdfimages` to extract 19 images into `temp-resources/chunks/keep-on-the-borderlands/images-claude/`. Per-page counts: p01=2, p02=1, p03=4, p04=1, p05=3, p06=2, p07=2, p08=1, p09=3, p10=0 (no images on page 10).
- Gemini image extraction note: Gemini used a Python script to extract 19 images into `temp-resources/chunks/keep-on-the-borderlands/images-gemini/`. Images found on pages 1–9; page 10 had none.
- Qwen image extraction note: Qwen used a Python script to extract 19 images into `temp-resources/chunks/keep-on-the-borderlands/images-qwen/`. Images found on pages 1–9; page 10 had none. Output preserved original image formats (PNG/JPEG), so extensions varied.
- Cross-tool summary: All tools extracted 19 images and agreed there are no images on page 10. Claude used `pdfimages` (CLI); Gemini/Qwen used Python; PyMuPDF extraction matched count. Placement in Markdown remains manual.
- pdf-reader MCP note: The pdf-reader MCP (https://github.com/SylphxAI/pdf-reader-mcp) exhibited the same two-column extraction issues as CLI/Python utilities (pdftotext, PyMuPDF, pdfplumber). It relies on similar text-stream extraction and suffers from column interleaving, spacing artifacts, and content loss on dense two-column layouts.
- Decision: Do not pursue further CLI/Python text extraction tests on other PDFs (e.g., Call of Cthulhu). The quality gap versus native AI extraction is too large for two-column layouts. This also applies to text-extraction MCPs like pdf-reader MCP.
- Recommendation: Prefer native AI extraction for text (Claude/Gemini/Qwen). Use a gm-kit-provided Python utility (PyMuPDF) for cross-platform image extraction only, invoked via `uv run` to avoid per-OS CLI dependencies.

## Next Steps
- Tooling adjustments: Add explicit instruction on handling duplicates and symbols.
