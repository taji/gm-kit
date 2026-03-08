# Step 9.5: Callout Formatting Check

## Task
Verify proper formatting of GM/Keeper notes and read-aloud text callouts.

## Input
- `phase8_file`: Path to phase8.md
- `callout_config`: Callout boundary definitions

## Instructions
1. Identify callout blocks:
   - Read Aloud sections
   - GM/Keeper notes
   - Boxed text/callouts
   - Quote blocks with attribution

2. Verify formatting:
   - Proper blockquote syntax (`>`)
   - Read-aloud markers present
   - GM note labels correct
   - Attribution lines properly formatted

3. Check boundaries:
   - Callouts start/end correctly
   - No callout content leaked into body
   - Proper nesting if applicable

## Output Format
Write to `step-output.json`:
```json
{
  "step_id": "9.5",
  "status": "success",
  "data": {
    "callouts_checked": 12,
    "issues": [],
    "score": 5
  },
  "rubric_scores": {
    "detection_accuracy": 5,
    "format_preservation": 5,
    "boundary_correctness": 5
  },
  "warnings": []
}
```

## Critical Failures
- Malformed assessment JSON
- Missing required fields
