# PDF to Markdown Conversion Architecture

This document captures the architecture and design decisions for the PDF to Markdown conversion pipeline, derived from research phases E4-01 through E4-06 and iterative POC testing.

**Version:** v10 (2026-01-29)
**Status:** Ready for implementation
**Related features:** E4-07a, E4-07b, E4-07c, E4-07d, E4-07e

---

## Overview

The conversion pipeline consists of 11 phases with 70 total steps, categorized by execution type:

| Category | Count | Description |
|----------|-------|-------------|
| Code | 49 | Deterministic automation via Python/PyMuPDF |
| Agent | 15 | Judgment calls requiring AI analysis |
| User | 5 | Confirmation steps requiring human decision |

### Design Principles

**Category Pyramid:** Maximize Code (reliable automation), then Agent (judgment calls), then User (only when needed).

**Generate Early, Confirm Late:** Create artifacts (JSON, detection data) early in the pipeline; defer user review until all analysis is complete.

**Primary Audience:** The agent, not the user. Prefer consistency over aesthetics.

---

## Operational Patterns

### Error Conditions

Each phase defines explicit error conditions that halt processing. Errors are reported with actionable guidance.

| Phase | Condition | Error Message | Action |
|-------|-----------|---------------|--------|
| 0 | PDF file not found or unreadable | `ERROR: Cannot open PDF - file not found or corrupted` | Verify file path and PDF integrity |
| 0 | Scanned PDF (< 100 chars extracted) | `ERROR: Scanned PDF detected - very little extractable text` | Run external OCR first (out of scope) |
| 0 | User declines to proceed | `ABORT: User cancelled after pre-flight report` | No action needed |
| 1 | Cannot create working directory | `ERROR: Cannot create output directory - check permissions` | Verify write permissions |
| 2 | Image removal fails | `ERROR: Failed to create text-only PDF` | Check PyMuPDF installation |
| 3 | No TOC found (embedded or visual) | `WARNING: No TOC found - hierarchy may be incomplete` | Continue with font-based detection only |
| 4 | Text extraction yields empty result | `ERROR: No text extracted from PDF` | Verify PDF has selectable text |
| 4 | Two-column issues > 50% of pages | `WARNING: Pervasive two-column issues detected - expect manual review` | User informed, continues with warning |
| 5-6 | Input markdown file missing | `ERROR: Phase input file not found - run previous phase first` | Resume from earlier checkpoint |
| 7 | Font-family JSON missing or invalid | `ERROR: font-family-mapping.json not found or malformed` | Re-run Phase 3 |
| 8 | TOC map empty and no font labels | `WARNING: No heading sources available - flat document structure` | Continue without hierarchy |
| 9 | Lint violations exceed threshold (20+) | `WARNING: Many lint violations - document may need significant cleanup` | User reviews issues |
| 10 | Cannot create diagnostic bundle | `WARNING: Failed to create zip bundle - files saved individually` | Check disk space |

### Retry Logic

Agent steps may produce malformed or incomplete output. The pipeline implements retry with validation:

**Retry Policy:**
- **Max attempts:** 3 per Agent step
- **Validation:** Check output against contract before accepting
- **Backoff:** None (immediate retry with refined prompt)
- **Escalation:** After 3 failures, log error and either skip step (if non-critical) or halt with user prompt

**Agent Step Criticality:**

Criticality indicates the impact on conversion quality if an agent step fails after 3 retries:
- **High**: Essential - halt and require user intervention
- **Medium**: Important - flag for user or skip with degraded output
- **Low**: Nice-to-have - skip silently, minor quality loss

| Step | Description | Criticality | On Failure After Retries |
|------|-------------|-------------|--------------------------|
| 3.2 | Parse visual TOC page | Medium | Skip - use font-based hierarchy only |
| 4.6 | Resolve split sentences at chunk boundaries | Low | Skip - minor sentence boundary issues acceptable |
| 6.4 | Fix OCR spelling artifacts (rn→m, l→1) | Low | Skip - spelling errors remain but don't block |
| 7.7 | Detect table structures | Medium | Skip - tables may not be detected |
| 8.7 | Convert tables to markdown format | Medium | Flag for user - tables render as text |
| 8.8 | Apply blockquote formatting to callouts | Medium | Flag for user - callouts may be plain text |
| 8.9 | Insert figure/map placeholders | Low | Skip - figure placeholders omitted |
| 9.1-9.5 | Quality checks (completeness, structure, flow, tables, callouts) | High | Halt - quality assessment required |
| 9.7-9.8 | Review TOC issues + two-column reading order | Medium | Flag for user - issues may remain |
| 10.2-10.3 | Quality ratings + document remaining issues | Low | Skip - report incomplete but conversion done |

