# Research: Installation and Walking Skeleton

**Phase 0 Output**: All unknowns resolved for implementation planning.

## Decisions

### Decision: Python Version 3.11+
- **Rationale**: Constitution requires Python 3.8+, but spec constraints align with 3.11+ for uv compatibility and modern features.
- **Alternatives Considered**: 3.8 (rejected for older stdlib limitations), 3.10 (rejected for minor version consistency).

### Decision: UV Tool Layout Adherence
- **Rationale**: Follows uv's standard cross-platform installation paths for consistency and reliability.
- **Alternatives Considered**: Custom installer (rejected for complexity), system package managers (rejected for cross-platform issues).

### Decision: Agent Validation Approach
- **Rationale**: Command existence check with helpful error messages, following spec-kit pattern for user experience.
- **Alternatives Considered**: No validation (rejected for poor UX), full integration tests (rejected as overkill for init phase).

### Decision: Script Generation Strategy
- **Rationale**: Template-based generation with platform-specific syntax variations, ensuring identical functionality.
- **Alternatives Considered**: Runtime interpretation (rejected for performance), external script files (rejected for distribution complexity).

### Decision: Sequence Number Handling
- **Rationale**: Filesystem scan for highest existing number, with directory creation if missing.
- **Alternatives Considered**: Database storage (rejected for overkill), config file (rejected for additional complexity).

### Decision: Template Storage
- **Rationale**: Local subfolder in gm-kit repo (gm-kit-templates) for version control and offline operation.
- **Alternatives Considered**: Remote download (rejected for network dependency), embedded strings (rejected for maintainability).

## Dependencies & Patterns

### UV Installation Patterns
- Research: Standard uv tool install creates predictable directory structures across platforms.
- Best Practice: Validate installation post-command, handle PATH setup variations.

### Agent Integration Patterns
- Research: Each agent has unique prompt/command locations and slash command syntax.
- Best Practice: Centralized config mapping agents to locations, with fallback for discontinued tools.

### Interactive CLI Patterns
- Research: pexpect enables reliable testing of prompts, input validation, and error scenarios.
- Best Practice: Simulate user interactions in tests, validate both success and failure paths.