# E2-09: Agent Autonomous Execution Audit

**Branch**: `009-agent-audit`
**Started**: 2026-02-24
**Purpose**: Determine which agent(s) can autonomously execute multi-step tasks
with file output. Results gate E4-07b architectural decision (SDK-based vs.
agent-orchestrated pipeline execution).

**Prior finding (E2-02, ~2025)**: CLI batch mode non-viable for codex-cli,
gemini, opencode — no clean slash-command invocation. Claude Code not tested.
All three candidates have had major updates since.

---

## Phase 1: Priority Candidates

Test Claude Code, Codex CLI, and OpenCode across 7 dimensions.

### Audit Matrix

| Agent | Model(s) | Vision | CLI Invocable? | Runs to Completion? | Slash Commands? | Generates Output Files? | Notes |
|-------|----------|--------|----------------|---------------------|-----------------|------------------------|-------|
| Claude Code | Claude 4.x Opus/Sonnet | confirmed | ✅ | ✅ | — | ✅ | Requires `--dangerously-skip-permissions`; cannot self-nest |
| Codex CLI | gpt-5.3-codex | unconfirmed | ✅ | ✅ | — | ✅ | `exec --full-auto -s workspace-write`; verbose by default, redirectable |
| OpenCode | Kimi K2.5 | confirmed | ✅ | ✅ | — | ✅ | `opencode run`; exits cleanly after one-time DB migration |

**Result values**: ✅ Pass / ❌ Fail / ⚠️ Partial / — Not tested

---

## Test Protocol

For each agent, run the following tests in order. Record pass/fail and any
notable observations (stall points, error modes, config requirements).

### Test 1: CLI Invocable?
Can the agent be launched from the command line in a non-interactive/batch mode?

```bash
# Example invocations to try:
# Claude Code
claude --print "Echo: hello world"

# Codex CLI
codex "Echo: hello world"

# OpenCode
opencode run "Echo: hello world"
```

Expected: Agent starts, runs without prompting for human input, exits cleanly.

---

### Test 2: Runs to Completion?
Given a multi-step task description, does the agent execute all steps without
stalling or requesting human confirmation mid-task?

**Task prompt:**
```
Create a file called test-output.txt in the current directory.
Write the text "Step 1 complete" on line 1.
Then write "Step 2 complete" on line 2.
Then write "Step 3 complete" on line 3.
Do not ask for confirmation. Complete all steps autonomously.
```

Expected: `test-output.txt` created with all 3 lines. No prompts mid-task.

---

### Test 3: Slash Commands to Completion?
Can the agent execute a gmkit slash command unaided from invocation to file output?

**Prerequisites**: `gmkit init` must be run first to install slash command scripts.

**Task prompt:**
```
Run the /gmkit.hello-gmkit slash command.
```

Expected: `greetings/greetingXX.md` file written to project folder.
This was non-viable for codex-cli/gemini/opencode in the E2-02 test.

---

### Test 4: Generates Output Files?
Does the agent reliably write structured output to specific workspace files?
(Simulates an agent pipeline step.)

**Task prompt:**
```
Read the file specs/009-agent-audit/test-inputs/step-input.json.
Process it according to the instructions inside.
Write your output to specs/009-agent-audit/test-outputs/step-output.json.
Do not print output to the terminal — write only to the file.
```

Test input file: `specs/009-agent-audit/test-inputs/step-input.json`
```json
{
  "step_id": "3.2",
  "instruction": "Parse the following visual TOC text and return a JSON array of entries, each with level (int), title (str), and page (int).",
  "input_text": "Contents\n  Introduction (page 3)\n  Chapter One (page 5)\n    Section 1.1 (page 7)\n    Section 1.2 (page 9)\n  Chapter Two (page 12)"
}
```

Expected output: `step-output.json` with valid JSON array. No terminal output.

---

## Findings

### Claude Code

**Date tested**: 2026-02-24
**Version**: 2.1.52
**Test environment**: Ubuntu (pop-os), gm-kit repo root, outside active Claude Code session

| Test | Result | Notes |
|------|--------|-------|
| 1: CLI Invocable | ✅ | `claude --print "Echo: hello world"` → "hello world", exit 0 |
| 2: Runs to Completion | ✅ | Requires `--dangerously-skip-permissions`; all 3 lines written, exit 0 |
| 3: Slash Commands | — | Deferred (requires `gmkit init`) |
| 4: Generates Output Files | ✅ | Correct JSON array (5 entries, levels, pages); requires `--dangerously-skip-permissions` |

**Overall**: Pass
**Recommendation**: Viable candidate

Detailed notes:
- `--print` mode suppresses interactive UI and exits cleanly after task completion.
- Without `--dangerously-skip-permissions`, Claude Code prompts for approval before
  writing files even in `--print` mode. The flag is required for fully autonomous operation.
