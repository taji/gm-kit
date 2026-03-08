# Agent Step Contracts (Overview)

This feature defines JSON Schema contracts per agent step. Each contract includes a shared metadata envelope and step-specific fields.

## Covered Steps (13 total)
3.2, 4.5, 6.4, 7.7, 8.7, 9.2–9.5, 9.7–9.8, 10.2–10.3

## Shared Metadata Envelope (applies to all steps)

```json
{
  "step_id": "string (e.g., '3.2')",
  "input_artifact": "string (path or reference)",
  "warnings": ["array of strings"],
  "errors": ["array of strings"],
  "notes": "string (optional)"
}
```

## Step-Specific Output Summaries

**Note on rubric evaluation**: Agent performs self-evaluation against rubric dimensions; scores are included in `step-output.json` (e.g., `score` field per quality dimension). No separate evaluation artifact is produced.

**Note on step 8.7 image paths**: Image paths in `step-input.json` are relative to project root (e.g., `tests/fixtures/pdf_convert/agents/inputs/table_pages/...`).

| Step | Output Type | Key Fields |
|------|------------|------------|
| 3.2 | Visual TOC | `entries[]` with `level`, `title`, `page`; written to `toc-extracted.txt` as indented text (2 spaces per level, `(page N)` notation) matching step 3.1 output format |
| 4.5 | Corrected text | `corrected_text`, `joins_made[]` with boundary locations |
| 6.4 | Corrected text | `corrected_text`, `corrections[]` with original/replacement/confidence, `flags[]` for uncertain |
| 7.7 | Table regions | `tables[]` with `table_id`, `page_num`, `bounding_box`, `rows`, `columns`, `cells[]` |
| 8.7 | Markdown tables | `tables[]` with `table_id`, `markdown` (pipe-delimited table string); page images rendered in step 7.7 are reused (not re-rendered) — Python crops the saved image using bounding box pixel coordinates before sending to vision LLM |
| 9.2 | Structural clarity | `heading_hierarchy_valid`, `issues[]`, `score` (1-5) |
| 9.3 | Text flow | `flow_issues[]`, `readability_score` (1-5) |
| 9.4 | Table integrity | `tables_checked`, `issues[]`, `score` (1-5) |
| 9.5 | Callout formatting | `callouts_checked`, `issues[]`, `score` (1-5) |
| 9.7 | TOC validation | `gaps[]`, `duplicates[]`, `suggestions[]`, `score` (1-5); inputs include `font-family-mapping.json` to distinguish TOC-sourced headings from font-inferred headings and reduce false-positive gap reports |
| 9.8 | Reading order | `issues[]`, `pervasive_flag` (bool, >15% threshold), `score` (1-5) |
| 10.2 | Quality ratings | `ratings` dict with dimension → score (1-5) per quality area |
| 10.3 | Remaining issues | `issues[]` (max 3) with `description`, `example`, `suggested_fix` |

## Schema Location

Per-step JSON Schema files: `src/gm_kit/pdf_convert/agents/schemas/step_X_Y.schema.json`

Schemas are Draft-07 compatible and validated using the `jsonschema` Python library.

## Shared Input Artifact: font-family-mapping.json

Step 9.7 receives `font-family-mapping.json` from the conversion workspace (written by Phase 3 step 3.6, updated by Phase 7 step 7.9). The agent uses this to distinguish TOC-sourced headings from font-inferred headings when assessing TOC validation gaps.

**Schema** (as produced by `phase3.py` step 3.6, updated by `phase7.py` step 7.9):

```json
{
  "version": "1.0",
  "signatures": [
    {
      "id": "sig001",
      "family": "TeX Gyre Heros Cn",
      "size": 18.0,
      "weight": "Bold",
      "style": "Normal",
      "frequency": 12,
      "samples": ["Chapter One", "Introduction"],
      "candidate_heading": true,
      "suggested_level": "H2",
      "label": "H2"
    }
  ],
  "metadata": {
    "total_signatures": 15,
    "candidate_headings": 5
  }
}
```

**Key fields for step 9.7:**
| Field | Source | Meaning for step 9.7 |
|-------|--------|----------------------|
| `candidate_heading` | Phase 3 code heuristic | Font appears heading-like (size, weight) |
| `suggested_level` | Phase 3 code heuristic | Estimated heading depth from font metrics |
| `label` | Phase 7 code + optional user review | Confirmed role (H1–H4, callout_gm, callout_read_aloud, null=unconfirmed) |

**Skepticism guidance for step 9.7:** A heading that exists in the rendered markdown but is NOT in the PDF's embedded TOC may be a false positive if its signature has `candidate_heading: true` and `label` was set by Phase 7 font heuristics only (no TOC confirmation). The agent should flag such gaps as "possible false positive — font-inferred heading" rather than a definitive structural gap.
