# Data Model — GM-Kit README & Structure Audit

## Entity: README
- **Purpose**: Primary onboarding document communicating mission, workflow, feature creation steps, and manual audit process.
- **Fields**:
  - `mission_overview` — description of Arcane Library focus and goals.
  - `workflow_summary` — ordered list detailing todos → prompts → specs → plans → tasks → implementation.
  - `feature_add_steps` — numbered instructions referencing `planning/prompts.md` and `/speckit.specify`.
  - `audit_instructions` — shell commands (`ls -a` or `tree -L 1`) plus checklist items for required directories/files.
  - `contributor_lifecycle` — detailed explanation of todos → prompts → specs → `/speckit.plan` → tasks → implementation → validation, including artifact locations and sync guidance.
  - `sync_guidance` — steps for keeping README in sync with planning docs after updates.
- **Relationships**:
- References `planning/project-overview.md` (context).
- References `planning/prompts.md` (feature prompts and epics).
- References audit evidence stored in PR descriptions or planning notes.

## Entity: Ignore List (`.gitignore`)
- **Purpose**: Prevent transient folders (`spec-kit/`, `temp-resources/`) from entering version control.
- **Fields**:
  - `standard_python_patterns` — existing ignore rules (bytecode, envs, etc.).
  - `project_specific_entries` — explicit lines for `spec-kit/` and `temp-resources/`.
- **Validation**:
  - Running `git status` after creating files within ignored directories shows no tracked changes.

## Entity: Audit Evidence
- **Purpose**: Record of manual audit proving repo readiness before PRs.
- **Fields**:
  - `snapshot_command` — output of `ls -a` or `tree -L 1` taken at repo root.
  - `checklist_status` — list marking presence of planning docs, Python config files, and ignored directories.
  - `notes` — deviations or follow-up actions if paths are missing.
- **Lifecycle**:
  - Generated prior to each PR touching docs or structure.
  - Stored in PR description or planning journal entry.
