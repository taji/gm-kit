# E7-02 Analyze-and-Prep Command Skeleton + Artifact Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a runnable `gmkit analyze-and-prep-pdf` command that creates or reuses the normal conversion workspace, emits a validated `prep/` subtree contract, and tracks prep lifecycle independently from the numeric conversion pipeline.

**Architecture:** Add a prep-specific CLI helper, prep state/contracts modules, and a prep orchestrator under `gm_kit.pdf_convert.prep`. Reuse the existing conversion workspace creation pattern, but keep prep state, status/resume behavior, and logging separate from the numeric phase engine.

**Tech Stack:** Python 3.13.7, Typer, pathlib, json/dataclasses, existing `gm_kit.pdf_convert.prep` registry, pytest with `CliRunner`, mypy, ruff.

---

## Planned File Structure

**Create**
- `src/gm_kit/pdf_convert/prep/contracts.py`
- `src/gm_kit/pdf_convert/prep/state.py`
- `src/gm_kit/pdf_convert/prep/orchestrator.py`
- `src/gm_kit/pdf_convert/prep/cli_helpers.py`
- `tests/unit/pdf_convert/prep/test_contracts.py`
- `tests/unit/pdf_convert/prep/test_state.py`
- `tests/unit/pdf_convert/prep/test_orchestrator.py`
- `tests/unit/pdf_convert/prep/test_cli_helpers.py`

**Modify**
- `src/gm_kit/cli.py`
- `src/gm_kit/pdf_convert/prep/__init__.py`
- `tests/unit/test_cli.py`
- `specs/e7-02-analyze-and-prep-command-skeleton/feature_journal.md`

**Do Not Modify In E7-02**
- `src/gm_kit/pdf_convert/orchestrator.py`
- `src/gm_kit/pdf_convert/state.py`
- `src/gm_kit/pdf_convert/phases/base.py`
- existing numeric conversion phase implementations

The prep command should reuse the normal workspace root but must not reuse the numeric conversion state machine or numeric `--phase`/`--from-step` controls.

---

### Task 1: Add Prep Contract and State Models

**Files:**
- Create: `src/gm_kit/pdf_convert/prep/contracts.py`
- Create: `src/gm_kit/pdf_convert/prep/state.py`
- Test: `tests/unit/pdf_convert/prep/test_contracts.py`
- Test: `tests/unit/pdf_convert/prep/test_state.py`

- [ ] **Step 1: Write the failing prep contract tests**

```python
from pathlib import Path

from gm_kit.pdf_convert.prep.contracts import (
    PREP_CONTRACT_VERSION,
    PrepArtifactEntry,
    PrepManifest,
    build_prep_paths,
)


def test_build_prep_paths__should_return_expected_subtree__when_workspace_provided(tmp_path: Path) -> None:
    paths = build_prep_paths(tmp_path / "workspace")

    assert paths.root == tmp_path / "workspace" / "prep"
    assert paths.manifest == tmp_path / "workspace" / "prep" / "prep-manifest.json"
    assert paths.state == tmp_path / "workspace" / "prep" / "prep-state.json"
    assert paths.complete == tmp_path / "workspace" / "prep" / "prep-complete.json"
    assert paths.log == tmp_path / "workspace" / "prep" / "logs" / "prep.log"


def test_prep_manifest__should_include_contract_version__when_serialized(tmp_path: Path) -> None:
    manifest = PrepManifest(
        contract_version=PREP_CONTRACT_VERSION,
        pdf_path=str(tmp_path / "sample.pdf"),
        workspace_path=str(tmp_path / "workspace"),
        artifacts=[PrepArtifactEntry(name="prep-state.json", status="ready")],
        phase_keys=["prep.initialize-workspace"],
        step_keys=["prep.initialize-workspace.bootstrap"],
        completed=False,
    )

    payload = manifest.to_dict()

    assert payload["contract_version"] == PREP_CONTRACT_VERSION
    assert payload["artifacts"][0]["name"] == "prep-state.json"
```

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_contracts.py -v`
Expected: FAIL because the prep contract module does not exist yet.

- [ ] **Step 2: Write the failing prep state tests**

```python
from pathlib import Path

from gm_kit.pdf_convert.prep.state import PrepRunState, PrepStatus, load_prep_state, save_prep_state


