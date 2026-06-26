# E7-09 Conversion Pipeline Key-Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace numeric step coupling in the conversion pipeline with stable key-based identity and key-based step workspaces, while keeping numeric ids only for display.

**Architecture:** Introduce a small shared identity layer for conversion steps, then move the orchestrator, agent runtime, and phase logic onto that identity instead of folder names or numeric parsing. Keep the user-facing logs readable with display ids, but make the persisted/resume identity and workspace layout key-driven end to end.

**Tech Stack:** Python 3.13, `typer`, `pathlib`, `dataclasses`, `pytest`, `ruff`

---

## File Map

- Create: `src/gm_kit/pdf_convert/step_identity.py`
- Modify: `src/gm_kit/pdf_convert/agents/agent_step.py`
- Modify: `src/gm_kit/pdf_convert/agents/base.py`
- Modify: `src/gm_kit/pdf_convert/agents/registry.py`
- Modify: `src/gm_kit/pdf_convert/agents/runtime.py`
- Modify: `src/gm_kit/pdf_convert/phases/base.py`
- Modify: `src/gm_kit/pdf_convert/phases/phase9.py`
- Modify: `src/gm_kit/pdf_convert/phases/phase10.py`
- Modify: `src/gm_kit/pdf_convert/orchestrator.py`
- Modify: `src/gm_kit/pdf_convert/state.py`
- Modify: `devtools/scripts/live_handoff_harness.py`
- Modify: `devtools/scripts/README.md`
- Modify: `tests/unit/pdf_convert/agents/test_agent_step.py`
- Modify: `tests/unit/pdf_convert/agents/test_base.py`
- Modify: `tests/unit/pdf_convert/agents/test_registry.py`
- Modify: `tests/unit/pdf_convert/agents/test_runtime.py`
- Modify: `tests/unit/pdf_convert/test_orchestrator.py`
- Modify: `tests/unit/pdf_convert/test_phase9.py`
- Modify: `tests/unit/pdf_convert/test_phase10.py`
- Modify: `tests/unit/pdf_convert/test_state.py`
- Modify: `tests/unit/pdf_convert/test_cli_args.py` only if CLI validation changes as a side effect
- Modify: `tests/unit/test_live_handoff_harness.py`

---

### Task 1: Add shared conversion step identity helpers

**Files:**
- Create: `src/gm_kit/pdf_convert/step_identity.py`
- Test: `tests/unit/pdf_convert/test_step_identity.py`

- [ ] **Step 1: Write the failing test**

```python
def test_step_identity__should_build_workspace_slug__when_given_display_and_key():
    identity = StepIdentity(
        step_key="text-flow-assessment",
        display_id="9.3",
        display_name="Text flow assessment",
        phase=9,
    )

    assert identity.workspace_slug == "text-flow-assessment"
    assert identity.display_label == "9.3"
    assert identity.workspace_path(Path("/tmp/work")).as_posix().endswith(
        "agent_steps/phase_9/text-flow-assessment"
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/unit/pdf_convert/test_step_identity.py -q`
Expected: fail because `StepIdentity` and its helpers do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StepIdentity:
    step_key: str
    display_id: str
    display_name: str
    phase: int

    @property
    def workspace_slug(self) -> str:
        return self.step_key

    @property
    def display_label(self) -> str:
        return self.display_id

    def workspace_path(self, output_dir: Path) -> Path:
        return output_dir / "agent_steps" / f"phase_{self.phase}" / self.workspace_slug
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/pdf_convert/test_step_identity.py -q`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/step_identity.py tests/unit/pdf_convert/test_step_identity.py
git commit -m "feat: add conversion step identity helpers"
```

### Task 2: Move agent handoff workspaces to key-based names

**Files:**
- Modify: `src/gm_kit/pdf_convert/agents/agent_step.py`
- Modify: `src/gm_kit/pdf_convert/agents/runtime.py`
- Modify: `tests/unit/pdf_convert/agents/test_agent_step.py`
- Modify: `tests/unit/pdf_convert/agents/test_runtime.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_write_agent_inputs__should_create_key_based_workspace__when_step_is_text_flow():
    step_dir = write_agent_inputs(
        step_key="text-flow-assessment",
        workspace=str(tmp_path),
        inputs={
            "phase": 9,
            "display_id": "9.3",
            "display_name": "Text flow / readability assessment",
        },
    )

    assert step_dir.name == "text-flow-assessment"
    assert step_dir.parent.name == "phase_9"
```

