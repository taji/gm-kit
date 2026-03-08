# Step 9.8: Review Two-Column Reading Order Issues

## Task
Identify reading order problems in two-column PDF conversions.

## Input
- `phase8_file`: Path to phase8.md
- `pdf_metadata`: Page layout information (if available)

## Instructions
1. Analyze text flow for two-column documents:
   - Verify left-to-right, top-to-bottom reading order
   - Check that column boundaries are respected
   - Identify any text that appears out of order

2. Calculate pervasiveness:
   - Count paragraphs/sections with reading order issues
   - Determine percentage of affected content
   - Flag if >15% threshold

3. Assess confidence:
   - High confidence: Clear order violations
   - Medium: Uncertain cases
   - Flag appropriately

## Output Format
Write to `step-output.json`:
```json
{
  "step_id": "9.8",
  "status": "success",
  "data": {
    "issues": [
      {
        "location": "page_12_column_2",
        "type": "column_boundary_violation",
        "confidence": "high"
      }
    ],
    "pervasive_flag": false,
    "affected_percentage": 5,
    "score": 4
  },
  "rubric_scores": {
    "order_correctness": 4,
    "confidence_flagging": 5,
    "threshold_adherence": 5
  },
  "warnings": []
}
```

## Critical Failures
- Malformed assessment JSON
- Missing required fields

## Note
If `pervasive_flag` is true (>15% affected), user review is recommended.
