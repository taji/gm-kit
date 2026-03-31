# Agent Step Test Fixtures

This directory contains test fixtures for the agent-driven pipeline steps.

## Structure

```
tests/fixtures/pdf_convert/agents/
├── inputs/
│   ├── step_3_2/          # TOC parsing inputs
│   ├── step_4_5/          # Sentence boundary inputs
│   ├── step_6_4/          # OCR correction inputs
│   ├── step_7_7/          # Table detection inputs (text + images)
│   ├── step_8_7/          # Table conversion inputs (images + flat text)
│   ├── step_9_2/          # Structural assessment inputs
│   ├── step_9_3/          # Text flow assessment inputs
│   ├── step_9_4/          # Table integrity inputs
│   ├── step_9_5/          # Callout formatting inputs
│   ├── step_9_7/          # TOC validation inputs
│   ├── step_9_8/          # Reading order inputs
│   ├── step_10_2/         # Quality ratings inputs
│   ├── step_10_3/         # Issues documentation inputs
│   └── table_pages/       # Full page images for table detection
└── golden/
    ├── step_3_2/          # Expected TOC outputs
    ├── step_4_5/          # Expected correction outputs
    ├── step_6_4/          # Expected OCR fix outputs
    ├── step_7_7/          # Expected table bbox outputs
    ├── step_8_7/          # Expected markdown table outputs
    ├── step_9_2/          # Expected assessment outputs
    ├── step_9_3/          # Expected flow assessment outputs
    ├── step_9_4/          # Expected table integrity outputs
    ├── step_9_5/          # Expected callout check outputs
    ├── step_9_7/          # Expected TOC validation outputs
    ├── step_9_8/          # Expected reading order outputs
    ├── step_10_2/         # Expected ratings outputs
    └── step_10_3/         # Expected issues outputs
```

## Fixture File Naming Convention

For table-related fixtures (7.7, 8.7):
```
{corpus}_{page_id}.{step_id}.{fixture_type}.{ext}

Examples:
- b2_keep_borderlands_p005.step_7_7.input.json
- homebrewery_with_toc_p002.step_8_7.golden.md
- cofc_quickstart_p015.table_crop.png
```

Where:
- `corpus`: b2_keep_borderlands, cofc_quickstart, homebrewery_with_toc, homebrewery_without_toc
- `page_id`: pXXX (1-based page number with leading zeros)
- `step_id`: step_X_Y format
- `fixture_type`: input, golden, table_crop, page
- `ext`: json, md, txt, png

## Corpus Reference

1. **B2 - Keep on the Borderlands**
   - Source: Dungeon Module B2
   - Fixture IDs: `b2_keep_borderlands_pXXX`
   - Tables: Armor Class, Equipment, Monster stats
   - Download: `download_b2_fixture.sh`

2. **CoC - Call of Cthulhu Quick-Start**
   - Source: CHA23131
   - Fixture IDs: `cofc_quickstart_pXXX`
   - Tables: Damage tables, skill tables
   - Download: `download_cofc_fixture.sh`

3. **Homebrewery with TOC**
   - Source: The Homebrewery - NaturalCrit.pdf
   - Fixture IDs: `homebrewery_with_toc_pXXX`
   - Tables: Example span-heavy table (edge case)

4. **Homebrewery without TOC**
   - Source: The Homebrewery - NaturalCrit - Without TOC.pdf
   - Fixture IDs: `homebrewery_without_toc_pXXX`
   - Note: No embedded TOC for visual TOC parsing tests

## Adding New Fixtures

1. Create fixture in appropriate `inputs/step_X_Y/` directory
2. Create corresponding golden file in `golden/step_X_Y/`
3. Follow naming convention above
4. Add note to this README if special handling required

## Multimodal Table Fixtures (7.7/8.7)

These steps require:
1. Text input (`.flat_text.txt`) - extracted text from table area
2. Image input (`.table_crop.png`) - cropped table image
3. Full page image (in `table_pages/`) - for step 7.7 vision pass
4. Input JSON (`.step_7_7.input.json`) - metadata including bbox
5. Golden output (`.step_8_7.golden.md`) - expected markdown table

The Homebrewery p002 table is documented as a **non-canonical edge case** - it uses span-heavy layout that may produce inconsistent markdown across different vision models. Use for detection/crop stress testing only.
