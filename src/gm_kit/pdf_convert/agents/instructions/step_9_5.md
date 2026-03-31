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
    "issues": [
      {
        "location": "page_8_callout_2",
        "type": "boundary_mismatch",
        "description": "Callout block starts correctly but extends one paragraph beyond the expected end marker."
      }
    ],
    "score": 4
  },
  "rubric_scores": {
    "detection_accuracy": 4,
    "format_preservation": 4,
    "boundary_correctness": 4
  },
  "warnings": ["One callout boundary appears ambiguous due to repeated end-marker text on the same page."]
}
```

## Rubric Scoring Requirements
- `rubric_scores` MUST include all required dimensions: `detection_accuracy`, `format_preservation`, `boundary_correctness`.
- Each dimension score MUST be an integer from 1 to 5.
- `warnings` MUST always be present (use `[]` when there are no warnings).

## Critical Failures
- Malformed assessment JSON
- Missing required fields
