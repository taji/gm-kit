"""Rubric definitions for agent step evaluation.

Each rubric defines scoring dimensions (1-5 scale) and critical failures.
The agent performs self-evaluation against these rubrics.
"""



class RubricDimension:
    """One scoring dimension within a rubric."""

    def __init__(
        self, name: str, description: str, scoring_guide: dict[int, str], weight: float = 1.0
    ):
        self.name = name
        self.description = description
        self.scoring_guide = scoring_guide
        self.weight = weight


class StepRubric:
    """Quality rubric for an agent step."""

    def __init__(
        self,
        step_id: str,
        dimensions: list[RubricDimension],
        critical_failures: list[str],
        min_score: int = 3,
        max_score: int = 5,
    ):
        self.step_id = step_id
        self.dimensions = dimensions
        self.critical_failures = critical_failures
        self.min_score = min_score
        self.max_score = max_score

    def validate_scores(self, scores: dict[str, int]) -> tuple[bool, list[str]]:
        """Validate rubric scores.

        Args:
            scores: Dict mapping dimension names to scores (1-5)

        Returns:
            Tuple of (passed, error_messages)
        """
        errors = []

        # Check all dimensions are present
        for dim in self.dimensions:
            if dim.name not in scores:
                errors.append(f"Missing score for dimension: {dim.name}")

        # Check score range
        for dim_name, score in scores.items():
            if score < self.min_score:
                errors.append(
                    f"Dimension '{dim_name}' score {score} below minimum {self.min_score}"
                )

        return len(errors) == 0, errors


# Content Repair Rubrics

RUBRIC_3_2 = StepRubric(
    step_id="3.2",
    dimensions=[
        RubricDimension(
            name="completeness",
            description="All TOC entries from the PDF are captured",
            scoring_guide={
                5: "100% of TOC entries captured with no omissions",
                4: "90-99% captured, minor omissions",
                3: "75-89% captured, some omissions",
                2: "50-74% captured, significant omissions",
                1: "<50% captured or major sections missing",
            },
        ),
        RubricDimension(
            name="level_accuracy",
            description="Heading hierarchy levels are correct (H1→H2→H3)",
            scoring_guide={
                5: "All levels correct, hierarchy perfectly preserved",
                4: "90%+ correct, minor level errors",
                3: "75-89% correct, some level mismatches",
                2: "50-74% correct, frequent level errors",
                1: "<50% correct or levels severely wrong",
            },
        ),
        RubricDimension(
            name="page_accuracy",
            description="Page numbers match the TOC",
            scoring_guide={
                5: "All page numbers correct",
                4: "90%+ correct, minor errors",
                3: "75-89% correct, some errors",
                2: "50-74% correct, frequent errors",
                1: "<50% correct",
            },
        ),
        RubricDimension(
            name="output_format",
            description="Output uses correct indented format (2 spaces per level)",
            scoring_guide={
                5: "Perfect format, all entries properly indented with (page N) notation",
                4: "Minor formatting issues, still machine-parseable",
                3: "Some formatting errors but structure intact",
                2: "Significant formatting errors",
                1: "Format incorrect or unparseable",
            },
        ),
    ],
    critical_failures=[
        "Missing sections present in PDF TOC",
        "Output format not parseable as indented text",
    ],
)

RUBRIC_4_5 = StepRubric(
    step_id="4.5",
    dimensions=[
        RubricDimension(
            name="correct_joins",
            description="Properly joined sentences that should be merged",
            scoring_guide={
                5: "All appropriate joins made correctly",
                4: "90%+ joins correct",
                3: "75-89% joins correct",
                2: "50-74% joins correct",
                1: "<50% joins correct",
            },
        ),
        RubricDimension(
            name="no_false_joins",
            description="No inappropriate sentence merges",
            scoring_guide={
                5: "Zero false joins",
                4: "1-2 minor false joins",
                3: "3-5 false joins",
                2: "6-10 false joins",
                1: ">10 false joins or merges across paragraphs",
            },
        ),
        RubricDimension(
            name="readability",
            description="Resulting text is readable and natural",
            scoring_guide={
                5: "Text flows naturally, no awkward joins",
                4: "Minor awkwardness in 1-2 places",
                3: "Some awkward joins but understandable",
                2: "Frequent awkward phrasing",
                1: "Text difficult to read due to joins",
            },
        ),
    ],
    critical_failures=["Sentences merged across unrelated paragraphs"],
)

