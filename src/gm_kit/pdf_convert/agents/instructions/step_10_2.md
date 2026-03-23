# Step 10.2: Include Quality Ratings

## Task
Generate quality ratings for the conversion across multiple dimensions.

## Input
- Quality assessment results from steps 9.2-9.5, 9.7-9.8
- Any intermediate scores and warnings

## Instructions
1. Compile quality ratings across dimensions:
   - Structural clarity (9.2)
   - Text flow/readability (9.3)
   - Table integrity (9.4)
   - Callout formatting (9.5)
   - TOC validation (9.7)
   - Reading order (9.8)

2. Calculate overall quality score (1-5 scale):
   - 5: Excellent, minimal issues
   - 4: Good, minor issues
   - 3: Acceptable, some issues
   - 2: Poor, significant issues
   - 1: Failed, major problems

3. Provide justification for each rating

## Output Format
Write to `step-output.json`:
```json
{
  "step_id": "10.2",
  "status": "success",
  "data": {
    "ratings": {
      "structural_clarity": {"score": 5, "justification": "Clean hierarchy, no skips"},
      "text_flow": {"score": 4, "justification": "Minor flow issue on page 12"},
      "table_integrity": {"score": 5, "justification": "All tables accurate"},
      "callout_formatting": {"score": 5, "justification": "Properly formatted"},
      "toc_validation": {"score": 4, "justification": "2 font-inferred gaps flagged"},
      "reading_order": {"score": 5, "justification": "Correct order throughout"},
      "overall": {"score": 4.7, "justification": "High quality conversion with minor TOC gaps"}
    }
  },
  "rubric_scores": {
    "rating_justification": 5,
    "dimension_coverage": 5,
    "score_consistency": 5
  },
  "warnings": []
}
```

## Rubric Scoring Requirements
- `rubric_scores` MUST include all required dimensions: `rating_justification`, `dimension_coverage`, `score_consistency`.
- Each dimension score MUST be an integer from 1 to 5.
- `warnings` MUST always be present (use `[]` when there are no warnings).

## Critical Failures
- Missing required dimensions
- Inconsistent scoring
- No justification provided

## Note
This JSON output is consumed by code step 10.4 to generate the human-readable conversion report.
