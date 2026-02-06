# Contract: PDF Conversion CLI

## Command: Full pipeline

**Input**:
- PDF path
- Output directory
- Optional flags (diagnostics, resume, phase, from-step, status)

**Expected Behavior**:
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
