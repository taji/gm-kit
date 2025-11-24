# Phase 0 Research — GM-Kit README & Structure Audit

## Decision 1: README emphasizes Arcane Library mission & prompts workflow
- **Decision**: Highlight the Arcane Library schema, link to `planning/project-overview.md`, and document the idea/prompt-based lifecycle (prompts → specs → plans → implementation) directly in README so no separate TODO list is required.
- **Rationale**: Maintainers rely on planning docs for authoritative scope; mirroring that hierarchy in README keeps contributors aligned without duplicating every detail.
- **Alternatives considered**:
  - *Keep README minimal and link only to planning folder*: rejected because new contributors would lack immediate context and might miss the prompt workflow.
  - *Copy full planning content into README*: rejected to avoid drift and duplication.

## Decision 2: Manual audit uses shell-native commands
- **Decision**: Instruct maintainers to run `ls -a` (or `tree -L 1` when available) plus a checklist enumerating required directories/files; no custom script.
- **Rationale**: Works across macOS/Linux/Windows without extra tooling, aligning with the user’s request to “audit the folder structure” manually.
- **Alternatives considered**:
  - *Ship a Python audit script*: rejected because user explicitly wants a manual audit and prefers no extra tooling.
  - *Rely on git hooks*: rejected because contributors may not have hooks installed, reducing reliability.

## Decision 3: `.gitignore` explicitly lists `spec-kit/` and `temp-resources/`
- **Decision**: Add direct entries for both directories at the bottom of `.gitignore`.
- **Rationale**: Ensures upstream reference clones and scratch assets never appear in `git status`, meeting success criteria.
- **Alternatives considered**:
  - *Use wildcard patterns (e.g., `*-resources/`)*: rejected because it risks ignoring legitimate directories unintentionally.
  - *Rely on global gitignore*: rejected because contributors cannot assume a shared global configuration.

## Decision 4: README instructions for adding features via prompts
- **Decision**: Include a numbered “Add a Feature” section describing how to pick a prompt from `planning/prompts.md`, run `/speckit.specify`, and keep README/planning synchronized.
- **Rationale**: Provides a reproducible process for new features, satisfying the requirement to “Include instructions … using the @prompts.md file as prompts.”
- **Alternatives considered**:
  - *Link to external documentation only*: rejected because the README must stand alone for onboarding.
  - *Describe the Spec-Kit workflow abstractly without steps*: rejected; success criteria require actionable instructions.

## Decision 5: Embedded contributor lifecycle section in README
- **Decision**: Add a contributor lifecycle section directly inside README that explicitly walks through todos → prompts → specs → `/speckit.plan` → tasks → implementation → validation, calling out where artifacts live and how to sync notes back to Obsidian.
- **Rationale**: Keeping the lifecycle in README avoids duplication and ensures new contributors see the guidance without hunting for separate files.
- **Alternatives considered**:
  - *Link to a separate document*: rejected to minimize drift between files and reduce navigation overhead.
  - *Fold details into the mission paragraph*: rejected to keep the mission concise while offering a clearly labeled lifecycle section.
