# GM-Kit

**Status: prealpha. Expect breaking changes.**

## What is gm-kit?

**gm-kit is an experimental, open-source toolkit for designing, analyzing, and preparing tabletop RPG adventures using structured workflows and AI-assisted tools.**

Rather than generating prose-heavy adventures, gm-kit treats scenarios as **systems**:
information flows, player decision points, failure modes, and table usability.

The project explores questions such as:
- Why do many published adventures fail at the table?
- How can scenario structure reduce GM cognitive load?
- How can AI assist prep and analysis without replacing human judgment?
- Can adventures be authored once and rendered many ways (GM notes, zines, PDFs, VTT assets)?

gm-kit is intentionally **markdown-first**, **spec-driven**, and **workflow-oriented**.
It is closer to a *lab notebook* or *design environment* than a finished product or framework.

This repository documents the tools, patterns, and experiments emerging from that exploration.

---

## What gm-kit is not

- Not a VTT
- Not a content generator that replaces the GM
- Not a polished framework or stable API
- Not a supported product with guaranteed maintenance or timelines

gm-kit prioritizes clarity, experimentation, and learning over completeness or stability.

## Mission Snapshot

- **Scenario distillation & expansion**
  - **Reduce**: Convert long prose (backstory, hooks, encounters, transitions, character beats, GM guidance) into crisp outlines and checklists.
  - **Expand**: Fill in missing GM details, roleplay notes, and structural gaps to ensure the scenario runs smoothly and aligns with your table.
- **System-agnostic**: Focus on story and scenario structure so content remains portable across systems.

## User Documentation
For now, the canonical user guide lives at `docs/user/user_guide.md`.

### Quick Start

gm-kit is not yet published to a package index. Installation is currently done directly from the GitHub repository.

1. Install: `uv tool install git+https://github.com/taji/gm-kit.git`
2. Initialize a workspace (creates the folder if it does not exist):
   - Interactive: `gmkit init /tmp/gmkit-test`
   - Non-interactive: `gmkit init /tmp/gmkit-test --agent claude --os macos/linux`
3. In your agent, run: `/gmkit.hello-gmkit "Hello from Agent!"`
4. Result: `greetings/greeting01.md` is created from the template.

For PDF conversion, use:
- Agent entrypoint: `/gmkit.pdf-to-markdown "<pdf-path>"`
- CLI entrypoint: `gmkit pdf-convert <pdf-path> --output <dir> --yes`

## Alternative: editable install (for contributors)

If someone is hacking on gm-kit itself:

```bash
git clone https://github.com/taji/gm-kit.git
cd gm-kit
uv pip install -e .
```

Note: `uv run --editable -- ...` is a **development-only** workflow for contributors running from a local clone. End users should run the installed `gmkit` command directly (no `--editable`).
### Supported Agents
`claude`, `codex-cli`, `opencode`, `gemini`, `qwen`

### Generated Files (Example)
```
/tmp/gmkit-test/
├── .gmkit/
│   ├── memory/
│   │   └── constitution.md
│   ├── scripts/
│   │   └── bash/
│   │       └── say-hello.sh
│   └── templates/
│       └── hello-gmkit-template.md
└── .claude/
    └── commands/
        └── gmkit.hello-gmkit.md
```

## Developer Documentation

### Contributions & Feedback

gm-kit is currently in an exploratory, prealpha phase.
The primary focus is on clarifying ideas, workflows, and structure.

- Bug reports, design discussions, and thoughtful feedback are welcome.
- Pull requests may be reviewed selectively or deferred while the core design evolves.
- There is no guarantee of response time or acceptance.

If you’re interested in experimenting with gm-kit or adapting it for your own use,
forking the repository is encouraged.

### Design & Development Philosophy

gm-kit now uses **Superpowers** as the active workflow for new feature design,
planning, and implementation work.

Features begin as prompts in `BACKLOG.md`, reference shared context in
`docs/team/project-overview.md`, and are refined into feature-specific design
and plan artifacts under `specs/` before implementation.

This approach is intended to:
- Keep intent and implementation aligned
- Reduce feature drift
- Make design decisions explicit and reviewable

Existing Spec-Kit artifacts remain in the repository as historical references
unless a feature is explicitly migrated or replaced.

### Workflow & Feature Creation
1. **Read the overview** in `docs/team/project-overview.md`.
2. **Pick or add a prompt** in `BACKLOG.md` (prompts are the backlog).
3. **Use Superpowers** to brainstorm, write the plan, and implement the feature.
4. **Store feature artifacts** in `specs/<feature-name>/` using:
   - `feature_journal.md`
   - `superpowers-design.md`
   - `superpowers-plan.md`
5. **Sync docs**: merge quickstarts into `docs/user/user_guide.md`, and update `ARCHITECTURE.md` when design changes.

#### Add a Feature (quick path)
1. Choose an epic/prompt from `BACKLOG.md`.
2. Create or reuse the feature folder under `specs/<feature-name>/`.
3. Keep `feature_journal.md` in that folder and append to it every session.
4. Use Superpowers to produce `superpowers-design.md` and `superpowers-plan.md` in that same folder.
5. Implement from the approved Superpowers plan.

### Testing Requirements
- PowerShell (`pwsh`) is required on Linux to run bash vs PowerShell parity tests.

### Dev Tools
- Agent install helpers live in `devtools/scripts/` (`agents.registry.sh`, `provision_agents.sh`, `remove_agents.sh`).

### Reference Docs
- Spec-Kit guidelines: `docs/team/speckit_guidelines.md`
- Prompt templates for new commands: `docs/team/speckit_prompt_templates_for_gmkit.md`
- Superpowers is the active workflow for new feature work; older Spec-Kit docs remain for historical context.
