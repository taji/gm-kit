# PDF to Markdown Conversion Report

## Metadata
- Source file: /home/todd/Dev/gm-kit/temp-resources/CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules.pdf
- Agent: codex
- LLM model: not visible
- Date: 2026-01-27
- Output file: /home/todd/Dev/gm-kit/temp-resources/conversions/call-of-cthulhu/codex/call-of-cthulhu-full.md

## Original Prompt
# PDF to Markdown Conversion Prompt (v2)

## Original Prompt Reference
This prompt should be included in your final conversion report for traceability.

---

## Overview

Convert the PDF file to well-structured Markdown using a multi-phase approach:
1. **Setup** - Create working folder structure
2. **Preprocessing** - Extract images, strip images from PDF, chunk if needed
3. **TOC Extraction** - Extract and parse the Table of Contents for hierarchy reference
4. **Text Extraction** - Convert PDF content to Markdown using your native capability
5. **Post-Processing** - Fix artifacts, spelling, and formatting issues
6. **Hierarchy Correction** - Apply proper heading levels using TOC and content analysis
7. **Quality Analysis** - Review output and document remaining issues
8. **Report Generation** - Produce detailed conversion report

---

## Phase 1: Setup

### Source File
```
temp-resources/CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules.pdf
```

### Working Folder Structure
Create your agent-specific working folder with this structure:
```
temp-resources/conversions/call-of-cthulhu/[agent]/
├── images/                    # Extracted images from PDF
├── preprocessed/              # Image-stripped PDF and chunks
├── chunks/                    # Individual chunk .md files (if chunking needed)
├── call-of-cthulhu-full.md   # Final merged markdown
└── conversion-report.md       # Your analysis report (includes this prompt)
```

Replace `[agent]` with: `claude`, `gemini`, `qwen`, or `codex`

**Important**: Only write to your own agent folder. Do not modify other agents' folders or the parent directory.

---

## Phase 2: Preprocessing

### 2.1 Image Extraction
Extract all images from the PDF and save them to the `images/` folder.

Use PyMuPDF (fitz):
```python
import fitz
import os

def extract_images(pdf_path, output_dir):
    """Extract all images from PDF and save to output directory."""
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)

    image_count = 0
    for page_num, page in enumerate(doc):
        for img_index, img in enumerate(page.get_images()):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            image_filename = f"page{page_num + 1:03d}_img{img_index + 1:02d}.{image_ext}"
            image_path = os.path.join(output_dir, image_filename)

            with open(image_path, "wb") as f:
                f.write(image_bytes)

            image_count += 1

    doc.close()
    return image_count
```

### 2.2 Image Stripping
Create an image-free version of the PDF for cleaner text extraction.

Use PyMuPDF (fitz):
```python
import fitz

def strip_images(input_pdf, output_pdf):
    """Remove all images from PDF and save to new file."""
    doc = fitz.open(input_pdf)

    for page in doc:
        # Get all images on the page
        images = page.get_images()
        for img in images:
            xref = img[0]
            # Remove the image by redacting its area
            rects = page.get_image_rects(xref)
            for rect in rects:
                page.add_redact_annot(rect)
        page.apply_redactions()

    doc.save(output_pdf)
    doc.close()
```

Save the stripped PDF to: `preprocessed/call-of-cthulhu-no-images.pdf`

### 2.3 Chunking (If Needed)
If the image-stripped PDF exceeds 15MB or 30 pages, split it into chunks.

