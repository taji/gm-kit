# E7-04 Chapter Segmentation + Chunk Planning Design

**Goal:** Add TOC-driven chapter segmentation and chunk planning so large PDFs produce deterministic, navigable chunk maps without merging chunks back into one markdown document by default.

## Architecture
E7-04 consumes the canonical TOC artifacts produced by E7-03 and turns the top-level outline entries into a structural chapter index plus a chunk plan for downstream markdown generation. The TOC remains authoritative for chapter order and structure, including front matter and appendices when they are present in the outline. Nested same-page bookmarks remain valid source data, but they do not become separate chapter segments. The planner uses a fixed 10-page budget: chapters at or below budget stay intact; oversized chapters split on page boundaries into 10-page pieces.

The feature remains prep-side only. It does not generate final markdown, does not merge chunks at the end, and does not alter the existing conversion pipeline semantics. It only describes how the downstream pipeline should segment content.

## Artifact Contract
E7-04 only emits chunk artifacts when chunking is actually needed.

Required artifacts when chunking is needed:
- `chapter-index.json`
- `chunk-plan.json`

`chapter-index.json` records the TOC-derived structural units:
- section id/key
- section title
- TOC level
- section kind: `front_matter`, `body`, or `appendix`
- start page
- end page
- page count
- split-needed flag

`chunk-plan.json` records the actual segmentation plan:
- chunk id/key
- source section id/key
- chunk kind: `chapter` or `page-split`
- ordinal within the source section
- start page
- end page
- page count
- downstream markdown target path
- budget metadata used to derive the chunk

If the document does not exceed the chapter budget, the prep run should not emit these two artifacts.

## Chunk Rules
- TOC order is the source of truth.
- Include TOC-visible front matter and appendices.
- Keep a chapter intact when it fits within the 10-page budget.
- Split an oversized chapter only on page boundaries.
- Do not split across chapter boundaries unless the chapter itself exceeds the budget.
- Do not merge chunk output into a single large markdown document by default.
- The result must be deterministic for a given PDF and budget.

## Failure Handling
- Missing or malformed TOC data fails chunk planning.
- Invalid page spans fail the chapter index builder.
- Overlapping or non-monotonic section spans fail validation instead of guessing.
- If chunking is not needed, skip plan artifact emission rather than writing empty placeholders.
- Failure messages should be sanitized and recorded through the prep failure path.

## Testing Strategy
- Verify TOC-visible front matter is included in the chapter index.
- Verify appendix sections are included when present.
- Verify chapters at or under budget remain single chunks.
- Verify oversized chapters split into 10-page page chunks.
- Verify nested same-page outline entries do not fragment chapter boundaries.
- Verify chunk planning is deterministic for the same input PDF.
- Verify malformed TOC data or invalid page spans fail cleanly.
- Verify no chunk artifacts are written when the document fits the budget.

## Scope Notes
- E7-04 does not generate markdown content.
- E7-04 does not merge chunks.
- E7-04 does not add guidance or annotations; later Epic 7 features own that.