def test_save_prep_state__should_round_trip_status__when_state_is_written(tmp_path: Path) -> None:
    path = tmp_path / "prep-state.json"
    state = PrepRunState(status=PrepStatus.INITIALIZED, current_phase_key=None, completed_steps=[])

    save_prep_state(path, state)
    loaded = load_prep_state(path)

    assert loaded is not None
    assert loaded.status == PrepStatus.INITIALIZED
    assert loaded.completed_steps == []
```

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_state.py -v`
Expected: FAIL because the prep state module does not exist yet.

- [ ] **Step 3: Implement the prep contract module**

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

PREP_CONTRACT_VERSION = "1"


@dataclass(frozen=True)
class PrepPaths:
    root: Path
    manifest: Path
    state: Path
    complete: Path
    log: Path


@dataclass(frozen=True)
class PrepArtifactEntry:
    name: str
    status: str


@dataclass(frozen=True)
class PrepManifest:
    contract_version: str
    pdf_path: str
    workspace_path: str
    artifacts: list[PrepArtifactEntry]
    phase_keys: list[str]
    step_keys: list[str]
    completed: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_prep_paths(workspace_dir: Path) -> PrepPaths:
    prep_root = workspace_dir / "prep"
    return PrepPaths(
        root=prep_root,
        manifest=prep_root / "prep-manifest.json",
        state=prep_root / "prep-state.json",
        complete=prep_root / "prep-complete.json",
        log=prep_root / "logs" / "prep.log",
    )
```

- [ ] **Step 4: Implement the prep state module**

```python
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path


class PrepStatus(str, Enum):
    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class PrepRunState:
    status: PrepStatus
    current_phase_key: str | None
    completed_steps: list[str]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "PrepRunState":
        return cls(
            status=PrepStatus(str(data["status"])),
            current_phase_key=data.get("current_phase_key") if data.get("current_phase_key") else None,
            completed_steps=[str(step) for step in data.get("completed_steps", [])],
        )


