"""Step artifact factories and input payload builders.

This module provides builders for creating input payloads for each agent step type:
- Content Repair steps (3.2, 4.5, 6.4)
- Quality Assessment steps (9.2-9.5, 9.7-9.8)
- Reporting steps (10.2-10.3)
"""

from pathlib import Path
from typing import Any

MIN_DOMAIN_TERM_LENGTH = 2


def build_content_repair_payload(
    step_id: str, phase_file: str, context: dict[str, Any], workspace: str
) -> dict[str, Any]:
    """Build input payload for content repair steps (3.2, 4.5, 6.4).

    These steps edit the phase file directly.

    Args:
        step_id: Step identifier
        phase_file: Path to phase file to edit
        context: Step-specific context data
        workspace: Conversion workspace

    Returns:
        Input payload for step-input.json
    """
    return {
        "step_id": step_id,
        "input_artifacts": {
            "phase_file": phase_file,
        },
        "optional_artifacts": {},
        "context": {"workspace": workspace, **context},
        "output_contract": f"schemas/step_{step_id.replace('.', '_')}.schema.json",
    }


def build_toc_parsing_payload(toc_text: str, total_pages: int, workspace: str) -> dict[str, Any]:
    """Build input payload for step 3.2 (visual TOC parsing).

    Args:
        toc_text: Text content of TOC page(s)
        total_pages: Total pages in document
        workspace: Conversion workspace

    Returns:
        Input payload for step-input.json
    """
    return build_content_repair_payload(
        step_id="3.2",
        phase_file="",  # TOC doesn't edit phase file
        context={
            "toc_text": toc_text,
            "total_pages": total_pages,
            "task": "parse_visual_toc",
        },
        workspace=workspace,
    )


def build_sentence_boundary_payload(
    phase4_file: str, chunk_boundaries: list[dict], workspace: str
) -> dict[str, Any]:
    """Build input payload for step 4.5 (sentence boundary resolution).

    Args:
        phase4_file: Path to phase4.md file
        chunk_boundaries: List of boundary locations
        workspace: Conversion workspace

    Returns:
        Input payload for step-input.json
    """
    return build_content_repair_payload(
        step_id="4.5",
        phase_file=phase4_file,
        context={
            "chunk_boundaries": chunk_boundaries,
            "task": "resolve_split_sentences",
        },
        workspace=workspace,
    )


def build_ocr_correction_payload(
    phase6_file: str, font_signatures: dict[str, Any], workspace: str
) -> dict[str, Any]:
    """Build input payload for step 6.4 (OCR spelling correction).

    Args:
        phase6_file: Path to phase6.md file
        font_signatures: Font signature mapping for domain term preservation
        workspace: Conversion workspace

    Returns:
        Input payload for step-input.json
    """
    return build_content_repair_payload(
        step_id="6.4",
        phase_file=phase6_file,
        context={
            "font_signatures": font_signatures,
            "preserve_terms": _extract_domain_terms(font_signatures),
            "task": "fix_ocr_spelling",
        },
        workspace=workspace,
    )


def build_quality_assessment_payload(
    step_id: str,
    phase8_file: str,
    context: dict[str, Any],
    workspace: str,
    font_family_mapping: str | None = None,
) -> dict[str, Any]:
    """Build input payload for quality assessment steps (9.2-9.5, 9.7-9.8).

    These steps analyze the full markdown document.

    Args:
        step_id: Step identifier
        phase8_file: Path to phase8.md (final markdown)
        context: Step-specific context
        workspace: Conversion workspace
        font_family_mapping: Optional path to font-family-mapping.json (for 9.7)

    Returns:
        Input payload for step-input.json
    """
    optional = {}
    if font_family_mapping and Path(font_family_mapping).exists():
        optional["font_family_mapping"] = font_family_mapping

    return {
        "step_id": step_id,
        "input_artifacts": {
            "phase8_file": phase8_file,
        },
        "optional_artifacts": optional,
        "context": {"workspace": workspace, **context},
        "output_contract": f"schemas/step_{step_id.replace('.', '_')}.schema.json",
    }


def build_structural_clarity_payload(
    phase8_file: str, toc_file: str, workspace: str
) -> dict[str, Any]:
    """Build input payload for step 9.2 (structural clarity assessment).

    Args:
        phase8_file: Path to phase8.md
        toc_file: Path to toc-extracted.txt
        workspace: Conversion workspace

    Returns:
        Input payload for step-input.json
    """
    return build_quality_assessment_payload(
        step_id="9.2",
        phase8_file=phase8_file,
        context={
            "toc_file": toc_file,
            "task": "assess_structural_clarity",
        },
        workspace=workspace,
    )