```python
def test_runtime__should_resolve_key_based_step_dir__when_step_key_is_text_flow():
    runtime = AgentStepRuntime(str(tmp_path))

    assert runtime._step_dir("text-flow-assessment").name == "text-flow-assessment"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`pytest tests/unit/pdf_convert/agents/test_agent_step.py tests/unit/pdf_convert/agents/test_runtime.py -q`
Expected: failures because step directories still derive from numeric ids.

- [ ] **Step 3: Write the minimal implementation**

```python
from gm_kit.pdf_convert.step_identity import StepIdentity


def write_agent_inputs(step_key: str, workspace: str, inputs: dict[str, Any], attempt: int = 1) -> Path:
    identity = StepIdentity(
        step_key=step_key,
        display_id=inputs["display_id"],
        display_name=inputs["display_name"],
        phase=inputs["phase"],
    )
    step_dir = identity.workspace_path(Path(workspace))
```

```python
def _step_dir(self, step_key: str) -> Path:
    step_def = self.registry.get(step_key)
    return Path(self.workspace) / "agent_steps" / f"phase_{step_def.phase}" / step_def.workspace_slug
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`pytest tests/unit/pdf_convert/agents/test_agent_step.py tests/unit/pdf_convert/agents/test_runtime.py -q`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/agents/agent_step.py src/gm_kit/pdf_convert/agents/runtime.py tests/unit/pdf_convert/agents/test_agent_step.py tests/unit/pdf_convert/agents/test_runtime.py
git commit -m "feat: key conversion agent workspaces"
```

### Task 3: Convert the phase 9 and phase 10 steps to stable keys

**Files:**
- Modify: `src/gm_kit/pdf_convert/phases/base.py`
- Modify: `src/gm_kit/pdf_convert/phases/phase9.py`
- Modify: `src/gm_kit/pdf_convert/phases/phase10.py`
- Modify: `src/gm_kit/pdf_convert/agents/registry.py`
- Modify: `tests/unit/pdf_convert/test_phase9.py`
- Modify: `tests/unit/pdf_convert/test_phase10.py`
- Modify: `tests/unit/pdf_convert/agents/test_registry.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_phase9__should_use_display_ids_for_logging__when_agent_steps_execute():
    result = phase.execute(output_dir, pdf_path)

    assert any(step.step_id == "9.3" for step in result.steps)
    assert any("text flow" in step.description.lower() for step in result.steps)
```

```python
def test_registry__should_expose_step_key_and_display_id__when_loading_phase9_step():
    step = get_step_registry().get("text-flow-assessment")

    assert step.step_key == "text-flow-assessment"
    assert step.display_id == "9.3"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`pytest tests/unit/pdf_convert/test_phase9.py tests/unit/pdf_convert/test_phase10.py tests/unit/pdf_convert/agents/test_registry.py -q`
Expected: failures because the registry still treats numeric ids as the only identity.

- [ ] **Step 3: Write the minimal implementation**

```python
@dataclass(frozen=True)
class AgentStepDefinition:
    step_key: str
    display_id: str
    phase: int
    description: str
    criticality: Criticality
    instruction_template: str
    contract_schema: str
    rubric_id: str | None = None
    workspace_slug: str | None = None
```

```python
steps_to_execute = [
    ("text-flow-assessment", "9.3", "Text flow / readability assessment"),
]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`pytest tests/unit/pdf_convert/test_phase9.py tests/unit/pdf_convert/test_phase10.py tests/unit/pdf_convert/agents/test_registry.py -q`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/phases/base.py src/gm_kit/pdf_convert/phases/phase9.py src/gm_kit/pdf_convert/phases/phase10.py src/gm_kit/pdf_convert/agents/registry.py tests/unit/pdf_convert/test_phase9.py tests/unit/pdf_convert/test_phase10.py tests/unit/pdf_convert/agents/test_registry.py
git commit -m "feat: migrate conversion steps to stable keys"
```