**Retry Prompt Enhancement:**
On retry, append to prompt:
```
Previous attempt produced invalid output. Specific issue: [validation error].
Please correct and ensure output matches the required format exactly.
```

**User Recovery After Agent Failure:**

When an agent step fails after 3 retries and requires user involvement (High or Medium criticality), the user is prompted with these options:

| Option | How | When to use |
|--------|-----|-------------|
| Provide manual input | Enter response at interactive prompt | User knows the correct answer |
| Re-run the step | `gmkit pdf-convert --from-step X.Y <dir>` | User fixed something external (e.g., edited source file) |
| Skip and continue | Type "skip" at prompt | Accept degraded output, fix manually later |

### User Interaction Format

User steps present choices in plain-text aligned format for terminal compatibility. Markdown tables are avoided because not all agent CLIs render them properly.

**Design Principles:**
- Use fixed-width aligned columns with unicode box-drawing or dashes
- Truncate long text samples at 30 characters with "..."
- Full data available in JSON files if user needs complete text
- Options presented as simple lettered choices (A/B/C/Custom)

**Standard User Prompt Template:**

```
══════════════════════════════════════════════════════════════
  Step X.Y: [Topic]
══════════════════════════════════════════════════════════════

Context: [Brief explanation of what was analyzed]

Analysis Summary:
  • [Key finding 1]
  • [Key finding 2]
  • [Key finding 3]

Options:
  A) [First option - typically recommended]
  B) [Second option]
  C) [Third option if applicable]
  Custom) Type your own response

Recommendation: Option A - [brief rationale]

Your choice [A/B/C/Custom]: _
```

**Step-Specific Formats:**

**Step 0.6 (Pre-flight Confirmation):**
```
══════════════════════════════════════════════════════════════
  Pre-flight Analysis Complete
══════════════════════════════════════════════════════════════

PDF: example-module.pdf (12.4 MB, 48 pages)

  Metric              Value              Note
  ─────────────────────────────────────────────────────────────
  Images              34                 Will be extracted to images/
  Text                extractable        Native text found
  TOC                 embedded           Will use PDF outline
  Fonts               8 families         Moderate complexity
  Copyright           "© 2024 Chaosium"  Found in metadata
  Complexity          moderate

User involvement required in: Phase 7 (font labels), Phase 9 (review)

Options:
  A) Proceed with conversion
  B) Abort

Your choice [A/B]: _
```

**Step 7.10 (Font Label Review):**
```
══════════════════════════════════════════════════════════════
  Font Family Label Review
══════════════════════════════════════════════════════════════

Detected 6 font families. Please verify labels:

  #   Font                   Size    Uses  Page  Sample (truncated)            Inferred
  ─────────────────────────────────────────────────────────────────────────────────────────
  1   TimesNewRoman-Bold     18pt    1     1     "Call of Cthulhu Quick..."    H1
  2   TimesNewRoman-Bold     14pt    8     3     "CHAPTER ONE: THE MDN..."     H2
  3   TimesNewRoman-Bold     12pt    24    5     "The Village"                 H3
  4   TimesNewRoman-Italic   10pt    15    7     "Keeper's Note: The pl..."    callout
  5   TimesNewRoman          10pt    847   3     "The villagers gathere..."    body
  6   Courier                9pt     32    12    "1d6 + 2"                     code

Full samples available in: font-family-mapping.json

Instructions:
  • Inferred labels shown above are applied by default
  • To change specific labels, use number:label format: "3:H3, 5:skip"
  • Heading labels accept either format: H1/H2/H3/H4 or #/##/###/####
  • Valid labels:
      H1 or #      = Heading level 1
      H2 or ##     = Heading level 2
      H3 or ###    = Heading level 3
      H4 or ####   = Heading level 4
      body         = Normal paragraph text
      callout      = GM notes, read-aloud, boxed text
      code         = Monospace/stat blocks
      skip         = Ignore this font (don't use for detection)
  • Type "confirm" to accept all inferred labels as shown

Changes (or "confirm"): _
```

