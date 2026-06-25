# E7-07 Convert Gating + Prep Artifact Consumption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `gmkit pdf-convert` consume prep artifacts when available, prefer reviewed prep guidance when present, and bootstrap missing baseline prep outputs so the legacy conversion command still works end-to-end.

**Architecture:** Add a small prep-artifact resolution layer that selects the effective guidance artifact by precedence and makes the bootstrap fallback explicit. The orchestrator uses that resolver up front so prep-backed conversion is preferred, while phase consumers keep reading guidance through the same shared loader path and naturally see reviewed guidance when it exists.

**Tech Stack:** Python 3.13, Typer CLI, existing conversion orchestrator, existing prep artifact loaders/contracts, pytest.

---

### Task 1: Add prep artifact resolution helpers

**Files:**
- Create: `src/gm_kit/pdf_convert/prep/resolution.py`
- Modify: `src/gm_kit/pdf_convert/prep/analysis_artifacts.py`
- Modify: `src/gm_kit/pdf_convert/prep/__init__.py`
- Test: `tests/unit/pdf_convert/prep/test_resolution.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_effective_prep_resolution__should_choose_reviewed_guidance__when_reviewed_exists(tmp_path):
    workspace = tmp_path / "output"
    prep_root = workspace / "prep"
    prep_root.mkdir(parents=True)
    (prep_root / "prep-guidance.resolved.json").write_text("{}")
    (prep_root / "prep-guidance.reviewed.json").write_text("{}")

    paths = build_effective_prep_artifact_paths(workspace, pdf_stem="source")

    assert paths.effective_guidance == prep_root / "prep-guidance.reviewed.json"
```

Add a second test that creates the baseline artifacts without `prep-guidance.reviewed.json` and asserts the effective guidance falls back to `prep-guidance.resolved.json`.

```python
def test_effective_prep_resolution__should_fall_back_to_baseline_guidance__when_reviewed_missing(tmp_path):
    workspace = tmp_path / "output"
    prep_root = workspace / "prep"
    prep_root.mkdir(parents=True)
    (prep_root / "prep-guidance.resolved.json").write_text("{}")

    paths = build_effective_prep_artifact_paths(workspace, pdf_stem="source")

    assert paths.effective_guidance == prep_root / "prep-guidance.resolved.json"
```

- [ ] **Step 2: Run the targeted tests**

Run: `pytest tests/unit/pdf_convert/prep/test_resolution.py -q`
Expected: failure because the resolution helper does not yet exist.

- [ ] **Step 3: Implement the prep resolution layer**

```python
@dataclass(frozen=True)
class EffectivePrepArtifactPaths:
    analysis: PrepAnalysisArtifactPaths
    effective_guidance: Path


def build_effective_prep_artifact_paths(
    workspace_dir: Path,
    pdf_stem: str,
) -> EffectivePrepArtifactPaths:
    analysis = build_analysis_artifact_paths(workspace_dir, pdf_stem=pdf_stem)
    effective_guidance = (
        analysis.reviewed_guidance
        if analysis.reviewed_guidance.exists()
        else analysis.guidance_resolved
    )
    return EffectivePrepArtifactPaths(analysis=analysis, effective_guidance=effective_guidance)
```

Add a helper that validates the baseline conversion contract and returns the missing artifact names in a deterministic order for reporting when prep artifacts are already present but malformed or incomplete.

- [ ] **Step 4: Re-run the targeted tests**

Run: `pytest tests/unit/pdf_convert/prep/test_resolution.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/prep/resolution.py src/gm_kit/pdf_convert/prep/analysis_artifacts.py src/gm_kit/pdf_convert/prep/__init__.py tests/unit/pdf_convert/prep/test_resolution.py
git commit -m "feat: add prep artifact resolution helpers"
```

### Task 2: Bootstrap conversion startup from prep or baseline inputs

