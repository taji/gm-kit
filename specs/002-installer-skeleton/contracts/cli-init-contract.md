# CLI Contract: gmkit init

**Purpose**: Defines the interface contract for the gmkit init command.

## Command Signature
```
gmkit init <temp-path> [--agent <agent-name>] [--os <os-type>]
```

## Parameters
- `temp-path`: Required absolute path to workspace directory
- `--agent`: Optional agent type (claude, codex-cli, gemini, qwen)
- `--os`: Optional OS type (macos/linux, windows)

## Input Validation
- temp-path: Must be writable, absolute path
- agent: Must be in supported list, validated for installation
- os: Must be "macos/linux" or "windows"

## Output
- Creates directory structure in temp-path:
  - .gmkit/scripts/{bash|powershell}/
  - .gmkit/templates/
  - .gmkit/memory/
- Generates files:
  - say-hello.{sh|ps1}
  - hello-gmkit-template.md
  - constitution.md
  - Agent-specific prompt files:
    - claude: .claude/commands/gmkit.hello-gmkit.md
    - codex-cli: .codex/prompts/gmkit.hello-gmkit.md
    - gemini: .gemini/commands/gmkit.hello-gmkit.toml
    - qwen: .qwen/commands/gmkit.hello-gmkit.toml

## Error Codes
- 1: Invalid temp path
- 2: Unsupported agent
- 3: Agent not installed
- 4: OS not supported

## Success Indicators
- All files created successfully
- No error output
- Exit code 0