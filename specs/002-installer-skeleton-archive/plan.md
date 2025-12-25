# Implementation Plan: Installation and Walking Skeleton

**Branch**: `002-installer-skeleton` | **Date**: 2025-12-19 | **Spec**: specs/002-installer-skeleton/spec.md
**Input**: Feature specification from `/specs/002-installer-skeleton/spec.md`

**Note**: This plan outlines the implementation of a Python/uv installer for GM-Kit with a walking skeleton CLI that generates agent-specific scripts and prompts.

## Summary

Build a Python CLI tool installed via uv that provides a "gmkit init" command. The command takes a required temp folder path and optional agent/OS parameters, creates the temp folder if it doesn't exist, creates .gmkit/scripts/bash/ (for Linux/MacOS) or .gmkit/scripts/powershell/ (for Windows), .gmkit/templates/, and .gmkit/memory/ subfolders, generates constitution.md in .gmkit/memory/, prompts for missing values interactively, and generates platform-appropriate scripts and agent prompts for the /hello-gmkit slash command. The /hello-gmkit command calls the hello-gmkit script, which processes a hello-gmkit.md template to fill in a basic greeting and writes it to a greeting/ folder (placeholder for future GM artifact generation). Include automated testing using pexpect for CLI interactions and subprocess for script execution verification.

## Technical Context

**Language/Version**: Python 3.11+ (matches pyproject.toml)  
**Primary Dependencies**: uv (installer), pexpect (testing interactive prompts), shutil (template copying)  
**Storage**: File system (writes scripts/prompts to temp workspace)  
**Testing**: pytest with pexpect for CLI interaction testing  
**Target Platform**: Cross-platform (Windows PowerShell, macOS/Linux bash)  
**Project Type**: CLI application  
**Performance Goals**: Command completion in under 30 seconds  
**Constraints**: Minimum Python 3.11, installation via `uv tool install gm-kit`  
**Scale/Scope**: Single command with agent/OS variations, generates .gmkit folder structure with constitution, includes hello-gmkit script for basic greeting generation

## Constitution Check

### I. Library-First
- **Status**: COMPLIANT - Implementation starts as a standalone CLI library with clear purpose (installer and init command)
- **Evidence**: Core functionality is self-contained in gm_kit package, independently testable

### II. CLI Interface
- **Status**: COMPLIANT - All functionality exposed via CLI with stdin/args → stdout, errors → stderr
- **Evidence**: gmkit init command uses typer for CLI interface, text-based I/O protocol

### III. Test-First (NON-NEGOTIABLE)
- **Status**: COMPLIANT - TDD enforced with unit tests required for all new code
- **Evidence**: FR-012 mandates test-first development, comprehensive test coverage planned

### IV. Integration Testing
- **Status**: COMPLIANT - Integration tests planned for CLI contract validation
- **Evidence**: pexpect-based tests for interactive prompts (FR-013), contract tests for init command

### V. Observability, Versioning & Breaking Changes
- **Status**: COMPLIANT - Text I/O ensures debuggability, structured logging planned
- **Evidence**: CLI outputs are text-based, logging via Python logging module

### VI. AI Agent Integration
- **Status**: COMPLIANT - Supports prioritized AI coding agents with dedicated prompts
- **Evidence**: FR-006 includes codex-cli and other prioritized agents, templates from gm-kit-templates subfolder

### VII. Interactive CLI Testing
- **Status**: COMPLIANT - Uses pexpect for testing interactive prompts
- **Evidence**: FR-013 mandates pexpect for gmkit init testing

### VIII. Cross-Platform Installation
- **Status**: COMPLIANT - Uses UV for installation with platform-specific bin paths
- **Evidence**: pyproject.toml configured for uv installation

**Overall**: All constitution principles are addressed and compliant.

## Project Structure

### Documentation (this feature)

```text
specs/002-installer-skeleton/
├── plan.md              # This file
├── research.md          # Technical research output
├── data-model.md        # Data structures and validation
├── quickstart.md        # User-facing quickstart guide
├── contracts/           # API/interface contracts
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
src/gm_kit/
├── __init__.py
├── cli.py               # Main CLI entry point with gmkit command group
├── init.py              # gmkit init command implementation
├── agents.py            # Agent definitions and prompt templates
├── scripts.py           # Cross-platform script generation (bash/powershell)
└── templates.py         # Template copy and management

tests/
├── unit/
│   ├── test_init.py     # Unit tests for init command
│   ├── test_agents.py   # Agent template tests
│   └── test_scripts.py  # Script generation tests
├── integration/
│   └── test_cli_flow.py # Full CLI flow tests with pexpect
└── conftest.py          # Test fixtures and configuration
```

**Structure Decision**: CLI-focused structure with clear separation of concerns - CLI interface, business logic, templates, and comprehensive test coverage including pexpect-based integration tests.

## Complexity Tracking

*No violations - this is a straightforward CLI implementation following established patterns.*</content>
<parameter name="filePath">/home/todd/Dev/gm-kit/specs/002-installer-skeleton/plan.md