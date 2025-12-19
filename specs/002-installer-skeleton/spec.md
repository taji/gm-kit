# Feature Specification: Installation and Walking Skeleton

**Feature Branch**: `002-installer-skeleton`  
**Created**: 2025-12-18  
**Status**: Draft  
**Input**: User description: "Deliver a Python/uv installer that installs GM-Kit and its basic dependencies. The \"gmkit init\" command (invoked from terminal) takes three inputs: 1) required path to temp folder for writing scripts/prompts, 2) optional coding agent type (copilot, claude, gemini, cursor-agent, qwen, opencode, codex, windsurf, kilicode, auggie, codebuddy, roo, q/Amazon Q, amp), 3) optional target OS (windows for PowerShell or macos/linux for bash). If optional parameters are not provided, the Python script prompts the user to select them, then writes bash/PowerShell scripts and agent prompts for the /hello-gmkit slash command. Include a minimal test harness that proves code/test/watch loops work, with automated tests invoking \"gmkit init\" using command line parameters and verifying script/prompt files are written to the specified temp workspace.

Success looks like: contributors can install once with uv, run \"gmkit init\" from terminal (with required temp path and optional agent/OS params), have scripts/prompts written for /hello-gmkit, proven by tests verifying files in temp workspace, plus documentation on extending the skeleton."

## Clarifications

### Session 2025-12-19
- Q: What is the source for project templates? → A: Dedicated subfolder (gm-kit-templates in gm-kit repo)
- Q: How should the system handle network failures during template download? → A: Retry automatically with exponential backoff; after max retries, show error and exit
- Q: What are the key technical constraints for gm-kit? → A: Minimum Python 3.8, uv for installation
- Q: How should the system handle unsupported agent types? → A: Show error with list of supported agents

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install GM-Kit and Initialize Scripts/Prompts (Priority: P1)

A contributor installs GM-Kit once using uv, then runs "gmkit init" from the terminal with a temp folder path (and optionally agent and OS), resulting in bash/PowerShell scripts and agent prompts for the /hello-gmkit slash command being written to the temp workspace.

**Why this priority**: This is the core functionality - providing the installer and init command that sets up the walking skeleton.

**Independent Test**: Can be fully tested by installing with uv, running gmkit init with params, and verifying scripts/prompts are written, delivering the basic installation and initialization.

**Acceptance Scenarios**:

1. **Given** a fresh environment, **When** contributor runs uv install for GM-Kit, **Then** GM-Kit is installed with basic dependencies
2. **Given** installed GM-Kit, **When** contributor runs `gmkit init /path/to/temp --agent claude --os linux`, **Then** bash scripts and claude prompts for /hello-gmkit are written to /path/to/temp
3. **Given** installed GM-Kit, **When** contributor runs `gmkit init /path/to/temp` (no optional params), **Then** user is prompted for agent and OS, then scripts/prompts are written

---

### User Story 2 - Automated Testing with CLI Parameters (Priority: P2)

Automated tests invoke "gmkit init" using command line parameters to prefill choices, populate the specified temp workspace, and verify that script/prompt files are correctly written.

**Why this priority**: Ensures the feature works reliably through automated testing.

**Independent Test**: Can be fully tested by running the test suite that calls gmkit init with params and checks file outputs, delivering confidence in the implementation.

**Acceptance Scenarios**:

1. **Given** test environment, **When** test runs `gmkit init /temp --agent codex --os windows`, **Then** PowerShell scripts and codex prompts are written and verified
2. **Given** test environment, **When** test runs `gmkit init /temp` (no params), **Then** prompts are simulated and scripts/prompts are written
3. **Given** test environment, **When** test checks file contents, **Then** all expected scripts and prompts match specifications

---

### User Story 3 - Documentation for Extending the Skeleton (Priority: P3)

The feature includes documentation explaining how the /hello-gmkit skeleton can be extended for future commands, including how scripts and prompts are structured.

**Why this priority**: Enables future development by providing guidance on the walking skeleton.

**Independent Test**: Can be fully tested by reviewing the documentation and confirming it covers extension patterns, delivering guidance for maintainers.

**Acceptance Scenarios**:

1. **Given** the feature implementation, **When** developer reads the documentation, **Then** they understand how to add new slash commands
2. **Given** documentation, **When** developer follows the patterns, **Then** new commands integrate seamlessly
3. **Given** documentation, **When** it's reviewed, **Then** it includes examples of script/prompt structures

---

### Edge Cases

- What happens when temp folder path is invalid or inaccessible?
- How does system handle unsupported agent types or OS values: show error with list of supported values
- What if user cancels prompts during interactive mode?
- How to handle cases where required dependencies are missing?
- How to handle network failures during template download: retry with exponential backoff, show error and exit after max attempts

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a Python/uv installer that installs GM-Kit and its basic dependencies
- **FR-002**: System MUST accept "gmkit init" command with required temp folder path and optional agent/OS parameters
- **FR-003**: System MUST prompt user for agent and OS selections if optional parameters are not provided
- **FR-004**: System MUST write appropriate bash/PowerShell scripts based on selected OS
- **FR-005**: System MUST write agent-specific prompts for the /hello-gmkit slash command
- **FR-006**: System MUST support all listed agents (copilot, claude, gemini, cursor-agent, qwen, opencode, codex-cli, windsurf, q/Amazon Q)
- **FR-007**: System MUST support Windows (PowerShell) and MacOS/Linux (bash) script generation
- **FR-008**: System MUST include automated tests that invoke gmkit init with CLI parameters
- **FR-009**: System MUST verify that script and prompt files are correctly written to temp workspace
- **FR-010**: System MUST provide documentation on extending the /hello-gmkit skeleton for future commands
- **FR-011**: System MUST use project templates from the gm-kit-templates subfolder in the gm-kit repo
- **FR-012**: System MUST follow test-first development (TDD) for all new code, with unit tests required
- **FR-013**: System MUST use pexpect for testing interactive CLI prompts in gmkit init

### Key Entities *(include if feature involves data)*

- **Coding Agent**: Represents supported AI CLI tools, with attributes like name and prompt template
- **Operating System**: Represents target platform (windows/maclinux), determining script type (powershell/bash)
- **Temp Workspace**: File system path where scripts and prompts are written
- **Script File**: Platform-specific executable script (bash or powershell) that dispatches commands
- **Prompt File**: Agent-specific text file containing slash command prompts

### Technical Constraints
- Minimum Python version: 3.8
- Installation method: uv

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Contributors can install GM-Kit with uv in under 5 minutes
- **SC-002**: gmkit init command completes script/prompt generation in under 30 seconds
- **SC-003**: Automated tests pass for all supported agent/OS combinations
- **SC-004**: 100% of test runs correctly write expected files to temp workspace
- **SC-005**: Documentation enables new command extensions within 1 hour of reading