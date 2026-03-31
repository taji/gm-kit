# devtools/scripts

Utility scripts for local agent/tooling setup and PDF-convert diagnostics.

## `provision_agents.sh`

Installs CLI agents from `agents.registry.sh` if missing, then verifies each with `--version`.

Run:

```bash
bash devtools/scripts/provision_agents.sh
```

Skip one or more agents:

```bash
bash devtools/scripts/provision_agents.sh --skip claude,codex-cli
```

## `remove_agents.sh`

Uninstalls agents listed in `agents.registry.sh`. Can run in dry-run mode and optionally purge known config/cache/share directories.

Run:

```bash
bash devtools/scripts/remove_agents.sh
```

Dry run:

```bash
bash devtools/scripts/remove_agents.sh --dry-run
```

Remove + purge:

```bash
bash devtools/scripts/remove_agents.sh --purge
```

## `agents.registry.sh`

Registry file consumed by `provision_agents.sh` and `remove_agents.sh`. Defines each agent's detect/install/verify/uninstall commands and purge paths.

Typical use:

```bash
source devtools/scripts/agents.registry.sh
```

## `pymupdf_callout_finder.py`

Diagnostic helper that scans a PDF for text between a start marker and end marker using PyMuPDF. Current defaults are hardcoded in the script.

Run:

```bash
uv run --python "$(cat .python-version)" --extra dev -- python devtools/scripts/pymupdf_callout_finder.py
```

## `pdf_convert_agent_handoff_loop.sh`

Debug runner for paused handoff flow. It runs `gmkit pdf-convert`, detects paused agent steps, runs Codex for each `step-instructions.md`, then resumes automatically until completion.

New run:

```bash
bash devtools/scripts/pdf_convert_agent_handoff_loop.sh \
  --pdf "tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.pdf" \
  --output-dir "./tmp/sc004-loop" \
  --gm-callout-config-file "./tmp/sc004-callout-rules.input.json"
```

Resume existing run:

```bash
bash devtools/scripts/pdf_convert_agent_handoff_loop.sh \
  --resume \
  --output-dir "./tmp/sc004-loop"
```

Capture a full console transcript while still streaming output live:

```bash
bash devtools/scripts/pdf_convert_agent_handoff_loop.sh \
  --pdf "tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.pdf" \
  --output-dir "./tmp/sc004-loop" \
  --gm-callout-config-file "./tmp/sc004-callout-rules.input.json" \
  2>&1 | tee "./tmp/sc004-loop-run.log"
```

Notes:
- Defaults: `--agent codex`, `--codex-sandbox workspace-write`, `--max-pauses 100`.
- For broad filesystem access during debugging, set `--codex-sandbox danger-full-access`.

## `live_handoff_harness.py` + `live_handoff_harness.sh`

Structured end-to-end live handoff harness for `gmkit pdf-convert`. This wraps the same pause/resume loop but also writes JSONL trace events and enforces handoff invariants (state/artifact/contract checks at each pause).
The harness sanitizes step instructions so the agent writes `step-output.json` only; resume is always executed by the harness (prevents double-resume loops).

Supported agents: codex (default), opencode, claude, gemini, qwen.

Run via shell wrapper:

```bash
bash devtools/scripts/live_handoff_harness.sh \
  --pdf "tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.pdf" \
  --output-dir "./tmp/sc004-harness" \
  --gm-callout-config-file "./tmp/sc004-callout-rules.input.json"
```

Resume:

```bash
bash devtools/scripts/live_handoff_harness.sh \
  --resume \
  --output-dir "./tmp/sc004-harness"
```

Trace output:
- Default: `<output-dir>/harness-trace.jsonl`
- Override: `--trace-file <path>`
- Console log (gmkit + agent stdout/stderr): default `<output-dir>/harness-console.log`, override with `--console-log-file <path>`

Useful options:
- `--agent codex|opencode|claude|gemini|qwen` (default: codex)
- `--model <model-name>` (agent-specific model selection, e.g., `gemini-2.5-flash`, `claude-sonnet-4`, `gpt-5.3-codex`)
- `--codex-sandbox workspace-write|danger-full-access|read-only` (codex only)
- `--max-pauses <n>`

Timing:
- Trace events include command durations (`duration_sec`) for gmkit and per-agent step invocations.
- Final `run_complete` event includes `phase_timings` derived from `.state.json` phase `started_at` / `completed_at`.
