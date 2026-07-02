# E7-06 Annotation Review UX + Skip Intent Capture Design

**Goal:** Add a prep review workflow that lets the user inspect/revise annotation proposals, enter explicit skip pages/ranges, and produce reviewed guidance for downstream conversion.

## Architecture
E7-06 builds directly on the E7-05 artifact model:
- `prep-guidance.defaults.json` = persisted intent/defaults
- `annotation-proposals.json` = raw proposal evidence
- `prep-guidance.resolved.json` = baseline downstream contract
- `annotated-prep.pdf` = visual review companion

E7-06 adds the missing review/revision layer between raw proposal generation and conversion consumption. The design keeps raw evidence separate from user-reviewed outcomes and makes review a separate step after prep completes.

The workflow has four concerns:
- visual review material
- structured review edits
- explicit skip intent capture
- final normalization with precedence rules

This remains prep-first and file-based. Prep produces artifacts and exits; a separate revise step reads the review artifacts and writes the reviewed guidance consumed by conversion.

## Review Model
E7-06 should use the existing CLI interaction style already present in the repository:
- generate artifacts
- prompt the user with review instructions
- allow file edits in a follow-up step
- revise reviewed guidance separately from prep

The review UX should not depend on a complex in-terminal bbox editor. Instead:
- generate `annotated-prep.pdf` with visible proposal boxes and IDs
- generate a structured editable review artifact
- prompt the user to accept, revise, or bypass
- on revise, apply edits and regenerate reviewed guidance

This matches the repo’s existing “generate artifact, then apply edits” pattern and is a better fit for a Python CLI than a bespoke terminal graphics editor.

## Artifact Contract
E7-06 should continue using the E7-05 artifacts and add the review artifacts under `<workspace>/prep/`:

- `prep-guidance.defaults.json`
- `annotation-proposals.json`
- `annotation-review.edits.json`
- `prep-guidance.resolved.json`
- `prep-guidance.reviewed.json`
- `annotated-prep.pdf`

### Artifact Flow Summary

| Artifact | Produced By | Consumed By | Purpose |
| --- | --- | --- | --- |
| `prep-guidance.defaults.json` | prep | proposal generation, review seeding | stores seed intent and defaults |
| `annotation-proposals.json` | prep | review PDF rendering, resolved guidance | captures raw machine-detected candidates |
| `annotated-prep.pdf` | prep | human reviewer | visual review surface for PDF annotations |
| `annotation-review.edits.json` | revise / extraction code | reviewed guidance generation | stores machine-extracted review decisions from the annotated PDF |
| `prep-guidance.resolved.json` | prep | conversion, revise step | baseline downstream contract after prep |
| `prep-guidance.reviewed.json` | revise | conversion | authoritative downstream contract after review |

The two pairs are intentionally similar in shape but different in role:

- `annotation-proposals.json` -> `prep-guidance.resolved.json` is detector evidence normalized into a baseline contract.
- `annotated-prep.pdf` -> `annotation-review.edits.json` -> `prep-guidance.reviewed.json` is human review surface -> extracted review state -> finalized contract.

### `annotated-prep.pdf`
Purpose:
- provide a human-readable visual review companion

Behavior:
- render proposal bounding boxes and stable proposal IDs
- label meaning remains canonical in JSON, not color
- failure to render is a prep failure because the review surface is required

This PDF is required review support only. It is never authoritative machine input.

### `annotation-review.edits.json`
Purpose:
- persist structured user review decisions and explicit skip intent

This becomes the user-editable review artifact. It should be generated even if the user accepts everything immediately, so the prep workspace always has a concrete record of review outcome.

Recommended shape:
- `review_mode`: `interactive`, `auto_accept`, or `bypass`
- `review_status`: `pending`, `accepted`, `revised`, or `auto_accepted`
- `skip_ranges_input`: raw user input such as `2,5,12-14`
- `skip_pages_explicit`: parsed explicit full-page skips
- `proposal_decisions`: per-proposal decisions keyed by `proposal_id`
- `updated_regions`: edited bbox/label/page overrides when applicable
- `notes`: optional free-form user note field

Example:

```json
{
  "review_mode": "interactive",
  "review_status": "revised",
  "skip_ranges_input": "2,5,12-14",
  "skip_pages_explicit": [2, 5, 12, 13, 14],
  "proposal_decisions": {
    "ap-0ab1234ef567": "accept",
    "ap-0cd2345fa678": "reject"
  },
  "updated_regions": {
    "ap-0ef3456ab789": {
      "page": 18,
      "bbox": [72.0, 250.0, 520.0, 600.0],
      "label": "table"
    }
  },
  "notes": ""
}
```

This artifact is not itself authoritative downstream input. It is the persisted review state that drives reviewed guidance.

### `prep-guidance.defaults.json`
E7-06 should extend this artifact rather than replace it.

It should continue to hold generation/review intent such as:
- table/callout/skip preferences
- non-interactive / auto-accept choice
- whether review was bypassed

