# Feature Specification: GM-Kit README & Structure Audit

**Feature Branch**: `001-readme-audit`  
**Created**: 2025-11-24  
**Status**: Draft  
**Input**: User description: "Scaffold a minimal README describing GM-Kit’s Arcane Library mission, add a `.gitignore` that excludes `temp-resources/` and `spec-kit/`, and then audit the folder structure and included files to verify the project is ready for python development, is pushed push to gihtub. Include instructions in the readme on how to add features using the @prompts.md file as prompts for spec-kit to create features from. Success looks like: a repo that is ready for python development, PRs, and ignores transient analysis folders."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mission-first README (Priority: P1)

A maintainer needs a concise README that explains GM-Kit’s Arcane Library mission, the prompts-driven workflow, and how to use `planning/prompts.md` entries with `/speckit.specify` to start new features, eliminating dependence on a separate TODO list.

**Why this priority**: The README is the first touchpoint for contributors; without these instructions, no one can confidently add features.

**Independent Test**: Read the README; confirm it covers the mission, references planning docs, and includes numbered steps for using prompts to generate specs.

**Acceptance Scenarios**:

1. **Given** a new contributor opens the repository, **When** they read the README, **Then** they can describe GM-Kit’s Arcane Library focus and workflow without additional docs.
2. **Given** a maintainer wants to start a feature, **When** they follow the README instructions, **Then** they can locate a prompt in `planning/prompts.md` and run `/speckit.specify` successfully.

---

### User Story 2 - Ignore transient directories (Priority: P1)

As the repo owner, I must ensure `.gitignore` excludes `spec-kit/` and `temp-resources/` so reference checkouts and scratch assets never reach PRs.

**Why this priority**: Leaking these folders risks bloating commits and potentially exposing licensed content.

**Independent Test**: Populate both directories locally and run `git status`; they must remain untracked every time.

**Acceptance Scenarios**:

1. **Given** a local clone of spec-kit in `spec-kit/`, **When** the developer runs `git status`, **Then** nothing under that folder shows up.
2. **Given** temporary research artifacts in `temp-resources/`, **When** staging files, **Then** the temporary artifacts stay ignored.

---

### User Story 3 - Manual structure audit (Priority: P2)

A maintainer wants a lightweight audit checklist in the README so each PR can document the repo structure (top-level snapshot + required files) proving the project is ready for Python development and GitHub pushes.

**Why this priority**: PR reviewers need proof the repo includes required tooling and ignores, without running custom scripts.

**Independent Test**: Follow the README’s audit instructions by capturing `ls -a` output and marking the checklist; verify that mandatory directories and files exist.

**Acceptance Scenarios**:

1. **Given** the README audit steps, **When** a maintainer prepares a PR, **Then** they can paste a snapshot and checklist confirming readiness.
2. **Given** a missing required path (e.g., `planning/`), **When** running the checklist, **Then** the omission becomes obvious before opening the PR.

---

### User Story 4 - Contributor lifecycle documentation (Priority: P2)

Community contributors need a dedicated section within README that explains, in detail, how todos become prompts, specs, plans, tasks, and final implementations, including where status is recorded and how to sync notes back to Obsidian.

**Why this priority**: Without lifecycle documentation, contributors may improvise workflows that fall out of sync with planning artifacts, creating inconsistent specs and plans.

**Independent Test**: Open the contributor guide referenced in README and confirm it enumerates every stage (todos → prompts → specs → /plan → tasks → implementation → validation) with clear ownership.

**Acceptance Scenarios**:

1. **Given** a new contributor, **When** they follow the contributor lifecycle doc, **Then** they can trace how to move a todo epic through prompts and Spec-Kit commands without asking for help.
2. **Given** a maintainer reviewing a PR, **When** they compare the PR’s journey against the lifecycle doc, **Then** they can verify each stage was completed and documented.

---

### Edge Cases

- Planning docs missing or renamed: README must tell contributors to restore `planning/project-overview.md` and `planning/prompts.md` before creating new features.
- New contributors on systems without `tree`: audit instructions should fall back to `ls -a` or equivalent, ensuring the process works everywhere.
- Repository without remotes configured: audit should rely solely on local filesystem checks so it works offline.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: README MUST describe GM-Kit’s Arcane Library mission, emphasizing the Arcane Library schema and why the toolkit exists.
- **FR-002**: README MUST outline the prompts-driven lifecycle (ideas/epics recorded directly as prompts → specs → plans → tasks → implementation → validation) and explicitly direct users to copy prompts from `planning/prompts.md` into `/speckit.specify` when adding features.
- **FR-003**: README MUST provide step-by-step guidance for keeping itself in sync with planning docs (update planning first, rerun audit, then refresh README).
- **FR-004**: README MUST document a manual audit consisting of a filesystem snapshot and a checklist verifying presence of planning docs, Python project files, and ignored directories prior to PRs.
- **FR-005**: `.gitignore` MUST ignore `spec-kit/` and `temp-resources/` so transient folders never appear in `git status` or PR diffs.
- **FR-006**: Maintainers MUST be able to demonstrate the audit in PR descriptions by following the README instructions without installing additional tooling.
- **FR-007**: README MUST include a contributor lifecycle section that explains, step-by-step, the enforced workflow (todos → prompts → specs → `/speckit.plan` → tasks → implementation → validation), highlights where prompts/artifacts are stored, and instructs how to sync decisions back to Obsidian.

### Key Entities

- **README**: Canonical onboarding document containing the mission statement, workflow instructions, feature creation steps, and audit process.
- **Ignore List**: `.gitignore` entries ensuring `spec-kit/` (upstream reference) and `temp-resources/` (scratch assets) remain untracked.
- **Audit Evidence**: Snapshot (`ls -a` or equivalent) plus checklist recorded in PR descriptions or planning journals that confirms required directories/files exist and ignored folders remain untracked.

## Assumptions & Dependencies

- Planning docs (`planning/project-overview.md`, `planning/prompts.md`) already exist or can be restored from version control so the README can reference them; no separate TODO list is maintained.
- Contributors have access to basic shell commands (`ls`, `tree`, or platform equivalents) to capture audit snapshots without installing extra tooling.
- Git is initialized locally; even if no remote is configured, contributors can run audits against the local filesystem.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of onboarding reviews confirm that reading the README alone enables a contributor to describe the Arcane Library mission and workflow.
- **SC-002**: Across 3 consecutive dry runs, adding files to `spec-kit/` or `temp-resources/` results in zero tracked changes in `git status`.
- **SC-003**: Every PR touching docs for the next release includes the audit snapshot + checklist outlined in the README.
- **SC-004**: Manual audit verifies the presence of `planning/`, `src/`, `pyproject.toml`, `uv.lock`, `.python-version`, and README instructions before tagging the next release branch, with no missing items recorded.
- **SC-005**: At least 3 reviewers confirm (during the next cycle) that the contributor lifecycle documentation lets them trace a feature from todo through validation without additional clarification.
