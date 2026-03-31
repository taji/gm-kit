"""Step 7.7: Table Detection - Two-pass multimodal approach.

This module provides instruction builders for the two-pass table detection:
1. Text scan: Identify likely table pages from extracted text
2. Vision confirmation: Render images and extract table bounding boxes from PDF pages.

Unlike other instruction files, this step is implemented in Python (not static
Markdown) because prompt content is selected dynamically per pass.
"""

from __future__ import annotations


def _extract_text_sample(extracted_text: str, max_chars: int = 3500) -> str:
    """Build a representative text sample with table-priority anchors.

    The old fixed-prefix truncation could cut off table sections that appear
    later on long pages, causing false negatives in pass-1 detection.
    """
    text = extracted_text.strip()
    if len(text) <= max_chars:
        return text

    anchors = [
        "Tables",
        "Weapons",
        "Armor Class",
        "Damage",
        "Range",
        "|",
    ]
    anchor_idx = -1
    for needle in anchors:
        idx = text.find(needle)
        if idx != -1:
            anchor_idx = idx
            break

    if anchor_idx != -1:
        half = max_chars // 2
        start = max(0, anchor_idx - half)
        end = min(len(text), start + max_chars)
        start = max(0, end - max_chars)
        snippet = text[start:end]
    else:
        # Fall back to head+tail so late-page table data still has a chance.
        head = text[: max_chars // 2]
        tail = text[-(max_chars // 2) :]
        snippet = head + "\n...\n" + tail

    return snippet


def build_text_scan_prompt(extracted_text: str, page_num: int) -> str:
    """Build prompt for text-based table detection scan.

    Args:
        extracted_text: Text content of the page
        page_num: 1-based page number

    Returns:
        Instruction prompt for the agent
    """
    guidance = (
        "The extracted text uses font-signature markers like `«sig012:Name»` and "
        "`«sig011:1d6»` to denote heading fonts versus repeating body fonts. Treat "
        "repeated signatures (e.g., multiple `sig011` entries clustered together) as "
        "rows and `sig012`/similar as column headers so you can reconstruct the table "
        "structure despite the markers."
    )

    reasoning_example = (
        '["Headers from sig012:Name/Damage/Range", '
        '"Repeated sig011 rows like Shortsword/1d6/Melee"]'
    )

    return f"""# Step 7.7 (Pass 1): Table Detection - Text Scan

## Task
Analyze the extracted text and determine if this page likely contains tables.

## Page Information
- Page number: {page_num}

## Extracted Text Sample
```
{_extract_text_sample(extracted_text)}
```

## Instructions
{guidance}

1. Look for table indicators in the text:
   - Multi-column layouts with aligned text
   - Tabular data patterns (numbers, labels, values in rows)
   - Table-like spacing or structure
   - Column headers (e.g., "Armor Class | Type")
   - Repeated patterns suggesting rows

2. Score likelihood of table presence (0-100)

3. Identify approximate table regions if present
4. Set handoff fields used by downstream pipeline code:
   - `tables_detected`: boolean (`true` when table_likelihood > 50 and a table is identified)
   - `tables`: array of detected table hints for pass-2 (can be empty when none found)
   - Each table hint should include: `table_id`, `text_context`, `confidence`, `confidence_note`

## Reasoning
Describe the cues that influenced your detection and include them in `data.reasoning`.
Example: `{reasoning_example}`.

## Output Format
Write to `step-output.json`:
```json
{{
  "step_id": "7.7",
  "status": "success",
  "data": {{
    "page_number": {page_num},
    "page_number_1based": {page_num},
    "table_likelihood": 85,
    "likely_tables": 2,
    "tables_detected": true,
    "text_indicators": ["column_headers", "tabular_spacing"],
    "tables": [
      {{
        "table_id": "page_{page_num:03d}_table_001",
        "text_context": "Weapons / Name Damage Range / Shortsword 1d6 Melee",
        "confidence": 0.93,
        "confidence_note": "Clear header+row pattern in extracted text"
      }}
    ],
    "reasoning": [
      "Headers detected via `sig012:Name/Damage/Range`",
      "Repeated `sig011` rows with Names, Damage, Range values",
      "Non-grammatical row fragments confirm the table span"
    ]
  }},
  "rubric_scores": {{
    "detection_recall": 5,
    "detection_precision": 5,
    "boundary_accuracy": 5
  }},
  "warnings": []
}}
```

If table likelihood > 50, the system will render this page as an image for Pass 2.
If no table is detected, return `"tables_detected": false` and `"tables": []`.
`rubric_scores` MUST include `detection_recall`, `detection_precision`, and `boundary_accuracy`
with integer values from 1 to 5.
`warnings` MUST always be present (use `[]` when no warnings apply).
If this pass does not produce table boundaries, set `boundary_accuracy` to 5 (N/A in text scan).

## Pre-Submit Checklist (Required)
Before you finish, validate your `step-output.json` against this checklist.
Rewrite the file if any item fails:
1. Top-level keys exist: `step_id`, `status`, `data`, `rubric_scores`, `warnings`
2. `step_id` is exactly `"7.7"` for this pass
3. `status` is one of: `success`, `warning`, `failed`
4. `data.tables_detected` is a boolean
5. `data.tables` is always present and is an array (empty array if none)
6. `rubric_scores` contains all keys: `detection_recall`, `detection_precision`, `boundary_accuracy`
7. Every rubric score is an integer from 1 to 5
8. `warnings` is always an array (use `[]` if no warnings)
"""


def build_vision_prompt(page_image_path: str, text_context: str) -> str:
    """Build prompt for vision-based table detection.

    Args:
        page_image_path: Path to the rendered page image (relative to project root)
        text_context: Text content of the page for context

    Returns:
        Instruction prompt for the agent with image reference
    """
    return f"""# Step 7.7 (Pass 2): Table Detection - Vision Confirmation

## Task
Analyze the page image and extract precise table bounding boxes.

## Input
- Page image: {page_image_path}
- Text context: Available in step-input.json

## Instructions
1. Examine the page image for tables
2. For each table found:
   - Identify the exact bounding box in pixel coordinates (x0, y0, x1, y1)
   - Count rows and columns
   - Note if it's a simple or complex table (merged cells, etc.)
   - Assign a table_id (t1, t2, etc.)

3. Bounding box format: top-left (x0, y0) to bottom-right (x1, y1)
   - Example: {{"x0": 67, "y0": 321, "x1": 633, "y1": 596}}

## Output Format
Write to `step-output.json`:
```json
{{
  "step_id": "7.7",
  "status": "success",
  "data": {{
    "tables": [
      {{
        "table_id": "t1",
        "page_number": 5,
        "bbox_pixels": {{"x0": 67, "y0": 321, "x1": 633, "y1": 596}},
        "rows": 9,
        "columns": 2,
        "cells": 18,
        "confidence_note": "Simple two-column lookup table"
      }}
    ]
  }},
  "rubric_scores": {{
    "detection_recall": 5,
    "detection_precision": 5,
    "boundary_accuracy": 5
  }},
  "warnings": []
}}
```

`rubric_scores` MUST include `detection_recall`, `detection_precision`, and `boundary_accuracy`
with integer values from 1 to 5.
`warnings` MUST always be present (use `[]` when no warnings apply).

## Pre-Submit Checklist (Required)
Before you finish, validate your `step-output.json` against this checklist.
Rewrite the file if any item fails:
1. Top-level keys exist: `step_id`, `status`, `data`, `rubric_scores`, `warnings`
2. `step_id` is exactly `"7.7"` for this pass
3. `status` is one of: `success`, `warning`, `failed`
4. `data.tables` is present and is an array
5. Each table object includes: `table_id`, `page_number`, `bbox_pixels`, `rows`, `columns`, `cells`
6. Each `bbox_pixels` includes integer `x0`, `y0`, `x1`, `y1` with `x1 > x0` and `y1 > y0`
7. `rubric_scores` contains all keys: `detection_recall`, `detection_precision`, `boundary_accuracy`
8. Every rubric score is an integer from 1 to 5
9. `warnings` is always an array (use `[]` if no warnings)

## Critical Failures
- Missing a table entirely
- Bounding boxes that miss significant table content
- Incorrect row/column counts for simple tables
"""