def save_prep_state(path: Path, state: PrepRunState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8")


def load_prep_state(path: Path) -> PrepRunState | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return PrepRunState.from_dict(data)
```

- [ ] **Step 5: Run the focused contract/state tests**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_contracts.py tests/unit/pdf_convert/prep/test_state.py -v`
Expected: PASS

- [ ] **Step 6: Commit the contract/state foundation**

```bash
git add src/gm_kit/pdf_convert/prep/contracts.py \
  src/gm_kit/pdf_convert/prep/state.py \
  tests/unit/pdf_convert/prep/test_contracts.py \
  tests/unit/pdf_convert/prep/test_state.py
git commit -m "feat(prep): add prep contract and state skeleton"
```

---

### Task 2: Add Prep Orchestrator Skeleton

**Files:**
- Create: `src/gm_kit/pdf_convert/prep/orchestrator.py`
- Modify: `src/gm_kit/pdf_convert/prep/__init__.py`
- Test: `tests/unit/pdf_convert/prep/test_orchestrator.py`

- [ ] **Step 1: Write the failing orchestrator tests**

```python
from pathlib import Path

from gm_kit.pdf_convert.prep.orchestrator import PrepOrchestrator


def test_prep_orchestrator__should_create_prep_contract_files__when_run_new_prep(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    orchestrator = PrepOrchestrator()
    exit_code = orchestrator.run_new_prep(pdf_path, output_dir=tmp_path / "workspace", auto_proceed=True)

    assert int(exit_code) == 0
    assert (tmp_path / "workspace" / "prep" / "prep-manifest.json").exists()
    assert (tmp_path / "workspace" / "prep" / "prep-state.json").exists()
    assert (tmp_path / "workspace" / "prep" / "prep-complete.json").exists()
    assert (tmp_path / "workspace" / "prep" / "logs" / "prep.log").exists()
```

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_orchestrator.py -v`
Expected: FAIL because the orchestrator does not exist yet.

- [ ] **Step 2: Implement the prep orchestrator skeleton**

```python
from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.orchestrator import create_output_directory
from gm_kit.pdf_convert.prep.contracts import (
    PREP_CONTRACT_VERSION,
    PrepArtifactEntry,
    PrepManifest,
    build_prep_paths,
)
from gm_kit.pdf_convert.prep.registry import PrepRegistry
from gm_kit.pdf_convert.prep.registry_types import PrepPhaseDefinition
from gm_kit.pdf_convert.prep.state import PrepRunState, PrepStatus, save_prep_state
class PrepOrchestrator:
    def __init__(self, console: Console | None = None, registry: PrepRegistry | None = None) -> None:
        self.console = console or Console()
        self.registry = registry or PrepRegistry(
            phases=[
                PrepPhaseDefinition("prep.initialize-workspace", 100, "Initialize Workspace"),
                PrepPhaseDefinition("prep.analyze-document", 200, "Analyze Document"),
                PrepPhaseDefinition("prep.extract-assets", 300, "Extract Assets"),
                PrepPhaseDefinition("prep.derive-structure", 400, "Derive Structure"),
                PrepPhaseDefinition("prep.plan-chunks", 500, "Plan Chunks"),
                PrepPhaseDefinition("prep.prepare-guidance", 600, "Prepare Guidance"),
                PrepPhaseDefinition("prep.propose-annotations", 700, "Propose Annotations"),
                PrepPhaseDefinition("prep.review-annotations", 800, "Review Annotations"),
                PrepPhaseDefinition("prep.finalize-prep-artifacts", 900, "Finalize Prep Artifacts"),
            ],
            steps=[],
        )

    def run_new_prep(
        self,
        pdf_path: Path,
        output_dir: Path | None = None,
        auto_proceed: bool = False,
    ) -> ExitCode:
        workspace_dir = create_output_directory(pdf_path, output_dir)
        prep_paths = build_prep_paths(workspace_dir)
        prep_paths.log.parent.mkdir(parents=True, exist_ok=True)
        prep_paths.root.mkdir(parents=True, exist_ok=True)

        state = PrepRunState(status=PrepStatus.RUNNING, current_phase_key=None, completed_steps=[])
        save_prep_state(prep_paths.state, state)

        prep_paths.log.write_text("== Prep Start ==\n", encoding="utf-8")

        manifest = PrepManifest(
            contract_version=PREP_CONTRACT_VERSION,
            pdf_path=str(pdf_path.resolve()),
            workspace_path=str(workspace_dir),
            artifacts=[
                PrepArtifactEntry(name="prep-state.json", status="ready"),
                PrepArtifactEntry(name="prep-complete.json", status="ready"),
                PrepArtifactEntry(name="logs/prep.log", status="ready"),
            ],
            phase_keys=[phase.phase_key for phase in self.registry.get_ordered_phases()],
            step_keys=[],
            completed=False,
        )
        prep_paths.manifest.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")

        completed_state = PrepRunState(
            status=PrepStatus.COMPLETED,
            current_phase_key=None,
            completed_steps=[],
        )
        save_prep_state(prep_paths.state, completed_state)
        prep_paths.complete.write_text('{"status":"completed"}\n', encoding="utf-8")
        return ExitCode.SUCCESS
```

- [ ] **Step 3: Run the focused orchestrator tests**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_orchestrator.py -v`
Expected: PASS

- [ ] **Step 4: Commit the prep orchestrator skeleton**

```bash
git add src/gm_kit/pdf_convert/prep/orchestrator.py \
  src/gm_kit/pdf_convert/prep/__init__.py \
  tests/unit/pdf_convert/prep/test_orchestrator.py
git commit -m "feat(prep): add prep orchestrator skeleton"
```

---

### Task 3: Add Prep CLI Helper Routing

**Files:**
- Create: `src/gm_kit/pdf_convert/prep/cli_helpers.py`
- Test: `tests/unit/pdf_convert/prep/test_cli_helpers.py`

- [ ] **Step 1: Write the failing prep CLI helper tests**

```python
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.prep.cli_helpers import run_analyze_and_prep_command


def test_run_analyze_and_prep_command__should_require_pdf_path__when_new_run_requested() -> None:
    with pytest.raises(SystemExit):
        run_analyze_and_prep_command(
            pdf_path=None,
            output=None,
            resume=False,
            status=False,
            yes=False,
        )


def test_run_analyze_and_prep_command__should_route_to_new_prep__when_pdf_path_provided(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    with patch("gm_kit.pdf_convert.prep.orchestrator.PrepOrchestrator") as mock_cls:
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_new_prep.return_value = ExitCode.SUCCESS
        mock_cls.return_value = mock_orchestrator

        with pytest.raises(SystemExit) as excinfo:
            run_analyze_and_prep_command(
                pdf_path=str(pdf_path),
                output=str(tmp_path / "workspace"),
                resume=False,
                status=False,
                yes=True,
            )

    assert excinfo.value.code == ExitCode.SUCCESS
```

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_cli_helpers.py -v`
Expected: FAIL because the helper module does not exist yet.

- [ ] **Step 2: Implement the prep CLI helper**

```python
from __future__ import annotations

from pathlib import Path

import typer

from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.prep.orchestrator import PrepOrchestrator


def run_analyze_and_prep_command(
    pdf_path: str | None,
    output: str | None,
    resume: bool,
    status: bool,
    yes: bool,
) -> None:
    operation_flags = [resume, status]
    if sum(bool(flag) for flag in operation_flags) > 1:
        typer.echo("ERROR: Cannot combine --resume and --status", err=True)
        raise typer.Exit(code=ExitCode.FILE_ERROR)

    orchestrator = PrepOrchestrator()

    if status:
        raise typer.Exit(code=orchestrator.show_status(Path(output or pdf_path or ".")))

    if resume:
        raise typer.Exit(code=orchestrator.resume_prep(Path(output or pdf_path or "."), auto_proceed=yes))

    if not pdf_path:
        typer.echo("ERROR: PDF path is required for new prep", err=True)
        raise typer.Exit(code=ExitCode.FILE_ERROR)

    raise typer.Exit(
        code=orchestrator.run_new_prep(
            Path(pdf_path),
            output_dir=Path(output) if output else None,
            auto_proceed=yes,
        )
    )
```

- [ ] **Step 3: Run the focused prep CLI helper tests**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_cli_helpers.py -v`
Expected: PASS

- [ ] **Step 4: Commit the prep CLI helper**

```bash
git add src/gm_kit/pdf_convert/prep/cli_helpers.py \
  tests/unit/pdf_convert/prep/test_cli_helpers.py
git commit -m "feat(prep): add analyze-and-prep CLI helper"
```

---

### Task 4: Register the New CLI Command

**Files:**
- Modify: `src/gm_kit/cli.py`
- Modify: `tests/unit/test_cli.py`

- [ ] **Step 1: Write the failing CLI command tests**

```python
from unittest.mock import patch

from typer.testing import CliRunner

from gm_kit.cli import app


def test_cli_analyze_and_prep_pdf__should_route_to_helper__when_invoked(tmp_path) -> None:
    runner = CliRunner()

    with patch("gm_kit.pdf_convert.prep.cli_helpers.run_analyze_and_prep_command") as mock_run:
        result = runner.invoke(
            app,
            [
                "analyze-and-prep-pdf",
                str(tmp_path / "sample.pdf"),
                "--output",
                str(tmp_path / "workspace"),
                "--yes",
            ],
        )

    assert result.exit_code == 0
    mock_run.assert_called_once()
```

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/test_cli.py -k analyze_and_prep -v`
Expected: FAIL because the CLI command is not registered yet.

- [ ] **Step 2: Implement the new Typer command**

```python
@app.command("analyze-and-prep-pdf")
def analyze_and_prep_pdf(
    pdf_path: str = typer.Argument(None, help="Path to the PDF file to analyze and prep"),
    output: str = typer.Option(None, "--output", help="Output directory [default: ./<pdf-basename>/]"),
    resume: bool = typer.Option(False, "--resume", help="Resume interrupted prep in directory"),
    status: bool = typer.Option(False, "--status", help="Show prep status for directory"),
    yes: bool = typer.Option(False, "--yes", help="Non-interactive mode (accept defaults)"),
) -> None:
    from gm_kit.pdf_convert.prep.cli_helpers import run_analyze_and_prep_command

    run_analyze_and_prep_command(
        pdf_path=pdf_path,
        output=output,
        resume=resume,
        status=status,
        yes=yes,
    )
```

- [ ] **Step 3: Run the focused CLI tests**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/test_cli.py -k analyze_and_prep -v`
Expected: PASS

- [ ] **Step 4: Commit the CLI registration**

```bash
git add src/gm_kit/cli.py tests/unit/test_cli.py
git commit -m "feat(cli): add analyze-and-prep-pdf command"
```

---

### Task 5: Finish Prep Status/Resume and Full Verification

**Files:**
- Modify: `src/gm_kit/pdf_convert/prep/orchestrator.py`
- Modify: `tests/unit/pdf_convert/prep/test_orchestrator.py`
- Modify: `specs/e7-02-analyze-and-prep-command-skeleton/feature_journal.md`

- [ ] **Step 1: Write the failing status/resume tests**

```python
from pathlib import Path

from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.prep.orchestrator import PrepOrchestrator


def test_prep_orchestrator__should_report_completed_status__when_complete_marker_exists(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")
    workspace = tmp_path / "workspace"

    orchestrator = PrepOrchestrator()
    orchestrator.run_new_prep(pdf_path, output_dir=workspace, auto_proceed=True)

    assert orchestrator.show_status(workspace) == ExitCode.SUCCESS


def test_prep_orchestrator__should_return_success__when_resume_called_after_completion(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")
    workspace = tmp_path / "workspace"

    orchestrator = PrepOrchestrator()
    orchestrator.run_new_prep(pdf_path, output_dir=workspace, auto_proceed=True)

    assert orchestrator.resume_prep(workspace, auto_proceed=True) == ExitCode.SUCCESS
```

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep/test_orchestrator.py -k "status or resume" -v`
Expected: FAIL because `show_status()` and `resume_prep()` are not implemented yet.

- [ ] **Step 2: Implement minimal prep status/resume behavior**

```python
def show_status(self, workspace_dir: Path) -> ExitCode:
    prep_paths = build_prep_paths(workspace_dir)
    state = load_prep_state(prep_paths.state)
    if state is None:
        return ExitCode.STATE_ERROR
    self.console.print(f"Prep status: {state.status.value}")
    return ExitCode.SUCCESS


def resume_prep(self, workspace_dir: Path, auto_proceed: bool = False) -> ExitCode:
    prep_paths = build_prep_paths(workspace_dir)
    state = load_prep_state(prep_paths.state)
    if state is None:
        return ExitCode.STATE_ERROR
    if state.status == PrepStatus.COMPLETED and prep_paths.complete.exists():
        return ExitCode.SUCCESS
    return ExitCode.SUCCESS
```

- [ ] **Step 3: Run the prep-focused verification suite**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep tests/unit/test_cli.py -k "prep or analyze_and_prep" -v`
Expected: PASS

- [ ] **Step 4: Run lint, typecheck, and targeted verification**

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- ruff check src/gm_kit/pdf_convert/prep tests/unit/pdf_convert/prep src/gm_kit/cli.py tests/unit/test_cli.py`
Expected: PASS

Run: `uv run --python "$(cat .python-version)" --extra dev --editable -- mypy src/gm_kit/pdf_convert/prep src/gm_kit/cli.py tests/unit/pdf_convert/prep tests/unit/test_cli.py`
Expected: PASS

- [ ] **Step 5: Record the implementation handoff**

Append a journal entry to `specs/e7-02-analyze-and-prep-command-skeleton/feature_journal.md` covering:
- files added and modified
- artifact contract shape delivered
- current prep command capabilities
- deferred items left for E7-03

- [ ] **Step 6: Commit the verified E7-02 skeleton**

```bash
git add src/gm_kit/cli.py \
  src/gm_kit/pdf_convert/prep \
  tests/unit/pdf_convert/prep \
  tests/unit/test_cli.py \
  specs/e7-02-analyze-and-prep-command-skeleton/feature_journal.md
git commit -m "feat(prep): add analyze-and-prep command skeleton"
```

---

## Self-Review

- Spec coverage is complete for the approved E7-02 design: CLI command, prep helper/orchestrator separation, workspace `prep/` subtree, contract artifacts, independent prep state, deterministic skeleton logging, and non-interactive routing are all covered by the task sequence above.
- No placeholders remain; every task names exact files, concrete test code, concrete implementation targets, and explicit verification commands.
- Type and naming consistency are maintained across the plan: `PrepManifest`, `PrepRunState`, `PrepOrchestrator`, and `run_analyze_and_prep_command()` are introduced once and reused consistently.
