# E7-08 Live Handoff Harness Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the live handoff harness into prep-only, convert-only, and prep-and-convert workflows while preserving unattended regression support and explicit artifact boundary checks.

**Architecture:** Keep the existing harness scripts, add a workflow mode layer, and validate the prep handoff before conversion starts. Prep and convert remain separate commands; the harness just sequences them and preserves the existing pause/resume execution loop for conversion.

**Tech Stack:** Bash wrapper, Python 3.13, existing `gmkit analyze-and-prep-pdf` and `gmkit pdf-convert` commands, pytest.

---

### Task 1: Add workflow mode tests

**Files:**
- Modify: `tests/unit/test_live_handoff_harness.py`
- Modify: `devtools/scripts/live_handoff_harness.py`

- [ ] **Step 1: Write the failing tests**

Add tests that prove the harness parses and validates the new workflow mode, and that the command builder targets the correct CLI for each mode.

Add one test for each mode:
- `prep-only` builds an `analyze-and-prep-pdf` command
- `convert-only` builds a `pdf-convert` command
- `prep-and-convert` builds both commands in sequence

- [ ] **Step 2: Run the targeted tests**

Run: `pytest tests/unit/test_live_handoff_harness.py -q`
Expected: failure until workflow mode handling exists.

- [ ] **Step 3: Implement the workflow mode layer**

Introduce a parser for a workflow/mode flag and helper functions that build the prep and convert command sequences independently.

- [ ] **Step 4: Re-run the targeted tests**

Run: `pytest tests/unit/test_live_handoff_harness.py -q`
Expected: PASS.

### Task 2: Split prep and convert orchestration

**Files:**
- Modify: `devtools/scripts/live_handoff_harness.py`
- Modify: `devtools/scripts/live_handoff_harness.sh`
- Test: `tests/unit/test_live_handoff_harness.py`

- [ ] **Step 1: Write the failing tests**

Add tests that prove:
- prep-only runs prep and stops
- convert-only refuses to start without a completed prep workspace
- prep-and-convert runs prep, verifies artifacts, then starts conversion

- [ ] **Step 2: Run the targeted tests**

Run: `pytest tests/unit/test_live_handoff_harness.py -q`
Expected: failure until orchestration is split.

- [ ] **Step 3: Implement the orchestration split**

Sequence the harness like this:
1. run prep if requested
2. validate prep completion artifacts
3. run conversion if requested
4. preserve the existing agent pause/resume loop for conversion

Keep the output trace format stable so existing log consumers remain usable.

- [ ] **Step 4: Re-run the targeted tests**

Run: `pytest tests/unit/test_live_handoff_harness.py -q`
Expected: PASS.

### Task 3: Update harness documentation and handoff notes

**Files:**
- Modify: `BACKLOG.md`
- Modify: `specs/e7-08-live-handoff-harness-split-prep-run-convert-run/feature_journal.md`

- [ ] **Step 1: Update the backlog wording**

Clarify that the harness now supports prep-only, convert-only, and prep-and-convert workflows with an explicit artifact handoff boundary.

- [ ] **Step 2: Update the feature journal**

Append a session entry summarizing the workflow split, the artifact boundary check, and any implementation-specific decisions.

- [ ] **Step 3: Re-run the narrowest relevant checks**

Run: `pytest tests/unit/test_live_handoff_harness.py -q`
Expected: PASS.