RUBRIC_6_4 = StepRubric(
    step_id="6.4",
    dimensions=[
        RubricDimension(
            name="correction_accuracy",
            description="OCR errors are correctly identified and fixed",
            scoring_guide={
                5: "100% accuracy on all corrections",
                4: "90-99% accuracy",
                3: "75-89% accuracy",
                2: "50-74% accuracy",
                1: "<50% accuracy",
            },
        ),
        RubricDimension(
            name="false_positive_rate",
            description="No false corrections of valid text",
            scoring_guide={
                5: "Zero false positives",
                4: "1-2 minor false positives",
                3: "3-5 false positives",
                2: "6-10 false positives",
                1: ">10 false positives",
            },
        ),
        RubricDimension(
            name="domain_term_preservation",
            description="TTRPG terms and abbreviations are preserved",
            scoring_guide={
                5: "100% domain terms preserved",
                4: "95-99% preserved",
                3: "85-94% preserved",
                2: "70-84% preserved",
                1: "<70% preserved or major TTRPG terms corrupted",
            },
        ),
    ],
    critical_failures=["Corrupting TTRPG terms (AC, HP, monster names, etc.)"],
)

# Table Processing Rubrics

RUBRIC_7_7 = StepRubric(
    step_id="7.7",
    dimensions=[
        RubricDimension(
            name="detection_recall",
            description="All tables in the document are detected",
            scoring_guide={
                5: "100% table detection, no tables missed",
                4: "90-99% detection, 1 minor table missed",
                3: "75-89% detection, some tables missed",
                2: "50-74% detection, significant misses",
                1: "<50% detection or major tables missed",
            },
        ),
        RubricDimension(
            name="detection_precision",
            description="No false table detections",
            scoring_guide={
                5: "Zero false positives",
                4: "1-2 minor false positives",
                3: "3-5 false positives",
                2: "6-10 false positives",
                1: ">10 false positives",
            },
        ),
        RubricDimension(
            name="boundary_accuracy",
            description="Table bounding boxes are accurate",
            scoring_guide={
                5: "All bounding boxes capture full tables with minimal excess",
                4: "90%+ accuracy, minor cropping issues",
                3: "75-89% accuracy, some cropping errors",
                2: "50-74% accuracy, significant boundary errors",
                1: "<50% accuracy or boxes miss major table content",
            },
        ),
    ],
    critical_failures=["Missing a table entirely"],
)

RUBRIC_8_7 = StepRubric(
    step_id="8.7",
    dimensions=[
        RubricDimension(
            name="row_column_fidelity",
            description="Table structure matches source (rows, columns, cells)",
            scoring_guide={
                5: "Perfect row/column/cell structure preservation",
                4: "90%+ structure preserved",
                3: "75-89% structure preserved",
                2: "50-74% structure preserved",
                1: "<50% structure preserved",
            },
        ),
        RubricDimension(
            name="markdown_validity",
            description="Output is valid markdown table syntax",
            scoring_guide={
                5: "Valid markdown, renders correctly in all viewers",
                4: "Valid markdown, minor rendering issues in some viewers",
                3: "Mostly valid, some syntax errors",
                2: "Significant syntax errors",
                1: "Invalid markdown or won't render",
            },
        ),
        RubricDimension(
            name="content_preservation",
            description="All cell text is preserved accurately",
            scoring_guide={
                5: "100% cell content preserved",
                4: "95-99% preserved, minor truncation",
                3: "85-94% preserved, some truncation",
                2: "70-84% preserved, significant data loss",
                1: "<70% preserved or major content loss",
            },
        ),
    ],
    critical_failures=["Truncated/lost cell data", "Invalid markdown table structure"],
)

# Quality Assessment Rubrics

RUBRIC_9_2 = StepRubric(
    step_id="9.2",
    dimensions=[
        RubricDimension(
            name="heading_hierarchy",
            description="Heading levels are valid (no skips, proper nesting)",
            scoring_guide={
                5: "Perfect hierarchy, no level skips, single H1",
                4: "90%+ valid, minor level issues",
                3: "75-89% valid, some skips",
                2: "50-74% valid, frequent skips",
                1: "<50% valid or major hierarchy problems",
            },
        ),
        RubricDimension(
            name="section_coherence",
            description="Sections have clear boundaries and coherence",
            scoring_guide={
                5: "All sections well-defined and coherent",
                4: "90%+ sections coherent",
                3: "75-89% sections coherent",
                2: "50-74% sections coherent",
                1: "<50% sections coherent",
            },
        ),
        RubricDimension(
            name="nesting_correctness",
            description="Subsections properly nested under parent sections",
            scoring_guide={
                5: "Perfect nesting throughout",
                4: "90%+ correct nesting",
                3: "75-89% correct nesting",
                2: "50-74% correct nesting",
                1: "<50% correct nesting",
            },
        ),
    ],
    critical_failures=["Malformed assessment JSON"],
)

