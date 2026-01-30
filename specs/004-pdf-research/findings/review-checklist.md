# PDF -> Markdown Review Checklist

Use this checklist for every PDF conversion. Mark each item and add brief notes.

## Metadata
- [ ] PDF title:
- [ ] Source file:
- [ ] Agent used (claude / gemini / qwen / codex):
- [ ] LLM model (if known, e.g., claude-opus-4-5, gemini-2.5-pro, qwen-max):
- [ ] Conversion approach (AI-only / CLI-Python / Hybrid):
- [ ] Tools/commands used:
- [ ] Output file:
- [ ] Date:

## Preprocessing
- [ ] Images extracted (count:    )
- [ ] Images stripped from PDF for text extraction
- [ ] Chunking required: Yes / No
  - If yes, chunk count:
  - Chunk size (pages):
  - Chunking rationale:

## TOC Extraction
- [ ] TOC extraction method (embedded outline / visual parse / inference):
- [ ] Sections identified (count:    )
- [ ] TOC issues encountered:

## Structural Accuracy
- [ ] Reading order correct (columns, multi-column flow, sidebars)
- [ ] Headings and hierarchy preserved (H1/H2/H3, section order)
- [ ] Heading levels match TOC structure
- [ ] Lists preserved (bullets/numbering, indentation)
- [ ] Tables legible and correctly structured (not converted to bullet lists)
- [ ] Page headers/footers removed or clearly separated

## Callouts & Special Blocks
- [ ] Boxed text/callouts preserved as blockquotes
- [ ] Read-aloud text tagged with `> **Read Aloud:**` prefix
- [ ] Keeper/GM notes tagged where distinguishable
- [ ] Maps/figures referenced with `[FIGURE: description]` placeholders
- [ ] Captions preserved or reattached to the right asset

## Text Quality & Cleanup
- [ ] No missing sections or skipped pages
- [ ] OCR quality acceptable (few garbled words)
- [ ] Hyphenation fixed at line/column breaks
- [ ] Column alignment spaces removed (extra gaps from two-column layout)
- [ ] Line breaks normalized (no mid-sentence hard wraps)
- [ ] Spelling errors corrected (notable corrections:                    )
- [ ] Special characters rendered correctly (Unicode, em-dashes, smart quotes)

## Quality Ratings (1-5)
- [ ] Structural clarity:    /5  (Are headings logical and navigable?)
- [ ] Text flow:    /5  (Does content read naturally without artifacts?)
- [ ] Table integrity:    /5  (Are tables properly formatted and readable?)
- [ ] Callout formatting:    /5  (Are boxed text/notes properly marked?)
- [ ] **Overall quality:    /5**

## Remaining Issues (up to 3)

### Issue 1:
- Location (section/heading):
- Problem:
- Example text: `                    `
- Suggested fix:

### Issue 2:
- Location (section/heading):
- Problem:
- Example text: `                    `
- Suggested fix:

### Issue 3:
- Location (section/heading):
- Problem:
- Example text: `                    `
- Suggested fix:

## Summary
- [ ] All pages represented in output
- [ ] Conversion report generated (if agent conversion)
- [ ] Recommended follow-up actions:
