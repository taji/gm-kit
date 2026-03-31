"""Run Step 7.7 text-scan prompt against a live agent model for rapid iteration."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from gm_kit.pdf_convert.agents.instructions.step_7_7 import build_text_scan_prompt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Invoke Step 7.7 (text scan) with a real agent without the full harness."
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Agent/model to use (e.g., opencode/gpt-5.3-codex, opencode/kimi-k2.5).",
    )
    parser.add_argument(
        "--fixture",
        default=Path(__file__).resolve().parents[3]
        / "tests"
        / "fixtures"
        / "pdf_convert"
        / "agents"
        / "inputs"
        / "step_7_7"
        / "Homebrewery_WeaponsTable_Phase4.md",
        type=Path,
        help="Path to the Phase 4 text snippet that the agent should analyze.",
    )
    parser.add_argument(
        "--workspace",
        default=Path.cwd() / "tmp" / "step_7_7_agent",
        type=Path,
        help="Workspace where step-output.json and logs will be written.",
    )
    parser.add_argument("--uv-cache-dir", default="/tmp/uvcache", help="UV cache directory.")
    return parser.parse_args()


def run_agent(args: argparse.Namespace) -> Path:
    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    output = workspace / "step-output.json"
    if output.exists():
        output.unlink()
    instructions = build_text_scan_prompt(args.fixture.read_text(encoding="utf-8"), page_num=2)
    instructions_file = workspace / "step-instructions.md"
    instructions_file.write_text(instructions, encoding="utf-8")
    cmd = [
        "opencode",
        "run",
        "--model",
        args.model,
        "Execute these instructions and write step-output.json in the current directory.",
        "--file",
        str(instructions_file),
    ]
    env = os.environ.copy()
    env["UV_CACHE_DIR"] = args.uv_cache_dir
    proc = subprocess.Popen(
        cmd,
        cwd=str(workspace),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    log = workspace / "agent.log"
    with log.open("w", encoding="utf-8") as f:
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            f.write(line)
        return_code = proc.wait()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, cmd)
    if not output.exists():
        raise FileNotFoundError(f"{output} missing after agent execution")
    return output


def main() -> int:
    args = parse_args()
    try:
        output = run_agent(args)
    except subprocess.CalledProcessError as exc:
        print("Agent failed:", exc, file=open(Path(args.workspace) / "agent.log", "a"))
        return 1
    data = json.loads(output.read_text(encoding="utf-8"))
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
