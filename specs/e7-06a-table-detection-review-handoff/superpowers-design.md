# E7-06a Table Detection Review Handoff Design

**Goal:** Move table detection into prep as a reviewable handoff so the user reviews only the annotated PDF while conversion consumes finalized table decisions from the prep contract.

## Architecture
E7-06a reuses the shared proposal and resolved-guidance contracts introduced in E7-05. Table detection is no longer a conversion-side concern. Instead, prep detects candidate tables, writes them as proposal evidence, renders an annotated PDF for human review, and persists final decisions into the authoritative resolved guidance artifact.

The architecture has four parts:
- proposal generation
- annotated review rendering
- review/update application
- conversion consumption

The key constraint is that the user reviews the PDF, not the JSON. JSON remains the machine contract for agents and code.

## Artifact Contract
E7-06a uses the E7-05 prep artifacts and does not introduce a table-specific reviewed manifest.

### `annotation-proposals.json`
Contains raw table proposal evidence with the shared proposal schema:
- `proposal_id`
- `label: "table"`
- `page`
- `bbox`
- `confidence`
- `metadata`

For E7-06a, table proposals should include enough provenance to explain why each region was suggested, but the proposal file remains evidence, not authority.

### `annotated-prep.pdf`
This is the only user-facing review surface. It shows table proposal overlays and stable proposal identifiers so the user can revise the detected boxes visually.

### `prep-guidance.resolved.json`
This remains the authoritative downstream contract. Finalized table decisions live here alongside other resolved guidance fields such as skip and callout data.

For tables, the resolved artifact should expose a stable `table_regions` collection. Each region should carry the minimum data needed by conversion:
- page
- bbox
- proposal_id when the region came from a proposal
- any normalized metadata required by downstream formatting

No separate `tables-manifest.reviewed.json` is introduced at this stage. That would duplicate the shared resolved-guidance contract without adding value.

## Workflow
1. Prep detects candidate tables from the existing prep artifacts and segmentation context.
2. Prep writes `annotation-proposals.json` with table proposals.
3. Prep renders `annotated-prep.pdf` with visible table overlays and proposal IDs.
4. The user reviews the PDF and edits bboxes or acceptance decisions through the revise/update command.
5. The revise/update command applies those edits into `prep-guidance.resolved.json`.
6. `pdf-convert` reads `prep-guidance.resolved.json` as authoritative input and formats tables from the finalized regions.

Automation can skip the manual review step when the resolved artifact already reflects accepted table decisions.

## Conversion Behavior
Conversion must treat finalized table data as input, not as a signal to rediscover tables.

Required behavior:
- if resolved table data exists, use it directly
- do not rerun table heuristics in conversion
- if resolved table data is missing, fail with actionable guidance rather than silently falling back

This keeps prep and conversion separated cleanly and prevents drift between review output and final markdown.

## Failure Handling
E7-06a should fail narrowly and predictably.

Rules:
- if table proposal generation fails entirely, prep should fail with a clear diagnostic
- if annotated PDF rendering fails, JSON artifacts can still be valid and usable
- if review/update edits reference an unknown proposal ID, the command should reject the update
- if conversion does not find resolved table data, it should halt and tell the user to rerun prep/review

The important invariant is that the resolved artifact is the only authoritative source for table decisions.

## Testing Strategy
E7-06a tests should prove:
- table proposal generation is deterministic for the same input artifacts
- annotated PDF rendering includes the expected proposal overlays and stable IDs
- review/update edits round-trip bbox changes into `prep-guidance.resolved.json`
- conversion consumes resolved table data and does not rediscover tables
- missing resolved table data produces an actionable error
- table review behavior stays compatible with the shared E7-05 proposal schema

## Scope Notes
E7-06a includes:
- prep-side table proposal generation
- annotated review rendering
- revise/update application for table decisions
- conversion-side consumption of finalized table data

E7-06a does not include:
- callout review handoff
- skip workflow changes beyond existing shared guidance handling
- TOC regeneration
- any new table-specific manifest outside the shared resolved guidance contract

That keeps the feature focused on the table review handoff and avoids introducing parallel artifact formats before the resolved contract proves insufficient.
