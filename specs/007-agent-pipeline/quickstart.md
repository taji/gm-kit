# Quickstart: PDF→Markdown Agent-Driven Pipeline

## Purpose
Validate agent-step prompt outputs against JSON contracts and rubrics for the reference corpus.

## Prerequisites
- Python 3.8+ with project dependencies installed (`uv sync`)
- LLM provider SDK installed with valid API key (e.g., `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, or equivalent env var for configured provider)
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
pytest tests/unit/pdf_convert/agents/ -v
```
Validates prompt construction, contract schemas, rubric definitions, error types.

### 2. Run contract tests (mock LLM)
```bash
pytest tests/contract/pdf_convert/agents/ -v
```
Validates each step's output schema with fixture inputs and mock LLM responses.

### 3. Run integration tests (real LLM calls)
```bash
pytest tests/integration/pdf_convert/agents/ -v
```
Requires a configured LLM provider with valid API key. Validates against reference corpus with real LLM calls. Checks SC-002 (90% first-pass), SC-003 (reproducible scores), SC-005 (zero false TTRPG corrections).

### 4. Run full pipeline end-to-end
```bash
gmkit pdf-convert "The Homebrewery - NaturalCrit.pdf" --output-dir ./output
```
Verifies SC-004: agent steps replace stubs without changing pipeline behavior.

## Success Criteria
- All 13 agent steps pass schema validation and rubric checks for the reference corpus
- 90%+ first-pass contract compliance (SC-002)
- Consistent rubric scores across repeated runs (SC-003)
- Zero false corrections on TTRPG domain terms (SC-005)
- End-to-end pipeline completes with same expected inputs/outputs as stub pipeline (SC-004)
