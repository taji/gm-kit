# Data Model: PDF Code Pipeline

## Entities

### ConversionState
Represents the current pipeline execution state.
- **Fields**: pdf_path, output_dir, current_phase, current_step, completed_phases, status, timestamps
- **Relationships**: references PhaseResult records and phase output files

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
- **Fields**: family, size, weight, style, sample_texts, label
- **Notes**: label is prefilled from TOC matching and heuristics

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
