# Step 8.7: Convert Tables to Markdown

## Task
Convert detected table regions into properly formatted markdown tables.

## Input
- `table_image`: Path to the cropped table image (from step 7.7)
- `table_crop`: Bounding box of the table region
- `flat_text`: The garbled/flat text extracted from the table area
- `table_id`: Identifier for this table
- `page_number`: 1-based page number

## Instructions
1. Examine the table image and the garbled flat text
2. Reconstruct the table structure:
   - Identify header row(s)
   - Count data rows and columns
   - Handle merged cells (use empty cells or appropriate spanning)
   - Preserve all cell content accurately
3. Create a properly formatted markdown table:
   - Use `|` as column separator
   - Include header separator line with alignment indicators
   - Ensure proper spacing for readability
   - Handle text alignment (left/center/right) based on content type

## Markdown Table Format
```markdown
| Header 1 | Header 2 | Header 3 |
|:---------|:--------:|---------:|
| Left     | Center   | Right    |
| Cell     | Cell     | Cell     |
```

## Output Format
Write to `step-output.json`:
```json
{
  "step_id": "8.7",
  "status": "success",
  "data": {
    "tables": [
      {
        "table_id": "t1",
        "markdown": "| Armor Class | Type of Armor |\n|:-----------:|:--------------|\n| 9 | None |\n| 8 | Shield only |",
        "rows": 9,
        "columns": 2
      }
    ],
    "changes_made": 1
  },
  "rubric_scores": {
    "row_column_fidelity": 5,
    "markdown_validity": 5,
    "content_preservation": 5
  },
  "warnings": []
}
```

## Important Notes
- **Edit the phase8.md file directly** - insert the markdown table at the correct location
- Preserve all text content from cells (don't truncate)
- Use appropriate alignment based on content (numbers right-aligned, text left-aligned)
- The `step-output.json` contains metadata only; actual table content goes in phase8.md

## Rubric Scoring Requirements
- `rubric_scores` MUST include all required dimensions: `row_column_fidelity`, `markdown_validity`, `content_preservation`.
- Each dimension score MUST be an integer from 1 to 5.
- `warnings` MUST always be present (use `[]` when there are no warnings).

## Edge Cases
- Wide tables that may need horizontal scrolling in markdown
- Tables with merged cells (use empty cells or note the merge)
- Multi-line cell content
- Tables with empty cells (preserve them)