**Files:**
- Modify: `src/gm_kit/pdf_convert/orchestrator.py`
- Modify: `src/gm_kit/pdf_convert/cli_helpers.py`
- Modify: `src/gm_kit/pdf_convert/preflight.py`
- Test: `tests/unit/pdf_convert/test_orchestrator.py`
- Test: `tests/unit/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Add tests that prove conversion bootstraps baseline metadata/preflight outputs when prep artifacts are absent and prefers prep-backed inputs when they are present.

```python
def test_run_new_conversion__should_bootstrap_baseline_outputs__when_prep_workspace_missing(tmp_path):
    pdf_path = tmp_path / "source.pdf"
    pdf_path.touch()
    orchestrator = Orchestrator()

    exit_code = orchestrator.run_new_conversion(pdf_path, output_dir=tmp_path / "output")

    assert exit_code == ExitCode.FILE_ERROR
```

Add a second test that creates `prep/prep-guidance.resolved.json` plus the other required baseline artifacts and asserts that startup reaches the existing conversion flow.

- [ ] **Step 2: Run the targeted tests**

Run: `pytest tests/unit/pdf_convert/test_orchestrator.py -k prep_workspace -v`
Expected: failure until startup bootstrapping and artifact selection are enforced before phase execution.

- [ ] **Step 3: Wire the prep-first startup loader**

```python
effective_paths = build_effective_prep_artifact_paths(output_dir, pdf_path.stem)
report = run_preflight(
    pdf_path,
    self.console,
    auto_proceed,
    output_dir,
    gm_callout_config_file,
    preflight_report_path=(
        effective_paths.analysis.preflight_report
        if effective_paths.analysis.preflight_report.exists()
        else None
    ),
)
```

Keep the startup behavior prep-first, but allow the command to bootstrap baseline analysis outputs when prep artifacts are absent.

- [ ] **Step 4: Re-run the targeted tests**

Run: `pytest tests/unit/pdf_convert/test_orchestrator.py tests/unit/test_cli.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/orchestrator.py src/gm_kit/pdf_convert/cli_helpers.py src/gm_kit/pdf_convert/preflight.py tests/unit/pdf_convert/test_orchestrator.py tests/unit/test_cli.py
git commit -m "feat: gate conversion on prep workspace validity"
```

### Task 3: Align phase consumers with reviewed-or-baseline guidance

**Files:**
- Modify: `src/gm_kit/pdf_convert/phases/phase8.py`
- Modify: `src/gm_kit/pdf_convert/phases/phase9.py`
- Modify: `src/gm_kit/pdf_convert/phases/phase10.py`
- Test: `tests/unit/pdf_convert/test_phase8.py`
- Test: `tests/unit/pdf_convert/test_phase9.py`
- Test: `tests/unit/pdf_convert/test_phase10.py`

- [ ] **Step 1: Write the failing tests**

Add regression tests that prove each phase uses the effective prep guidance path and prefers reviewed guidance when it exists.

```python
def test_phase8__should_use_reviewed_guidance__when_reviewed_artifact_exists(tmp_path):
    phase = Phase8()
    pdf_path = tmp_path / "source.pdf"
    pdf_path.touch()
    state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)
    (tmp_path / "source-phase6.md").write_text("Content")
    prep_root = tmp_path / "prep"
    prep_root.mkdir(parents=True)
    (prep_root / "prep-guidance.resolved.json").write_text(
        json.dumps({"skip_pages": [], "skip_regions": [], "table_regions": [], "callout_regions": []})
    )
    (prep_root / "prep-guidance.reviewed.json").write_text(
        json.dumps(
            {
                "skip_pages": [],
                "skip_regions": [],
                "table_regions": [
                    {"page": 2, "bbox": [1.0, 2.0, 3.0, 4.0], "proposal_id": "reviewed"}
                ],
                "callout_regions": [],
            }
        )
    )

    captured_inputs = {}

    def _execute(step_id, inputs):
        if step_id == "8.7":
            captured_inputs[step_id] = inputs
        envelope = MagicMock()
        envelope.data = {"score": 5}
        envelope.rubric_scores = {"overall": 5}
        return envelope, MagicMock()

    mock_agent_step_runtime.return_value.execute_step.side_effect = _execute
    phase.execute(state)

    assert captured_inputs["8.7"]["context"]["prep_guidance"]["table_regions"][0]["proposal_id"] == "reviewed"
