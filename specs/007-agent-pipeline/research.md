# Research Notes: PDF→Markdown Agent-Driven Pipeline

## Decision 1: JSON schema format for step contracts

**Decision:** Use per-step JSON Schema definitions (Draft-07) for agent outputs, with a shared metadata envelope (step_id, input_artifact, warnings, errors, notes).

**Rationale:** Provides deterministic validation for contract testing and consistent integration with the code pipeline. Draft-07 is well-supported by the `jsonschema` Python library.

**Alternatives considered:**
- Free-form text outputs only (hard to validate)
- Markdown-only contracts (difficult to validate programmatically)
- Pydantic-only schemas (less portable, harder to share with non-Python tools)

---

## Decision 2: Rubric evaluation approach

**Decision:** LLM-based rubric evaluation performed by the configured agent (via the same file-handoff workflow) at temperature=0 with structured JSON output. Per-step rubric with minimum 3/5 per dimension and zero critical failures.

**Rationale:** Quality dimensions (structural clarity, text flow, readability) are semantic and cannot be evaluated by rule-based code. Temperature=0 and structured output schemas provide consistent/reproducible results (SC-003). "Deterministic" means consistent given explicit criteria, not bit-identical.

**Alternatives considered:**
- Global aggregate score across steps (masks per-step quality issues)
- Critical-only gating (risk of low-quality outputs passing)
- Rule-based/programmatic evaluation (cannot judge semantic quality)
- Hybrid approach (adds complexity without clear benefit — all dimensions are semantic)

---

## Decision 3: Contract testing strategy

**Decision:** Combine JSON schema validation with golden file comparison and structural checks.

**Rationale:** JSON schema ensures shape correctness; golden files and structural checks catch semantic regressions. Golden files are generated from first successful corpus run, then manually reviewed and committed.

**Alternatives considered:**
- Schema validation only (insufficient for content regressions)
- Golden file only (brittle to minor formatting changes)

---

## Decision 4: Agent execution model and provider handling

**Decision:** Use an agent-orchestrated execution model. Python writes workspace input/instruction files and validates outputs, while the running agent performs the LLM work and writes `step-output.json`. No Python SDK calls for LLM inference are used in E4-07b.

**Rationale:** E2-09 confirmed that supported agent CLIs can execute multi-step workflows autonomously using workspace files. This avoids provider SDK/auth complexity in Python code and matches the E4-07b design goal of replacing agent stubs with file-based handoff steps. SC-003 reproducibility is achieved through explicit rubrics, temperature=0 instructions in prompts, and structured output contracts.

**Alternatives considered:**
- Python provider abstraction layer (`client.py`) with direct SDK calls — rejected because E4-07b is now agent-orchestrated
- Single-provider implementation — rejected (multi-agent support remains a project requirement)
- Local models only — rejected due to quality limits for semantic and multimodal tasks

---

## Decision 5: Instruction/prompt storage format

**Decision:** Store step instructions primarily as markdown template files (`instructions/step_X_Y.md`) with variable substitution, with a Python module only for step 7.7 due to its two-pass prompt construction (text-scan + vision confirmation).

**Rationale:** Markdown templates are easy to review, diff, and hand off to the running agent. Most steps only need variable substitution, not executable logic. Step 7.7 is the exception because it builds different prompts for separate passes.

**Alternatives considered:**
- Python module per step — rejected as unnecessary complexity for mostly static instructions
- Jinja2 templates — rejected (extra dependency without meaningful benefit)
- YAML configuration — rejected (less readable for long agent instructions)

---

## Decision 6: Table detection approach (steps 7.7, 8.7)

**Decision:** Two-pass multimodal approach. Step 7.7 uses the extracted text to identify which pages likely contain tables, then renders only those pages as images on-demand via PyMuPDF and sends them to the vision LLM for confirmation and bounding box extraction. Step 8.7 crops the confirmed table regions and sends cropped image + garbled flat text to the vision LLM to reconstruct properly structured markdown. Page images are not pre-rendered — rendering is on-demand only for flagged pages.

**Rationale:** PyMuPDF Phase 2 removes embedded images and produces a text-only PDF — it does not pre-render pages as images. Page rendering must happen on-demand. The two-pass approach (text scan first, image render only for flagged pages) avoids rendering and uploading images for every page of a potentially long PDF. The extracted text alone (even garbled for tables) has enough signal for an LLM to identify likely table pages before committing to image rendering. Vision is then used for the structural work that text cannot provide: row/column boundaries, merged cells, header identification.

**Alternatives considered:**
- Code heuristics pre-filter + AI confirmation: Code scans text for spacing/alignment signals before AI. Rejected because the flat text extracted by PyMuPDF loses most alignment signals that would make code heuristics reliable.
- AI text scan + AI image in one pass: Merge steps 7.7 and 8.7 into a single agent call. Rejected because detection (which pages have tables) and conversion (what the markdown should be) are distinct concerns with different inputs and contracts.
- Render all pages upfront: Simple but expensive for long PDFs; unnecessary for pages with no tables.
- Camelot/Tabula: Require ruled lines; many TTRPG tables are unruled or use decorative borders.
- Custom CV model: Training data shortage, maintenance burden.

---

## Decision 7: Large document handling for quality assessment steps

**Decision:** Agent steps send the full markdown to the LLM where context window permits. A preflight token estimate gates large documents: if estimated tokens exceed the threshold (default 100,000), the user is warned and prompted to skip in interactive mode, or warned and auto-proceeded in non-interactive (`--yes`) mode. Chunking with overlapping windows is deferred to a future feature.

**Rationale:** Step 9.3 (text flow assessment) is particularly sensitive to chunking — flow issues span paragraph and section boundaries, so splitting the document would cause cross-boundary issues to be missed. Sending the full markdown is the correct approach. The 100,000-token threshold provides a safety valve for very large PDFs without complicating the E4-07b implementation. The `--yes` flag pattern is already established in the pipeline for non-interactive mode.

**Known constraint:** PDFs that produce markdown exceeding the selected agent/model context window will produce incomplete or failed assessments for step 9.3. This is acceptable for E4-07b's reference corpus (small TTRPG PDFs). A future feature should implement overlapping-window chunking for large documents.

**Alternatives considered:**
- Chunking with overlapping windows now — adds significant complexity, violates YAGNI for the reference corpus
- Sampling (beginning/middle/end) — misses issues in unsampled sections; not appropriate for a quality gate

## Decision 8: Agent step library structure

**Decision:** Self-contained subpackage at `src/gm_kit/pdf_convert/agents/` with file-handoff APIs for writing agent inputs/instructions and reading/validating agent outputs (e.g., `write_agent_inputs(...)`, `read_agent_output(...)`). A higher-level wrapper may orchestrate these calls, but file handoff is the core interface.

**Rationale:** Library-first (Constitution I): independently testable, clear boundary. Phase files replace stubs by calling into the agents library, which owns instruction templates, contracts, rubric definitions, and workspace I/O/validation behavior. The running agent, not Python, performs the LLM inference.

**Alternatives considered:**
- Inline agent logic in each phase file (violates library-first, hard to test)
- Separate top-level package (unnecessary separation from pdf_convert)
- Plugin/registry pattern (over-engineering for 13 fixed steps)