Chunking guidelines:
- Target chunk size: 10-15 pages for text-heavy content
- Target chunk size: 5-10 pages for visually complex layouts
- Preserve logical boundaries (don't split mid-section if avoidable)

Use PyMuPDF for chunking:
```python
import fitz

def chunk_pdf(input_pdf, output_dir, pages_per_chunk=10):
    """Split PDF into chunks of specified page count."""
    doc = fitz.open(input_pdf)
    total_pages = len(doc)
    chunks = []

    for start in range(0, total_pages, pages_per_chunk):
        end = min(start + pages_per_chunk, total_pages)
        chunk_doc = fitz.open()
        chunk_doc.insert_pdf(doc, from_page=start, to_page=end - 1)

        chunk_filename = f"chunk_{start + 1:03d}-{end:03d}.pdf"
        chunk_path = os.path.join(output_dir, chunk_filename)
        chunk_doc.save(chunk_path)
        chunk_doc.close()
        chunks.append(chunk_path)

    doc.close()
    return chunks
```

Save chunks to: `preprocessed/`

---

## Phase 3: TOC Extraction

Extract the Table of Contents from the PDF before text conversion. This serves as your reference for correct heading hierarchy.

### 3.1 Extract TOC
Try to extract the embedded TOC outline first:
```python
import fitz

def extract_toc(pdf_path):
    """Extract TOC from PDF outline."""
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()  # Returns list of [level, title, page]
    doc.close()
    return toc
```

### 3.2 Parse Visual TOC
If no embedded outline exists, locate the "Table of Contents" or "Contents" page and parse it manually. Look for:
- Page number references (e.g., "Combat ....... 13")
- Indentation indicating hierarchy
- Section numbering patterns

### 3.3 Document the TOC
Save the extracted TOC to a temporary reference file or hold in memory for Phase 6.

**Note**: The TOC may contain special characters or formatting artifacts (dots, symbols). Clean these during extraction.

---

## Phase 4: Text Extraction

Convert the preprocessed PDF (or chunks) to Markdown using your native PDF reading capability.

### Structural Requirements
- Preserve heading hierarchy (H1/H2/H3) - initial pass can use placeholder levels
- Maintain correct reading order (handle two-column layouts properly)
- Preserve lists with correct indentation and numbering
- Convert tables to Markdown table format (not bullet lists)

### Callouts & Special Blocks
- Format boxed text/callouts as blockquotes (`>`)
- Tag read-aloud text with `> **Read Aloud:**` prefix
- Tag GM/Keeper notes with `> **Keeper Note:**` prefix where distinguishable
- Use placeholders for figures: `[FIGURE: description]` or `[MAP: description]`
- Use placeholders for symbols that cannot be rendered: `[SYMBOL: description]`

### Text Quality (Initial Pass)
- Remove page headers and footers (page numbers, running titles)
- Preserve all content - do not skip sections or paragraphs

### Do NOT (in this phase)
- Fix spelling or hyphenation (handled in Phase 5)
- Finalize heading levels (handled in Phase 6)
- Add content not present in the source

### Output
- If chunked: Save each chunk as `chunks/chunk_XXX-YYY.md`
- If not chunked: Save directly to `call-of-cthulhu-full.md`

---

## Phase 5: Post-Processing

### 5.1 Merge Chunks (if applicable)
If you created chunk files, merge them:
1. Concatenate chunks in page order
2. Remove duplicate headers/footers at chunk boundaries
3. Resolve split sentences or paragraphs at chunk edges
4. Ensure section continuity across boundaries

### 5.2 Fix Two-Column Artifacts
Two-column PDF layouts often produce:
- Extra spaces from column gutter alignment
- Text from alternating columns interleaved incorrectly
- Sentence fragments

Review and fix these issues.

### 5.3 Fix Line Break Issues
- Remove mid-sentence hard line breaks (normalize to paragraph flow)
- Preserve intentional line breaks (poetry, addresses, lists)
- Remove excessive blank lines (max 2 consecutive)

### 5.4 Fix Hyphenation
Rejoin words split by end-of-line hyphenation:
- "investi-\ngator" → "investigator"
- Preserve intentional hyphens (compound words, proper nouns)

### 5.5 Fix Spelling
Review for common OCR/extraction errors:
- Character substitutions (rn→m, l→1, O→0)
- Doubled characters
- Missing spaces between words
- Extra spaces within words

Use context to identify and fix errors. Document any uncertain corrections.

### 5.6 Fix Special Characters
- Replace garbled Unicode with correct characters
- Fix smart quotes if needed (or normalize to straight quotes)
- Ensure em-dashes, en-dashes render correctly

---

## Phase 6: Hierarchy Correction

Apply correct heading levels using the TOC from Phase 3 and content analysis.

### 6.1 Identify Heading Patterns
Look for these indicators:
- **ALL CAPS text** - Often major sections (H1 or H2)
- **Title Case on its own line** - Often subsections
- **Numbered sections** ("Act 1", "Part II", "1.0", "A.") - Follow numbering hierarchy
- **Bold or styled text** - May indicate headings in source

### 6.2 Apply TOC Hierarchy
Map headings to the TOC structure:
- TOC level 1 → `# H1`
- TOC level 2 → `## H2`
- TOC level 3 → `### H3`

### 6.3 Infer Missing Hierarchy
For sections not in the TOC:
- Use visual/formatting cues from the source
- Maintain consistency with surrounding content
- When uncertain, prefer deeper nesting (H3 over H2)

### 6.4 Verify Hierarchy
- No H3 should appear before any H2
- No H2 should appear before any H1
- Heading levels should not skip (H1 → H3 without H2)

---

## Phase 7: Quality Analysis

Read the complete final Markdown file and assess quality.

### 7.1 Completeness Check
- Verify all pages are represented
- Confirm no sections are missing
- Check that tables are present and formatted

### 7.2 Readability Assessment
Rate the following (1-5 scale):
- **Structural clarity**: Are headings logical and navigable?
- **Text flow**: Does content read naturally without artifacts?
- **Table integrity**: Are tables properly formatted and readable?
- **Callout formatting**: Are boxed text/notes properly marked?

### 7.3 Identify Remaining Issues
Document up to 3 specific remaining issues with examples:
- Quote the problematic text
- Explain the issue
- Note location (section/heading where it appears)
- Suggest fix if known

---

## Phase 8: Report Generation

Create `conversion-report.md` with the following structure:

```markdown
# PDF to Markdown Conversion Report

## Metadata
- Source file: [full path]
- Agent: [claude/gemini/qwen/codex]
- LLM model: [if visible to you, include the specific model ID, e.g., claude-opus-4-5-20251101, gemini-2.5-pro, qwen-max, etc.]
- Date: [YYYY-MM-DD]
- Output file: [path to final markdown]

## Original Prompt
[Include the complete prompt you were given - this entire document]

## Approach Summary
[Describe your actual process, including:]
- Preprocessing steps taken
- Chunking decision and rationale
- Text extraction method used
- Post-processing techniques applied
- Any deviations from the prompt and why

## Phase Results

### Phase 2: Preprocessing
- Images extracted: [count]
- Image-stripped PDF size: [size]
- Chunking: [yes/no, if yes: chunk count and sizes]

### Phase 3: TOC Extraction
- TOC method: [embedded outline / visual parse / inference]
- Sections identified: [count]
- TOC issues encountered: [describe any]

### Phase 4: Text Extraction
- Extraction method: [native read / OCR / hybrid]
- Pages processed: [count]
- Initial issues noted: [list]

### Phase 5: Post-Processing
- Mashed TOC cleanup: removed any remaining in-text TOC lines that collapsed into a single line
- TOC indentation: derived from the level column in toc-extracted.txt (level 1 = no indent, level 2 = two spaces, etc.)
- Two-column artifacts fixed: [yes/no, examples]
- Hyphenation fixes: [count]
- Spelling corrections: [count, list notable ones]
- Line break normalizations: [count]

### Phase 6: Hierarchy Correction
- Heading pattern used: [describe]
- H1 count: [n]
- H2 count: [n]
- H3 count: [n]
- Hierarchy issues resolved: [describe]

## Quality Assessment

### Ratings (1-5)
- Structural clarity: [n]/5
- Text flow: [n]/5
- Table integrity: [n]/5
- Callout formatting: [n]/5
- Overall quality: [n]/5

### Remaining Issues (up to 3)

#### Issue 1: [Title]
- **Location**: [section/heading]
- **Problem**: [description]
- **Example**: `[quoted text]`
- **Suggested fix**: [if known]

#### Issue 2: [Title]
[same format]

#### Issue 3: [Title]
[same format]

## Unresolved Challenges
[Describe any aspects of the conversion that could not be fully addressed and why]

## Recommendations
[Suggestions for improving future conversions of similar documents]
```

---

## Success Criteria

The conversion is successful if:
1. All 50 pages of content are represented in the output
2. Heading hierarchy is consistent and matches document structure
3. Tables are formatted as Markdown tables (not bullet lists)
4. Boxed text/callouts are formatted as blockquotes
5. No obvious missing sections
6. Text flows naturally without significant artifacts
7. Conversion report is complete and honest about quality

---

## Notes

- **Do not fabricate content** - Only include text present in the source PDF
- **Document uncertainties** - If unsure about a conversion choice, note it in the report
- **Preserve game mechanics** - Stats, dice notation (1d6, 2d10), and rules text must be accurate
- **Image placeholders** - Use `[FIGURE: description]` where images were removed; the extracted images in `images/` can be reinserted later

## Approach Summary
Replaced the initial redaction-based stripping with PyMuPDF image deletion (delete_image + garbage=4 + deflate=True), producing a much smaller no-images PDF that preserves text. Conversion now uses direct text extraction from the no-images PDF and a light cleanup pass (TOC block replacement from toc-extracted.txt to preserve line breaks, TOC leader cleanup, bullet normalization, heading heuristics, hyphenation repair, paragraph line-merge). Phase 6 now combines TOC mapping with a font-family mapping pass to apply headings, callouts, and quote formatting based on font size/family. OCR is no longer required for this file.

## Scripts Used
- Image removal: /home/todd/Dev/gm-kit/temp-resources/conversions/call-of-cthulhu/codex/remove_images_delete.py
- Phase pipeline (phases 4-6): /home/todd/Dev/gm-kit/temp-resources/conversions/call-of-cthulhu/codex/convert_pipeline_steps.py
- Font family sampler: /home/todd/Dev/gm-kit/temp-resources/conversions/call-of-cthulhu/codex/font_family_sampler.py
- Legacy conversion (not used for final output): /home/todd/Dev/gm-kit/temp-resources/conversions/call-of-cthulhu/codex/convert_no_images_to_markdown.py

## Phase Results

### Phase 2: Preprocessing
- Images extracted: 109
- Image-stripped PDF size: 1184899 bytes
- Chunking: no (direct conversion from no-images PDF)

### Phase 3: TOC Extraction
- TOC method: embedded outline
- Sections identified: 25
- TOC issues encountered: none noted (titles appear complete)

### Phase 4: Text Extraction
- Extraction method: native text extraction from no-images PDF (PyMuPDF)
- Pages processed: 50
- Initial issues noted: line breaks within paragraphs; some title-casing noise

### Phase 5: Post-Processing
- Mashed TOC cleanup: removed any remaining in-text TOC lines that collapsed into a single line
- TOC indentation: derived from the level column in toc-extracted.txt (level 1 = no indent, level 2 = two spaces, etc.)
- Two-column artifacts fixed: partial (paragraph line-merge only)
- Hyphenation fixes: handled during merge pass
- Spelling corrections: 0 (not manually corrected)
- Line break normalizations: 0

### Phase 6: Hierarchy Correction
- Heading pattern used: TOC-driven H1/H2/H3 plus font-family mapping for headings and callouts
- Callouts: `gm_note` labels rendered as blockquotes with **GM Note:** prefix
- Quotes: `quote` rendered as italic blockquote; `quote_author` rendered as em-dash author line
- Drop labels: `-` removes repeated headers/footers entirely
- Body labels: `body` now strips any pre-existing heading markers in the line
- Inline headings: split mixed lines when heading-labeled phrases appear inside a paragraph (e.g., “Winners and Losers”).

## Quality Assessment

### Ratings (1-5)
- Structural clarity: 3/5
- Text flow: 3/5
- Table integrity: 2/5
- Callout formatting: 2/5
- Overall quality: 3/5

### Remaining Issues (up to 3)

#### Issue 1: Heading hierarchy needs refinement
- **Location**: Multiple sections
- **Problem**: Heuristic headings may not align with TOC levels; H1 is missing.
- **Example**: Section titles appear as H2/H3 without a top-level H1.
- **Suggested fix**: Map extracted TOC levels to explicit H1/H2/H3 headings.

#### Issue 2: Tables flattened
- **Location**: Rules tables
- **Problem**: Tables are not consistently reconstructed as Markdown tables.
- **Example**: Lists appear as prose rather than pipe tables.
- **Suggested fix**: Add table detection pass based on alignment/column spacing.

#### Issue 3: Callouts not consistently marked
- **Location**: Boxed text / read-aloud sections
- **Problem**: Callouts are not reliably converted to blockquotes.
- **Example**: Boxed guidance renders as plain paragraphs.
- **Suggested fix**: Detect boxed text markers or styling cues during extraction.

## Unresolved Challenges
Direct text extraction preserves content, but formatting cues (tables, boxed text, exact heading levels) are not encoded in the text layer. Further structure inference is needed to reach high-fidelity Markdown.

## Recommendations
Use TOC mapping for heading levels, add a table reconstruction pass, and detect callout blocks by layout cues or keyword prefixes.
Add a scope disclaimer: conversion is meant to make the module understandable to the agent, not perfectly formatted for human reading; users can refine formatting after the baseline conversion (with agent help if desired).
Add a diagnostics/debug mode that zips a work-area bundle (original PDF, per-phase Markdown iterations, and a run report capturing what was attempted, what worked, what was abandoned, and issues encountered) for GitHub issue reporting.

## MVP Follow-ups
- Remove OCR fallback from the MVP; assume text‑extractable PDFs and direct users to external tools for image‑only scans.
- Add a late-stage (Phase 7) review step where any text removal happens after structure is stabilized.
- Define which phases are code-driven vs agent-driven vs user-confirmed; some issues are best handled by automated logic, others by agent fixes, and others by prompting the user for confirmation.
- Include a user-review pass that surfaces oddities with suggested fixes (e.g., inline headings like “Firearms” appearing mid-sentence) and asks the user before applying changes.
- Perform deduplication via user-confirmed prompts to avoid accidental loss of critical content.
- Detect scenario keywords like “Keeper’s Note/Notes” and prompt the user to map them to gm_note formatting.
- Default gm_note formatting should be blockquote-based for portability: `> **GM Note:** ...`
## Font Family Sampling (POC)
- Script: temp-resources/conversions/call-of-cthulhu/codex/font_family_sampler.py
- Output samples: temp-resources/conversions/call-of-cthulhu/codex/font-family-samples.md
- Mapping (with samples + prefilled labels): temp-resources/conversions/call-of-cthulhu/codex/font-family-mapping.json
- Purpose: collect representative text examples per font size/family so the user can label which sizes correspond to headings, read-aloud, GM notes, etc.
- Phase 6 uses the mapping to format headings/callouts/quotes in the final Markdown.


- Prefill logic: labels guessed by matching sample text to TOC titles (level 1 -> #, level 2 -> ##, level 3 -> ###).
- Samples: limited to 8 lines per font family (dominant span per line).
- Drop behavior: family-level "-" is treated as body; remove unwanted headers/footers via search/replace or manual cleanup.
- Size note: including all samples ballooned the mapping to ~9,000 lines (~260 KB), which is too large to edit comfortably.
- Quote format applied: `quote` -> `> *text*`, `quote_author` -> `> — Author`
