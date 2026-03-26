# Step 6.4: Fix OCR Spelling Errors

## Task
Correct OCR-induced spelling errors and character substitutions while preserving TTRPG domain terms.

## Input
- `phase6_file`: Path to the phase6.md file with extracted text
- `font_signatures`: Mapping of font signatures to help identify headings vs body text

## Instructions
1. Scan text for common OCR artifacts:
   - Character substitutions: `rn`→`m`, `l`→`1`, `O`→`0`, `0`→`O`
   - Common misspellings based on OCR noise patterns
2. **Preserve TTRPG terminology** - do not "correct":
   - Monster names (e.g., "Beholder", "Mind Flayer")
   - Game abbreviations (e.g., "AC", "HP", "DC", "STR", "DEX")
   - Location names
   - Proper nouns from the TOC/headings
3. Err on the side of **flagging** uncertain corrections
4. **Edit the phase6.md file directly** - do not embed full content in output
5. Pay special attention near table-like content where abbreviations are common

## Output Format
Write metadata to `step-output.json`:
```json
{
  "step_id": "6.4",
  "status": "success",
  "data": {
    "changes_made": 8,
    "corrections": [
      {"original": "conveming", "replacement": "converting", "confidence": "high", "location": "page_12"}
    ],
    "flags": [
      {"text": "ST 15", "reason": "possible abbreviation - not corrected", "location": "page_45_table"}
    ]
  },
  "rubric_scores": {
    "correction_accuracy": 5,
    "false_positive_rate": 5,
    "domain_term_preservation": 5
  },
  "warnings": ["Low confidence in 3 OCR text spans; left unchanged and recorded in data.flags."]
}
```

## Rubric Scoring Requirements
- `rubric_scores` MUST include all required dimensions: `correction_accuracy`, `false_positive_rate`, `domain_term_preservation`.
- Each dimension score MUST be an integer from 1 to 5.
- `warnings` MUST always be present (use `[]` when there are no warnings).

## Edge Cases
- Scanned PDFs with pre-baked OCR errors
- Agent-driven OCR workflows (user provides OCR'd text externally)
- Table content with stats and abbreviations
- Monster stat blocks with game-specific notation
