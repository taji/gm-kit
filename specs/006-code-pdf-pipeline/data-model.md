# Data Model: PDF Code Pipeline

## Entities

### ConversionState
Represents the current pipeline execution state.
- **Fields**: pdf_path, output_dir, current_phase, current_step, completed_phases, status, timestamps, config
- **Relationships**: references PhaseResult records and phase output files
- **Notes**: `config` dict stores runtime settings including `gm_keyword`, `gm_callout_config_file` (resolved path), `cli_args`, and `auto_proceed`

### PhaseResult
Represents the result of executing a single phase.
- **Fields**: phase_num, status, steps[], warnings[], errors[], output_file, duration
- **Relationships**: contains StepResult entries

### StepResult
Represents a single step outcome within a phase.
- **Fields**: step_id, description, status, message, duration

### PhaseStatus (Enum)
Valid status values for phases and steps.
- **Values**: SUCCESS, WARNING, ERROR, SKIPPED
- **Notes**: WARNING indicates non-fatal anomaly; pipeline continues. See spec §Terminology for examples.

### FontSignature
Represents a font-based signature used for heading inference.
- **Fields**: id, family, size, weight, style, sample_texts, suggested_level, label
- **Notes**:
  - `id`: Unique identifier (e.g., "sig001") for reference in text markers
  - `suggested_level`: Algorithm's numeric heading guess (1, 2, 3) for diagnostics
  - `label`: User-confirmed markdown heading ("H1", "H2", "H3", or null) or callout label ("callout_gm", "callout_sidebar", "callout_read_aloud") used for final output

### CalloutConfig
Represents the callout boundary configuration file (`callout_config.json`).
- **Fields**: Array of callout definition objects
- **Callout Definition Fields**: start_text (required), end_text (required), label (optional, defaults to "callout_gm")
- **Notes**:
  - Created as an empty array `[]` in the output directory if not provided via `--gm-callout-config-file`
  - Loaded by Phase 7 to identify font signatures whose content falls within callout boundaries
  - Valid labels: `callout_gm`, `callout_sidebar`, `callout_read_aloud`, or custom labels prefixed with `callout_`
- **Example**:
  ```json
  [
    {"start_text": "Keeper's Note:", "end_text": "End of Note", "label": "callout_gm"},
    {"start_text": "Read Aloud:", "end_text": "End Read Aloud", "label": "callout_read_aloud"}
  ]
  ```

### FontMapping
Represents the font signature mapping file used in label review.
- **Fields**: signatures[] (FontSignature), metadata, version

### ImageManifest
Represents image positions for later link injection.
- **Fields**: page, x/y coordinates, width/height, filename

### ConversionReport
Represents the final run summary.
- **Fields**: summary, quality ratings, remaining issues, diagnostics bundle references

## Validation Rules

- FontSignature MUST include family + size + weight + style.
- ConversionState MUST reference an existing output directory.
- PhaseResult MUST include at least one StepResult.
- ImageManifest entries MUST include page and filename.
- CalloutConfig entries MUST include start_text and end_text; label is optional.
- CalloutConfig file MUST be valid JSON (array of objects) or empty file (treated as empty array).
