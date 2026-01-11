# Quickstart: Installation and Walking Skeleton

## Installation

1. Ensure uv is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Install gmkit: `uv tool install gmkit-cli`
3. Verify: `gmkit --help`

## Initialize Project

1. Create temp workspace: `mkdir /tmp/gmkit-test`
2. Run init: `gmkit init /tmp/gmkit-test --agent claude --os macos/linux`
3. Or interactive: `gmkit init /tmp/gmkit-test` (prompts for agent/OS)

### Agent Examples

**Claude (most common):**
```bash
gmkit init /tmp/gmkit-test --agent claude --os macos/linux
```

**Other supported agents:**
```bash
gmkit init /tmp/gmkit-test --agent codex-cli --os macos/linux
gmkit init /tmp/gmkit-test --agent gemini --os windows  
gmkit init /tmp/gmkit-test --agent qwen --os macos/linux
```

## Generated Files

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
└── .claude/                    # Claude-specific folder
    └── commands/
        └── gmkit.hello-gmkit.md # Claude uses .md files
```

### Other Agent Folder Structures
- **codex-cli**: `.codex/prompts/gmkit.hello-gmkit.md`
- **gemini**: `.gemini/commands/gmkit.hello-gmkit.toml`  
- **qwen**: `.qwen/commands/gmkit.hello-gmkit.toml`

**Agent-specific examples**:
- **claude**: `.claude/commands/gmkit.hello-gmkit.md`
- **codex-cli**: `.codex/prompts/gmkit.hello-gmkit.md`  
- **gemini**: `.gemini/commands/gmkit.hello-gmkit.toml`
- **qwen**: `.qwen/commands/gmkit.hello-gmkit.toml`

## Use Slash Command

1. Open your coding agent (claude/codex-cli/gemini/qwen)
2. Invoke: `/gmkit.hello-gmkit "Hello from Agent!"`
   - For claude/codex-cli: Uses `.md` prompt files
   - For gemini/qwen: Uses `.toml` prompt files
3. Result: Creates `greetings/greeting01.md` with filled template

## Next Steps

- Extend scripts for additional slash commands
- Add templates for campaign/scenario generation
- Test with different agents and platforms
