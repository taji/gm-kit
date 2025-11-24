# Contract: README Structure

| Section | Required Content | Acceptance Criteria |
|---------|------------------|---------------------|
| Title & Mission | State that GM-Kit follows Kelsey Dionne’s Arcane Library prep schema and Spec-Kit workflows. | Readers can summarize the mission in one sentence after reading the opening section. |
| Workflow Summary | Describe the lifecycle: todos → prompts → specs → plans → tasks → implementation, referencing `planning/project-overview.md`. | Steps are ordered and reference the authoritative planning docs by path. |
| Feature Creation Instructions | Provide numbered steps telling contributors to copy prompts from `planning/prompts.md` into `/speckit.specify`, then follow clarify/plan/implement phases. | A newcomer can follow the steps to create a new feature spec without additional help. |
| Contributor Lifecycle Section | Within README, elaborate each lifecycle stage, storage locations, and how to sync notes back to Obsidian. | Contributors can trace a feature from todo through validation and know where to store artifacts. |
| Manual Audit | Explain how to capture `ls -a` (or `tree -L 1`) plus the checklist of required directories/files, and how to paste the results into PRs/planning notes. | Running the documented steps produces the same artifact auditors expect. |
| Sync Guidance | Outline how to update planning docs first, rerun the audit, and then refresh the README to stay in sync. | README changes always reference the latest planning context, preventing drift. |
