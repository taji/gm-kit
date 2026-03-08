# Step 9.4: Table Integrity Check

## Task
Verify the integrity and accuracy of converted tables.

## Input
- `phase8_file`: Path to phase8.md
- `table_manifest`: List of tables detected in step 7.7/8.7

## Instructions
1. Check each converted table:
   - Row/column count matches source
   - Cell content is accurate and complete
   - No truncation or data loss
   - Proper markdown formatting

2. Validate table structure:
   - Header rows are correctly formatted
   - Alignment is appropriate for content
   - No broken table syntax

3. Flag issues:
   - Missing cells
   - Incorrect data
   - Formatting problems
   - Tables that should exist but don't

## Output Format
Write to `step-output.json`:
```json
{
  "step_id": "9.4",
  "status": "success",
  "data": {
    "tables_checked": 3,
    "issues": [
      {"table_id": "t2", "issue": "missing_cell", "row": 5, "column": 2}
    ],
    "score": 4
  },
  "rubric_scores": {
    "cell_accuracy": 4,
    "structure_preservation": 5,
    "alignment_check": 5
  },
  "warnings": ["Table t2 has empty cell at row 5, col 2"]
}
```

## Critical Failures
- Malformed assessment JSON
- Missing required fields
- Tables with major data corruption
