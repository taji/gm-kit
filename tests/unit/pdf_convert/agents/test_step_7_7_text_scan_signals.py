"""Unit harness for probing Step 7.7 text-scan heuristics without hitting the full agent."""

# NOTE: This test simulates the table-detection cues deterministically.
# It is meant for heuristic tuning only and does not invoke an actual agent;
# keep it out of CI until it proves value and cost-efficiency.

from __future__ import annotations

from pathlib import Path

from gm_kit.pdf_convert.agents.instructions.step_7_7 import build_text_scan_prompt

FIXTURE_ROOT = Path(__file__).resolve().parents[3] / "fixtures" / "pdf_convert"
HOME_BREWERY_MD = FIXTURE_ROOT / "The Homebrewery - NaturalCrit - To Render To Pdf.md"
HOME_BREWERY_PHASE4 = FIXTURE_ROOT / "agents" / "inputs" / "step_7_7" / "Homebrewery_WeaponsTable_Phase4.md"


def _parse_sig_lines(text: str) -> list[tuple[str, str]]:
    entries = []
    for line in (line.strip() for line in text.splitlines()):
        if not line or not line.startswith("«sig"):
            continue
        closing = line.rfind("»")
        if closing == -1:
            continue
        body = line[4:closing]
        sig, sep, content = body.partition(":")
        if sep != ":" or not sig or not content:
            continue
        sig = sig.lstrip("0") or sig
        entries.append((sig, content.strip()))
    return entries


def _simulate_text_scan(extracted_text: str, page_num: int = 2) -> dict[str, object]:
    entries = _parse_sig_lines(extracted_text)
    header_sig = "12"
    row_sig = "11"
    column_headers = [entry for entry in entries if entry[0] == header_sig]
    total_sig011 = sum(1 for sig, _ in entries if sig == row_sig)
    column_count = len(column_headers) if column_headers else 3
    repeated_rows = total_sig011 // column_count

    grammar_rows = repeated_rows

    signal_score = 0
    if column_headers:
        signal_score += 40
    signal_score += min(30, repeated_rows * 10)
    signal_score += min(20, grammar_rows * 3)

    result = {
        "step_id": "7.7",
        "status": "success",
        "data": {
            "page_number": page_num,
            "table_likelihood": min(100, signal_score),
            "likely_tables": max(0, repeated_rows),
            "table_likelihood_score": signal_score,
            "tables_detected": bool(signal_score >= 60 and column_headers and repeated_rows >= 2),
            "text_indicators": [
                name
                for name, present in [
                    ("column_headers", bool(column_headers)),
                    ("repeating_rows", repeated_rows >= 2),
                    ("grammar_break_row", grammar_rows >= 1 and bool(column_headers)),
                ]
                if present
            ],
        },
        "rubric_scores": {"detection_recall": 5, "detection_precision": 5, "boundary_accuracy": 5},
        "warnings": [],
    }
    return result


def _load_intro_snippet() -> str:
    full_text = HOME_BREWERY_MD.read_text(encoding="utf-8")
    return full_text.split("### Tables")[0]


def test_homebrewery_markdown_signals_table_detected() -> None:
    markdown = HOME_BREWERY_PHASE4.read_text(encoding="utf-8")
    prompt = build_text_scan_prompt(markdown, page_num=2)
    assert "Step 7.7" in prompt

    result = _simulate_text_scan(markdown)
    assert result["data"]["tables_detected"] is True
    assert result["data"]["table_likelihood"] >= 70
    assert "column_headers" in result["data"]["text_indicators"]
    assert "grammar_break_row" in result["data"]["text_indicators"]


def test_homebrewery_intro_snippet_not_table() -> None:
    intro = _load_intro_snippet()
    result = _simulate_text_scan(intro, page_num=1)
    assert result["data"]["tables_detected"] is False
    assert result["data"]["table_likelihood"] < 60
    assert "column_headers" not in result["data"]["text_indicators"]
