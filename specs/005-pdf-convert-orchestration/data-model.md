# Data Model: PDF to Markdown Command Orchestration

**Date**: 2026-01-29
**Feature**: 005-pdf-convert-orchestration

## Entities

### ConversionState

Tracks progress through the pipeline. Persisted in `.state.json`.

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version for compatibility (e.g., "1.0") |
| `pdf_path` | string | Absolute path to source PDF |
| `output_dir` | string | Absolute path to output directory |
| `started_at` | ISO8601 | Conversion start timestamp |
| `updated_at` | ISO8601 | Last state update timestamp |
| `current_phase` | int | Phase currently executing (0-10) |
| `current_step` | string | Step currently executing (e.g., "5.3") |
| `completed_phases` | int[] | List of completed phase numbers |
| `phase_results` | PhaseResult[] | Results for each completed phase |
| `status` | enum | "in_progress", "completed", "failed", "cancelled" |
| `error` | ErrorInfo? | Error details if status is "failed" |
| `diagnostics_enabled` | bool | Whether --diagnostics flag was set |

**State Transitions**:
```
[new] --start--> in_progress --complete--> completed
                     |
                     +--error--> failed
                     |
                     +--cancel--> cancelled
```

### PDFMetadata

Extracted PDF properties. Persisted in `metadata.json`.

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | PDF title from metadata (may be empty) |
| `author` | string | Author name from metadata |
| `creator` | string | Creating application |
| `producer` | string | PDF producer |
| `copyright` | string? | Copyright notice if found |
| `page_count` | int | Total pages |
| `file_size_bytes` | int | File size in bytes |
| `has_toc` | bool | Whether embedded TOC exists |
| `image_count` | int | Total images across all pages |
| `font_count` | int | Unique font families detected |
| `extracted_at` | ISO8601 | When metadata was extracted |

### PreflightReport

Analysis results shown to user before conversion. Not persisted (derived from metadata).

| Field | Type | Description |
|-------|------|-------------|
| `pdf_name` | string | Filename for display |
| `file_size_display` | string | Human-readable size (e.g., "12.4 MB") |
| `page_count` | int | From metadata |
| `image_count` | int | From metadata |
| `text_extractable` | bool | True if >100 chars extracted |
| `toc_approach` | enum | "embedded", "visual", "none" |
| `font_complexity` | enum | "low", "moderate", "high" |
| `overall_complexity` | enum | "low", "moderate", "high" |
| `warnings` | string[] | Any pre-flight warnings |
| `user_involvement_phases` | int[] | Phases requiring user input |

### PhaseResult

Result of executing a single phase.

| Field | Type | Description |
|-------|------|-------------|
| `phase_num` | int | Phase number (0-10) |
| `name` | string | Phase name |
| `status` | enum | "success", "warning", "error", "skipped" |
| `started_at` | ISO8601 | Phase start time |
| `completed_at` | ISO8601 | Phase end time |
| `steps` | StepResult[] | Individual step results |
| `output_file` | string? | Primary output file path |
| `warnings` | string[] | Non-fatal warnings |
| `errors` | string[] | Error messages if failed |

### StepResult

Result of executing a single step within a phase.

| Field | Type | Description |
|-------|------|-------------|
| `step_id` | string | Step identifier (e.g., "0.1", "5.3") |
| `description` | string | Step description |
| `status` | enum | "success", "warning", "error", "skipped" |
| `duration_ms` | int | Execution time in milliseconds |
| `output_file` | string? | Output file if applicable |
| `message` | string? | Additional info or error message |

### ErrorInfo

Error details for failed conversions.

| Field | Type | Description |
|-------|------|-------------|
| `phase` | int | Phase where error occurred |
| `step` | string | Step where error occurred |
| `code` | string | Error code for programmatic handling |
| `message` | string | Human-readable error message |
| `recoverable` | bool | Whether resume might succeed |
| `suggestion` | string | Suggested action for user |

## Relationships

```
ConversionState
    ├── 1:1 PDFMetadata (referenced via output_dir/metadata.json)
    ├── 1:N PhaseResult (embedded in phase_results array)
    │       └── 1:N StepResult (embedded in steps array)
    └── 0:1 ErrorInfo (embedded if status="failed")
```

## Validation Rules

### ConversionState
- `version` must match current schema version for resume
- `pdf_path` must exist and be readable
- `output_dir` must be writable
- `current_phase` must be 0-10
- `current_step` must match pattern `\d+\.\d+`
- `completed_phases` must be sorted ascending
- `completed_phases` values must be < `current_phase`

### PDFMetadata
- `page_count` must be > 0
- `file_size_bytes` must be > 0
- `font_count` must be >= 0
- `image_count` must be >= 0

### PreflightReport
- `font_complexity` derived from `font_count`:
  - low: 1-5 fonts
  - moderate: 6-15 fonts
  - high: 16+ fonts
- `overall_complexity` derived from combination of font complexity, page count, image count

## Enumerations

### ConversionStatus
```
in_progress  # Conversion actively running
completed    # All phases finished successfully
failed       # Stopped due to error
cancelled    # User cancelled (e.g., declined pre-flight)
```

### PhaseStatus / StepStatus
```
success   # Completed without issues
warning   # Completed with non-fatal warnings
error     # Failed, may be recoverable
skipped   # Intentionally skipped (e.g., resume)
```

### TOCApproach
```
embedded  # PDF has embedded outline
visual    # Need agent to parse visual TOC page
none      # No TOC detected
```

### Complexity
```
low       # Simple PDF, minimal user review needed
moderate  # Average complexity
high      # Complex layout, expect more user involvement
```
