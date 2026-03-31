# Step 3.2: Parse Visual TOC Page

## Task
Parse the visual TOC (Table of Contents) page from the PDF and extract hierarchical entries.

## Input
- `toc_visual_text`: Text content of the TOC page(s)
- `total_pages`: Total number of pages in the document

## Instructions
1. Identify the TOC page by looking for headings like "Contents", "Table of Contents", or similar
2. Extract entries with their hierarchy levels:
   - Level 1: Main chapters/sections (no indent)
   - Level 2: Subsections (2-space indent)
   - Level 3: Sub-subsections (4-space indent)
3. Capture the page number for each entry in `(page N)` format
4. Output format: indented text with 2 spaces per level
   - Example: `Chapter One (page 5)` / `  Section 1.1 (page 7)`

## Output Format
Write a JSON object to `step-output.json`:
```json
{
  "step_id": "3.2",
  "status": "success",
  "data": {
    "entries": [
      {"level": 1, "title": "Introduction", "page": 3},
      {"level": 1, "title": "Chapter One", "page": 5},
      {"level": 2, "title": "Section 1.1", "page": 7}
    ]
  },
  "rubric_scores": {
    "completeness": 5,
    "level_accuracy": 5,
    "page_accuracy": 5,
    "output_format": 5
  },
  "warnings": []
}
```

## Rubric Scoring Requirements
- `rubric_scores` MUST include all required dimensions: `completeness`, `level_accuracy`, `page_accuracy`, `output_format`.
- Each dimension score MUST be an integer from 1 to 5.
- `warnings` MUST always be present (use `[]` when there are no warnings).

## Edge Cases
- If no TOC found, return empty entries array with appropriate warning
- Handle multi-page TOCs
- Ignore page numbers in the middle of content (only capture end-of-line page numbers)
