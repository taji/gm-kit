# Data Model: PDF->Markdown Agent-Driven Pipeline

## Entities

### AgentStepDefinition
- **Represents**: Static definition for one agent step in E4-07b (13 total)
- **Key attributes**:
  - `step_id` (str): Step identifier, e.g. `"3.2"`, `"4.5"`, `"10.3"` (9.1 excluded)
  - `phase` (int): Phase number (3, 4, 6, 7, 8, 9, 10)
  - `description` (str): Human-readable step purpose
  - `criticality` (enum): `HIGH`, `MEDIUM`, `LOW`
  - `instruction_template` (str): Template path (`instructions/step_X_Y.md` or `step_7_7.py`)
  - `contract_schema` (str): JSON schema path (`schemas/step_X_Y.schema.json`)
  - `rubric_id` (str | None): Rubric identifier for quality-evaluated steps
- **Behavior**: Provides metadata for workspace file generation, validation, retry policy, and escalation

### AgentStepWorkspaceRequest
- **Represents**: Files and metadata prepared by Python code for the running agent to execute a step
- **Key attributes**:
  - `step_id` (str)
  - `workspace_dir` (str): Conversion workspace root
  - `step_dir` (str): `{workspace}/agent_steps/step_X_Y/`
  - `input_file` (str): `step-input.json`
  - `instruction_file` (str): `step-instructions.md`
  - `attempt_number` (int): 1..3
  - `resume_command` (str): `uv run --python "$(cat .python-version)" --extra dev -- gmkit pdf-convert --resume <workspace>`
- **Serialized artifacts**:
  - `step-input.json`: structured inputs and file paths
  - `step-instructions.md`: rendered instruction template + standard resume footer

### AgentStepInputPayload
- **Represents**: Step-specific input payload written to `step-input.json`
- **Key attributes**:
  - `step_id` (str)
  - `input_artifacts` (dict[str, str]): Required artifact names -> workspace paths
  - `optional_artifacts` (dict[str, str]): Optional inputs (e.g., `font-family-mapping.json` for 9.7)
  - `context` (dict): Step-specific parameters (thresholds, flags, corpus metadata, etc.)
  - `output_contract` (str): Contract schema path or identifier
  - `image_paths` (dict[str, str] | None): For multimodal steps (7.7, 8.7), paths to page/crop images **relative to project root** (e.g., `tests/fixtures/pdf_convert/agents/inputs/table_pages/...`)
- **Validation**: Presence/shape checked by Python before writing workspace request

### AgentStepOutputEnvelope
- **Represents**: Contract-validated output written by the running agent to `step-output.json`
- **Key attributes**:
  - `step_id` (str)
  - `status` (enum): `success`, `warning`, `failed`
  - `data` (dict): Step-specific result payload (or metadata-only payload for in-place markdown edits)
  - `rubric_scores` (dict[str, int] | None): Self-evaluation scores per dimension (1-5) for quality-assessed steps
  - `critical_failures` (list[str] | None): Any rubric-declared critical failures
  - `warnings` (list[str]): Non-fatal issues
  - `notes` (str | None): Additional agent notes
- **Validation**: Must conform to per-step JSON Schema before pipeline resumes
- **Note**: For steps 4.5, 6.4, 8.7 (markdown-modifying steps), `data` contains metadata only (status, changes_made); the actual content is written directly to the phase file specified in `step-input.json`

### AgentStepErrorEnvelope
- **Represents**: Structured step failure for missing inputs or repeated validation failures (FR-008)
- **Key attributes**:
  - `step_id` (str)
  - `error` (str): Description of what failed
  - `recovery` (str): Actionable guidance
- **Serialized as**: JSON in FR-008 format

### StepContract
- **Represents**: JSON Schema defining required fields and structural constraints for a step output
- **Key attributes**:
  - `step_id` (str)
  - `schema` (dict): JSON Schema Draft-07
  - `required_fields` (list[str])
  - `version` (str | None)
- **Behavior**: `validate(output: dict) -> list[ValidationError]`

### StepRubric
- **Represents**: Quality rubric for steps that require semantic evaluation
- **Key attributes**:
  - `step_id` (str)
  - `dimensions` (list[RubricDimension])
  - `critical_failures` (list[str])
  - `min_score` (int): `3`
  - `max_score` (int): `5`
