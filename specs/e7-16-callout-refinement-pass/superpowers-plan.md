# E7-16 Optional Callout Refinement Pass Implementation Plan

> **For agentic workers:** Use the smallest possible implementation slices, keep the worktree as the source of truth, and do not run refinement against the root repo by accident.

**Goal:** Add an optional image-capable refinement pass for ambiguous callout proposals, with a mock-agent path for tests and a clean bypass when refinement is skipped or unsupported.

**Architecture:** Keep the current code-first callout detection intact. Insert a narrow refinement step that consumes only the proposals flagged by multi-block traversal hints, asks an image-capable agent to adjust geometry, and then renders the review PDF from the refined geometry. Preserve raw evidence and keep the user review contract unchanged.

The refinement images must be rendered from the original source PDF, not from `annotated-prep.pdf`. Each crop should include padding so the agent can see the callout background, border, and nearby context before it decides whether the box needs to expand or contract.

**Tech Stack:** Python 3.13.7, existing prep pipeline modules under `src/gm_kit/pdf_convert/prep/`, PyMuPDF for page imagery, pytest for unit/integration coverage, `just` for repo checks.

---

## Planned File Areas

**Likely create or modify**
- `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- `src/gm_kit/pdf_convert/prep/handlers.py`
- `src/gm_kit/pdf_convert/prep/orchestrator.py`
- `src/gm_kit/pdf_convert/prep/callout_detection.py`
- `src/gm_kit/pdf_convert/prep/refinement.py` or equivalent helper module
- `src/gm_kit/pdf_convert/prep/refinement_images.py` or equivalent helper module
- `tests/unit/pdf_convert/prep/test_callout_detection.py`
- `tests/unit/pdf_convert/prep/test_handlers.py`
- `tests/unit/pdf_convert/prep/test_orchestrator.py`
- `tests/integration/pdf_convert/test_callout_refinement_pass.py`
- `specs/e7-16-callout-refinement-pass/feature_journal.md`

The exact module split can stay small if the helper logic is straightforward, but the refinement code should not be scattered across unrelated files.

---

## Task 1: Define the refinement contract and helper path

**Files:**
- Create or modify the prep refinement helper module
- Modify `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- Modify `src/gm_kit/pdf_convert/prep/callout_detection.py`

- [ ] **Step 1: Add the failing contract tests**

Write tests that prove:
- a proposal with a multi-block traversal hint is eligible for refinement
- a proposal without a hint is not sent to the refinement pass
- a refinement response can replace the original bbox
- a missing refinement response leaves the original bbox unchanged

Suggested test names:

```python
def test_refine_callout_proposals__should_apply_agent_geometry__when_a_hint_is_flagged() -> None:
    ...

def test_refine_callout_proposals__should_skip_unflagged_proposals__when_no_hint_is_present() -> None:
    ...
```

- [ ] **Step 2: Implement the minimal helper**

Add a small refinement helper that:
- accepts raw proposals and refinement hints
- extracts the eligible proposal subset
- prepares the agent input bundle
- renders crops from the original PDF with enough padding for context
- applies only valid geometry updates
- preserves raw proposal data when refinement is absent or invalid

- [ ] **Step 3: Run the focused unit tests**

Run:
`uv run --python "3.13.7" --extra dev -- pytest tests/unit/pdf_convert/prep/test_callout_detection.py -q`

Expected: the new refinement-related tests fail first, then pass once the helper exists.

---

## Task 2: Wire the refinement step into prep orchestration

**Files:**
- Modify `src/gm_kit/pdf_convert/prep/handlers.py`
- Modify `src/gm_kit/pdf_convert/prep/orchestrator.py`
- Modify `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- Modify `tests/unit/pdf_convert/prep/test_handlers.py`
- Modify `tests/unit/pdf_convert/prep/test_orchestrator.py`

- [ ] **Step 1: Add tests for the orchestration branches**

Cover these cases:
- refinement runs when enabled and supported
- refinement is skipped when the CLI flag is set
- refinement is skipped when the active agent lacks image capability
- the pipeline logs a clear reason for bypass

- [ ] **Step 2: Implement the orchestration step**

Update the prep handler/orchestrator so it:
- loads the raw proposals and refinement hints
- checks the explicit skip flag first
- checks image capability second
- invokes refinement only for eligible proposals
- writes the refined proposal artifact used to render the review PDF

Keep the raw evidence artifact separate so debugging remains possible after a failed or partial refinement.

- [ ] **Step 3: Run the orchestration tests**

Run:
`uv run --python "3.13.7" --extra dev -- pytest tests/unit/pdf_convert/prep/test_handlers.py tests/unit/pdf_convert/prep/test_orchestrator.py -q`

Expected: the new skip/capability-gate tests pass and the existing prep flow remains intact.

---

## Task 3: Add the mock-agent test path

**Files:**
- Create a test double or fixture module under `tests/`
- Modify integration test support for the analyze-prep path
- Modify any live-handoff harness support if needed

- [ ] **Step 1: Define the mock-agent behavior**

The mock agent should:
- accept the same refinement prompt shape as the real agent
- return deterministic refined geometry for known fixtures
- support a no-op or skip response for negative-path coverage
- operate on crops rendered from the source PDF so the test path matches the production input contract

- [ ] **Step 2: Add an end-to-end integration test**

Verify the analyze-prep workflow can run with the mock agent and produce:
- a refined annotation artifact
- a rendered annotated PDF
- the same reviewed contract path as the real workflow

Suggested test name:

```python
def test_analyze_and_prep_pdf__should_refine_flagged_callouts__when_mock_agent_is_enabled() -> None:
    ...
```

- [ ] **Step 3: Run the integration slice**

Run:
`uv run --python "3.13.7" --extra dev -- pytest tests/integration/pdf_convert/test_callout_refinement_pass.py -q`

Expected: PASS without calling a real agent.

---

## Task 4: Update docs and journal

**Files:**
- Modify `specs/e7-16-callout-refinement-pass/feature_journal.md`
- Modify any prep docs or runbook references that mention the refinement path

- [ ] **Step 1: Record the implementation decisions**

Append a factual journal entry covering:
- the refinement contract
- the skip/capability gate behavior
- the mock-agent path
- any chosen artifact filenames

- [ ] **Step 2: Reconcile any user-facing docs if needed**

If the refinement pass changes the user-visible analyze flow, update the relevant README or usage notes so the optional refinement behavior is discoverable.

- [ ] **Step 3: Commit**

```bash
git add \
  src/gm_kit/pdf_convert/prep \
  tests/unit/pdf_convert/prep \
  tests/integration/pdf_convert/test_callout_refinement_pass.py \
  specs/e7-16-callout-refinement-pass/feature_journal.md
git commit -m "feat: add optional callout refinement pass"
```