- Cannot be invoked as a subprocess from within an active Claude Code session
  (blocked by `CLAUDECODE` env var to prevent nested session resource conflicts).
  In pipeline use, it would be invoked as a top-level process, so this is not a blocker.
- Test 4: Parsed TOC correctly — 5 entries, level inferred from indentation (2-space→1,
  4-space→2), "Contents" header excluded. Output matched expected schema exactly.
- Production invocation pattern: `claude --print --dangerously-skip-permissions "<prompt>"`

---

### Codex CLI

**Date tested**: 2026-02-24
**Version**: codex-cli 0.101.0
**Model**: gpt-5.3-codex
**Test environment**: Ubuntu (pop-os), gm-kit repo root

| Test | Result | Notes |
|------|--------|-------|
| 1: CLI Invocable | ✅ | `codex exec --full-auto "Echo: hello world"` → exit 0 |
| 2: Runs to Completion | ✅ | All 3 lines written, exit 0; output redirected to /dev/null |
| 3: Slash Commands | — | Deferred |
| 4: Generates Output Files | ✅ | Correct JSON array (5 entries); exit 0; output redirected to /dev/null |

**Overall**: Pass
**Recommendation**: Viable candidate

Detailed notes:
- Invocation pattern: `codex exec --full-auto -s workspace-write "<prompt>" > /dev/null 2>&1`
- `exec` subcommand is the non-interactive batch mode (not the default interactive CLI).
- `--full-auto` sets approval=never and sandbox=workspace-write; `-s workspace-write` makes
  the sandbox explicit.
- By default, Codex prints full reasoning trace, tool calls, and MCP output to stdout.
  Redirecting to `/dev/null` gives clean pipeline behavior — viability determined by file
  output and exit code only.
- Project-level `.codex/config.toml` was loading knowledge-graph MCP on every invocation,
  consuming ~22k tokens for a simple echo. Removed knowledge-graph MCP from project config;
  pdf-reader MCP retained.
- Auth token expired between sessions — required `codex login` before testing. Expected
  periodic maintenance, not a structural blocker.
- Vision capability unconfirmed (not tested in this audit).

---

### OpenCode

**Date tested**: 2026-02-24
**Version**: 1.2.2
**Model**: Kimi K2.5
**Test environment**: Ubuntu (pop-os), gm-kit repo root

| Test | Result | Notes |
|------|--------|-------|
| 1: CLI Invocable | ✅ | `opencode run "Echo: hello world"` → exit 0; clean after one-time DB migration |
| 2: Runs to Completion | ✅ | All 3 lines written, exit 0 |
| 3: Slash Commands | — | Deferred |
| 4: Generates Output Files | ✅ | Valid JSON array written to correct path; exit 0 |

**Overall**: Pass
**Recommendation**: Viable candidate

Detailed notes:
- Invocation pattern: `opencode run "<prompt>" > /dev/null 2>&1`
- Pre-flight testing showed a 30s hang (exit 124) — this was the one-time SQLite DB
  migration running on first use. After migration, `opencode run` exits cleanly.
- No flags required for autonomous operation — runs non-interactively by default.
- Test 4 minor deviation: included "Contents" header as `{"level": 0, "title": "Contents",
  "page": null}` where Claude Code and Codex excluded it. JSON is valid; interpretation
  difference only.
- Output is suppressed cleanly via `> /dev/null 2>&1`; file output is the reliable signal.

---

## Decision

**Minimum bar**: At least one agent must pass Tests 1, 2, and 4 for the
agent-orchestrated model to be viable. Test 3 (slash commands) is secondary —
the pipeline uses CLI commands, not slash commands directly.

| Outcome | Decision |
|---------|----------|
| ≥1 agent passes Tests 1+2+4 | Agent-orchestrated model confirmed → revise E4-07b plan, remove client.py |
| No agent passes Tests 1+2+4 | SDK-based model confirmed → proceed with current E4-07b plan as-is |
| Partial passes only | Evaluate hybrid: code steps autonomous, agent steps interactive |

**Decision recorded**: 2026-02-24
**Chosen approach**: Agent-orchestrated model confirmed.

All three Phase 1 candidates (Claude Code, Codex CLI, OpenCode) passed Tests 1, 2, and 4.
The minimum bar is met. E4-07b will use the agent-orchestrated model:
- Remove `client.py` from the E4-07b plan
- Define workspace artifact protocol (input/output file contract per step)
- Document the transition model (batch groups + CLI handoff points)
- The running agent controls pipeline flow; Code steps are CLI invocations;
  Agent steps are performed by the agent itself.

---

## Phase 2 (if needed)

If no Phase 1 candidate passes, expand to Gemini CLI, Claude Desktop, and
others per BACKLOG.md E2-09 scope. Defer until Phase 1 is complete.