**Step 9.9 (Header/Footer Removal):**
```
══════════════════════════════════════════════════════════════
  Header/Footer Removal
══════════════════════════════════════════════════════════════

Detected candidates (appear on 3+ pages):

  #   Text                        Pages     Freq    Recommendation
  ─────────────────────────────────────────────────────────────────────────
  1   "Page 12"                   2-50      98%     Remove (page number)
  2   "Chapter One: The Villa..." 5-20      32%     Keep (varies by section)
  3   "© 2024 Chaosium Inc."      1-50      100%    Remove (copyright footer)
  4   "Call of Cthulhu Quick..."  1-50      100%    Remove (running header)

Options:
  A) Remove items 1, 3, 4 (recommended)
  B) Remove all detected
  C) Remove none
  Custom) Specify which to remove (e.g., "1,3,4")

Your choice [A/B/C/Custom]: _
```

**Step 9.10-9.11 (Final Review):**
```
══════════════════════════════════════════════════════════════
  Final Review: 3 Issues Found
══════════════════════════════════════════════════════════════

Issue 1 of 3: Heading Hierarchy
  Location: Line 142 (Section: The Cave)
  Problem:  H4 follows H2 (skipped H3)
  Before:   "#### The Hidden Passage"
  Fix:      "### The Hidden Passage"

  [A] Apply fix  [B] Skip  [C] Custom: _

──────────────────────────────────────────────────────────────

Issue 2 of 3: OCR Artifact
  Location: Line 287
  Problem:  Likely "rn" → "m" error
  Before:   "The ancient torne"
  Fix:      "The ancient tome"

  [A] Apply fix  [B] Skip  [C] Custom: _

──────────────────────────────────────────────────────────────

Issue 3 of 3: Two-Column Reading Order
  Location: Lines 45-52
  Problem:  Text appears out of order
  Before:   "...end of left column. Start of right column..."
  Fix:      [Manual review recommended]

  [A] Apply fix  [B] Skip  [C] Custom: _

══════════════════════════════════════════════════════════════
Summary: 3 issues shown
Apply all suggested fixes? [yes/no/review]: _
```

---

## Phase Summary

| Phase | Name | Steps | Primary Category |
|-------|------|-------|------------------|
| 0 | Pre-flight Analysis | 6 | Code (1 User) |
| 1 | Image Extraction | 4 | Code |
| 2 | Image Removal | 3 | Code |
| 3 | TOC & Font Extraction | 6 | Code (1 Agent) |
| 4 | Text Extraction & Merge | 7 | Code (1 Agent) |
| 5 | Character-Level Fixes | 9 | Code |
| 6 | Word/Token-Level Fixes | 5 | Code (1 Agent) |
| 7 | Structural Detection | 10 | Code (1 Agent, 1 User) |
| 8 | Hierarchy Application | 12 | Code (3 Agent) |
| 9 | Quality & Review | 11 | Agent/User |
| 10 | Report & Diagnostics | 6 | Code (2 Agent) |

---

## Detailed Phase Specifications

### Phase 0: Pre-flight Analysis

| Step | Description | Category |
|------|-------------|----------|
| 0.1 | Load PDF and extract metadata (file size, page count, title, author, creator, copyright if present) | Code |
| 0.2 | Count images across all pages | Code |
| 0.3 | Detect embedded TOC presence | Code |
| 0.4 | Check text extractability (scanned PDF detection) | Code |
| 0.5 | Analyze font families and estimate complexity | Code |
| 0.6 | Present pre-flight report and user involvement notice; await confirmation | User |

**Output:**
- Pre-flight report displayed to user
- `metadata.json` with extracted PDF metadata for use in copyright notices

**Pre-flight Report Contents:**
- File metrics: size, page count, image count, font family count
- Copyright info (if found): title, author, publisher, copyright notice
- Chunking decision: whether file exceeds threshold (30 pages or 15MB)
- TOC approach: embedded outline found vs visual parsing needed
- Text extractability: native text vs scanned (scanned = out of scope warning)
- Complexity assessment: low/moderate/high based on metrics
- User involvement notice: list of phases requiring user input

**Warnings that may appear:**
- "Scanned PDF detected" - Very little extractable text; recommend external OCR first
- "Very large file" - May require extended processing
- "No embedded TOC" - Agent will need to parse visual TOC page
- "Many font families (20+)" - Complex hierarchy; expect more user review in Phase 7
- "Two-column layout likely" - Potential reading order issues; Phase 9 review important

**User confirmation required before proceeding to Phase 1.**

### Phase 1: Image Extraction

