# Data Model: PDF→Markdown Agent-Driven Pipeline

## Entities

### AgentStep (abstract base)
- **Represents**: A single agent step in the pipeline, defining prompt, contract, and rubric
- **Key attributes**:
  - `step_id` (str): Step identifier, e.g. "3.2", "9.1"
  - `phase` (int): Phase number (3, 4, 6, 7, 8, 9, 10)
  - `description` (str): Human-readable step description
  - `criticality` (enum): HIGH, MEDIUM, LOW — determines escalation behavior
- **Behavior**: `execute(inputs) -> StepOutput` — builds prompt, calls LLM, validates, evaluates

### StepOutput
- **Represents**: The validated, evaluated output of an agent step execution
- **Key attributes**:
  - `step_id` (str): Which step produced this output
  - `data` (dict): Step-specific output payload (varies per step)
  - `metadata` (OutputMetadata): Shared envelope fields
  - `evaluation` (EvaluationResult | None): Rubric evaluation if performed
- **Serialized as**: JSON conforming to step's contract schema

### OutputMetadata (shared envelope)
- **Represents**: Common metadata for all agent step outputs
- **Key attributes**:
  - `step_id` (str): Step identifier
  - `input_artifact` (str): Path or reference to input
  - `warnings` (list[str]): Non-fatal issues encountered
  - `errors` (list[str]): Errors encountered (empty on success)
  - `notes` (str | None): Optional additional context
- **Validation**: JSON Schema applied to all outputs

### PromptTemplate
- **Represents**: A parameterized prompt for a single agent step
- **Key attributes**:
  - `step_id` (str): Step identifier
  - `task` (str): What the step does
  - `input_format` (str): Description of expected input structure
  - `output_format` (str): Description of expected output structure
  - `edge_cases` (list[str]): Edge case handling instructions
- **Behavior**: `build_prompt(inputs: dict) -> str` — constructs the full prompt with concrete input data

### StepContract
- **Represents**: JSON Schema defining required fields and constraints for a step's output
- **Key attributes**:
  - `step_id` (str): Step identifier
  - `schema` (dict): JSON Schema Draft-07 document
  - `required_fields` (list[str]): Top-level required fields
- **Behavior**: `validate(output: dict) -> list[ValidationError]` — returns empty list if valid
- **Storage**: `agents/schemas/step_X_Y.schema.json`

### StepRubric
- **Represents**: Evaluation criteria for scoring step output quality
- **Key attributes**:
  - `step_id` (str): Step identifier
  - `dimensions` (list[RubricDimension]): Scoring dimensions (3 per step)
  - `critical_failures` (list[str]): Conditions that cause immediate failure
  - `min_score` (int): Minimum acceptable score per dimension (3)
  - `max_score` (int): Maximum score (5)
- **Behavior**: `build_evaluation_prompt(output: dict) -> str` — constructs rubric evaluation prompt for LLM

### RubricDimension
- **Represents**: A single scoring dimension within a rubric
- **Key attributes**:
  - `name` (str): Dimension name (e.g., "Completeness", "Level accuracy")
  - `description` (str): What this dimension measures
  - `scoring_guide` (dict[int, str]): Score-to-description mapping (1-5)

### EvaluationResult
- **Represents**: The outcome of rubric evaluation for a step output
- **Key attributes**:
  - `step_id` (str): Step identifier
  - `passed` (bool): Whether all dimensions meet minimum and no critical failures
  - `dimension_scores` (dict[str, int]): Dimension name → score (1-5)
  - `critical_failures` (list[str]): Detected critical failures (empty if none)
  - `feedback` (str): LLM evaluator's summary feedback
- **Serialized as**: JSON

### AgentStepError
- **Represents**: A structured error when a step fails
- **Key attributes**:
  - `step_id` (str): Step identifier
  - `error` (str): Description of what went wrong
  - `recovery` (str): Actionable guidance to fix
- **Serialized as**: JSON per FR-008 format

### TestArtifact
- **Represents**: Input/output pair from the reference corpus for testing
- **Key attributes**:
  - `step_id` (str): Step identifier
  - `corpus_pdf` (str): Which PDF this artifact is from
  - `input_data` (dict | str): Step input (varies per step)
  - `golden_output` (dict): Expected step output for comparison
- **Storage**: `tests/fixtures/pdf_convert/agents/inputs/` and `golden/`

## Relationships

```
AgentStep 1──1 PromptTemplate     (each step has one prompt)
AgentStep 1──1 StepContract       (each step has one contract)
AgentStep 1──1 StepRubric         (each step has one rubric)
StepRubric 1──* RubricDimension   (each rubric has 3 dimensions)
AgentStep 1──* StepOutput         (each step produces outputs per execution)
StepOutput 1──1 OutputMetadata    (every output has metadata envelope)
StepOutput 0──1 EvaluationResult  (output may have rubric evaluation)
AgentStep 1──* TestArtifact       (each step has test artifacts per corpus PDF)
AgentStep 0──1 AgentStepError     (step may produce error instead of output)
```

## State Transitions

### Step Execution States

```
PENDING → EXECUTING → VALIDATING → EVALUATING → COMPLETED
                 ↓          ↓            ↓
              RETRYING ← RETRYING ←  RETRYING  (up to 3 attempts total)
                                        ↓
                                    ESCALATED → HALTED (High)
                                              → FLAGGED (Medium)
                                              → SKIPPED (Low)
```

### Integration with E4-07a PhaseStatus

| Agent State | Maps to PhaseStatus |
|------------|---------------------|
| COMPLETED | SUCCESS |
| FLAGGED | WARNING |
| SKIPPED | WARNING (Low criticality) |
| HALTED | ERROR |
