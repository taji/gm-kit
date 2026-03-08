# Step 9.2: Structural Clarity Assessment

## Task
Evaluate the structural clarity of the converted markdown document.

## Input
- `phase8_file`: Path to phase8.md (final markdown with headings applied)
- `toc_file`: Path to toc-extracted.txt

## Instructions
1. Verify heading hierarchy integrity:
   - Check for level skips (e.g., H1 → H3 without H2)
   - Verify single H1 rule (document title)
   - Confirm TOC hierarchy matches heading levels

2. Assess section coherence:
   - Sections have clear boundaries
   - No orphaned content
   - Logical flow from section to section

3. Check nesting correctness:
   - Proper indentation of subsections
   - Consistent nesting depth

## Output Format
Write to `step-output.json`:
```json
{
  "step_id": "9.2",
  "status": "success",
  "data": {
    "heading_hierarchy_valid": true,
    "issues": [],
    "score": 5
  },
  "rubric_scores": {
    "heading_hierarchy": 5,
    "section_coherence": 5,
    "nesting_correctness": 5
  },
  "warnings": []
}
```

## Critical Failures
- Malformed assessment JSON
- Missing required fields in output