Recommended additions:
- `review_requested`
- `auto_accept_annotations`
- `capture_skip_intent`

This keeps default/user intent distinct from the actual review result stored in `annotation-review.edits.json`.

### `prep-guidance.resolved.json`
This remains the baseline downstream contract written by prep.

It is regenerated from:
- raw proposals
- guidance input intent
- review edits
- explicit skip page/range input
- overlap precedence rules

This artifact should stay downstream-oriented and deterministic. It is the baseline consumed by automation when no reviewed artifact exists.

### `prep-guidance.reviewed.json`
This is the reviewed downstream contract written by the revise command.

It is regenerated from the resolved baseline plus the edited review artifact and becomes the authoritative input for conversion when present.

Recommended additions:
- `review_summary` metadata with concise provenance such as:
  - `mode`
  - `status`
  - `explicit_skip_input_present`

The reviewed artifact should stay downstream-oriented. It should not become a dump of the full review session.

## Review UX
Review should be explicit and file-based.

Recommended flow:
1. Run prep analysis and proposal generation
2. Render `annotated-prep.pdf`
3. Seed `annotation-review.edits.json`
4. Exit prep with review instructions
5. User edits the review artifact and/or the PDF annotations
6. Run the revise command to produce `prep-guidance.reviewed.json`
7. Conversion consumes the reviewed artifact when present

This keeps prep deterministic and makes the review boundary explicit.

## Non-Interactive UX
Non-interactive mode must not pretend the user reviewed anything manually.

Rules:
- if `--yes` / auto-proceed is used, prep writes review artifacts and the automation path can proceed without revision
- `annotation-review.edits.json` should still be written
- `prep-guidance.resolved.json` should record concise review provenance
- `prep-guidance.reviewed.json` is optional and only written by the revise command

This satisfies the requirement that non-interactive mode record bypass/auto-accept behavior in artifacts.

## Skip Intent Capture
E7-06 should support explicit skip input in human-friendly syntax:
- `2`
- `2,5,12-14`
- whitespace-tolerant forms like `2, 5, 12-14`

Parsing rules:
- 1-based inclusive page numbers
- ranges must be ascending
- duplicates collapse to unique sorted pages
- invalid tokens fail clearly
- pages outside document bounds fail clearly

Persist both:
- raw input string
- parsed normalized page list

This preserves user intent faithfully while still giving downstream code a deterministic contract.

## Review Semantics
Per-proposal decisions should support:
- `accept`
- `reject`
- `edit`

Edit support should allow:
- updated `bbox`
- updated `page`
- updated `label`

If a proposal is edited, the updated region should keep provenance traceable back to its original `proposal_id`.

The raw proposal artifact should never be mutated after generation. User changes belong in the review artifact and then flow into the resolved artifact.

## Overlap Rule
`skip` takes precedence for exclusion.

That rule should apply in this order:
1. explicit full-page skips remove all table/callout/region content from those pages
2. explicit skip regions remove overlapping table/callout regions
3. accepted/edited skip proposals apply before table/callout inclusion

Resolved output should never contain table/callout regions that conflict with final skip decisions.

Overlap should be determined by:
- same page
- bbox intersection for region-level comparisons

## State Transitions
E7-06 should make the existing prep phases meaningful:

- `prep.review-annotations`
  - render `annotated-prep.pdf`
  - seed `annotation-review.edits.json`
  - write `prep-guidance.resolved.json`
  - exit with review instructions

- follow-up revise command
  - consume the review artifact
  - apply review decisions and edits
  - enforce overlap precedence
  - write `prep-guidance.reviewed.json`

E7-05’s initial resolved guidance remains the baseline artifact for automation and conversion when no reviewed artifact exists.

## Failure Handling
E7-06 failures should be explicit and bounded.

Rules:
- invalid skip syntax fails with actionable diagnostics
- invalid edited bbox/page/label data fails before revision
- missing raw proposal artifact is a hard prep failure
- missing annotated PDF is tolerated if review JSON artifacts are valid
- partial review state should remain editable, not destructive

## Testing Strategy
E7-06 tests should prove:
- skip page/range parsing is deterministic and validated
- `annotation-review.edits.json` seeds and round-trips correctly
- non-interactive runs produce review artifacts without requiring the revise command
- the revise command writes `prep-guidance.reviewed.json` from edited review artifacts
- edited proposals override raw proposals in final guidance
- skip precedence removes overlapping table/callout regions
- `annotated-prep.pdf` is required support output, not the authoritative contract

## Scope Notes
E7-06 includes:
- review-state artifact definition
- annotated review PDF rendering
- skip page/range capture and parsing
- review revision into the reviewed artifact
- revision command behavior that writes reviewed guidance
- precedence application into final reviewed guidance

E7-06 does not include:
- downstream markdown generation changes
- changing the conversion consumer to prefer reviewed guidance
- a graphical bbox editor inside the terminal
- rethinking the E7-05 raw proposal contract
