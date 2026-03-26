"""Step 7.7: Table Detection - Two-pass multimodal approach.

This module provides instruction builders for the two-pass table detection:
1. Text scan: Identify likely table pages from extracted text
2. Vision confirmation: Render images and extract table bounding boxes from PDF pages.

Unlike other instruction files, this step is implemented in Python (not static
Markdown) because prompt content is selected dynamically per pass.
"""


def build_text_scan_prompt(extracted_text: str, page_num: int) -> str:
    """Build prompt for text-based table detection scan.

    Args:
        extracted_text: Text content of the page
        page_num: 1-based page number

    Returns:
        Instruction prompt for the agent
    """
    return f"""# Step 7.7 (Pass 1): Table Detection - Text Scan

## Task
Analyze the extracted text and determine if this page likely contains tables.

## Page Information
- Page number: {page_num}

## Extracted Text Sample
```
{extracted_text[:2000]}
```

## Instructions
1. Look for table indicators in the text:
   - Multi-column layouts with aligned text
   - Tabular data patterns (numbers, labels, values in rows)
   - Table-like spacing or structure
   - Column headers (e.g., "Armor Class | Type")
   - Repeated patterns suggesting rows

2. Score likelihood of table presence (0-100)

3. Identify approximate table regions if present

## Output Format
Write to `step-output.json`:
```json
{{
  "step_id": "7.7",
  "status": "success",
  "data": {{
    "page_number": {page_num},
    "table_likelihood": 85,
    "likely_tables": 2,
    "text_indicators": ["column_headers", "tabular_spacing"]
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
`rubric_scores` MUST include `detection_recall`, `detection_precision`, and `boundary_accuracy`
with integer values from 1 to 5.
`warnings` MUST always be present (use `[]` when no warnings apply).
If this pass does not produce table boundaries, set `boundary_accuracy` to 5 (N/A in text scan).
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

## Critical Failures
- Missing a table entirely
- Bounding boxes that miss significant table content
- Incorrect row/column counts for simple tables
"""