| Step | Description | Category |
|------|-------------|----------|
| 1.1 | Create working folder structure | Code |
| 1.2 | Extract all images from PDF to `images/` subfolder | Code |
| 1.3 | Log image count and locations | Code |
| 1.4 | Log image positions (page, coordinates) to `images/image-manifest.json` | Code |

**Output:**
- `images/` folder with extracted images
- `images/image-manifest.json` (page numbers, coordinates, filenames for link injection)

### Phase 2: Image Removal

| Step | Description | Category |
|------|-------------|----------|
| 2.1 | Create text-only PDF by deleting image objects | Code |
| 2.2 | Save to `preprocessed/` subfolder | Code |
| 2.3 | Verify file size reduction | Code |

**Output:** `preprocessed/<filename>-no-images.pdf`

**Implementation (from POC):**
```python
import fitz

with fitz.open(input_pdf) as doc:
    for page in doc:
        image_list = page.get_images(full=True)  # full=True required
        for img in image_list:
            xref = img[0]
            page.delete_image(xref)
    doc.save(output_pdf, garbage=4, deflate=True)  # cleanup options on save()
```

**Notes:**
- `full=True` on `get_images()` ensures all image references are returned
- `garbage=4` removes unused objects for maximum size reduction
- `deflate=True` compresses streams
- Combined, `garbage=4` and `deflate=True` significantly reduce output file size (e.g., 50-page PDF from 2.1MB to 142KB in POC testing)
- This approach replaced an earlier redaction-based method that was less effective

### Phase 3: TOC & Font Extraction

| Step | Description | Category |
|------|-------------|----------|
| 3.1 | Extract embedded TOC outline via PyMuPDF | Code |
| 3.2 | If no embedded TOC, parse visual TOC page | Agent |
| 3.3 | Save TOC to `toc-extracted.txt` | Code |
| 3.4 | Sample font families/sizes from PDF | Code |
| 3.5 | Generate `font-family-mapping.json` with samples | Code |
| 3.6 | Pre-fill labels by matching samples to TOC titles | Code |

**Output:**
- `toc-extracted.txt` (format: `level|title|page`)
- `font-family-mapping.json`

**Note:** Step 3.2 must produce same output format as 3.1 for downstream compatibility.

**Label Inference Logic (Step 3.6):**

The label inference system pre-fills heading/structure labels to minimize user effort in Step 7.10.

**Single H1 Rule:** Each document must have exactly one H1 (the document title). All TOC-based headings start at H2 to ensure proper hierarchy. This follows HTML/accessibility best practices and prevents heading level conflicts.

*Document title (H1) identification:*
1. Check PDF metadata for "Title" field
2. If metadata empty, check cover page for largest text element
3. If no clear title found, use filename as H1 (agent can refine in Phase 8)
4. Mark this font as H1 (there will be only one H1 in the document)

*Primary method - TOC matching (with H2 offset):*
1. Extract TOC entries with their levels (from step 3.1 or 3.2)
2. Search for each TOC entry's text in the document body
3. Identify which font (family + size + style) that text uses
4. Assign label with offset: TOC level 1 → H2, TOC level 2 → H3, TOC level 3 → H4, etc.

