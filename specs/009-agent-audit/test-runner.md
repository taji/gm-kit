# E2-09: Agent Audit — Manual Test Runner

**Branch**: `009-agent-audit`
**Created**: 2026-02-24
**Purpose**: Step-by-step test script for the 4-test audit protocol.
Record your results in `findings.md` as you go.

---

## Pre-Flight Checklist

Run these before starting any tests:

```bash
# Verify installed versions
claude --version
codex --version
opencode --version

# All tests run from gm-kit repo root — agents are sandboxed to project dir
cd ~/Dev/gm-kit
pwd  # should show .../gm-kit
```

> **Note**: OpenCode preliminary finding — `opencode run` does not exit cleanly
> (hangs after sending prompt). Test 1 for OpenCode may be a ❌. Confirm below.

---

## AGENT 1: Claude Code

### Test 1 — CLI Invocable?

Run this in a **new terminal** (not inside an existing Claude Code session):

```bash
claude --print "Echo: hello world"
```

**Pass criteria**: Prints output, exits cleanly. No interactive prompts.
**Record**: version shown, exit code (`echo $?`), any errors.

---

### Test 2 — Runs to Completion?

Run from the **gm-kit repo root** in a **new terminal**:

```bash
cd ~/Dev/gm-kit
claude --print --dangerously-skip-permissions \
  "Create a file called specs/009-agent-audit/test-workspace/test-output.txt. Write the text 'Step 1 complete' on line 1. Then write 'Step 2 complete' on line 2. Then write 'Step 3 complete' on line 3. Do not ask for confirmation. Complete all steps autonomously."
cat specs/009-agent-audit/test-workspace/test-output.txt
```

**Pass criteria**: `test-output.txt` exists with all 3 lines. No mid-task prompts.
**Note**: `--dangerously-skip-permissions` required for autonomous file writes.
**Record**: file contents, any confirmation dialogs, exit code.

---

### Test 3 — Slash Commands?

Skip for now — requires `gmkit init` to be run first.
Mark as **Deferred** in findings.md.

---

### Test 4 — Generates Output Files?

Run from the **gm-kit repo root** in a **new terminal**:

```bash
cd ~/Dev/gm-kit
claude --print --dangerously-skip-permissions \
  "Read the file specs/009-agent-audit/test-inputs/step-input.json. Process it according to the instructions inside. Write your output to specs/009-agent-audit/test-outputs/step-output.json. Do not print output to the terminal — write only to the file."
cat specs/009-agent-audit/test-outputs/step-output.json
```

**Pass criteria**: `step-output.json` exists with a valid JSON array of TOC entries (level, title, page). Nothing printed to terminal (or minimal status only).

**Expected output shape**:
```json
[
  {"level": 1, "title": "Introduction", "page": 3},
  {"level": 1, "title": "Chapter One", "page": 5},
  {"level": 2, "title": "Section 1.1", "page": 7},
  {"level": 2, "title": "Section 1.2", "page": 9},
  {"level": 1, "title": "Chapter Two", "page": 12}
]
```

**Record**: file contents, whether output also appeared in terminal, exit code.

---

## AGENT 2: Codex CLI

> **Pre-req**: Run `codex login` and complete auth before these tests.

### Test 1 — CLI Invocable?

```bash
codex exec --full-auto "Echo: hello world"
echo "EXIT: $?"
```

**Pass criteria**: Prints "hello world", exits cleanly (exit 0). No interactive prompts.
**Note**: Codex prints full reasoning/tool trace to stdout. This is expected — verbose by
design. For production use, redirect to `/dev/null` and rely on file output only.
**Record**: exit code, model shown in header, any auth errors.

---

### Test 2 — Runs to Completion?

```bash
cd ~/Dev/gm-kit
codex exec --full-auto \
  -s workspace-write \
  "Create a file called specs/009-agent-audit/test-workspace/test-output.txt. Write the text 'Step 1 complete' on line 1. Then write 'Step 2 complete' on line 2. Then write 'Step 3 complete' on line 3. Do not ask for confirmation. Complete all steps autonomously." > /dev/null 2>&1
echo "EXIT: $?"
cat specs/009-agent-audit/test-workspace/test-output.txt
```