- **Behavior**: Defines scoring criteria used by the running agent for rubric evaluation (temperature=0, structured output)

### RubricDimension
- **Represents**: One scoring dimension within a rubric
- **Key attributes**:
  - `name` (str)
  - `description` (str)
  - `scoring_guide` (dict[int, str]): 1-5 score descriptions

### EvaluationResult
- **Represents**: Rubric evaluation outcome for a step output
- **Key attributes**:
  - `step_id` (str)
  - `passed` (bool)
  - `dimension_scores` (dict[str, int])
  - `critical_failures` (list[str])
  - `feedback` (str)
- **Serialized as**: JSON (step-specific or shared schema)

### StepAttemptRecord
- **Represents**: One execution attempt for an agent step (used for retry tracking)
- **Key attributes**:
  - `step_id` (str)
  - `attempt_number` (int): 1..3
  - `validation_passed` (bool)
  - `rubric_passed` (bool | None)
  - `failure_reason` (str | None)
  - `retry_prompt_appendix` (str | None): Validation or rubric feedback appended to next instructions

### TokenPreflightResult
- **Represents**: Preflight estimate outcome for large markdown quality-assessment steps (FR-015)
- **Key attributes**:
  - `step_id` (str)
  - `estimated_tokens` (int)
  - `threshold` (int): Default 100,000 tokens, override via `GM_TOKEN_THRESHOLD` env var
  - `exceeds_threshold` (bool)
  - `user_choice` (enum | None): `proceed`, `skip`, `auto_proceed`
- **Applies to**: Quality Assessment + Reporting steps that send full markdown

### TestArtifact
- **Represents**: Step-specific test fixture set derived from the reference corpus
- **Key attributes**:
  - `step_id` (str)
  - `corpus_pdf` (str): One of the three reference PDFs
  - `input_payload` (dict | str): Fixture input data
  - `golden_output` (dict | str): Expected output artifact
  - `artifact_type` (enum): `unit_fixture`, `contract_fixture`, `golden`, `integration_sample`
- **Storage**: `tests/fixtures/pdf_convert/agents/inputs/` and `golden/`

## Relationships

```text
AgentStepDefinition 1--1 StepContract
AgentStepDefinition 1--0..1 StepRubric
StepRubric 1--* RubricDimension

AgentStepDefinition 1--* AgentStepWorkspaceRequest
AgentStepWorkspaceRequest 1--1 AgentStepInputPayload
AgentStepWorkspaceRequest 1--0..1 AgentStepOutputEnvelope
AgentStepWorkspaceRequest 1--0..1 AgentStepErrorEnvelope
AgentStepWorkspaceRequest 1--* StepAttemptRecord

AgentStepOutputEnvelope 0..1--1 EvaluationResult
AgentStepDefinition 1--* TestArtifact
AgentStepDefinition 0..*--1 TokenPreflightResult
```

## State Transitions

### Agent Step Lifecycle (file-handoff model)

```text
PENDING
  -> REQUEST_WRITTEN        (step-input.json + step-instructions.md written)
  -> AWAITING_AGENT         (CLI exits; agent performs step)
  -> OUTPUT_READ            (resume reads step-output.json)
  -> CONTRACT_VALIDATING
     -> RETRY_REQUEST_WRITTEN (invalid output; retry instructions appended) -> AWAITING_AGENT
     -> RUBRIC_EVALUATING      (if rubric applies)
        -> COMPLETED           (passes rubric)
        -> RETRY_REQUEST_WRITTEN (fails rubric/recoverable)
        -> ESCALATED           (max retries reached)

ESCALATED -> HALTED   (High)
ESCALATED -> FLAGGED  (Medium)
ESCALATED -> SKIPPED  (Low)
```

### Integration with E4-07a PhaseStatus

| Agent Step Outcome | Maps to PhaseStatus |
|--------------------|---------------------|
| COMPLETED          | SUCCESS |
| FLAGGED            | WARNING |
| SKIPPED            | WARNING |
| HALTED             | ERROR |

## Scope Notes

- E4-07b covers **13 agent steps**; step `9.1` is intentionally excluded (handled by code-level checks in E4-07a).
- Steps `4.5`, `6.4`, and `8.7` may edit phase markdown files in place; in those cases `step-output.json` carries metadata/summary fields rather than the full revised markdown content.