```

Add matching tests for phase 9 and phase 10 that confirm reviewed guidance is preferred for agent payloads and baseline guidance remains the fallback. Use the same workspace setup and assert the captured `prep_guidance` payload contains the reviewed `proposal_id` when both files exist.

- [ ] **Step 2: Run the targeted tests**

Run: `pytest tests/unit/pdf_convert/test_phase8.py tests/unit/pdf_convert/test_phase9.py tests/unit/pdf_convert/test_phase10.py -q`
Expected: failure where any phase still uses the wrong guidance source or misses the fallback behavior.

- [ ] **Step 3: Normalize the shared guidance loader usage**

```python
effective_paths = build_effective_prep_artifact_paths(output_dir, pdf_name)
prep_guidance = load_effective_prep_guidance(effective_paths.analysis).to_dict()
```

Keep the phase logic unchanged beyond the guidance source swap. The phases should still fail clearly when the underlying prep guidance file is malformed, but they should not rediscover prep data themselves.

- [ ] **Step 4: Re-run the targeted tests**

Run: `pytest tests/unit/pdf_convert/test_phase8.py tests/unit/pdf_convert/test_phase9.py tests/unit/pdf_convert/test_phase10.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gm_kit/pdf_convert/phases/phase8.py src/gm_kit/pdf_convert/phases/phase9.py src/gm_kit/pdf_convert/phases/phase10.py tests/unit/pdf_convert/test_phase8.py tests/unit/pdf_convert/test_phase9.py tests/unit/pdf_convert/test_phase10.py
git commit -m "feat: prefer reviewed prep guidance during conversion"
```

### Task 4: Update docs and handoff notes

**Files:**
- Modify: `BACKLOG.md`
- Modify: `docs/user/user_guide.md`
- Modify: `specs/e7-07-convert-gating-prep-artifact-consumption/feature_journal.md`

- [ ] **Step 1: Write the failing docs checks**

Update any existing CLI or user-facing help tests that mention conversion startup so they describe prep-first gating and the reviewed-versus-baseline fallback.

- [ ] **Step 2: Update the docs**

Document the conversion contract in the user guide:
1. run prep for the richest artifact set
2. let conversion bootstrap baseline metadata/preflight outputs when prep artifacts are absent
3. run conversion
4. let conversion use `prep-guidance.reviewed.json` when present, otherwise `prep-guidance.resolved.json`
5. treat reviewed guidance as optional and baseline guidance as the conversion fallback

Update `BACKLOG.md` to reflect that E7-07 is about prep artifact consumption and startup gating, not callout discovery.

- [ ] **Step 3: Update the feature journal**

Append a session entry recording the prep-first bootstrap policy, the reviewed fallback policy, and the fact that legacy callout-config removal is deferred.

- [ ] **Step 4: Re-run the narrowest relevant checks**

Run: `just lint` and `just test` if the touched area is small enough to validate directly; otherwise run the focused pytest slices used above.
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add BACKLOG.md docs/user/user_guide.md specs/e7-07-convert-gating-prep-artifact-consumption/feature_journal.md
git commit -m "docs: record E7-07 prep gating contract"
```

## Coverage Check

- Prep artifact resolution helpers: Task 1
- Fail-fast conversion startup gating: Task 2
- Reviewed-versus-baseline guidance consumption: Task 3
- User docs and feature handoff notes: Task 4

## Risks

- The existing conversion flow still creates and resumes state in a way that assumes direct PDF input; startup gating needs to be added without breaking resume behavior.
- `phase8`, `phase9`, and `phase10` already have prep-guidance loaders, so the main risk is changing the source of truth inconsistently across phases.
- Legacy `gm_callout_config_file` plumbing stays in scope for a later refactor; do not remove it in this feature.
