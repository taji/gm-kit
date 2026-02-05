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

## Alternative: editable install (for contributors)

If someone is hacking on gm-kit itself:

```bash
git clone https://github.com/taji/gm-kit.git
cd gm-kit
uv pip install -e .
```
### Supported Agents
`claude`, `codex-cli`, `gemini`, `qwen`

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

gm-kit is developed using Spec-Kit.

Features begin as prompts in `BACKLOG.md`, reference shared context in
`docs/team/project-overview.md`, and are refined into formal specifications
under `specs/` before implementation.

This approach is intended to:
- Keep intent and implementation aligned
- Reduce feature drift
- Make design decisions explicit and reviewable

### Workflow & Feature Creation
1. **Read the overview** in `docs/team/project-overview.md`.
2. **Pick or add a prompt** in `BACKLOG.md` (prompts are the backlog).
3. **Run** `/speckit.specify`, then `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`.
4. **Sync docs**: merge quickstarts into `docs/user/user_guide.md`, and update `ARCHITECTURE.md` when design changes.

#### Add a Feature (quick path)
1. Choose an epic/prompt from `BACKLOG.md`.
2. Copy the prompt into `/speckit.specify` and attach `docs/team/project-overview.md` + `BACKLOG.md`.
3. Run `/speckit.plan`, `/speckit.tasks`, `/speckit.implement` for the feature folder.

### Testing Requirements
- PowerShell (`pwsh`) is required on Linux to run bash vs PowerShell parity tests.

### Dev Tools
- Agent install helpers live in `devtools/scripts/` (`agents.registry.sh`, `provision_agents.sh`, `remove_agents.sh` ).

### Reference Docs
- Spec-Kit guidelines: `docs/team/speckit_guidelines.md`
- Prompt templates for new commands: `docs/team/speckit_prompt_templates_for_gmkit.md`
