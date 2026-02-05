"""Shared constants for the PDF conversion pipeline."""

PHASE_NAMES = {
    0: "Pre-flight Analysis",
    1: "Image Extraction",
    2: "Image Removal",
    3: "TOC & Font Extraction",
    4: "Text Extraction",
    5: "Character-Level Fixes",
    6: "Structural Formatting",
    7: "Font Label Assignment",
    8: "Heading Insertion",
    9: "Lint & Final Review",
    10: "Report Generation",
}

PHASE_MIN = min(PHASE_NAMES)
PHASE_MAX = max(PHASE_NAMES)
PHASE_COUNT = PHASE_MAX - PHASE_MIN + 1
