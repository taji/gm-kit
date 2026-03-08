# Quickstart: PDF→Markdown Agent-Driven Pipeline

## Purpose
Validate agent-step prompt outputs against JSON contracts and rubrics for the reference corpus.

## Prerequisites
- Python 3.8+ with project dependencies installed (`uv sync --extra dev`)
- A supported agent CLI installed and authenticated/configured for live end-to-end runs (for example: Claude Code, Codex CLI, or OpenCode)
- Optional: set `GM_AGENT` to choose the agent for live end-to-end runs (default is `codex`)
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

### 3. Run integration tests (deterministic, no live LLM calls)
```bash
GM_AGENT=codex uv run --python "$(cat .python-version)" --extra dev -- pytest tests/integration/pdf_convert/agents/ -v
```
Runs integration coverage with a monkeypatched runtime to validate pause/resume and cross-phase artifact handoff deterministically. This does not execute a live external LLM CLI.

### 4. Run full integration suite from task runner
```bash
just test-integration
```
For corpus fixtures used in broader tests, download scripts are:
```bash
bash tests/fixtures/pdf_convert/download_b2_fixture.sh
bash tests/fixtures/pdf_convert/download_cofc_fixture.sh
```

### 5. Run full pipeline end-to-end
```bash
GM_AGENT=codex uv run --python "$(cat .python-version)" --extra dev -- gmkit pdf-convert "tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.pdf" --output ./tmp/quickstart-e2e --yes
```
Verifies SC-004: agent steps replace stubs without changing pipeline behavior. Use an output folder inside the repository to avoid trust-directory errors with some CLIs.

Current known behavior for Codex live runs: if agent steps fail with `Agent exited with code 1`, inspect `<output>/conversion.log` and `<output>/agent_steps/step_*/` artifacts to diagnose agent runtime/auth issues.

## Success Criteria
- All 13 agent steps pass schema validation and rubric checks for the reference corpus
- 90%+ first-pass contract compliance (SC-002)
- Consistent rubric scores across repeated runs (SC-003)
- Zero false corrections on TTRPG domain terms (SC-005)
- End-to-end pipeline completes with same expected inputs/outputs as stub pipeline (SC-004)
