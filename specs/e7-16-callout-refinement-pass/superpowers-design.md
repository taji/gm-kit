# E7-16 Optional Callout Refinement Pass Design

## Goal

Add an optional second pass after code-based callout detection that can refine only the callout proposals flagged as ambiguous by multi-block traversal hints.

## Scope

This design is limited to the prep-side callout refinement flow for `gmkit analyze-and-prep-pdf`.

Included:
- code-first callout detection remains the primary pass
- refinement only runs for proposals flagged by multi-block traversal hints
- the pass is explicitly skippable with a CLI flag
- the orchestrator exits cleanly when vision refinement is requested but not yet supplied
- a mock handoff path is available for automated tests and CI
- refinement happens before the user review step
- reviewed guidance remains the final user-authored contract

Excluded:
- changing the initial callout detection heuristics
- changing table detection
- changing TOC generation
- making the review PDF optional
- replacing the existing reviewed guidance contract

## Canonical Flow

E7-15 established the first-pass callout detector and the hint artifact that records multi-block boundary warnings.

E7-16 adds a follow-up refinement handoff:
1. code detects callout proposals and emits refinement hints
2. the orchestrator decides whether refinement is enabled
3. if refinement is requested, the orchestrator writes a request artifact and exits cleanly
4. the outer agent or test harness performs the vision-aware refinement
5. the outer agent writes a response artifact and re-invokes the command
6. the orchestrator reads the refinement response and applies the geometry update
7. the user still reviews the resulting annotated PDF
8. the user may still revise guidance into `prep-guidance.reviewed.json`

The second pass is not a replacement for human review. It is a targeted geometry correction handoff for ambiguous proposals that are already known to need attention.

## Architecture

The refinement flow should preserve three separate responsibilities:
- code detects anchors and initial bounding boxes
- the outer agent performs the vision-aware refinement when requested
- the orchestrator resumes from a returned refinement artifact and continues prep

The pipeline needs a clear handoff gate:
- explicit CLI skip flag disables refinement
- if no vision-capable path is available, the orchestrator writes the request and pauses instead of guessing
- failed refinement must not block the rest of prep unless the user explicitly asks for strict behavior later

The refinement pass should operate on a narrow subset of proposals:
- proposals tagged by `annotation-refinement-hints.json`
- proposals whose hint reason indicates multi-block traversal or boundary uncertainty

The refinement result should be a derived artifact, not an overwrite of raw evidence. The raw proposal and hint artifacts remain the source of truth for what the detector first observed.

## Artifact Flow

Existing prep-side artifacts remain the base layer:
- `annotation-proposals.json` stores the first-pass proposals
- `annotation-refinement-hints.json` stores ambiguous proposal hints
- `prep-guidance.resolved.json` stores authoritative downstream guidance before user edits
- `annotated-prep.pdf` is the user review surface
- `prep-guidance.reviewed.json` remains the final reviewed contract

E7-16 introduces a refinement request/response pair that captures the external vision handoff before review.

The request artifact must include enough information to:
- map back to the original proposal
- identify the page and annotation id
- provide the cropped image or review context the outer agent needs
- record the reason the proposal was flagged

The response artifact must include enough information to:
- map back to the original proposal
- record the revised rectangle
- record the reason for the change
- record when the refinement left a proposal unchanged

## Handoff Contract

The outer agent should receive a focused prompt and page-level image evidence for each ambiguous proposal.

Minimal request bundle:
- source pdf path
- proposal id
- page number
- raw proposal rectangle
- refinement hint reason
- extracted page image or cropped region image rendered from the original source PDF
- crop padding around the proposal so surrounding fills, borders, and nearby text remain visible
- relevant nearby text context

The refinement image must come from the original PDF render, not from `annotated-prep.pdf`. The user review PDF is a downstream artifact and must not feed back into geometry refinement.

The crop should be wide enough to preserve visual context:
- include the callout background fill when present
- include the callout border when present
- include nearby text that helps the agent determine the true extent of the note

For documents like the Homebrewery fixture, that means the outer agent should see the colored callout background, not just the text baseline or the annotation overlay.

Minimal response bundle:
- proposal id
- action: `refine` or `leave_unchanged`
- revised bounding box when refinement is requested
- short rationale for the decision
- optional confidence / uncertainty note

The code should apply the returned geometry only when the response artifact is valid. If the response is missing or invalid, the orchestrator should keep the existing geometry and continue from the raw proposal set.

## Capability and Skip Rules

Refinement must be skipped when any of the following are true:
- the user passes the explicit skip flag
- no proposals are flagged for refinement

Default behavior should be opportunistic:
- request refinement when supported and not explicitly skipped
- otherwise continue with the raw proposals and log why refinement was bypassed

The log output should be explicit enough for debugging but not noisy enough to drown out the normal prep flow.

## Mock Handoff Contract

Automated tests must not depend on paid or remote agent usage.

E7-16 therefore needs a mock handoff implementation that:
- accepts the same request shape as the real agent-facing workflow
- returns deterministic refinement output for test fixtures
- can be swapped into the harness without changing orchestration code
- can emulate both successful refinement and skip/no-op behavior
- is intentionally low-fidelity and only meant to keep the analyze flow moving
- should not be treated as a substitute for a real image-capable refinement model

The mock should be step-specific rather than generic. The test fixture should be able to verify that the pipeline reaches the refinement handoff and that the resulting geometry is applied consistently.

## User Experience

From the user’s perspective:
- the command still produces an annotated PDF for review
- callouts that are already clear remain unchanged
- callouts flagged as ambiguous may be adjusted automatically when supported
- the user can still revise the rendered PDF and run the existing review/update flow

The user should not need to interact with the refinement handoff directly unless they are debugging or explicitly opting into a stricter mode later.

## Testing Strategy

E7-16 must prove:
- refinement is requested only when hints are present and the pass is enabled
- the explicit skip flag bypasses refinement
- the mock handoff can drive the orchestration path in CI
- valid refinement responses update proposal geometry
- invalid or missing refinement responses fall back to raw proposal geometry
- the review contract remains intact

## Acceptance Outcome

E7-16 is complete when the prep pipeline can optionally refine ambiguous callout geometry through an external vision handoff, while:
- preserving raw detection evidence
- keeping the manual review flow intact
- supporting a deterministic mock-handoff path for CI
- avoiding unnecessary agent calls when refinement is skipped or unsupported