RUBRIC_9_3 = StepRubric(
    step_id="9.3",
    dimensions=[
        RubricDimension(
            name="reading_order",
            description="Text follows correct left-to-right, top-to-bottom flow",
            scoring_guide={
                5: "Perfect reading order",
                4: "90%+ correct order",
                3: "75-89% correct order",
                2: "50-74% correct order",
                1: "<50% correct order",
            },
        ),
        RubricDimension(
            name="paragraph_integrity",
            description="Paragraphs are complete and not fragmented",
            scoring_guide={
                5: "100% paragraph integrity",
                4: "90-99% integrity",
                3: "75-89% integrity",
                2: "50-74% integrity",
                1: "<50% integrity",
            },
        ),
        RubricDimension(
            name="flow_continuity",
            description="Text transitions smoothly between sections",
            scoring_guide={
                5: "Perfect flow continuity",
                4: "90%+ continuous",
                3: "75-89% continuous",
                2: "50-74% continuous",
                1: "<50% continuous",
            },
        ),
    ],
    critical_failures=["Malformed assessment JSON"],
)

RUBRIC_9_4 = StepRubric(
    step_id="9.4",
    dimensions=[
        RubricDimension(
            name="cell_accuracy",
            description="Table cells match source content",
            scoring_guide={
                5: "100% cell accuracy",
                4: "95-99% accurate",
                3: "85-94% accurate",
                2: "70-84% accurate",
                1: "<70% accurate",
            },
        ),
        RubricDimension(
            name="structure_preservation",
            description="Table structure (rows, cols, headers) preserved",
            scoring_guide={
                5: "Perfect structure preservation",
                4: "90%+ preserved",
                3: "75-89% preserved",
                2: "50-74% preserved",
                1: "<50% preserved",
            },
        ),
        RubricDimension(
            name="alignment_check",
            description="Cell alignment appropriate for content type",
            scoring_guide={
                5: "All alignments appropriate",
                4: "90%+ appropriate",
                3: "75-89% appropriate",
                2: "50-74% appropriate",
                1: "<50% appropriate",
            },
        ),
    ],
    critical_failures=["Malformed assessment JSON"],
)

RUBRIC_9_5 = StepRubric(
    step_id="9.5",
    dimensions=[
        RubricDimension(
            name="detection_accuracy",
            description="Callouts are correctly identified",
            scoring_guide={
                5: "100% callout detection accuracy",
                4: "95-99% accurate",
                3: "85-94% accurate",
                2: "70-84% accurate",
                1: "<70% accurate",
            },
        ),
        RubricDimension(
            name="format_preservation",
            description="Callout formatting (blockquotes, labels) preserved",
            scoring_guide={
                5: "Perfect format preservation",
                4: "90%+ preserved",
                3: "75-89% preserved",
                2: "50-74% preserved",
                1: "<50% preserved",
            },
        ),
        RubricDimension(
            name="boundary_correctness",
            description="Callout start/end boundaries are accurate",
            scoring_guide={
                5: "All boundaries correct",
                4: "90%+ correct",
                3: "75-89% correct",
                2: "50-74% correct",
                1: "<50% correct",
            },
        ),
    ],
    critical_failures=["Malformed assessment JSON"],
)

RUBRIC_9_7 = StepRubric(
    step_id="9.7",
    dimensions=[
        RubricDimension(
            name="gap_detection",
            description="TOC gaps and mismatches are identified",
            scoring_guide={
                5: "All gaps accurately detected with proper severity",
                4: "90%+ gaps detected",
                3: "75-89% gaps detected",
                2: "50-74% gaps detected",
                1: "<50% gaps detected",
            },
        ),
        RubricDimension(
            name="duplicate_detection",
            description="Duplicate TOC entries are found",
            scoring_guide={
                5: "All duplicates detected",
                4: "90%+ duplicates detected",
                3: "75-89% duplicates detected",
                2: "50-74% duplicates detected",
                1: "<50% duplicates detected",
            },
        ),
        RubricDimension(
            name="actionable_suggestions",
            description="Suggestions help fix identified issues",
            scoring_guide={
                5: "All suggestions actionable and specific",
                4: "90%+ suggestions actionable",
                3: "75-89% actionable",
                2: "50-74% actionable",
                1: "<50% actionable",
            },
        ),
        RubricDimension(
            name="font_source_awareness",
            description="Distinguishes TOC-sourced from font-inferred headings",
            scoring_guide={
                5: "Perfect distinction, appropriate skepticism applied",
                4: "90%+ accurate distinction",
                3: "75-89% accurate",
                2: "50-74% accurate",
                1: "<50% accurate or no distinction made",
            },
        ),
    ],
    critical_failures=["Malformed assessment JSON"],
)