### Task 4: Persist and resume conversion state by step key

**Files:**
- Modify: `src/gm_kit/pdf_convert/state.py`
- Modify: `src/gm_kit/pdf_convert/orchestrator.py`
- Modify: `tests/unit/pdf_convert/test_state.py`
- Modify: `tests/unit/pdf_convert/test_orchestrator.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_conversion_state__should_persist_current_step_key__when_serialized():
    state = ConversionState(pdf_path="/tmp/input.pdf", output_dir="/tmp/out")
    state.current_step_key = "text-flow-assessment"

    data = state.to_dict()

    assert data["current_step_key"] == "text-flow-assessment"
```

```python
def test_orchestrator__should_resume_by_step_key__when_state_contains_key():
    exit_code = orchestrator.run_from_step(output_dir, "text-flow-assessment")

    assert exit_code == ExitCode.SUCCESS
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`pytest tests/unit/pdf_convert/test_state.py tests/unit/pdf_convert/test_orchestrator.py -q`
Expected: failures because the state model and resume path still assume numeric step ids.

- [ ] **Step 3: Write the minimal implementation**

```python
class ConversionState:
    current_step_key: str = "prep.initialize-workspace"
    current_step_display: str = "0.1"
```

```python
def run_from_step(self, output_dir: Path, step_key: str, auto_proceed: bool = False, agent_debug: bool | None = None) -> ExitCode:
    step = self.registry.get(step_key)
    state.current_step_key = step_key
    state.current_step_display = step.display_id
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`pytest tests/unit/pdf_convert/test_state.py tests/unit/pdf_convert/test_orchestrator.py -q`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/state.py src/gm_kit/pdf_convert/orchestrator.py tests/unit/pdf_convert/test_state.py tests/unit/pdf_convert/test_orchestrator.py
git commit -m "feat: resume conversion by stable step key"
```

### Task 5: Update harness docs and validation for key-based step folders

**Files:**
- Modify: `devtools/scripts/live_handoff_harness.py`
- Modify: `devtools/scripts/README.md`
- Modify: `tests/unit/pdf_convert/test_cli_args.py` only if command-line validation changes

- [ ] **Step 1: Write the failing test**

```python
def test_live_handoff_harness__should_parse_key_based_step_dir__when_agent_pauses():
    step_dir = Path("/tmp/run/agent_steps/phase_9/text-flow-assessment")

    assert parse_pause_step_dir(f"Paused in `{step_dir}`.") == step_dir
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
`pytest tests/unit/test_live_handoff_harness.py -q`
Expected: failure because the harness still expects numeric `step_9_3` paths.

- [ ] **Step 3: Write the minimal implementation**

```python
PAUSE_STEP_RE = re.compile(r"`([^`]*agent_steps/phase_\d+/[^`]*)`")

def step_id_from_dir(step_dir: Path) -> str:
    return step_dir.name
```

- [ ] **Step 4: Run the test to verify it passes**

Run:
`pytest tests/unit/test_live_handoff_harness.py -q`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add devtools/scripts/live_handoff_harness.py devtools/scripts/README.md tests/unit/test_live_handoff_harness.py
git commit -m "feat: support key-based harness step folders"
```

### Task 6: Run the focused verification set

**Files:**
- No new files; verify the completed changeset

- [ ] **Step 1: Run the narrow test set**

Run:
`pytest tests/unit/pdf_convert/test_step_identity.py tests/unit/pdf_convert/agents/test_agent_step.py tests/unit/pdf_convert/agents/test_runtime.py tests/unit/pdf_convert/agents/test_registry.py tests/unit/pdf_convert/test_phase9.py tests/unit/pdf_convert/test_phase10.py tests/unit/pdf_convert/test_state.py tests/unit/pdf_convert/test_orchestrator.py -q`

- [ ] **Step 2: Run the repository quality checks that touch the modified areas**

Run:
`just lint`

- [ ] **Step 3: Run type checks**

Run:
`just typecheck`

- [ ] **Step 4: Run the targeted conversion tests or harness checks**

Run:
`pytest tests/unit/pdf_convert -q`

- [ ] **Step 5: Commit any last cleanup**

```bash
git add -A
git commit -m "feat: complete conversion key-migration cleanup"
```
