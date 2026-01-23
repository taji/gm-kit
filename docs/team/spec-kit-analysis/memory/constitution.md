# GM-Kit Constitution
<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->

## Core Principles

### I. Library-First
Every feature starts as a standalone library; Libraries must be self-contained, independently testable, documented; Clear purpose required - no organizational-only libraries.

### II. CLI Interface
Every library exposes functionality via CLI; Text in/out protocol: stdin/args → stdout, errors → stderr; Support JSON + human-readable formats.

### III. Test-First (NON-NEGOTIABLE)
TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced.

### IV. Integration Testing
Focus areas requiring integration tests: New library contract tests, Contract changes, Inter-service communication, Shared schemas.

### V. Observability, Versioning & Breaking Changes, Simplicity
Text I/O ensures debuggability; Structured logging required; MAJOR.MINOR.BUILD format; Start simple, YAGNI principles.

### VI. AI Agent Integration
Support prioritized AI coding agents (claude, gemini, qwen, codex-cli) with dedicated templates from local repo folders (templates/, templates/commands/, scripts/, memory/). Agent-specific prompts must be generated for /gmkit commands, with fallback for discontinued tools.

### VII. Interactive CLI Testing
Use pexpect for testing interactive prompts in `gmkit init`; all tests must simulate user input/output to validate edge cases like unsupported agents or network failures.

### VIII. Cross-Platform Installation
Require UV for installation with platform-specific bin paths (~/.local/bin on Unix, %USERPROFILE%\.local\bin on Windows); include retry logic for downloads with exponential backoff.

## Additional Constraints

Technology stack: Python 3.8+, typer, rich, httpx, uv for dependency management; no unsafe features (e.g., eval, pickle). Security: No credential storage in gmkit; rely on OS keychains or env vars for AI tools. Performance: Init command completes in <30 seconds; downloads retry on failure.

## Development Workflow

Quality Gates: Run just test, just lint, just typecheck, bandit, uv audit before commits; coverage >80%. Review Process: PRs must include tests, pass all gates, and sync to user-guide.md/ARCHITECTURE.md.

## Governance

Constitution supersedes all other practices; amendments require documentation, approval, migration plan. All PRs/reviews must verify compliance; complexity must be justified; use AGENTS.md for runtime development guidance.

**Version**: 1.2 | **Ratified**: 2025-12-19 | **Last Amended**: 2025-12-26
