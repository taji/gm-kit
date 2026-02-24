# Plan Quality Checklist: PDF→Markdown Agent-Driven Pipeline

**Purpose**: Validate implementation plan completeness and consistency against the updated spec (post-walkthrough, FR-012 through FR-016 added, 13 steps)
**Created**: 2026-02-20
**Resolved**: 2026-02-22
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md)
**Predecessor Checklist**: `requirements.md` (42/42 as of 2026-02-15 — note: CHK005 there references "14 agent steps" and is now stale; marked 2026-02-22)

---

## Plan-Spec Consistency

- [x] CHK001 — Is the plan Summary's step count still "14 Agent-category steps" instead of the current 13? [Consistency, Spec §FR-011, plan.md §Summary] — Fixed: "13 Agent-category steps"
- [x] CHK002 — Does the plan's Implementation Order section reference "9.1-9.5" instead of the current "9.2-9.5"? [Consistency, Spec §FR-011, plan.md §Implementation Order] — Fixed
- [x] CHK003 — Does the Project Structure prompts/ listing include `step_9_1.py` despite step 9.1 being dropped? [Consistency, Spec §FR-011, plan.md §Project Structure] — Fixed: entry removed
- [x] CHK004 — Are the Rubric Dimensions table entries for step 9.1 correctly annotated as dropped (not merely empty)? [Clarity, plan.md §Rubric Dimensions] — Already passing: ~~Dropped~~ annotation present
- [x] CHK005 — Is the plan's Scale/Scope consistent with 13 steps × 3 corpus PDFs = 39 executions? [Consistency, Spec §FR-011, plan.md §Technical Context] — Already passing
- [x] CHK006 — Does the requirements.md checklist's CHK005 item ("14 agent steps") need to be marked stale or superseded now that the scope is 13? [Consistency, checklists/requirements.md §CHK005] — Fixed: stale warning added to requirements.md CHK005

## New FR Coverage in Plan

- [x] CHK007 — Does the plan specify how FR-012's output format requirement (step 3.2 must produce indented text matching step 3.1, not pipe-delimited) is enforced — in the prompt template, contract schema, or both? [Coverage, Spec §FR-012, Gap] — Fixed: noted in Implementation Order step 3.2 and Rubric Dimensions table (new "Output format" dimension)
- [x] CHK008 — Does the plan address FR-013's two distinct OCR scenarios (pre-baked text layer vs. agent-driven OCR resume-from-phase) in the step 6.4 prompt design notes? [Coverage, Spec §FR-013, Gap] — Fixed: noted in Implementation Order step 6.4
- [x] CHK009 — Is FR-015 (preflight token threshold) represented anywhere in the plan — as a shared utility, a step-level guard, or an infrastructure concern for Quality Assessment steps? [Coverage, Spec §FR-015, Gap] — Fixed: `token_preflight.py` utility added to Foundation; env var `GM_TOKEN_THRESHOLD`; Dependency Notes section added
- [x] CHK010 — Does the plan specify how the `font-family-mapping.json` input (FR-016) is passed to the step 9.7 agent invocation — specifically which phase file provides it and from which workspace path? [Coverage, Spec §FR-016, Gap] — Fixed: step 9.7 notes in Implementation Order; schema documented in contracts/agent-steps.md
- [x] CHK011 — Are the step groupings in the plan's Implementation Order updated to reflect FR-011's exclusion of step 9.1? The "Quality Assessment" group currently lists 9.1-9.5; should be 9.2-9.5. [Consistency, Spec §FR-011, plan.md §Implementation Order] — Fixed (same fix as CHK002)

## Multimodal Design Specification

- [x] CHK012 — Are the two distinct LLM calls within step 7.7 (text-scan call + vision call) represented as separate prompt modules in the Project Structure, or is one `step_7_7.py` expected to handle both? [Clarity, Spec §FR-014, plan.md §Project Structure] — Fixed: `step_7_7.py` annotated as having two `build_prompt()` fns (`build_text_scan_prompt()` + `build_vision_prompt()`)
- [x] CHK013 — Is the intermediate page image artifact (rendered on-demand by step 7.7, reused by step 8.7) represented in the file structure — with a defined naming convention, workspace subdirectory, and cleanup policy? [Completeness, Spec §FR-014, Gap] — Fixed: `{workspace}/page_images/page_{n:03d}.png`; 150 DPI PNG; cleanup after pipeline
- [x] CHK014 — Is step 8.7's image reuse mechanism (load from step 7.7's saved images, crop with PIL/Pillow, do NOT re-render) explicitly stated in the plan's Step Execution Flow or step 8.7 notes? [Completeness, Spec §FR-014] — Fixed: documented in Implementation Order step 8.7 bullet
- [x] CHK015 — Is the on-demand rendering condition (only pages flagged by the text-scan pass) documented in the plan with enough precision to guide the step 7.7 implementation? [Clarity, Spec §FR-014, plan.md §Step Execution Flow] — Already passing: step execution flow documents 3a/3b/3c sequence

## Provider-Agnostic Architecture

