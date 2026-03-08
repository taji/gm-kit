# Quickstart: PDF→Markdown Agent-Driven Pipeline

## Purpose
Validate agent-step prompt outputs against JSON contracts and rubrics for the reference corpus.

## Prerequisites
- Python 3.8+ with project dependencies installed (`uv sync --extra dev`)
- A supported agent CLI installed and authenticated/configured (for live agent-step integration testing), e.g. Claude Code, Codex CLI, or OpenCode
- Optional: set `GM_AGENT` to choose agent for integration tests (default is `codex`)
- Reference corpus PDFs in `tests/fixtures/pdf_convert/`:
  - `The Homebrewery - NaturalCrit.pdf` (with TOC)
  - `The Homebrewery - NaturalCrit - Without TOC.pdf`
  - `CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules.pdf` (run `download_cofc_fixture.sh`)

## Reference Corpus
- The Homebrewery - NaturalCrit.pdf (with TOC)
- The Homebrewery - NaturalCrit - Without TOC.pdf
- CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules.pdf

## Steps

### 1. Run unit tests (no LLM required)
```bash
uv run --python "$(cat .python-version)" --extra dev -- pytest tests/unit/pdf_convert/agents/ -v
```
Validates workspace I/O, instruction generation, contract validation helpers, and error types.

### 2. Run contract tests (fixture-based, no live agent)
```bash
uv run --python "$(cat .python-version)" --extra dev -- pytest tests/contract/pdf_convert/agents/ -v
```
Validates each step's output schema with fixture outputs and structural checks.

### 3. Run integration tests (live agent execution)
```bash
GM_AGENT=codex uv run --python "$(cat .python-version)" --extra dev -- pytest tests/integration/pdf_convert/agents/ -v
```
Requires a supported agent CLI that can read/write workspace files and resume the pipeline. Validates against the reference corpus using the agent-orchestrated workflow. Checks SC-002 (90% first-pass), SC-003 (reproducible outcomes), and SC-005 (zero false TTRPG corrections).

### 4. Run corpus-specific integration tests (parallel CI)
```bash
# Run tests against specific PDFs (for parallel CI jobs)
just test-corpus-homebrewery  # Homebrewery with TOC
just test-corpus-b2           # Keep on the Borderlands (requires download)
just test-corpus-coc          # Call of Cthulhu (requires download)
```
Each command runs the full pipeline against one reference corpus PDF, enabling parallel test execution in CI. Run `download_b2_fixture.sh` and `download_cofc_fixture.sh` first if needed.

### 5. Run full pipeline end-to-end
```bash
uv run --python "$(cat .python-version)" --extra dev -- gmkit pdf-convert "tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.pdf" --output ./output
```
Verifies SC-004: agent steps replace stubs without changing pipeline behavior. The pipeline will pause at agent steps, write `step-input.json` and `step-instructions.md`, and resume after the agent writes `step-output.json` and runs `uv run --python "$(cat .python-version)" --extra dev -- gmkit pdf-convert --resume <workspace>`.

## Success Criteria
- All 13 agent steps pass schema validation and rubric checks for the reference corpus
- 90%+ first-pass contract compliance (SC-002)
- Consistent rubric scores across repeated runs (SC-003)
- Zero false corrections on TTRPG domain terms (SC-005)
- End-to-end pipeline completes with same expected inputs/outputs as stub pipeline (SC-004)
