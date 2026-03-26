# Step 9.7: Review TOC Validation Issues

## Task
Identify and report TOC validation gaps and duplicates.

## Input
- `phase8_file`: Path to phase8.md
- `toc_file`: Path to toc-extracted.txt
- `font_family_mapping`: JSON with font signature labels

## Instructions
1. Compare TOC entries to actual headings in markdown:
   - Map TOC entries to heading levels
   - Identify gaps (headings in TOC but not in doc, or vice versa)
   - Find duplicate entries

2. Use font-family-mapping.json to distinguish:
   - TOC-sourced headings (confirmed in original TOC)
   - Font-inferred headings (detected by Phase 7 heuristics)

3. Apply appropriate skepticism:
   - Font-inferred headings may be false positives
   - Flag gaps as "possible false positive — font-inferred" if uncertain
   - Distinguish between definite gaps and uncertain ones

4. Provide actionable suggestions:
   - Recommend heading level adjustments
   - Suggest missing TOC entries
   - Note potential false positives

## Output Format
Write to `step-output.json`:
```json
{
  "step_id": "9.7",
  "status": "success",
  "data": {
    "gaps": [
      {
        "type": "missing_in_doc",
        "toc_entry": "Section 3.2",
        "heading_level": 2,
        "note": "possible false positive - font-inferred heading"
      }
    ],
    "duplicates": [
      {
        "title": "Appendix A",
        "locations": ["toc_line_42", "toc_line_57"],
        "note": "Duplicate TOC entry appears twice at the same heading level."
      }
    ],
    "suggestions": [
      "Verify 'Appendix A' is correctly labeled as H2"
    ],
    "score": 4
  },
  "rubric_scores": {
    "gap_detection": 4,
    "duplicate_detection": 5,
    "actionable_suggestions": 5,
    "font_source_awareness": 5
  },
  "warnings": ["2 gaps detected with font-inferred headings"]
}
```

## Rubric Scoring Requirements
- `rubric_scores` MUST include all required dimensions: `gap_detection`, `duplicate_detection`, `actionable_suggestions`, `font_source_awareness`.
- Each dimension score MUST be an integer from 1 to 5.
- `warnings` MUST always be present (use `[]` when there are no warnings).

## Critical Failures
- Malformed assessment JSON
- Missing required fields
