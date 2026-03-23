# Step 4.5: Resolve Split Sentences at Chunk Boundaries

## Task
Identify and repair sentences that were incorrectly split at chunk/page boundaries during text extraction.

## Input
- `phase4_file`: Path to the phase4.md file with font signature markers
- `chunk_boundaries`: List of chunk/page boundary locations

## Instructions
1. Scan the text for sentences that end with hyphenation at chunk boundaries
2. Identify sentence fragments that should be joined:
   - Look for hyphenated words at line ends (e.g., "convert-\ning" → "converting")
   - Look for sentences split across page breaks
3. Join the fragments into complete sentences
4. Remove unnecessary hyphenation
5. **Edit the phase4.md file directly** - do not embed full content in output

## Output Format
Write metadata to `step-output.json`:
```json
{
  "step_id": "4.5",
  "status": "success",
  "data": {
    "changes_made": 12,
    "joins_made": [
      {"location": "page_5_line_23", "type": "hyphenation", "original": "convert-\ning", "corrected": "converting"}
    ]
  },
  "rubric_scores": {
    "correct_joins": 5,
    "no_false_joins": 5,
    "readability": 5
  },
  "warnings": []
}
```

## Rubric Scoring Requirements
- `rubric_scores` MUST include all required dimensions: `correct_joins`, `no_false_joins`, `readability`.
- Each dimension score MUST be an integer from 1 to 5.
- `warnings` MUST always be present (use `[]` when there are no warnings).

## Edge Cases
- Be conservative: don't join across paragraph boundaries
- Preserve intentional line breaks in poetry/blockquotes
- Flag uncertain cases rather than auto-fix
