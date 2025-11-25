# GM-Kit

GM-Kit lets a GM reshape the contents of a long-form published scenario PDF into a bullet-pointed outline inspired by Kelsey Dionne’s Arcane Library format, using Spec-Kit workflows (CLI scaffolding + agent-executed commands/templates). It adds value by reliably turning long scenario prose (backstory, hooks, encounters, transitions, character beats, GM guidance) into crisp Arcane Library–style outlines and checklists that preserve critical links and clues while reducing cognitive load at the table. It keeps story flow intact by mapping those details into one-page encounter outlines with clear transitions between encounters.

## Mission Snapshot
- **Arcane Library output:** Scenario ingest, distillation, and authoring target Synopsis, Background, Word to the GM, Pacing/Transitions, Intro Page, and the one-page encounter schema (Approach → Developments → Dramatic Question → Challenge/Social → Character Cards → GM Guidance → Transition).
- **System-agnostic & Obsidian-friendly:** Use Stat Source references instead of mechanics and rely on Markdown with YAML frontmatter plus relative links so Obsidian vaults stay portable.
- **Spec-Kit alignment:** Each feature starts from the prompts in `planning/prompts.md`, references the overview in `planning/project-overview.md`, and lands as a documented plan plus implementation artifacts under `specs/`.

## Workflow & Feature Creation
1. **Read the overview** in `planning/project-overview.md` to understand the current vision and epics.
2. **Pick or add a prompt** in `planning/prompts.md` that matches the feature idea (prompts are the backlog—no separate TODO list).
3. **Run** `/speckit.specify` with the prompt text to generate the spec under `specs/<feature>/spec.md`. Follow with `/speckit.plan`, `/speckit.tasks`, and `/speckit.implement` as usual.
4. **Capture decisions** in `planning/Gm-Kit Development Journal.md` or Obsidian, then sync those notes back into git so future contributors can trace the work.

### Add a Feature (quick path)
1. Choose an epic/prompt from `planning/prompts.md` (or add a new entry aligned with the overview).
2. Copy the prompt text into `/speckit.specify` and attach `planning/project-overview.md` + `planning/prompts.md` as context.
3. Run `/speckit.plan`, `/speckit.tasks`, and `/speckit.implement` on the generated feature folder.
4. Update planning docs if the epic or prompt changes, then re-run the manual audit (below) before opening a PR.

## Manual Structure Audit
Before each PR, run a lightweight manual audit so reviewers (and downstream AI agents) see the same structure:

1. Capture the top-level layout with `ls -a` (or `tree -L 1` if available) and paste the snapshot into the PR description or `planning/Gm-Kit Development Journal.md`.
2. Walk through the checklist from `specs/001-readme-audit/contracts/manual-audit.md` and confirm each item:
   - `[ ] planning/` — planning docs, prompts, journals
   - `[ ] spec-kit/` — upstream reference checkout (ignored by git)
   - `[ ] src/` — GM-Kit source
   - `[ ] temp-resources/` — scratch assets (ignored by git)
   - `[ ] README.md` — Arcane Library overview + workflow instructions
   - `[ ] justfile` — developer commands
   - `[ ] pyproject.toml` — project metadata
   - `[ ] uv.lock` — dependency lockfile
   - `[ ] .python-version` — interpreter pin
   - `[ ] specs/` — feature artifacts
3. Note any additions/removals discovered during the audit and update this README + planning docs accordingly.

`temp-resources/` (scratch assets) and `spec-kit/` (upstream reference) stay outside git history via `.gitignore`. Add new ignore rules whenever additional transient folders appear.

## Contributor Lifecycle
1. **Prompts as backlog**: Epics live in `planning/project-overview.md` and `planning/prompts.md`. Capture new ideas directly as prompts.
2. **Specification**: Use `/speckit.specify` to produce the feature spec (`specs/<feature>/spec.md`).
3. **Planning**: Run `/speckit.plan` and `/speckit.tasks`; record decisions or clarifications in the journal/Obsidian, then commit the outputs.
4. **Implementation**: Follow `/speckit.implement` tasks, keeping notes about audits, README updates, and ignore rules in `planning/Gm-Kit Development Journal.md`.
5. **Validation & Sync**: Re-run the manual audit, ensure README references remain accurate, and include the snapshot + checklist in your PR description.

The planning docs are the source of truth—update them first, then align README/feature docs to match.

## Keep README & Planning In Sync
1. Update `planning/project-overview.md` and `planning/prompts.md` whenever goals or prompts change.
2. Reflect the changes here (mission, workflow, contributor lifecycle, audit instructions) so onboarding stays frictionless.
3. Run the manual audit after documentation changes and attach the results to the PR along with a note in `planning/Gm-Kit Development Journal.md`.

If the README and planning docs ever diverge, the planning docs win; reconcile this file immediately after adjusting planning artifacts.
