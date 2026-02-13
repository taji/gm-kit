# User Guide

Use this outline as the canonical user-facing documentation. Keep it current by merging feature-specific quickstarts into the sections below.

## Overview
- GM-Kit helps GMs initialize a project workspace with agent-specific prompts, scripts, and templates.
- Current focus: PDF → Markdown conversion via `gmkit pdf-convert` (code-driven pipeline with per-phase artifacts).

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
### PDF → Markdown (`gmkit pdf-convert`)
1. Run `gmkit pdf-convert <pdf-path> --output <output-dir>`.
2. Review generated phase outputs and the final markdown draft.
3. Optionally re-run a phase or resume from an existing output directory.

#### Common Commands
- Full pipeline: `gmkit pdf-convert <pdf-path> --output <output-dir> --yes`
- Re-run a phase: `gmkit pdf-convert --phase <n> <output-dir>`
- Resume: `gmkit pdf-convert --resume <output-dir>`
- Status: `gmkit pdf-convert --status <output-dir>`
- Diagnostics bundle: `gmkit pdf-convert <pdf-path> --output <output-dir> --diagnostics`
- Callout config: `gmkit pdf-convert <pdf-path> --output <output-dir> --gm-callout-config-file callout_config.json`

#### Key Outputs
```
<output-dir>/
├── .state.json
├── metadata.json
├── toc-extracted.txt
├── font-family-mapping.json
├── callout_config.json
├── images/
│   └── image-manifest.json
├── preprocessed/
│   └── <filename>-no-images.pdf
├── <filename>-phase4.md
├── <filename>-phase5.md
├── <filename>-phase6.md
├── <filename>-phase8.md
├── conversion-report.md
└── diagnostic-bundle.zip (when --diagnostics is set)
```

Notes:
- `callout_config.json` is created automatically if not provided; edit it before proceeding if you need custom callout boundaries.
- `font-family-mapping.json` captures font signatures (family + size + weight + style) used for heading inference.
- `diagnostic-bundle.zip` contains state, metadata, and phase outputs for troubleshooting.

### /gmkit.hello-gmkit
This is a walking-skeleton placeholder command retained for onboarding and basic flow validation.
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

- `gmkit pdf-convert <pdf-path> [--output <dir>] [--yes]`
- `gmkit pdf-convert --phase <n> <dir>`
- `gmkit pdf-convert --resume <dir>`
- `gmkit pdf-convert --status <dir>`
- `gmkit pdf-convert --diagnostics <pdf-path> --output <dir>`

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

## Contributor CI
- Pull requests to `master` run Linux CI gates (lint, typecheck, unit, integration, parity, security audit) via `just` tasks.
- Parity checks compare bash vs PowerShell-generated outputs on Linux (PowerShell is installed in CI as needed).

## Release Notes / Changes
- Notable changes that affect user behavior or compatibility.
- Migration/upgrade steps when required.

> Keep this guide in sync with new features; it should be the single source of truth for user-facing behavior.
