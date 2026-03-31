import json
import os
import subprocess
from pathlib import Path

import pytest

from gm_kit.pdf_convert.agents.instructions.step_7_7 import build_text_scan_prompt

HOME_BREWERY_PHASE4 = (
    Path(__file__).resolve().parents[4]
    / "tests"
    / "fixtures"
    / "pdf_convert"
    / "agents"
    / "inputs"
    / "step_7_7"
    / "Homebrewery_WeaponsTable_Phase4.md"
)

AGENT_MODEL = os.environ.get("STEP_7_7_AGENT_MODEL")

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    AGENT_MODEL is None,
    reason="Set STEP_7_7_AGENT_MODEL to run the live agent table-detection test.",
)
def test_step_7_7_real_agent_detects_weapons(tmp_path: Path) -> None:
    instructions = build_text_scan_prompt(HOME_BREWERY_PHASE4.read_text(), page_num=2)
    step_dir = tmp_path / "step_7_7_agent"
    step_dir.mkdir(parents=True, exist_ok=True)
    result_file = step_dir / "step-output.json"

    cmd = [
        "codex",
        "exec",
        "--full-auto",
        "-s",
        "workspace-write",
        "--skip-git-repo-check",
        "--model",
        AGENT_MODEL,
        "-",
    ]
    env = os.environ.copy()
    env["UV_CACHE_DIR"] = "/tmp/uvcache"

    completed = subprocess.run(
        cmd,
        cwd=str(step_dir),
        env=env,
        input=instructions,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert result_file.exists(), "Agent run failed to write step-output.json"

    data = json.loads(result_file.read_text(encoding="utf-8"))
    assert data["data"]["tables_detected"] is True
    assert data["data"]["table_likelihood"] >= 70
    reasoning = data["data"].get("reasoning", [])
    assert isinstance(reasoning, list)
    combined = " ".join(reasoning).lower()
    assert "header" in combined or "sig012" in combined
    assert "row" in combined or "sig011" in combined
