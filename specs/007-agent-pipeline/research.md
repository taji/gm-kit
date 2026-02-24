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

**Decision:** LLM-based rubric evaluation using the configured provider at temperature=0 with structured JSON output. Per-step rubric with minimum 3/5 per dimension and zero critical failures.

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

## Decision 4: LLM provider and configuration

**Decision:** Provider-agnostic abstraction layer (`client.py`) that supports multiple LLM backends. Constitution VI mandates support for prioritized AI agents (Claude, Gemini, Qwen, Codex, etc.). Temperature=0 for all agent steps and rubric evaluations. Structured JSON output enforced at the abstraction layer.

**Rationale:** gmkit is used by multiple AI agents, not just Claude. The client abstraction provides a common interface (`call(prompt, schema) -> dict`) that each provider implements. Provider selection is configured at runtime (env var or config). All providers must support temperature=0 and structured JSON output for SC-003 reproducibility. Vision-capable providers are required for table detection steps (7.7, 8.7).

**Alternatives considered:**
- Single-provider (Claude only) — violates Constitution VI multi-agent mandate
- Local models only — insufficient quality for semantic tasks like table detection
- No abstraction (direct SDK calls per provider) — duplicates retry/validation logic across providers

---

## Decision 5: Prompt storage format

**Decision:** Python modules (one per step) rather than text template files.

**Rationale:** Python modules allow parameterized prompt construction, type checking via mypy, direct imports in tests, and conditional logic for edge cases. Each module exposes a `build_prompt(inputs: dict) -> str` function.

**Alternatives considered:**
- Jinja2 templates (additional dependency, no type checking)
- Plain text files with string formatting (no parameterization, error-prone)
- YAML configuration (verbose, no logic support)

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

## Decision 8: Large document handling for quality assessment steps

**Decision:** Agent steps send the full markdown to the LLM where context window permits. A preflight token estimate gates large documents: if estimated tokens exceed the threshold (default 100,000), the user is warned and prompted to skip in interactive mode, or warned and auto-proceeded in non-interactive (`--yes`) mode. Chunking with overlapping windows is deferred to a future feature.

**Rationale:** Step 9.3 (text flow assessment) is particularly sensitive to chunking — flow issues span paragraph and section boundaries, so splitting the document would cause cross-boundary issues to be missed. Sending the full markdown is the correct approach. The 100,000-token threshold provides a safety valve for very large PDFs without complicating the E4-07b implementation. The `--yes` flag pattern is already established in the pipeline for non-interactive mode.

**Known constraint:** PDFs that produce markdown exceeding the provider's context window will produce incomplete or failed assessments for step 9.3. This is acceptable for E4-07b's reference corpus (small TTRPG PDFs). A future feature should implement overlapping-window chunking for large documents.

**Alternatives considered:**
- Chunking with overlapping windows now — adds significant complexity, violates YAGNI for the reference corpus
- Sampling (beginning/middle/end) — misses issues in unsampled sections; not appropriate for a quality gate

## Decision 7: Agent step library structure

**Decision:** Self-contained subpackage at `src/gm_kit/pdf_convert/agents/` with public API `run_agent_step(step_id, inputs) -> StepOutput`.

**Rationale:** Library-first (Constitution I): independently testable, clear boundary. Phase files call `run_agent_step()` where stubs currently live. The agents module owns prompts, contracts, rubrics, and the LLM client.

**Alternatives considered:**
- Inline agent logic in each phase file (violates library-first, hard to test)
- Separate top-level package (unnecessary separation from pdf_convert)
- Plugin/registry pattern (over-engineering for 14 fixed steps)
