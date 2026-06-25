# E7-03 Rehost Existing Analysis Logic into Prep Flow

## Summary

E7-03 extends the E7-02 `gmkit analyze-and-prep-pdf` skeleton by wiring real analysis-producing behavior into the prep-first flow. The feature reuses existing conversion-side analysis logic wherever behavior is already correct, extracting narrow shared helpers only when direct reuse is too tightly coupled to numeric conversion orchestration.

The goal is not to redesign the PDF conversion pipeline. The goal is to make the prep flow produce real, reusable artifacts for document analysis while minimizing regressions in the existing conversion-first path.

## Scope

In scope for E7-03:
- rehost existing metadata/preflight behavior into prep orchestration
- rehost existing image extraction behavior into prep orchestration
- rehost existing `no-images PDF` creation into prep orchestration
- rehost existing TOC acquisition behavior into prep orchestration
- emit prep artifacts through the E7-02 prep contract
- extract narrow shared helpers only when necessary to reuse behavior safely from both prep and conversion

Out of scope for E7-03:
- conversion gating on prep completion (`E7-07`)
- chapter segmentation or chunk planning (`E7-04`)
- guidance or annotation proposal systems (`E7-05`)
- interactive annotation review or skip capture (`E7-06`)
- broad cleanup refactors of the numeric conversion pipeline

## Design Goals

1. Reuse current analysis behavior where it is already correct.
2. Avoid functional regressions in the numeric conversion flow.
3. Keep prep artifact ownership in the prep pipeline.
4. Make the E7-02 prep contract real without expanding scope into later Epic 7 features.
5. Standardize naming so prep outputs are unambiguous to users and developers.

## Canonical Terminology

The canonical term for the PDF derivative with images removed or suppressed is:
- `no-images PDF`

This replaces earlier `text-only PDF` wording.

Rationale:
- `text-only` is overloaded and easy to confuse with markdown output, extracted plain text, or OCR text
- the artifact is still a PDF, not a text export
- `no-images PDF` is clearer in logs, docs, and manifest references

Preferred naming conventions:
- user-facing docs/logs: `no-images PDF`
- artifact/file naming: `no-images.pdf` or `source.no-images.pdf`
- internal helper naming may use more technical wording only when needed, but consistency is preferred

## Architecture

E7-03 builds on the E7-02 prep command and registry-backed prep orchestrator.

The prep pipeline remains the runtime owner of:
- workspace prep paths
- prep manifest entries
- prep state transitions
- prep completion rules

Existing conversion-side logic remains the behavior source wherever reuse is practical.

### Reuse Strategy

Use selective reuse with minimal extraction:
- if an existing helper or analysis path already exposes a usable boundary, call it from prep directly
- if current behavior is embedded too deeply inside numeric phase execution, extract the narrowest shared helper required for safe reuse
- do not reimplement behavior under `prep/` simply for aesthetic separation
- do not broaden extraction into general cleanup refactors unless the prep use case requires it

### Ownership Boundaries

Shared helpers may compute or derive data, but prep owns:
- artifact destination paths
- manifest inventory entries
- prep step status recording
- prep lifecycle transitions

Numeric conversion remains responsible for its own state machine and numeric orchestration behavior.

## Phase Mapping

E7-03 uses the existing Epic 7 prep phase model without redefining phase ownership.

### `prep.analyze-document`
Responsible for:
- metadata extraction
- preflight/readiness analysis already present in the existing flow

### `prep.extract-assets`
Responsible for:
- image extraction
- `no-images PDF` generation

### `prep.derive-structure`
Responsible for:
- canonical TOC acquisition

This keeps asset derivation separate from structural understanding and preserves the intended meaning of the phase names introduced in E7-01.

## Artifact Model

E7-03 does not introduce a second artifact contract. It populates the E7-02 prep contract with real outputs.

Required E7-03 artifact categories:
- metadata/preflight artifact output(s)
- extracted image artifact set
- `no-images PDF`
- canonical TOC artifact
- updated `prep-manifest.json` inventory entries
- updated `prep-state.json` progression reflecting actual completed steps

The exact artifact filenames should follow existing project conventions where that helps preserve behavior and reduce migration risk. Prep owns the final artifact placement under `<workspace>/prep/`.

## Extraction Guidance

Potential extraction targets exist only where the current conversion implementation is too entangled for safe prep reuse.

Expected extraction classes:
- narrow metadata/preflight helper extraction
- narrow image extraction and `no-images PDF` helper extraction
- narrow TOC acquisition helper extraction

Extraction rules:
- extract the smallest stable unit that allows both prep and conversion to call the same behavior
- keep existing numeric conversion behavior intact after extraction
- avoid moving unrelated orchestration logic into shared modules
- keep file responsibilities clear and testable

## Error Handling

E7-03 is conservative about completion semantics and failure reporting.

Rules:
- reused analysis failures surface as prep step failures with sanitized, prep-scoped errors
- partial artifacts may exist after failure, but `prep-complete.json` must never be written unless all required E7-03 artifacts are valid and the prep contract is consistent
- failed steps must still be represented clearly in prep state and manifest context where applicable
- prep error reporting must remain deterministic and suitable for harness/CI assertions

## Regression Policy

Regression risk is the central concern for E7-03.

Policy:
- preserve existing analysis output semantics unless a change is explicitly required by the new prep contract
- avoid changing numeric conversion behavior purely to make prep integration cleaner
- when extraction is necessary, prove both prep and numeric conversion callers still behave equivalently enough to preserve correctness

This feature is successful only if it rehosts behavior, not if it quietly changes it.

## Testing Strategy

Testing should emphasize reuse fidelity and artifact correctness.

Required coverage:
- unit tests for any newly extracted shared helpers
- prep orchestrator tests proving artifact emission for:
  - metadata/preflight outputs
  - image extraction outputs
  - `no-images PDF`
  - canonical TOC outputs
- tests that verify manifest inventory references produced artifacts correctly
- tests that verify failed reused steps update prep state correctly and do not emit `prep-complete.json`
- targeted regression tests that compare prep-produced outputs or helper results against legacy conversion behavior where practical

Out of scope for E7-03 tests:
- chapter chunking
- guidance/annotation systems
- conversion gating behavior

## Success Criteria

E7-03 is successful when:
- `gmkit analyze-and-prep-pdf` produces real prep analysis artifacts instead of only skeleton contract files
- the prep flow emits canonical TOC, extracted image outputs, and a `no-images PDF` using mostly existing behavior paths
- prep artifacts remain compatible with the E7-02 contract
- numeric conversion behavior is not regressed by the reuse/extraction work
- naming and logs consistently use `no-images PDF` terminology
