# GM-Kit

GM-Kit helps GMs turn long-form scenarios into succinct, bullet-pointed outlines using a common shorthand format. It provides a CLI that initializes a project workspace with agent-specific prompts, scripts, and templates so you can run slash commands and generate consistent prep artifacts.

## Mission Snapshot
- **Scenario distillation:** Convert long prose (backstory, hooks, encounters, transitions, character beats, GM guidance) into crisp outlines and checklists.
- **System-agnostic:** Focus on story and scenario structure so content stays portable across systems.
- **Spec-Kit alignment:** Features start from prompts in `BACKLOG.md`, reference `docs/team/project-overview.md`, and land as specs under `specs/`.

## User Documentation
For now, the canonical user guide lives at `docs/user/user_guide.md`.

### Quick Start
1. Install: `uv tool install gmkit-cli`
2. Initialize a workspace (creates the folder if it does not exist):
   - Interactive: `gmkit init /tmp/gmkit-test`
   - Non-interactive: `gmkit init /tmp/gmkit-test --agent claude --os macos/linux`
3. In your agent, run: `/gmkit.hello-gmkit "Hello from Agent!"`
4. Result: `greetings/greeting01.md` is created from the template.

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
Developer guidance lives under `docs/team/` and should be kept in sync with the README.

### Workflow & Feature Creation
1. **Read the overview** in `docs/team/project-overview.md`.
2. **Pick or add a prompt** in `BACKLOG.md` (prompts are the backlog).
3. **Run** `/speckit.specify`, then `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`.
4. **Sync docs**: merge quickstarts into `docs/user/user_guide.md`, and update `ARCHITECTURE.md` when design changes.

### Add a Feature (quick path)
1. Choose an epic/prompt from `BACKLOG.md`.
2. Copy the prompt into `/speckit.specify` and attach `docs/team/project-overview.md` + `BACKLOG.md`.
3. Run `/speckit.plan`, `/speckit.tasks`, `/speckit.implement` for the feature folder.

### Testing Requirements
- PowerShell (`pwsh`) is required on Linux to run bash vs PowerShell parity tests.

### Dev Tools
- Agent install helpers live in `devtools/scripts/` (`agents.registry.sh`, `provision_agents.sh`, `remove_agents.sh`).

### Reference Docs
- Spec-Kit guidelines: `docs/team/speckit_guidelines.md`
- Prompt templates for new commands: `docs/team/speckit_prompt_templates_for_gmkit.md`
