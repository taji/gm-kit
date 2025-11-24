# Quickstart — GM-Kit README & Structure Audit

1. **Update README**
   - Add mission overview referencing the Arcane Library schema.
   - Document the prompt-driven workflow (ideas captured as prompts → specs → `/speckit.plan` → tasks → implementation → validation) and reference planning docs (`planning/project-overview.md`, `planning/prompts.md`).
   - Add “Add a Feature” section with numbered instructions for copying prompts into `/speckit.specify`.
   - Embed a contributor lifecycle section (within README) that details todos → prompts → specs → `/speckit.plan` → tasks → implementation → validation, including where each artifact lives.
   - Describe the manual audit (snapshot command + checklist) and remind contributors to paste results into PRs.
   - Include guidance on keeping README and planning docs synchronized.

2. **Adjust `.gitignore`**
   - Append explicit entries for `spec-kit/` and `temp-resources/`.
   - Verify with `git status` after creating files in those directories.

3. **Run Manual Audit**
   - Capture `ls -a` (or `tree -L 1`) at repo root.
   - Walk the checklist (planning/, specs/, src/, README.md, `.gitignore`, `pyproject.toml`, `uv.lock`, `.python-version`, ignored directories).
   - Paste snapshot + checklist into PR description or planning journal entry.

4. **Validation**
   - Confirm README instructions allow a newcomer to start a feature without external docs.
   - Ensure `spec-kit/` and `temp-resources/` remain untracked in git.