- [x] CHK016 — Does the plan specify the interface requirements for `client.py` (method signatures, expected return shape, error contract) so that any provider can be wired in without changes to the calling code? [Clarity, plan.md §Project Structure, Gap] — Fixed: `complete(prompt, *, vision=False, images=None) -> str`; raises `ProviderError`, `VisionNotSupportedError`; in Foundation notes + Key Design Decisions
- [x] CHK017 — Does the plan define how vision capability is declared or validated in the provider abstraction — i.e., what happens at startup or step invocation if the configured provider does not support vision? [Completeness, Spec §FR-014, Gap] — Fixed: `VisionNotSupportedError` raised at invocation; validated per-call not at startup; Key Design Decisions row added
- [x] CHK018 — Are there requirements in the plan for a fallback or error path when vision capability is absent but steps 7.7 or 8.7 are invoked? [Edge Case, Spec §FR-014, Gap] — Fixed: not a silent fallback — step fails, criticality-based escalation applies (same as other critical failures)
- [x] CHK019 — Is the provider-agnostic constraint (Constitution VI v1.4) referenced in the plan's Constitution Check section? [Completeness, plan.md §Constitution Check] — Fixed: Constitution VI row updated to reference v1.4 and `client.py` abstraction

## Test Strategy Coverage

- [x] CHK020 — Does the test strategy specify how multimodal inputs (rendered page images) are represented in unit tests where the LLM client is mocked — mock image path? stub binary? [Completeness, plan.md §Test Strategy, Gap] — Fixed: `Path("fixtures/agents/images/stub_page.png")` passed to mock client; stub PNG in fixtures
- [x] CHK021 — Does the test strategy address how FR-015 (preflight token threshold) is unit-tested — including both the interactive-mode branch and the `--yes` auto-proceed branch? [Completeness, Spec §FR-015, Gap] — Fixed: mock `input()` for skip branch; short markdown strings to trigger threshold
- [x] CHK022 — Does the test strategy describe how provider-agnostic behavior is validated — e.g., are there contract tests for the `client.py` abstraction layer itself? [Completeness, plan.md §Test Strategy, Gap] — Fixed: `test_client_contract.py` added to contract tests
- [x] CHK023 — Are golden file plans for vision-based steps (7.7, 8.7) defined — specifically, how expected bounding-box coordinates are captured from real PDF corpus inputs and maintained across runs? [Completeness, plan.md §Test Strategy, Gap] — Fixed: golden files at 150 DPI; must be regenerated if DPI changes; stored in `tests/fixtures/pdf_convert/agents/golden/step_7_7/` and `step_8_7/`
- [x] CHK024 — Does the integration test strategy specify which provider is used for CI runs (where non-interactive `--yes` mode applies) and how API credentials are managed? [Completeness, plan.md §Test Strategy, Gap] — Fixed: `GM_LLM_PROVIDER` env var; API keys via provider-specific env vars; `pytest.mark.integration` skip if no key

## Dependency & Environment Specification

- [x] CHK025 — Is the `font-family-mapping.json` file format documented in `data-model.md` or `contracts/agent-steps.md` so that implementers of step 9.7 know what fields to expect? [Completeness, Spec §FR-016, Gap] — Fixed: full schema + key-field table + skepticism guidance added to contracts/agent-steps.md
- [x] CHK026 — Are the PyMuPDF API calls required for on-demand page rendering (specific method names, DPI, output format) referenced or documented in the plan or research.md? [Clarity, Spec §FR-014] — Fixed: `fitz.Document.load_page(n).get_pixmap(dpi=150)` + `pixmap.save()` in Dependency Notes
- [x] CHK027 — Is the token estimation heuristic (~4 chars/token) referenced in FR-015 documented as a configurable parameter in the plan, or is it hardcoded? [Clarity, Spec §FR-015] — Fixed: `GM_TOKEN_THRESHOLD` env var (default 100000); noted as rough estimate not used for billing
- [x] CHK028 — Are Pillow's image operations (load, crop, save) sufficient for the bounding-box cropping in step 8.7, and is any precision concern (sub-pixel rendering, DPI mismatch) addressed? [Completeness, Spec §FR-014, Assumption] — Fixed: crop formula with `scale = dpi / 72` documented in Dependency Notes

## Acceptance Criteria Alignment

- [x] CHK029 — Does the plan's rubric for step 3.2 include a dimension that validates output format matches the indented-text convention (FR-012) rather than just structural completeness? [Completeness, Spec §FR-012, plan.md §Rubric Dimensions] — Fixed: "Output format (indented text, not pipe-delimited per FR-012)" added to step 3.2 dimensions
- [x] CHK030 — Does the plan's rubric for step 9.7 include a dimension that accounts for the skepticism requirement on font-inferred headings (FR-016)? [Completeness, Spec §FR-016, plan.md §Rubric Dimensions] — Fixed: "Font-source awareness (skepticism for font-inferred headings per FR-016)" added to step 9.7 dimensions
- [x] CHK031 — Does the plan's rubric for step 9.3 (text flow) address the FR-015 scenario where the step is skipped due to token threshold? Is a skipped step's quality rating defined? [Completeness, Spec §FR-015, Gap] — Fixed: Quality Assessment group in Implementation Order documents `StepStatus.SKIPPED` (not scored; not a rubric failure)

## Review Sign-Off

- **Validation**: 31/31 items passing (2026-02-22)
- **Reviewer**: claude-sonnet-4-6
- **Status**: Ready for `/speckit.tasks`

## Notes

- Check items off as completed: `[x]`
- Add inline findings when an item reveals a gap
- Items marked `[Gap]` indicate requirements absent from the plan
- Items marked `[Consistency]` indicate mismatches between spec and plan
- Items marked `[Assumption]` indicate unvalidated assumptions in the plan
- This checklist was generated after the step-by-step agent walkthrough session (2026-02-20)
  that produced FR-012 through FR-016 and dropped step 9.1 from scope
- All items resolved in session 2026-02-22
