# Research: PDF Code Pipeline

## Decisions

### Decision 1: Use full font signatures for heading inference
- **Decision**: Use font family + size + weight + style for signature matching and label inference.
- **Rationale**: Family-only signatures fail for documents where headings share the same family but differ by weight/style (confirmed in Homebrewery and Call of Cthulhu analysis).
- **Alternatives considered**: Family-only signatures; size-only signatures.

### Decision 2: Code/Agent/User step ownership follows architecture tables
- **Decision**: E4-07a implements all Code-category steps; Agent and User steps are integration points only.
- **Rationale**: Keeps scope aligned with E4-07a and avoids duplicating E4-07b/E4-07c responsibilities.
- **Alternatives considered**: Implementing selected agent/user steps in code (rejected due to feature split).

### Decision 3: Use architecture decision log as sequencing constraints
- **Decision**: Enforce sequencing constraints from the architecture doc (e.g., 5.2 before 5.3; 7.9 before 7.10; 8.1 first; 8.10 single H1 logic).
- **Rationale**: These decisions encode known dependencies and reduce regressions.
- **Alternatives considered**: Reordering steps based on implementation convenience (rejected).

### Decision 4: POC scripts are reference-only
- **Decision**: Use POC scripts as guidance only; do not copy verbatim.
- **Rationale**: POC is Call of Cthulhu-specific and may contain hardcoded assumptions.
- **Alternatives considered**: Direct reuse of POC code (rejected).

### Decision 5: Error handling follows architecture error conditions table
- **Decision**: Use explicit error conditions from the architecture doc as the source of user-visible errors and tests.
- **Rationale**: Keeps error handling consistent across phases and predictable in CLI output.
- **Alternatives considered**: Ad-hoc error messages per phase (rejected).

## Notes

- The architecture document provides authoritative phase/step definitions, label inference logic (including multi-span TOC matching), and decision log constraints.
- Prior art scripts exist under `specs/004-pdf-research/poc-scripts/` and must be treated as reference-only.