RUBRIC_9_8 = StepRubric(
    step_id="9.8",
    dimensions=[
        RubricDimension(
            name="order_correctness",
            description="Two-column reading order is correct",
            scoring_guide={
                5: "100% correct reading order",
                4: "90%+ correct",
                3: "75-89% correct",
                2: "50-74% correct",
                1: "<50% correct",
            },
        ),
        RubricDimension(
            name="confidence_flagging",
            description="Uncertain cases are appropriately flagged",
            scoring_guide={
                5: "All uncertain cases flagged with confidence levels",
                4: "90%+ appropriately flagged",
                3: "75-89% flagged",
                2: "50-74% flagged",
                1: "<50% flagged",
            },
        ),
        RubricDimension(
            name="threshold_adherence",
            description=">15% threshold properly applied for pervasive flag",
            scoring_guide={
                5: "Threshold correctly applied",
                4: "90%+ correct threshold application",
                3: "75-89% correct",
                2: "50-74% correct",
                1: "<50% correct",
            },
        ),
    ],
    critical_failures=["Malformed assessment JSON"],
)

# Reporting Rubrics

RUBRIC_10_2 = StepRubric(
    step_id="10.2",
    dimensions=[
        RubricDimension(
            name="rating_justification",
            description="Each rating has clear justification",
            scoring_guide={
                5: "All ratings well-justified with specific evidence",
                4: "90%+ well-justified",
                3: "75-89% justified",
                2: "50-74% justified",
                1: "<50% justified",
            },
        ),
        RubricDimension(
            name="dimension_coverage",
            description="All quality dimensions are rated",
            scoring_guide={
                5: "All required dimensions present and rated",
                4: "90%+ dimensions covered",
                3: "75-89% covered",
                2: "50-74% covered",
                1: "<50% covered or missing key dimensions",
            },
        ),
        RubricDimension(
            name="score_consistency",
            description="Scores are consistent with assessment findings",
            scoring_guide={
                5: "Perfect consistency with assessment data",
                4: "90%+ consistent",
                3: "75-89% consistent",
                2: "50-74% consistent",
                1: "<50% consistent",
            },
        ),
    ],
    critical_failures=["Missing required dimensions"],
)

RUBRIC_10_3 = StepRubric(
    step_id="10.3",
    dimensions=[
        RubricDimension(
            name="issue_clarity",
            description="Issues are clearly described and understandable",
            scoring_guide={
                5: "All issues crystal clear with specific locations",
                4: "90%+ clear",
                3: "75-89% clear",
                2: "50-74% clear",
                1: "<50% clear or vague descriptions",
            },
        ),
        RubricDimension(
            name="example_quality",
            description="Examples illustrate the issues well",
            scoring_guide={
                5: "All examples perfect illustrations",
                4: "90%+ good examples",
                3: "75-89% good examples",
                2: "50-74% good examples",
                1: "<50% good examples",
            },
        ),
        RubricDimension(
            name="actionable_guidance",
            description="Suggested fixes are actionable",
            scoring_guide={
                5: "All guidance immediately actionable",
                4: "90%+ actionable",
                3: "75-89% actionable",
                2: "50-74% actionable",
                1: "<50% actionable",
            },
        ),
    ],
    critical_failures=["Truncated or empty report", "No actionable guidance"],
)

# Registry of all rubrics
RUBRICS: dict[str, StepRubric] = {
    "3.2": RUBRIC_3_2,
    "4.5": RUBRIC_4_5,
    "6.4": RUBRIC_6_4,
    "7.7": RUBRIC_7_7,
    "8.7": RUBRIC_8_7,
    "9.2": RUBRIC_9_2,
    "9.3": RUBRIC_9_3,
    "9.4": RUBRIC_9_4,
    "9.5": RUBRIC_9_5,
    "9.7": RUBRIC_9_7,
    "9.8": RUBRIC_9_8,
    "10.2": RUBRIC_10_2,
    "10.3": RUBRIC_10_3,
}


def get_rubric(step_id: str) -> StepRubric | None:
    """Get rubric for a step.

    Args:
        step_id: Step identifier (e.g., '3.2')

    Returns:
        StepRubric or None if not found
    """
    return RUBRICS.get(step_id)


def get_all_rubrics() -> dict[str, StepRubric]:
    """Get all rubrics.

    Returns:
        Dict mapping step_id to StepRubric
    """
    return RUBRICS.copy()
