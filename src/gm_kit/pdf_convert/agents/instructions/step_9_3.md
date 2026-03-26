# Step 9.3: Text Flow / Readability Assessment

## Task
Assess the text flow and readability of the converted markdown document.

## Input
- `phase8_file`: Path to phase8.md
- Total document text (full markdown)

## Instructions
1. Evaluate reading order:
   - Text flows logically from top to bottom
   - Paragraph order makes sense
   - No jumbled sentences or fragments

2. Check paragraph integrity:
   - Paragraphs are complete thoughts
   - No mid-paragraph breaks
   - Proper paragraph grouping

3. Assess flow continuity:
   - Transitions between sections are smooth
   - No abrupt content changes
   - Consistent narrative flow

4. Check for remaining artifacts:
   - Gutter spacing artifacts
   - Page break issues
   - Header/footer noise

## Token Preflight
**Note**: This step processes the full document. If estimated tokens > 100,000, the user will be warned about potential accuracy degradation in heading hierarchy and TOC alignment detection.

## Output Format
Write to `step-output.json`:
```json
{
  "step_id": "9.3",
  "status": "success",
  "data": {
    "flow_issues": [
      {
        "location": "page_12_paragraph_3",
        "type": "column_order_mix",
        "description": "Sentence order appears to jump from right column back to left column."
      }
    ],
    "readability_score": 4
  },
  "rubric_scores": {
    "reading_order": 4,
    "paragraph_integrity": 4,
    "flow_continuity": 4
  },
  "warnings": ["Detected probable page-break noise near page_12_paragraph_3; issue may be layout-induced."]
}
```

## Rubric Scoring Requirements
- `rubric_scores` MUST include all required dimensions: `reading_order`, `paragraph_integrity`, `flow_continuity`.
- Each dimension score MUST be an integer from 1 to 5.
- `warnings` MUST always be present (use `[]` when there are no warnings).

## Critical Failures
- Malformed assessment JSON
- Missing required fields
