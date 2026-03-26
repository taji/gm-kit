#!/usr/bin/env python3
"""Live handoff harness for gmkit pdf-convert pause/resume workflows.

This harness runs gmkit, detects paused agent steps, runs the configured agent on each
step-instructions.md, validates step-output.json shape, and resumes until
completion (or failure). It writes a JSONL trace for audit/debugging.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

# Matches ANSI escape sequences (colour codes, cursor movement, etc.)
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b[@-Z\\-_]")

PAUSE_STEP_RE = re.compile(r"`([^`]*agent_steps/step_[^`]*)`")
PHASE_RE = re.compile(r"Phase\s+(\d+)/10")


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Live agent handoff harness for gmkit pdf-convert."
    )
    parser.add_argument(
        "--output-dir", required=True, help="Conversion workspace/output directory."
    )
    parser.add_argument("--pdf", help="PDF path for a fresh run (omit when using --resume).")
    parser.add_argument("--resume", action="store_true", help="Resume an existing conversion.")
    parser.add_argument("--gm-callout-config-file", help="Optional GM callout config file path.")
    parser.add_argument(
        "--agent",
        default="codex",
        choices=["codex", "opencode", "claude", "gemini", "qwen"],
        help="Agent to use for executing paused steps (default: codex).",
    )
    parser.add_argument(
        "--model",
        help="Model to use with the agent (e.g., gemini-2.5-flash, claude-sonnet-4, gpt-5.3-codex). Agent-specific.",
    )
    parser.add_argument(
        "--codex-sandbox",
        default="workspace-write",
        choices=["workspace-write", "danger-full-access", "read-only"],
        help="Codex sandbox mode for step execution.",
    )
    parser.add_argument("--max-pauses", type=int, default=100, help="Safety cap for pause cycles.")
    parser.add_argument("--uv-cache-dir", default="/tmp/uvcache", help="UV cache directory.")
    parser.add_argument("--trace-file", help="JSONL trace output file path.")
    parser.add_argument(
        "--console-log-file",
        help="Write combined gmkit + agent console output to this file.",
    )
    return parser.parse_args()


def read_state(workspace: Path) -> dict[str, Any]:
    state_file = workspace / ".state.json"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def assertion(assertions: list[dict[str, Any]], aid: str, ok: bool, msg: str) -> bool:
    assertions.append({"id": aid, "ok": ok, "msg": msg})
    return ok


def write_trace(trace_file: Path, payload: dict[str, Any]) -> None:
    trace_file.parent.mkdir(parents=True, exist_ok=True)
    with trace_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return _ANSI_RE.sub("", text)


def _prefix_lines(text: str, prefix: str) -> str:
    """Prefix every non-empty line with a source tag.

    Empty lines (blank separators) are passed through unprefixed so the log
    retains its natural paragraph spacing.
    """
    lines = text.splitlines(keepends=True)
    out = []
    for line in lines:
        stripped = line.rstrip("\r\n")
        if stripped:
            out.append(f"[{prefix}] {line}")
        else:
            out.append(line)
    return "".join(out)


def emit_output(
    text: str,
    console_log_file: Path | None,
    source: Literal["GMKIT", "AGENT", "HARNESS"] = "GMKIT",
) -> None:
    """Print text to stdout and append a tagged, ANSI-clean copy to the log file.

    Args:
        text: Raw output to emit.
        console_log_file: Path to the combined console log, or None to skip.
        source: Provenance tag written to the log file (terminal output is
            emitted raw so colours are preserved).
    """
    if not text:
        return
    # Terminal: emit raw (preserves colour/formatting for interactive use).
    print(text, end="")
    if console_log_file is not None:
        console_log_file.parent.mkdir(parents=True, exist_ok=True)
        # Log file: strip ANSI then prefix every content line with source tag.
        clean = _strip_ansi(text)
        tagged = _prefix_lines(clean, source)
        with console_log_file.open("a", encoding="utf-8") as f:
            f.write(tagged)


def sanitize_agent_instructions(instructions: str, step_dir: Path | None = None) -> str:
    """Strip in-prompt resume command so harness owns resume sequencing.

    Args:
        instructions: Raw instruction text from step-instructions.md.
        step_dir: Absolute path to the step directory. When provided, the
            harness note includes the exact required output path so the agent
            cannot accidentally write to the wrong location.
    """
    marker = "\n## After Completing This Step"
    idx = instructions.find(marker)
    if idx != -1:
        instructions = instructions[:idx].rstrip() + "\n"

    if step_dir is not None:
        output_path = step_dir / "step-output.json"
        harness_note = (
            "\n\n## Harness Note\n"
            "Do not run `gmkit pdf-convert --resume` yourself.\n\n"
            "### Output File Checklist\n"
            "Before exiting, verify ALL of the following:\n\n"
            f"- [ ] Write `step-output.json` to this **exact absolute path**:\n"
            f"  `{output_path}`\n"
            f"- [ ] The file must be inside the step directory:\n"
            f"  `{step_dir}/`\n"
            "- [ ] Do NOT write it to the workspace root or any parent directory.\n"
            "- [ ] Confirm the file exists at the path above before exiting.\n"
            "- [ ] Do not write any other files outside this step directory.\n"
        )
    else:
        harness_note = (
            "\n\n## Harness Note\n"
            "Do not run `gmkit pdf-convert --resume` yourself. "
            "Write `step-output.json` only and exit.\n"
        )

    return instructions + harness_note


def build_gmkit_cmd(args: argparse.Namespace, python_version: str, resume: bool) -> list[str]:
    cmd = [
        "uv",
        "run",
        "--python",
        python_version,
        "--extra",
        "dev",
        "--",
        "gmkit",
        "pdf-convert",
    ]
    if args.gm_callout_config_file:
        cmd.extend(["--gm-callout-config-file", args.gm_callout_config_file])
    if resume:
        cmd.append("--resume")
    if args.pdf and not resume:
        cmd.append(str(args.pdf))
    cmd.extend(["--output", str(args.output_dir)])
    if not resume:
        cmd.append("--yes")
    return cmd


def run_cmd(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
    stdin_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        input=stdin_text,
    )
    return result


def parse_pause_step_dir(combined_output: str) -> Path | None:
    m = PAUSE_STEP_RE.search(combined_output)
    if m:
        return Path(m.group(1))
    return None


def step_id_from_dir(step_dir: Path) -> str:
    """Convert a step directory name to a step ID string.

    Examples:
        step_4_5      -> 4.5
        step_6_4      -> 6.4
        step_7_7_p1   -> 7.7_p1   (page/part suffixes preserve their underscore)
        step_10_2     -> 10.2
    """
    name = step_dir.name
    if not name.startswith("step_"):
        return name
    # Strip the leading "step_" prefix.
    remainder = name[len("step_") :]
    # The numeric portion is one or two digits, a separator underscore, and one
    # or two digits (e.g. "4_5", "10_2", "7_7").  Everything after that is a
    # non-numeric suffix (e.g. "_p1") that must be kept verbatim.
    m = re.match(r"^(\d+)_(\d+)(_.+)?$", remainder)
    if m:
        major, minor, suffix = m.group(1), m.group(2), m.group(3) or ""
        return f"{major}.{minor}{suffix}"
    # Fallback: leave as-is (unknown format).
    return remainder


def parse_phase(combined_output: str) -> int | None:
    m = PHASE_RE.search(combined_output)
    if m:
        return int(m.group(1))
    return None


def format_phase(num: int | None) -> str:
    if num is None:
        return "unknown"
    token_map = {
        1: "ONE",
        2: "TWO",
        3: "THREE",
        4: "FOUR",
        5: "FIVE",
        6: "SIX",
        7: "SEVEN",
        8: "EIGHT",
        9: "NINE",
        10: "TEN",
    }
    return token_map.get(num, str(num))


def validate_step_output(
    step_dir: Path, step_id: str, validator: Any, contract_violation_type: type[Exception]
) -> tuple[bool, str]:
    output_file = step_dir / "step-output.json"
    if not output_file.exists():
        return False, "step-output.json missing"
    try:
        output_data = json.loads(output_file.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"invalid JSON: {exc}"
    try:
        validator.validate(step_id=step_id, output=output_data)
    except contract_violation_type as exc:
        return False, f"contract violation: {exc.validation_errors}"
    return True, "contract valid"


def run_status(
    output_dir: Path, cwd: Path, env: dict[str, str], python_version: str
) -> subprocess.CompletedProcess[str]:
    cmd = [
        "uv",
        "run",
        "--python",
        python_version,
        "--extra",
        "dev",
        "--",
        "gmkit",
        "pdf-convert",
        "--status",
        str(output_dir),
    ]
    return run_cmd(cmd, cwd=cwd, env=env)


def build_agent_cmd(
    agent: str,
    codex_sandbox: str,
    instructions: str | None = None,
    model: str | None = None,
    instructions_file: Path | None = None,
) -> tuple[list[str], str | None]:
    """Build agent command list based on agent type.

    Args:
        agent: Agent name (codex, opencode, claude, gemini, qwen)
        codex_sandbox: Sandbox mode for codex (workspace-write, danger-full-access, read-only)
        instructions: Instructions text to pass to agent (if applicable)
        model: Model to use (e.g., gemini-2.5-flash). Only used by agents that support it.
        instructions_file: Path to a file containing instructions. When provided and the
            agent supports it, the file is passed via a --file flag rather than as an
            inline argument. This avoids shell-escaping issues with large prompts and
            sidesteps the Claude 4.6 "assistant message prefill" API restriction.

    Returns:
        Tuple of (command list, stdin text or None). For most agents, instructions
        are passed via stdin. For Gemini, instructions are passed via --prompt.

    Raises:
        ValueError: If agent is not supported
    """
    agent_lower = agent.lower()

    if agent_lower == "codex":
        # Codex supports --model flag for selecting specific model
        cmd = [
            "codex",
            "exec",
            "--full-auto",
            "-s",
            codex_sandbox,
            "--skip-git-repo-check",
        ]
        if model:
            cmd.extend(["--model", model])
        cmd.append("-")
        return cmd, instructions
    elif agent_lower == "opencode":
        # OpenCode uses 'run' command for batch/non-interactive mode.
        # Default to kimi-k2.5: strong long-context reasoning, no prefill restrictions.
        # Claude 4.6 models are intentionally avoided here — Anthropic removed support
        # for assistant-message prefill in that generation, which breaks OpenCode's
        # internal conversation loop (raises "conversation must end with a user message").
        effective_model = model if model else "opencode/kimi-k2.5"
        cmd = [
            "opencode",
            "run",
            "--model",
            effective_model,
        ]
        if instructions_file and instructions_file.exists():
            # Preferred path: pass instructions as an attached file.
            # The prompt message must come before --file; opencode treats trailing
            # positional args after --file as additional file paths, not the message.
            cmd.append("Execute these instructions and write the required output files.")
            cmd.extend(["--file", str(instructions_file)])
        elif instructions:
            # Fallback: pass instructions inline (small prompts only).
            cmd.append(instructions)
        else:
            cmd.append("Execute the task described in step-instructions.md")
        return cmd, None
    elif agent_lower == "claude":
        # Claude uses --print for non-interactive/batch mode
        # Supports --model flag for model selection
        # Uses --permission-mode bypassPermissions for auto-approval
        cmd = [
            "claude",
            "--print",
            "--permission-mode",
            "bypassPermissions",
        ]
        if model:
            cmd.extend(["--model", model])
        cmd.append("-")
        return cmd, instructions
    elif agent_lower == "gemini":
        # Gemini uses --prompt for instructions and --yolo for auto-approval
        # Does not use stdin - instructions go via --prompt
        # Supports --model flag for selecting specific model
        cmd = [
            "gemini",
            "--yolo",
        ]
        if model:
            cmd.extend(["--model", model])
        if instructions:
            cmd.extend(["--prompt", instructions])
        return cmd, None
    elif agent_lower == "qwen":
        # Qwen uses --continue with yolo approval mode
        # Supports --model flag for model selection
        cmd = [
            "qwen",
            "--continue",
            "--approval-mode=yolo",
        ]
        if model:
            cmd.extend(["--model", model])
        cmd.append("-")
        return cmd, instructions
    else:
        raise ValueError(
            f"Unsupported agent: {agent}. Supported: codex, opencode, claude, gemini, qwen"
        )


def main() -> int:
    args = parse_args()
    if args.resume and args.pdf:
        print("ERROR: Use either --resume or --pdf (not both).", file=sys.stderr)
        return 2
    if not args.resume and not args.pdf:
        print("ERROR: Provide --pdf for fresh run, or use --resume.", file=sys.stderr)
        return 2

    root = Path(__file__).resolve().parents[2]
    output_dir = Path(args.output_dir).resolve()
    if args.pdf:
        pdf_path = Path(args.pdf).resolve()
        if not pdf_path.exists():
            print(f"ERROR: PDF not found: {pdf_path}", file=sys.stderr)
            return 2
    if args.gm_callout_config_file and not Path(args.gm_callout_config_file).exists():
        print(f"ERROR: Callout config not found: {args.gm_callout_config_file}", file=sys.stderr)
        return 2

    # Imported lazily so `--help` works without project import path setup.
    from gm_kit.pdf_convert.agents.contracts import ContractValidator
    from gm_kit.pdf_convert.agents.errors import ContractViolation

    python_version = (root / ".python-version").read_text(encoding="utf-8").strip()
    env = dict(os.environ)
    env["GM_AGENT"] = args.agent
    env["UV_CACHE_DIR"] = args.uv_cache_dir

    run_id = f"handoff-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6]}"
    trace_file = (
        Path(args.trace_file).resolve() if args.trace_file else output_dir / "harness-trace.jsonl"
    )
    console_log_file = (
        Path(args.console_log_file).resolve()
        if args.console_log_file
        else output_dir / "harness-console.log"
    )
    validator = ContractValidator()

    write_trace(
        trace_file,
        {
            "ts": now_iso(),
            "run_id": run_id,
            "event": "run_start",
            "workspace": str(output_dir),
            "assertions": [],
            "notes": "Live handoff harness started",
        },
    )

    pause_count = 0
    next_resume = args.resume

    while True:
        gmkit_cmd = build_gmkit_cmd(args, python_version, resume=next_resume)
        gmkit_start = time.perf_counter()
        gmkit_res = run_cmd(gmkit_cmd, cwd=root, env=env)
        gmkit_duration_sec = round(time.perf_counter() - gmkit_start, 3)
        combined = (gmkit_res.stdout or "") + (gmkit_res.stderr or "")
        emit_output(combined, console_log_file, source="GMKIT")

        phase = parse_phase(combined)
        step_dir = parse_pause_step_dir(combined)
        state = read_state(output_dir)

        write_trace(
            trace_file,
            {
                "ts": now_iso(),
                "run_id": run_id,
                "event": "gmkit_exit",
                "workspace": str(output_dir),
                "phase": phase,
                "exit_code": gmkit_res.returncode,
                "duration_sec": gmkit_duration_sec,
                "state": state,
                "assertions": [],
            },
        )

        if step_dir is not None:
            pause_count += 1
            if pause_count > args.max_pauses:
                write_trace(
                    trace_file,
                    {
                        "ts": now_iso(),
                        "run_id": run_id,
                        "event": "assertion_failure",
                        "workspace": str(output_dir),
                        "assertions": [
                            {"id": "A-MAX-PAUSES", "ok": False, "msg": "Exceeded max pause limit"}
                        ],
                    },
                )
                return 1

            step_id = step_id_from_dir(step_dir)
            assertions: list[dict[str, Any]] = []
            ok = True
            ok &= assertion(assertions, "A-STEPDIR", step_dir.exists(), "step dir exists")
            ok &= assertion(
                assertions,
                "A-STEP-INPUT",
                (step_dir / "step-input.json").exists(),
                "step-input exists",
            )
            ok &= assertion(
                assertions,
                "A-STEP-INSTR",
                (step_dir / "step-instructions.md").exists(),
                "step-instructions exists",
            )
            ok &= assertion(
                assertions,
                "A-STATE-STEP",
                str(state.get("current_step", "")) == step_id,
                "state current_step matches paused step",
            )

            write_trace(
                trace_file,
                {
                    "ts": now_iso(),
                    "run_id": run_id,
                    "event": "pause_detected",
                    "workspace": str(output_dir),
                    "phase": phase,
                    "step_id": step_id,
                    "state": state,
                    "artifacts": {
                        "step_dir": str(step_dir),
                        "input_exists": (step_dir / "step-input.json").exists(),
                        "instructions_exists": (step_dir / "step-instructions.md").exists(),
                        "output_exists": (step_dir / "step-output.json").exists(),
                    },
                    "assertions": assertions,
                },
            )

            if not ok:
                return 1

            instructions_raw = (step_dir / "step-instructions.md").read_text(encoding="utf-8")
            instructions = sanitize_agent_instructions(instructions_raw, step_dir=step_dir)
            # Write sanitized instructions to a separate file so agents that support
            # --file (e.g. OpenCode) can receive them without shell-escaping issues.
            # Kept on disk after the step for post-run inspection/debugging.
            instructions_processed = step_dir / "step-instructions-processed.md"
            instructions_processed.write_text(instructions, encoding="utf-8")
            agent_cmd, stdin_text = build_agent_cmd(
                args.agent,
                args.codex_sandbox,
                instructions=instructions,
                model=args.model,
                instructions_file=instructions_processed,
            )
            agent_start = time.perf_counter()
            agent_res = run_cmd(agent_cmd, cwd=step_dir, env=env, stdin_text=stdin_text)
            agent_duration_sec = round(time.perf_counter() - agent_start, 3)
            agent_out = (agent_res.stdout or "") + (agent_res.stderr or "")
            emit_output(agent_out, console_log_file, source="AGENT")

            valid, msg = validate_step_output(step_dir, step_id, validator, ContractViolation)
            write_trace(
                trace_file,
                {
                    "ts": now_iso(),
                    "run_id": run_id,
                    "event": "agent_exit",
                    "workspace": str(output_dir),
                    "phase": phase,
                    "step_id": step_id,
                    "agent_exit_code": agent_res.returncode,
                    "duration_sec": agent_duration_sec,
                    "assertions": [{"id": "A-STEP-OUTPUT", "ok": valid, "msg": msg}],
                },
            )
            if agent_res.returncode != 0 or not valid:
                return 1

            next_resume = True
            continue

        status_res = run_status(output_dir, cwd=root, env=env, python_version=python_version)
        status_out = (status_res.stdout or "") + (status_res.stderr or "")
        emit_output(status_out, console_log_file, source="GMKIT")
        completed = "Status: completed" in status_out

        state_after = read_state(output_dir)
        phase_timings: list[dict[str, Any]] = []
        for item in state_after.get("phase_results", []):
            if not isinstance(item, dict):
                continue
            started_at = item.get("started_at")
            completed_at = item.get("completed_at")
            duration_sec = None
            if isinstance(started_at, str) and isinstance(completed_at, str):
                try:
                    start_dt = datetime.fromisoformat(started_at)
                    end_dt = datetime.fromisoformat(completed_at)
                    duration_sec = round((end_dt - start_dt).total_seconds(), 3)
                except Exception:
                    duration_sec = None
            phase_timings.append(
                {
                    "phase": item.get("phase", 0),
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "duration_sec": duration_sec,
                }
            )

        final_assertions: list[dict[str, Any]] = []
        assertion(
            final_assertions,
            "A-COMPLETED",
            completed,
            "conversion completed" if completed else "conversion not completed",
        )

        write_trace(
            trace_file,
            {
                "ts": now_iso(),
                "run_id": run_id,
                "event": "run_complete",
                "workspace": str(output_dir),
                "completed": completed,
                "phase": phase,
                "phase_timings": phase_timings,
                "assertions": final_assertions,
            },
        )

        if not completed:
            return 1

        break

    return 0


if __name__ == "__main__":
    sys.exit(main())
