# User Guide

Use this outline as the canonical user-facing documentation. Keep it current by merging feature-specific quickstarts into the sections below.

## Overview
- GM-Kit helps GMs initialize a project workspace with agent-specific prompts, scripts, and templates.
- Current focus: a walking skeleton command (`/gmkit.hello-gmkit`) that demonstrates the flow end to end.

## Getting Started
### Prerequisites
- `uv` installed (https://astral.sh/uv)
- A supported agent: claude, codex-cli, gemini, or qwen

### Installation
1. Install GM-Kit: `uv tool install gmkit-cli`
2. Verify: `gmkit --help`

### Initialize a Project
GM-Kit will create the folder if it does not exist.

1. Choose a workspace path (example: `/tmp/gmkit-test`)
2. Run init:
   - Non-interactive: `gmkit init /tmp/gmkit-test --agent claude --os macos/linux`
   - Interactive: `gmkit init /tmp/gmkit-test` (prompts for agent/OS)

### Agent Examples
```bash
gmkit init /tmp/gmkit-test --agent claude --os macos/linux
gmkit init /tmp/gmkit-test --agent codex-cli --os macos/linux
gmkit init /tmp/gmkit-test --agent gemini --os windows
gmkit init /tmp/gmkit-test --agent qwen --os macos/linux
```

## Core Workflows
### /gmkit.hello-gmkit
1. Run `gmkit init` to generate prompts, scripts, and templates.
2. In your agent, invoke: `/gmkit.hello-gmkit "Hello from Agent!"`
3. Result: `greetings/greeting01.md` (or next sequence number) is created from the template.

#### Invoking the Command in Your Agent
- Open your preferred AI agent and point it at your project folder.
- Enter the slash command as a single line in the agent prompt:
  - `/gmkit.hello-gmkit "Hello from Agent!"`
- The agent uses the installed prompt and runs the generated script behind the scenes.

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

Agent prompt locations:
- **claude**: `.claude/commands/gmkit.hello-gmkit.md`
- **codex-cli**: `.codex/prompts/gmkit.hello-gmkit.md`
- **gemini**: `.gemini/commands/gmkit.hello-gmkit.toml`
- **qwen**: `.qwen/commands/gmkit.hello-gmkit.toml`

## Commands and Controls
### CLI
- `gmkit init <path> --agent <agent> --os <macos/linux|windows>`
  - `--agent`: the AI assistant you use to generate GM content (claude, codex-cli, gemini, qwen).
  - `--os`: the operating system where you run that assistant (macos/linux or windows).
- `gmkit init <path>` (interactive prompt for agent/OS)

## Configuration
- Settings users can change (env vars, config files, toggles).
- Defaults, safe ranges, and how to revert.

## Data and Accounts
- What data is stored, where, and how to manage it.
- Account roles/permissions and limits that affect users.

## Troubleshooting and FAQ
### Common Issues
- `Unsupported agent`: use one of `claude`, `codex-cli`, `gemini`, or `qwen`.
- `os must be 'macos/linux' or 'windows'`: pass one of those values or use interactive mode.

## Release Notes / Changes
- Notable changes that affect user behavior or compatibility.
- Migration/upgrade steps when required.

> Keep this guide in sync with new features; it should be the single source of truth for user-facing behavior.
