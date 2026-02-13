# Contract: PDF Conversion CLI

## Command: Full pipeline

**Input**:
- PDF path
- Output directory
- Optional flags (diagnostics, resume, phase, from-step, status, yes)
- Optional `--gm-keyword` (repeatable): Custom keywords to detect GM callouts
- Optional `--gm-callout-config-file`: Path to a JSON file defining custom callout boundaries. Each entry has `start_text`, `end_text`, and optional `label` (defaults to `callout_gm`). If not provided, an empty default `callout_config.json` is created in the output directory.

**Expected Behavior**:
- Creates default `callout_config.json` in output directory if `--gm-callout-config-file` is not provided
- During pre-flight confirmation, displays the callout config file path and offers an "R" (Resume) option so the user can edit the file before proceeding
- Produces per-phase artifacts
- Produces final markdown output
- Emits human-readable progress and error messages

## Command: Phase execution

**Input**:
- Phase number
- Output directory

**Expected Behavior**:
- Runs only the requested phase
- Produces that phase's output file and updates state

## Command: Resume

**Input**:
- Output directory

**Expected Behavior**:
- Resumes from last successful phase/step
- Updates active conversion state

## Command: Status

**Input**:
- Output directory

**Expected Behavior**:
- Prints conversion status and completed phases
