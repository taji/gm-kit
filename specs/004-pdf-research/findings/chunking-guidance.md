# Chunking Guidance (Research Notes)

These notes summarize practical chunking choices for AI-only PDF→Markdown conversion.
Use them to pick chunk sizes and merge strategy during E4-01–E4-06 testing.

## When to Chunk
- Chunk AI inputs to stay under agent upload/token limits.
- Avoid chunking for CLI/Python extraction; only chunk later if using AI for cleanup.

## Recommended Workflow
1. Use `qpdf --json=1` to inspect per-page content/image streams.
2. Estimate per-page byte weight from stream lengths.
3. Choose page ranges that keep each chunk under the target size limit.
4. Run `qpdf --pages` to produce the chunk PDFs.

## Chunk Boundaries
- Default to page-based chunks.
- Use section/heading boundaries only if headings are highly reliable.
- Avoid overlap unless gaps or cutoffs are observed during review.

## Suggested Chunk Sizes (Conservative)
- Dense or complex layouts: 5–10 pages per chunk.
- Cleaner text-heavy PDFs: 10–15 pages per chunk.
- If output quality degrades, reduce chunk size and increase overlap.

## Agent Upload Limits (Reference)
- Gemini: ~50 MB per file
- Claude: ~32 MB per file
- Qwen: 20 MB per file (hard limit)
- Codex CLI: instruction file limit is 32 KiB by default; large file handling depends on model context window

## Practical Guidance
- Target **19 MB max** chunk size to stay within Qwen’s limit across all agents.
- Treat **20 MB** as a hard ceiling.
- If a chunk exceeds 19 MB, split that page range further.

## Two-Column PDFs (Known Limitation)
- `pdftotext`-only extraction can drop or reorder content in dense two-column layouts.
- For two-column PDFs, prefer OCR or multimodal PDF readers (Claude/Gemini) when available.

## Merge Guidance
- Deduplicate repeated headers/footers across chunks.
- Resolve split sentences at chunk edges.
- Carry forward section headers when a chunk starts mid-section.

## Notes From Prior Work
- A 334-page rulebook was successfully split into ~10–55 page chunks,
  producing chunk files in the ~1–10 MB range.