*Fallback heuristics (when TOC doesn't cover all fonts):*

| Signal | Inferred Label |
|--------|----------------|
| Document title (from metadata/cover) | H1 (only one per document) |
| Largest non-title font in document | H2 |
| Second largest non-title font | H3 |
| Bold + larger than body text | H3 or H4 (by relative size) |
| Most frequent font in document | body |
| Monospace / Courier font family | code |
| ALL CAPS + larger than body | heading (minimum H2, level by size) |
| Very small font (< 8pt or smallest in doc) | skip (likely footnotes/page numbers) |

*Callout detection (keyword-based, not font-based):*

Callouts (GM notes, read-aloud text, boxed text) cannot be reliably inferred from font alone—publishers use inconsistent styling (italic, bold, different fonts, shaded boxes). Instead, detection relies on **keyword scanning** during Phase 7:

| Keyword Pattern | Callout Type |
|-----------------|--------------|
| "Keeper's Note:", "Keeper:", "For the Keeper:" | GM note |
| "GM Note:", "GM:", "For the GM:" | GM note |
| "Read Aloud:", "Read aloud:", "Read to players:" | Read-aloud |
| "Player Handout:", "Handout:" | Player handout |

Agent judgment in Phase 8 handles ambiguous cases (boxed text without keywords, visual sidebars described in the PDF).

*Example flow (Phase 3 - font inference):*
```
1. Document title identification:
   - PDF metadata "Title" = "Call of Cthulhu Quick-Start Rules"
   - Title font: TimesNewRoman-Bold @ 18pt
   - Inferred label: TimesNewRoman-Bold @ 18pt → H1 (only one)

2. TOC entry "Chapter One: The Village" is level 1
3. Find "Chapter One: The Village" in document body
4. Text uses TimesNewRoman-Bold @ 14pt
5. Inferred label: TimesNewRoman-Bold @ 14pt → H2 (TOC level 1 + 1)

6. TOC entry "The Inn" is level 2
7. Text uses TimesNewRoman-Bold @ 12pt
8. Inferred label: TimesNewRoman-Bold @ 12pt → H3 (TOC level 2 + 1)

9. Font TimesNewRoman @ 10pt is most frequent (not in TOC)
10. Inferred label: TimesNewRoman @ 10pt → body

11. Font Courier @ 9pt detected
12. Inferred label: Courier @ 9pt → code
```

*Example flow (Phase 7 - keyword-based callout detection):*
```
1. Scan text for keyword patterns
2. Found "Keeper's Note:" at line 142
3. Mark paragraph as callout (GM note)

4. Found "Read Aloud:" at line 287
5. Mark paragraph as callout (read-aloud)
```

### Phase 4: Text Extraction & Merge

| Step | Description | Category |
|------|-------------|----------|
| 4.1 | Check if PDF exceeds size/page threshold | Code |
| 4.2 | Chunk PDF into smaller files if needed | Code |
| 4.3 | Detect candidate headers/footers (flags only, no removal) | Code |
| 4.4 | Extract text from each chunk to markdown | Code |
| 4.5 | Merge chunk markdown files in page order | Code |
| 4.6 | Resolve split sentences at chunk boundaries | Agent |
| 4.7 | Detect two-column reading order issues (early warning) | Code |

**Output:** Merged markdown file (e.g., `<filename>-phase4.md`)

**Note:** Header/footer removal deferred to Phase 9 for user confirmation.

**Note:** Step 4.7 provides early detection of two-column issues. If pervasive (>15%), warns user before investing effort in later phases. Actual fix/review remains in Phase 9.

### Phase 5: Character-Level Fixes

| Step | Description | Category |
|------|-------------|----------|
| 5.1 | Fix two-column gutter spacing artifacts | Code |
| 5.2 | Fix end-of-line hyphenation (rejoin split words) | Code |
| 5.3 | Normalize line breaks (remove mid-sentence hard wraps) | Code |
| 5.4 | Fix garbled/strange Unicode characters | Code |
| 5.5 | Normalize quotes (smart quotes to straight) | Code |
| 5.6 | Normalize em-dashes and en-dashes | Code |
| 5.7 | Remove excessive blank lines (max 2 consecutive) | Code |
| 5.8 | Clean TOC leader artifacts (dots, symbols) | Code |
| 5.9 | Format TOC block with indented bullets | Code |

**Output:** `<filename>-phase5.md`

**Decision:** Always normalize quotes (5.5) - consistency over aesthetics, primary audience is agent.

**Decision:** Step 5.2 (hyphenation) runs before 5.3 (line breaks) so hyphen patterns (`word-\n`) are detected before line breaks are normalized.

### Phase 6: Word/Token-Level Fixes

| Step | Description | Category |
|------|-------------|----------|
| 6.1 | Normalize bullet characters (bullet to dash) | Code |
| 6.2 | Fix missing spaces between words | Code |
| 6.3 | Fix extra spaces within words | Code |
| 6.4 | Fix spelling errors (OCR artifacts: rn to m, l to 1, O to 0) | Agent |
| 6.5 | Split merged numbered list items | Code |

**Output:** `<filename>-phase6.md`

**CONCERN:** Step 6.5 flagged for potential unwanted side effects (may drop lines incorrectly).

**Step 6.4 Guidance - Preserving Domain Terminology:**

TTRPG modules contain domain-specific terms (monster names, locations, game terms) that look like spelling errors but must be preserved. The agent should use these heuristics:

| Signal | Action |
|--------|--------|
| Capitalized word (not at sentence start) | Preserve - likely proper noun |
| Word appears multiple times in document | Preserve - intentional term |
| Word appears in TOC or headings | Preserve - key term |
| Obvious OCR pattern (rn→m, l→1) AND result is dictionary word | Fix |
| Uncertain | Flag for user, don't auto-fix |

*Examples:*

| Text | Action | Reason |
|------|--------|--------|
| "The ancient torne" | Fix → "tome" | OCR error, "torne" not a word |
| "Nyarlathotep rises" | Preserve | Capitalized, proper noun |
| "the investigator's Sanity" | Preserve | Capitalized mid-sentence |
| "entered the rnansion" | Fix → "mansion" | Classic rn→m OCR error |
| "the Shoggoth attacks" | Preserve | Capitalized, appears in TOC |

### Phase 7: Structural Detection

| Step | Description | Category |
|------|-------------|----------|
| 7.1 | Build heading map from TOC (validate: flag gaps/duplicates for Phase 9) | Code |
| 7.2 | Load font-family mapping JSON | Code |
| 7.3 | Detect ALL CAPS headings | Code |
| 7.4 | Detect Title Case headings | Code |
| 7.5 | Detect GM/Keeper note keywords | Code |
| 7.6 | Detect read-aloud text markers | Code |
| 7.7 | Detect table structures | Agent |
| 7.8 | Detect inline/embedded headings within spans | Code |
| 7.9 | Update font-family-mapping.json with ALL detection findings | Code |
| 7.10 | Review font-family labels, prompt user if clarification needed | User |

**Output:** Updated `font-family-mapping.json` with detection labels and notes

**Decision:** Step 7.8 (inline heading detection) runs before 7.9 so findings update JSON before user review.

### Phase 8: Hierarchy Application

| Step | Description | Category |
|------|-------------|----------|
| 8.1 | Split spans to isolate embedded headings | Code |
| 8.2 | Apply heading levels (TOC exact match first, then font-family pattern match) | Code |
| 8.3 | Apply GM note blockquote formatting | Code |
| 8.4 | Apply read-aloud blockquote formatting | Code |
| 8.5 | Apply quote formatting (italic + attribution) | Code |
| 8.6 | Convert detected tables to markdown format | Agent |
| 8.7 | Apply blockquote formatting to callout boxes | Agent |
| 8.8 | Insert figure/map placeholders | Agent |
| 8.9 | Insert commented image links using manifest data | Code |
| 8.10 | Ensure single H1 at top (demote other H1s to H2, cascade child headings) | Code |
| 8.11 | Validate heading hierarchy (no level skips) | Code |
| 8.12 | Insert copyright notice block at document top (above H1) using metadata from step 0.1 | Code |

**Output:** `<filename>-phase8.md`

**Decision:** Step 8.1 (split spans) runs first so embedded headings are isolated before heading levels are applied in 8.2.

**Decision:** Step 8.9 inserts commented-out image links (e.g., `<!-- ![description](images/page005_img01.png) -->`) so position is preserved but not visible. User or agent can uncomment if desired.

**Step 8.10 Single-H1 Logic:**

Documents should have exactly one H1 (the title). If multiple H1s exist:
1. Keep the first H1 as the document title
2. Demote all other H1s to H2
3. Cascade demotion to child headings (H2→H3, H3→H4, etc.)

*Example:*
```
Before:                              After:
# Chapter One          (H1)          # Module Title         (H1 - added/kept)
## The Village         (H2)          ## Chapter One         (demoted)
### The Inn            (H3)          ### The Village        (cascaded)
# Chapter Two          (H1)          #### The Inn           (cascaded)
## The Forest          (H2)          ## Chapter Two         (demoted)
                                     ### The Forest         (cascaded)
```

**Note:** PDFs often have multiple title-like elements (cover page, interior title page, half-title). The pipeline handles this by keeping the first H1 encountered and demoting subsequent title-sized text to H2. No agent judgment required.

### Phase 9: Quality & Review

| Step | Description | Category |
|------|-------------|----------|
| 9.1 | Completeness check - verify all pages represented | Agent |
| 9.2 | Structural clarity assessment | Agent |
| 9.3 | Text flow / readability assessment | Agent |
| 9.4 | Table integrity check | Agent |
| 9.5 | Callout formatting check | Agent |
| 9.6 | Run markdown linter (pymarkdownlnt) and flag violations | Code |
| 9.7 | Review TOC validation issues (gaps, duplicates) | Agent |
| 9.8 | Two-column reading order: detect issues, fix if isolated (<15%), flag if pervasive (>15%) | Agent |
| 9.9 | Present header/footer candidates with smart analysis, user confirms removal | User |
| 9.10 | Present remaining issues (including lint violations) to user with suggested fixes | User |
| 9.11 | User confirms or provides corrections | User |

**Output:** Final validated markdown

**Decision:** Two-column fix (9.8) uses threshold - isolated issues fixed by agent, pervasive issues flagged for user decision.

**Decision:** Header/footer removal (9.9) deferred from Phase 4 to allow smart analysis and user confirmation.

### Phase 10: Report & Diagnostics

| Step | Description | Category |
|------|-------------|----------|
| 10.1 | Generate conversion report markdown | Code |
| 10.2 | Include quality ratings (1-5 scale) | Agent |
| 10.3 | Document up to 3 remaining issues with examples | Agent |
| 10.4 | Create diagnostic zip bundle (if `--diagnostics` flag specified) | Code |
| 10.5 | Include phase-by-phase markdown iterations (in bundle) | Code |
| 10.6 | Include original prompt for traceability (in bundle) | Code |

**Output:**
- `conversion-report.md` (always generated)
- `diagnostic-bundle.zip` (only if `--diagnostics` flag specified)

**Note:** Steps 10.5 and 10.6 only execute when `--diagnostics` is specified, as their output goes into the bundle.

---

## Testing Strategy

### Code Steps (49 steps) - Development/CI

Standard TDD approach:
- Unit tests for each function/module
- Integration tests for phase transitions
- Property-based tests for invariants

### Regression Testing Principle

**Any anomaly discovered during integration testing that requires a code change must be accompanied by a new unit test covering that specific anomaly.**

This ensures:
- Every PDF-specific fix gets a dedicated test
- The test suite grows to cover real-world edge cases found in actual PDFs
- Future changes don't regress previously fixed issues

**Workflow:**
1. Integration test reveals anomaly (e.g., specific PDF produces garbled output in step 5.4)
2. Isolate the minimal input that triggers the issue
3. Write a failing unit test with that input
4. Fix the code to pass the test
5. Verify integration test now passes

### Agent Steps (15 steps) - Development/CI Only

These tests validate agent prompts during development and CI. Production users do not run these tests - they execute the validated pipeline directly.

| Approach | Description | Best For |
|----------|-------------|----------|
| Contract testing | Define input/output contracts | Structured output (3.2, 7.8) |
| Rubric-based evaluation | Define criteria output must meet | Quality checks (9.1-9.5) |
| Golden file comparison | Compare to known-good output, check key elements | Complex transformations (8.6, 8.7) |
| Structural validation | Validate markdown structure is well-formed | Table conversion, hierarchy |
| Property-based testing | Define invariants (e.g., TOC count matches headings) | Cross-phase consistency |
| Agent-as-judge | Second agent evaluates output against criteria | Subjective quality (6.4, 9.3) |

### Markdown Linting - Production Step

Unlike agent testing, markdown linting (step 9.6) runs during production conversions as a user-facing quality check. Lint violations are surfaced to the user in step 9.10.

Tool: `pymarkdownlnt`

Key rules:
- MD001: Heading levels increment by one
- MD003: Heading style consistency
- MD007: Unordered list indentation
- MD012: Multiple consecutive blank lines
- MD022: Headings surrounded by blank lines
- MD041: First line is top-level heading

---

## Dependencies

| Dependency | Purpose | Install |
|------------|---------|---------|
| PyMuPDF (fitz) | PDF operations (image extraction, text extraction, TOC) | `pip install pymupdf` |
| pymarkdownlnt | Markdown linting | `pip install pymarkdownlnt` |

---

## Feature Split

### E4-07a: Code-Driven Pipeline

**Scope:** All 49 Code-category steps

**Deliverables:**
- Python package with modular phase functions
- Unit and integration test suite
- CLI interface for running pipeline

**Phases covered:** 1, 2, most of 3-8, scaffolding for 9-10

### E4-07b: Agent-Driven Pipeline

**Scope:** All 15 Agent-category steps

**Deliverables:**
- Prompt templates for each agent step
- Contract definitions for input/output
- Rubric definitions for evaluation
- Integration with Code pipeline

**Steps covered:** 3.2, 4.6, 6.4, 7.7, 8.6-8.8, 9.1-9.5, 9.7-9.8, 10.2-10.3

### E4-07c: User Interaction Workflow

**Scope:** All 5 User-category steps

**Deliverables:**
- Interactive prompts for user confirmation
- Before/after display for proposed changes
- Smart analysis presentation (headers/footers)
- Correction capture and application

**Steps covered:** 7.10, 9.9-9.11

### E4-07d: Image Link Injection

**Scope:** Image position tracking and commented link injection

**Deliverables:**
- Image manifest generation during extraction (step 1.4)
- Commented image link injection during hierarchy application (step 8.9)
- Licensing caution documentation

**Steps covered:** 1.4, 8.9

### E4-07e: Command Orchestration

**Scope:** `/gmkit.pdf-to-markdown` command and CLI interface

**Deliverables:**
- Command prompt file defining full conversion flow
- CLI interface (`gmkit pdf-convert`) with resume/retry capabilities
- Pre-flight analysis (Phase 0)
- State tracking (`.state.json`) for progress and resumability
- User involvement notices and interaction patterns
- Bash and PowerShell script templates for setup
- Integration orchestration for E4-07a/b/c/d components

**CLI Interface:**
```bash
gmkit pdf-convert <pdf-path> --output <dir>      # Full pipeline
gmkit pdf-convert <pdf-path> --output <dir> --diagnostics  # Include diagnostic bundle
gmkit pdf-convert --resume <conversion-dir>      # Resume from checkpoint
gmkit pdf-convert --phase 5 <conversion-dir>     # Re-run specific phase
gmkit pdf-convert --from-step 5.3 <conversion-dir>  # Re-run from step
gmkit pdf-convert --status <conversion-dir>      # Check progress
```

**Steps covered:** 0.1-0.6 (Pre-flight), orchestration of all phases

---

## Key Decisions Log

| Decision | Rationale |
|----------|-----------|
| Phase 0 pre-flight | Analyze PDF and set user expectations before committing to full pipeline |
| 3.2 uses Agent | TOC formats vary widely; agent judgment needed |
| 5.2 before 5.3 | Hyphenation fix needs line breaks intact to detect `word-\n` pattern |
| 5.5 always normalizes quotes | Consistency over aesthetics; agent is primary audience |
| 4.3 detects only, 9.9 removes | User confirmation prevents accidental content loss |
| 4.7 early two-column detection | Warn user early if pervasive issues; avoid wasted effort in later phases |
| 7.9 before 7.10 | Inline heading detection informs JSON before user review |
| 8.1 split spans first | Embedded headings must be isolated before heading levels applied |
| 9.8 uses threshold | Isolated issues (<15%) fixed; pervasive flagged for user |
| pymarkdownlnt for linting | Pure Python, pip installable, configurable rules |
| Explicit error conditions | Learned from spec-kit: clear "If X: ERROR" patterns aid debugging |
| Agent retry with max 3 | Learned from spec-kit: validation checkpoints with bounded retries |
| Table-based user prompts | Learned from spec-kit: structured options improve UX and reduce ambiguity |
| Single H1 document structure | HTML/accessibility best practice; TOC level 1 → H2, title is sole H1 |

---

## Flagged Concerns

| Step | Concern |
|------|---------|
| 6.5 | Split merged numbered list items may have unwanted side effects (drop lines incorrectly) |

---

## References

- Findings: `specs/004-pdf-research/findings/`
- Checklist: `specs/004-pdf-research/findings/review-checklist.md`

## Prior Art (POC Scripts)

The Codex POC scripts in `specs/004-pdf-research/poc-scripts/` demonstrate approaches for several phases. **Reference for learning; implement fresh based on this architecture.**

| File | Phases | Notes |
|------|--------|-------|
| `poc-scripts/remove_images_delete.py` | Phase 2 | Image removal - approach adopted in architecture |
| `poc-scripts/convert_pipeline_steps.py` | Phases 4-6 | Text extraction, cleanup, hierarchy - study for patterns |
| `poc-scripts/font_family_sampler.py` | Phase 3 | Font sampling and label inference |
| `poc-scripts/toc-extracted.txt` | Phase 3 | Example output format for step 3.3 |
| `poc-scripts/font-family-mapping.json` | Phase 3 | Example output format for step 3.5 |
| `poc-scripts/conversion-report.md` | All | POC conversion report with lessons learned |
| `findings/call-of-cthulhu-codex-report.md` | All | Detailed findings report (incorporates earlier Qwen/Gemini learnings) |

**Guidance:**
- Study POC to understand edge cases encountered
- Do not copy POC code directly - it may have hardcoded assumptions
- Implement fresh based on architecture spec
- POC is Call of Cthulhu specific; implementation must generalize
