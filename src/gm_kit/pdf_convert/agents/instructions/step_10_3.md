# Step 10.3: Document Remaining Issues

## Task
Document up to 3 remaining issues with examples for the conversion report.

## Input
- All quality assessment results (steps 9.x)
- Warnings from all phases
- User corrections (if any)

## Instructions
1. Identify the most significant remaining issues:
   - Prioritize issues by impact on usability
   - Focus on actionable problems
   - Include specific examples

2. For each issue (max 3):
   - Clear description of the problem
   - Concrete example from the document
   - Suggested fix or workaround
   - Severity level

3. Ensure issues are:
   - Actionable (user can do something about it)
   - Specific (not vague "check this" statements)
   - Prioritized (most important first)

## Output Format
Write to `step-output.json`:
```json
{
  "step_id": "10.3",
  "status": "success",
  "data": {
    "issues": [
      {
        "severity": "medium",
        "description": "Table on page 15 has merged cells that weren't preserved",
        "example": "The 'Special' column in the Equipment table has merged cells for 'None' entries",
        "suggested_fix": "Manually split merged cells or note the merge in a comment",
        "location": "page_15_equipment_table"
      },
      {
        "severity": "low",
        "description": "Minor OCR error in monster stat block",
        "example": "'Mind Flayer' rendered as 'Mind Flayer' in stat block",
        "suggested_fix": "Use find/replace to correct the name",
        "location": "page_42_stat_block"
      }
    ]
  },
  "rubric_scores": {
    "issue_clarity": 5,
    "example_quality": 5,
    "actionable_guidance": 5
  },
  "warnings": []
}
```

## Critical Failures
- Truncated or empty report
- No actionable guidance
- Vague descriptions without examples

## Note
This JSON output is consumed by code step 10.4 to generate the human-readable conversion report.