def build_text_flow_payload(phase8_file: str, workspace: str) -> dict[str, Any]:
    """Build input payload for step 9.3 (text flow assessment).

    Args:
        phase8_file: Path to phase8.md
        workspace: Conversion workspace

    Returns:
        Input payload for step-input.json
    """
    return build_quality_assessment_payload(
        step_id="9.3",
        phase8_file=phase8_file,
        context={
            "task": "assess_text_flow",
        },
        workspace=workspace,
    )


def build_toc_validation_payload(
    phase8_file: str, toc_file: str, font_family_mapping: str, workspace: str
) -> dict[str, Any]:
    """Build input payload for step 9.7 (TOC validation).

    Args:
        phase8_file: Path to phase8.md
        toc_file: Path to toc-extracted.txt
        font_family_mapping: Path to font-family-mapping.json
        workspace: Conversion workspace

    Returns:
        Input payload for step-input.json
    """
    return build_quality_assessment_payload(
        step_id="9.7",
        phase8_file=phase8_file,
        context={
            "toc_file": toc_file,
            "task": "validate_toc",
        },
        workspace=workspace,
        font_family_mapping=font_family_mapping,
    )


def build_reading_order_payload(
    phase8_file: str, pdf_metadata: dict | None, workspace: str
) -> dict[str, Any]:
    """Build input payload for step 9.8 (reading order review).

    Args:
        phase8_file: Path to phase8.md
        pdf_metadata: Page layout metadata (if available)
        workspace: Conversion workspace

    Returns:
        Input payload for step-input.json
    """
    return build_quality_assessment_payload(
        step_id="9.8",
        phase8_file=phase8_file,
        context={
            "pdf_metadata": pdf_metadata or {},
            "task": "review_reading_order",
        },
        workspace=workspace,
    )


def build_reporting_payload(
    step_id: str, assessment_results: dict[str, Any], workspace: str
) -> dict[str, Any]:
    """Build input payload for reporting steps (10.2, 10.3).

    These steps aggregate quality assessment results.

    Args:
        step_id: Step identifier
        assessment_results: Results from quality assessment steps
        workspace: Conversion workspace

    Returns:
        Input payload for step-input.json
    """
    return {
        "step_id": step_id,
        "input_artifacts": {},
        "optional_artifacts": {},
        "context": {
            "workspace": workspace,
            "assessment_results": assessment_results,
            "task": "generate_report" if step_id == "10.2" else "document_issues",
        },
        "output_contract": f"schemas/step_{step_id.replace('.', '_')}.schema.json",
    }


def _extract_domain_terms(font_signatures: dict[str, Any]) -> list[str]:
    """Extract TTRPG domain terms from font signatures for preservation.

    Args:
        font_signatures: Font signature mapping

    Returns:
        List of terms to preserve
    """
    terms = set()

    # Common TTRPG abbreviations
    terms.update(
        [
            "AC",
            "HP",
            "DC",
            "STR",
            "DEX",
            "CON",
            "INT",
            "WIS",
            "CHA",
            "THAC0",
            "XP",
            "GP",
            "SP",
            "CP",
            "PP",
            "EP",
            "DM",
            "GM",
            "PC",
            "NPC",
            "BBEG",
        ]
    )

    # Extract terms from font signature samples
    if isinstance(font_signatures, dict):
        for sig_data in font_signatures.values():
            if isinstance(sig_data, dict):
                samples = sig_data.get("samples", [])
                for sample in samples:
                    # Keep capitalized words (likely proper nouns/terms)
                    words = sample.split()
                    for word in words:
                        clean = word.strip(".,;:!?()[]{}").upper()
                        if len(clean) >= MIN_DOMAIN_TERM_LENGTH and clean.isalpha():
                            terms.add(clean)

    return sorted(list(terms))


def build_table_integrity_payload(
    phase8_file: str, tables_manifest: str, workspace: str
) -> dict[str, Any]:
    """Build input payload for step 9.4 (table integrity check).

    Args:
        phase8_file: Path to phase8.md
        tables_manifest: Path to tables-manifest.json from step 7.7
        workspace: Conversion workspace

    Returns:
        Input payload for step-input.json
    """
    return build_quality_assessment_payload(
        step_id="9.4",
        phase8_file=phase8_file,
        context={
            "tables_manifest": tables_manifest,
            "task": "check_table_integrity",
        },
        workspace=workspace,
    )


def build_callout_formatting_payload(
    phase8_file: str, gm_callout_config: str, workspace: str
) -> dict[str, Any]:
    """Build input payload for step 9.5 (callout formatting check).

    Args:
        phase8_file: Path to phase8.md
        gm_callout_config: Path to GM callout configuration file
        workspace: Conversion workspace

    Returns:
        Input payload for step-input.json
    """
    return build_quality_assessment_payload(
        step_id="9.5",
        phase8_file=phase8_file,
        context={
            "gm_callout_config": gm_callout_config,
            "task": "check_callout_formatting",
        },
        workspace=workspace,
    )
