# E7-05 Guidance + Annotation Proposal System Design

**Goal:** Add prep guidance artifacts and machine-readable annotation proposal generation for `table`, `callout`, and `skip`, while keeping resolved guidance deterministic and authoritative for later conversion.

## Architecture
E7-05 builds on the prep-first baseline from E7-03 and the chapter/chunk planning outputs from E7-04. It adds a guidance-and-proposal layer that consumes existing prep artifacts, applies user/default guidance intent, and produces machine-readable annotation proposals plus a normalized resolved guidance contract.

The architecture separates four concerns:
- input guidance intent
- raw proposal evidence
- resolved authoritative guidance
- optional visual review rendering

This separation is intentional. Raw proposals are evidence for review and later revision workflows; they are not the direct authoritative input to downstream conversion. The authoritative prep output is `prep-guidance.resolved.json`.

E7-05 does not implement interactive review/revision UX. That belongs to E7-06. E7-05 prepares for that later workflow by giving proposals stable IDs, shared structure, bbox metadata, and provenance.

## Artifact Contract
E7-05 introduces the following prep artifacts under `<workspace>/prep/`:

- `prep-guidance.input.json`
- `annotation-proposals.json`
- `prep-guidance.resolved.json`
- `annotated-prep.pdf` (optional)

### `prep-guidance.input.json`
Purpose:
- capture explicit user preferences and defaults that influence proposal generation and guidance normalization

Typical content:
- skip-related preferences
- table detection preferences
- callout handling preferences
- auto-accept/bypass indicators when relevant later

This is input intent, not final conversion instruction.

### `annotation-proposals.json`
Purpose:
- capture raw machine-generated proposal evidence for later review and normalization

This is the primary proposal artifact. It is JSON, not PDF.

Each proposal uses a shared base schema:
- `proposal_id`
- `label`
- `page`
- `bbox`
- `confidence`
- `metadata`

Allowed labels:
- `table`
- `callout`
- `skip`

Common semantics:
- `label` is canonical behavior
- `bbox` defines the proposed region
- `page` is 1-based
- `confidence` is a numeric confidence signal
- `metadata` holds label-specific and provenance-specific detail

`skip` must support both:
- full-page skip proposals
- region skip proposals

Example:

```json
{
  "proposal_id": "p-017",
  "label": "skip",
  "page": 12,
  "bbox": [0, 0, 612, 792],
  "confidence": 0.96,
  "metadata": {
    "scope": "full-page",
    "reason": "map insert",
    "source": "code"
  }
}
```

### `prep-guidance.resolved.json`
Purpose:
- provide the single authoritative, normalized downstream contract

This artifact is the only guidance/annotation file later conversion features should treat as authoritative.

It should normalize accepted/defaulted guidance into deterministic fields such as:
- `skip_pages`
- `skip_regions`
- `table_regions`
- `callout_regions`

It may also carry normalized policy information derived from `prep-guidance.input.json` where needed, but it should stay concise and downstream-oriented.

The resolved artifact must not require downstream conversion to reinterpret raw proposal confidence, provenance, or review evidence.

### `annotated-prep.pdf`
Purpose:
- optional visual review companion

This artifact is helpful for human inspection, but it is not authoritative. Visual style, color, and overlay treatment are review aids only. Semantic label behavior remains canonical in JSON.

## Shared Proposal Schema
All proposal labels use the same base record shape:
- `proposal_id`
- `label`
- `page`
- `bbox`
- `confidence`
- `metadata`

Benefits:
- simpler validation
- easier review tooling later
- shared serialization and testing
- easier conversion from visual revisions back into structured data in E7-06

Label-specific semantics belong in `metadata`, not in separate top-level schemas.

## Generation Strategy
E7-05 should be conservative and provenance-aware.

Proposal generation should use:
- existing prep artifacts
- structure and segmentation context from E7-04
- reusable code heuristics where reliable
- AI-assisted generation only where heuristics are insufficient

Expected tendencies:
- `table` proposals: layout/structure heuristics first
- `callout` proposals: heuristics plus AI assistance where needed
- `skip` proposals: explicit rules plus detected anomalous/irrelevant regions or full pages

Proposal provenance should be first-class metadata. Each proposal should preserve source details such as:
- `source: code`
- `source: ai`
- `source: hybrid`

Metadata should also preserve enough explanation to support later review:
- heuristic reason
- concise AI rationale summary if AI-generated
- confidence provenance where helpful

E7-05 does not need to solve perfect detection. It needs to produce deterministic, machine-readable proposal evidence and a normalized authoritative guidance artifact.

## Normalization Rules
Normalization is the process that converts raw proposal evidence plus input intent into `prep-guidance.resolved.json`.

Rules:
- resolved output is authoritative
- raw proposals remain separate evidence
- label semantics are canonical
- full-page skips and region skips are both supported
- downstream fields should be stable and explicit

Normalization must not depend on visual overlay artifacts.

The later review workflow in E7-06 may update resolved output after user edits, but E7-05 must define the contract clearly enough that later features do not need to redesign it.

## Failure Handling
E7-05 failures should be explicit and narrow.

Rules:
- if proposal generation fails entirely, prep fails with sanitized diagnostics
- if one proposal type fails but others succeed, partial success is allowed only if the resolved contract can represent the incomplete state explicitly and truthfully
- `prep-guidance.resolved.json` must never imply successful proposal acceptance when generation actually failed
- failure to render `annotated-prep.pdf` should not invalidate a prep run if the JSON artifacts are complete and valid
- proposal IDs must be stable and deterministic for the same input artifact set

This keeps JSON artifacts as the durable machine contract while treating visual rendering as optional support output.

## Testing Strategy
E7-05 tests must prove:
- `prep-guidance.input.json` validates and round-trips
- `annotation-proposals.json` uses the shared base schema across `table`, `callout`, and `skip`
- `skip` supports both full-page and region proposals
- resolved guidance normalizes accepted/defaulted proposals into deterministic downstream fields
- proposal provenance/source metadata is preserved
- optional annotated PDF rendering does not invalidate otherwise-complete prep output
- proposal IDs are deterministic for the same inputs
- artifact content is deterministic for the same fixture inputs

## Scope Notes
E7-05 includes:
- prep guidance input artifact definition
- annotation proposal artifact definition
- resolved guidance artifact definition
- proposal generation behavior
- normalization behavior
- optional visual review artifact support

E7-05 does not include:
- interactive review/revision UX
- visual bbox editing workflow
- conversion consumption/gating
- final markdown generation

Those belong to later Epic 7 features, especially E7-06 and E7-07.