**Pass criteria**: `test-output.txt` exists with all 3 lines. Exit 0.
**Note**: Console output suppressed — viability is determined by file content + exit code.
**Record**: file contents, exit code.

---

### Test 3 — Slash Commands?

Skip for now. Mark as **Deferred** in findings.md.

---

### Test 4 — Generates Output Files?

```bash
cd ~/Dev/gm-kit
codex exec --full-auto \
  -s workspace-write \
  "Read the file specs/009-agent-audit/test-inputs/step-input.json. Process it according to the instructions inside. Write your output to specs/009-agent-audit/test-outputs/step-output.json. Do not print output to the terminal — write only to the file." > /dev/null 2>&1
echo "EXIT: $?"
cat specs/009-agent-audit/test-outputs/step-output.json
```

**Pass criteria**: `step-output.json` exists with valid JSON array. Exit 0.
**Note**: Console output suppressed — viability determined by file content + exit code.
**Record**: file contents, exit code.

---

## AGENT 3: OpenCode

> **Preliminary finding**: `opencode run` did not exit on its own during pre-flight
> testing (killed by 30s timeout). Test 1 likely ❌. Run to confirm.

### Test 1 — CLI Invocable?

```bash
timeout 30 opencode run "Echo: hello world"
echo "EXIT: $?"
```

**Pass criteria**: Prints output, exits before 30s timeout (exit 0, not 124).
**Fail signal**: exit code 124 = killed by timeout (does not exit autonomously).
**Record**: output, exit code, time taken.

---

### Test 2 — Runs to Completion?

Only run if Test 1 passes. If Test 1 was exit 124, record Test 2 as ❌ (blocked).

```bash
cd ~/Dev/gm-kit
timeout 60 opencode run \
  "Create a file called specs/009-agent-audit/test-workspace/test-output.txt. Write 'Step 1 complete' on line 1, 'Step 2 complete' on line 2, 'Step 3 complete' on line 3. Do not ask for confirmation. Complete all steps autonomously."
echo "EXIT: $?"
cat specs/009-agent-audit/test-workspace/test-output.txt 2>/dev/null || echo "(file not created)"
```

**Pass criteria**: File created, exit 0 (not 124).
**Record**: file contents, exit code.

---

### Test 3 — Slash Commands?

Skip for now. Mark as **Deferred**.

---

### Test 4 — Generates Output Files?

Only run if Test 1 passes.

```bash
cd ~/Dev/gm-kit
timeout 120 opencode run \
  "Read the file specs/009-agent-audit/test-inputs/step-input.json. Process it according to the instructions inside. Write your output to specs/009-agent-audit/test-outputs/step-output.json. Do not print output to the terminal — write only to the file."
echo "EXIT: $?"
cat specs/009-agent-audit/test-outputs/step-output.json 2>/dev/null || echo "(file not created)"
```

**Pass criteria**: File created with valid JSON array. Exit 0 (not 124).
**Record**: file contents, exit code.

---

## Results Template

Copy into `findings.md` as you complete each agent:

```
**Date tested**: 2026-02-24
**Version**: [from --version]
**Model**: [model used]

| Test | Result | Notes |
|------|--------|-------|
| 1: CLI Invocable    | ✅/❌/⚠️ | [exit code, behavior] |
| 2: Runs to Completion | ✅/❌/⚠️ | [file contents or failure mode] |
| 3: Slash Commands   | —        | Deferred |
| 4: Generates Output Files | ✅/❌/⚠️ | [file contents or failure mode] |

**Overall**: Pass / Fail / Partial
**Notes**: [stall points, config required, error modes]
```

---

## Decision Rule

After all three agents tested:

| Outcome | Decision |
|---------|----------|
| ≥1 agent: Tests 1+2+4 all ✅ | Agent-orchestrated confirmed → revise E4-07b plan |
| No agent: Tests 1+2+4 all ✅ | SDK-based confirmed → proceed with current E4-07b plan |
| Partial passes only | Evaluate hybrid approach |

Report results back and I'll update `findings.md` and record the architectural decision.
