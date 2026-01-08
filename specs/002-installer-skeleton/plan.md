# Implementation Plan: Installation and Walking Skeleton

**Branch**: `002-installer-skeleton` | **Date**: 2025-12-26 | **Spec**: specs/002-installer-skeleton/spec.md
**Input**: Feature specification from specs/002-installer-skeleton/spec.md

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Deliver a cross-platform Python CLI tool (gmkit) installed via uv, with init command that generates agent-specific scripts, prompts, and templates for a walking skeleton slash command (/gmkit.hello-gmkit) that creates sequenced greeting files.

## Technical Context

Language/Version: Python 3.11+ (constitution requirement, matches spec constraints)
Primary Dependencies: uv (installer), typer/rich (CLI framework, constitution)
Storage: Filesystem (scripts, templates, memory files)
Testing: pytest + pexpect (constitution, for interactive prompts)
Target Platform: macOS/Linux (bash), Windows (PowerShell)
Project Type: CLI tool
Performance Goals: gmkit init completes in <30 seconds
Constraints: No unsafe Python features (eval, pickle), no network post-install, idempotent init
Scale/Scope: Single-user operation, supports 10+ coding agents, cross-platform scripts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. Library-First**: PASS - gmkit-cli is a standalone CLI library with clear purpose (TTRPG GM tooling installer).

**II. CLI Interface**: PASS - Exposes functionality via gmkit command with stdin/args → stdout, JSON + human-readable output.

**III. Test-First**: PASS - TDD enforced, tests written before implementation (pytest + pexpect).

**IV. Integration Testing**: PASS - Contract tests for new CLI, inter-agent communication via slash commands.

**V. Observability**: PASS - Text I/O debuggable, structured logging; Versioning follows MAJOR.MINOR.BUILD.

**VI. AI Agent Integration**: PASS - Supports prioritized agents with templates from local repo folders (templates/, templates/commands/, scripts/), fallback for discontinued tools.

**VII. Interactive CLI Testing**: PASS - pexpect for testing gmkit init prompts, validates unsupported agents/network failures.

**VIII. Cross-Platform Installation**: PASS - UV with platform-specific paths, retry logic with exponential backoff.

**Additional Constraints**: PASS - Python 3.8+, typer/rich/httpx/uv; no unsafe features; security via OS keychains/env; performance <30s init.

**Gates**: Simplicity (no unnecessary abstraction), Anti-Abstraction (direct implementation), No Future-Proofing (MVP focus) - all PASS.

## Project Structure

### Documentation (this feature)

```text
specs/002-installer-skeleton/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/gm_kit/                    # Existing Python package
├── __init__.py
├── cli.py                      # Main CLI entry point (new)
├── installer.py                # UV installer logic (new)
├── init.py                     # gmkit init command logic (new)
├── validator.py                # Agent validation (new)
├── script_generator.py         # Bash/PowerShell script generation (new)
├── template_manager.py         # Template handling, TOML generation, and validation (new)
└── agent_config.py             # Agent-specific configurations (folder paths, file formats per data-model.md)

templates/                      # Source templates in gm-kit repo (mirroring spec-kit)
├── commands/                   # Source prompt files for slash commands
│   ├── gmkit.hello-gmkit.md     # Source template (single source of truth)
└── hello-gmkit-template.md     # Output template for greetings

scripts/                        # Source scripts
├── bash/
│   └── say-hello.sh            # Bash script template
└── powershell/
    └── say-hello.ps1           # PowerShell script template

memory/                         # Constitution and shared memory
└── constitution.md             # GM-Kit principles

tests/
├── unit/                       # Unit tests
│   ├── test_cli.py
│   ├── test_installer.py
│   ├── test_init.py
│   ├── test_validator.py
│   ├── test_script_generator.py
│   ├── test_template_manager.py
│   └── test_agent_config.py
├── integration/                # Integration tests
│   ├── test_full_init_flow.py
│   ├── test_agent_validation.py
│   └── test_toml_validation.py  # TOML generation and validation tests
└── contract/                   # Contract tests for CLI interfaces
    └── test_cli_contracts.py

```

**Structure Decision**: Single project CLI structure - builds on existing gm_kit package with new modules for installer/init functionality. Tests follow constitution requirements with pexpect for interactive testing. Agent-specific configurations reference the enhanced CLI contract specifications for exact folder paths and file formats.

## Template Generation Strategy

### Agent-Specific File Generation
The implementation uses a single-source approach where `templates/commands/gmkit.hello-gmkit.md` in the gm-kit repo serves as the master template, with agent-specific generation during initialization:

1. **Source Templates**: Maintain `.md` prompt files as single source of truth in `templates/commands/` (gm-kit repo)
2. **Agent-Specific Generation**: During `gmkit init`, generate agent-appropriate files in user project:
   - **claude**: Copy to `.claude/commands/gmkit.hello-gmkit.md`
   - **codex-cli**: Copy to `.codex/prompts/gmkit.hello-gmkit.md`
   - **gemini**: Generate `.gemini/commands/gmkit.hello-gmkit.toml` with embedded content
   - **qwen**: Generate `.qwen/commands/gmkit.hello-gmkit.toml` with embedded content

3. **TOML File Generation (Gemini/Qwen)**:
   - Read source `.md` content and embed in `.toml` format:
   ```toml
   description = "GM-Kit Hello World command for TTRPG game mastering"
   
   prompt = """
   [EMBEDDED_MARKDOWN_CONTENT_HERE]
   """
   ```
4. **Template Manager Logic**:
   - For claude/codex-cli: Direct file copy from source templates
   - For gemini/qwen: Read `.md` content and generate `.toml` files with embedded content
   - This approach ensures single source of truth while supporting agent-specific formats

5. **Benefits**:
   - No duplicate content maintenance in gm-kit repo
   - Consistent prompting across all agents
   - Agent-specific format compliance without overhead
6. **TOML Validation Strategy**:
   - Use Python built-in `tomllib` library for validation (FR-017)
   - No external dependencies required for format verification
   - Clear error reporting with detailed location information
   - Validation-only approach (no TOML writing needed)

## Contract Integration

The implementation must reference the enhanced CLI contract specifications:

- **CLI Interface**: Follow `contracts/cli-init-contract.md` for exact command signature, validation rules, and error handling
- **Agent-Specific Output**: Use contract-defined folder paths and file formats for each agent
- **Validation Requirements**: Implement agent validation and TOML validation per contract specifications
- **Error Handling**: Follow contract-defined error messages and recovery procedures

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - implementation follows constitution principles without unnecessary complexity. All requirements align with enhanced specifications and contract definitions.
