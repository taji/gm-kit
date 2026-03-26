"""Integration tests for agent pipeline pause/resume and step handoff."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from gm_kit.pdf_convert.agents.agent_step import write_agent_inputs
from gm_kit.pdf_convert.agents.base import AgentStepOutputEnvelope, StepStatus
from gm_kit.pdf_convert.agents.errors import AgentStepError
from gm_kit.pdf_convert.agents.runtime import AgentStepRuntime
from gm_kit.pdf_convert.phases.phase7 import Phase7
from gm_kit.pdf_convert.phases.phase8 import Phase8
from gm_kit.pdf_convert.phases.phase9 import Phase9
from gm_kit.pdf_convert.state import ConversionState

pytestmark = pytest.mark.integration

HOME_BREWERY_PDF = (
    Path(__file__).resolve().parents[4]
    / "tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.pdf"
)


def _step_status(result: Any, step_id: str) -> str:
    for step in result.steps:
        if step.step_id == step_id:
            return step.status.value
    raise AssertionError(f"Step {step_id} not found in result")


class TestAgentPipelineIntegration:
    """Integration coverage for pause/resume and 7.7 -> 8.7 -> 9.4/9.5 handoff."""

    @pytest.fixture
    def workspace(self, tmp_path: Path) -> Path:
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def test_pause_resume__should_require_output_then_complete__when_output_written(
        self, workspace: Path
    ) -> None:
        """Runtime resume fails without output, then succeeds when output exists."""
        runtime = AgentStepRuntime(str(workspace))

        write_agent_inputs(
            step_id="3.2",
            workspace=str(workspace),
            inputs={"source_pdf": "dummy.pdf", "toc_page_image": "toc.png"},
            attempt=1,
        )

        with pytest.raises(AgentStepError, match="step-output.json"):
            runtime.resume_step("3.2")

        output_file = workspace / "agent_steps" / "step_3_2" / "step-output.json"
        output_file.write_text(
            json.dumps(
                {
                    "step_id": "3.2",
                    "status": "success",
                    "data": {"toc_entries": ["Chapter One (page 4)"]},
                    "warnings": [],
                    "rubric_scores": {
                        "completeness": 5,
                        "level_accuracy": 5,
                        "page_accuracy": 5,
                        "output_format": 5,
                    },
                }
            ),
            encoding="utf-8",
        )

        envelope, status = runtime.resume_step("3.2")
        assert envelope is not None
        assert status == StepStatus.COMPLETED
        assert envelope.step_id == "3.2"
        assert envelope.data["toc_entries"] == ["Chapter One (page 4)"]

        state_json = json.loads((workspace / ".state.json").read_text(encoding="utf-8"))
        assert state_json["current_step"] == "3.2"
        assert state_json["agent_step_status"] == "COMPLETED"

    def test_handoff_7_7_to_8_7_to_9_5__should_produce_expected_artifacts(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Run Phase 7/8/9 with mocked agent runtime and verify handoff artifacts."""
        if not HOME_BREWERY_PDF.exists():
            pytest.skip(f"Fixture not available: {HOME_BREWERY_PDF}")

        pdf_name = HOME_BREWERY_PDF.stem
        phase6_file = workspace / f"{pdf_name}-phase6.md"
        phase6_file.write_text(
            "\n".join(
                [
                    "<!-- Page 1 -->",
                    "«sig001:INTRODUCTION»",
                    "",
                    "<!-- Page 2 -->",
                    "Example",
                    "Head A Head B",
                    "1A 2A",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        (workspace / "font-family-mapping.json").write_text(
            json.dumps(
                {
                    "version": "1.0",
                    "signatures": [
                        {
                            "id": "sig001",
                            "size": 14,
                            "label": "H1",
                            "family": "Times",
                            "weight": 400,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        (workspace / "toc-extracted.txt").write_text("Introduction (page 1)\n", encoding="utf-8")

        state = ConversionState(
            pdf_path=str(HOME_BREWERY_PDF),
            output_dir=str(workspace),
            config={},
        )

        def fake_execute_step(
            self: AgentStepRuntime, step_id: str, inputs: dict[str, Any], attempt: int = 1
        ):
            # Normalise paged step IDs (e.g. 7.7_p1, 7.7_p2) to base ID for routing.
            base_step_id = step_id.split("_p")[0] if "_p" in step_id else step_id
            if base_step_id == "7.7":
                if inputs.get("phase") == "text_scan":
                    if inputs.get("page_number_1based") == 2:
                        return (
                            AgentStepOutputEnvelope(
                                step_id="7.7",
                                status="success",
                                data={
                                    "tables_detected": True,
                                    "tables": [
                                        {
                                            "table_id": "page_002_table_001",
                                            "text_context": "Head A Head B",
                                        }
                                    ],
                                },
                                warnings=[],
                            ),
                            StepStatus.COMPLETED,
                        )
                    return (
                        AgentStepOutputEnvelope(
                            step_id="7.7",
                            status="success",
                            data={"tables_detected": False, "tables": []},
                            warnings=[],
                        ),
                        StepStatus.COMPLETED,
                    )
                return (
                    AgentStepOutputEnvelope(
                        step_id="7.7",
                        status="success",
                        data={"bbox_pixels": {"x0": 100, "y0": 100, "x1": 450, "y1": 280}},
                        warnings=[],
                    ),
                    StepStatus.COMPLETED,
                )

            if base_step_id == "8.7":
                return (
                    AgentStepOutputEnvelope(
                        step_id="8.7",
                        status="success",
                        data={
                            "markdown_table": "\n".join(
                                [
                                    "| Col A | Col B |",
                                    "| --- | --- |",
                                    "| 1A | 2A |",
                                ]
                            )
                        },
                        warnings=[],
                    ),
                    StepStatus.COMPLETED,
                )

            if base_step_id in {"9.2", "9.3", "9.4", "9.5", "9.7", "9.8"}:
                return (
                    AgentStepOutputEnvelope(
                        step_id=step_id,
                        status="success",
                        data={"score": 4},
                        warnings=[],
                    ),
                    StepStatus.COMPLETED,
                )

            raise AssertionError(f"Unexpected step call: {step_id} (base: {base_step_id})")

        monkeypatch.setattr(AgentStepRuntime, "execute_step", fake_execute_step)

        phase7_result = Phase7().execute(state)
        assert _step_status(phase7_result, "7.7") == "success"

        tables_manifest = workspace / "tables-manifest.json"
        assert tables_manifest.exists()
        manifest_data = json.loads(tables_manifest.read_text(encoding="utf-8"))
        assert manifest_data["total_count"] >= 1
        assert manifest_data["tables"][0]["table_id"] == "page_002_table_001"
        assert (workspace / "page_images" / "page_002.png").exists()

        phase8_result = Phase8().execute(state)
        assert _step_status(phase8_result, "8.7") == "success"

        phase8_file = workspace / f"{pdf_name}-phase8.md"
        assert phase8_file.exists()
        phase8_text = phase8_file.read_text(encoding="utf-8")
        assert "| Col A | Col B |" in phase8_text
        assert (workspace / "table_crops" / "page_002_table_001_crop.png").exists()

        phase9_result = Phase9().execute(state)
        assert _step_status(phase9_result, "9.4") == "success"
        assert _step_status(phase9_result, "9.5") == "success"
        assert not phase9_result.is_error
