# GM-Kit

GM-Kit lets a GM reshape the contents of a long-form published scenario PDF into a bullet-pointed outline inspired by Kelsey Dionne’s Arcane Library format, using Spec-Kit workflows (CLI scaffolding + agent-executed commands/templates). It adds value by reliably turning long scenario prose (backstory, hooks, encounters, transitions, character beats, GM guidance) into crisp Arcane Library–style outlines and checklists that preserve critical links and clues while reducing cognitive load at the table. It keeps story flow intact by mapping those details into one-page encounter outlines with clear transitions between encounters.

## Mission Snapshot
- **Arcane Library output:** Scenario ingest, distillation, and authoring target Synopsis, Background, Word to the GM, Pacing/Transitions, Intro Page, and the one-page encounter schema (Approach → Developments → Dramatic Question → Challenge/Social → Character Cards → GM Guidance → Transition).
- **System-agnostic & Obsidian-friendly:** Use Stat Source references instead of mechanics and rely on Markdown with YAML frontmatter plus relative links so Obsidian vaults stay portable.
- **Spec-Kit alignment:** Each feature starts from the prompts in `BACKLOG.md`, references the overview in `planning/project-overview.md`, and lands as a documented plan plus implementation artifacts under `specs/`.

## Workflow & Feature Creation
1. **Read the overview** in `planning/project-overview.md` to understand the current vision and epics.
2. **Pick or add a prompt** in `BACKLOG.md` that matches the feature idea (prompts are the backlog—no separate TODO list).
3. **Run** `/speckit.specify` with the prompt text to generate the spec under `specs/<feature>/spec.md`. Follow with `/speckit.plan`, `/speckit.tasks`, and `/speckit.implement` as usual.
4. **Capture decisions** in `planning/Gm-Kit Development Journal.md` or Obsidian, then sync those notes back into git so future contributors can trace the work.

### Add a Feature (quick path)
1. Choose an epic/prompt from `BACKLOG.md` (or add a new entry aligned with the overview).
2. Copy the prompt text into `/speckit.specify` and attach `planning/project-overview.md` + `BACKLOG.md` as context.
3. Run `/speckit.plan`, `/speckit.tasks`, and `/speckit.implement` on the generated feature folder.
4. Update planning docs if the epic or prompt changes, then re-run the manual audit (below) before opening a PR.

## Contributor Lifecycle
1. **Prompts as backlog**: Epics live in `planning/project-overview.md` and `BACKLOG.md`. Capture new ideas directly as prompts.
2. **Specification**: Use `/speckit.specify` to produce the feature spec (`specs/<feature>/spec.md`).
3. **Planning**: Run `/speckit.plan` and `/speckit.tasks`; record decisions or clarifications in the journal/Obsidian, then commit the outputs.
4. **Implementation**: Follow `/speckit.implement` tasks, keeping notes about audits, README updates, and ignore rules in `planning/Gm-Kit Development Journal.md`.

## Keep README & Planning In Sync
1. Update `planning/project-overview.md` and `BACKLOG.md` whenever goals or prompts change.
2. Reflect the changes here (mission, workflow, contributor lifecycle, audit instructions) so onboarding stays frictionless.
