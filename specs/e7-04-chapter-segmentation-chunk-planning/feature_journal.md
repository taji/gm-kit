Session: 2026-06-16 - E7-04 Feature Start
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-16

Work Completed:
1. Reviewed the E7-04 backlog scope and the E7-03 completion state as the prep baseline.
2. Confirmed the preferred chunking direction: chapter-first segmentation with a fixed 10-page fallback for oversized chapters.
3. Identified `Curse of Strahd` as a representative large-document shape for the chunk planning rule.

Key Decisions:
- Chapter boundaries are authoritative when present.
- Oversized chapters should split on page boundaries into 10-page chunks.
- No automatic merge back into a single markdown document by default.

Current State:
- E7-04 is in design/brainstorming.
- No implementation work has started.

Next Steps:
1. Finish the E7-04 design for chapter index and chunk-plan artifacts.
2. Write the E7-04 Superpowers design doc inside this feature folder after user approval.

Recorded by: codex (gpt-5)

Session: 2026-06-16 - E7-04 Review Corrections
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-16

Work Completed:
1. Re-reviewed E7-04 against the approved design and the real `Curse of Strahd` outline shape.
2. Refactored chunk planning to derive sections from top-level outline entries so nested same-page bookmarks no longer break prep runs.
3. Corrected the chunk-plan contract to use singular `source_section_id` and per-section ordinals for page-split chunks.
4. Updated the E7-04 design and plan docs to reflect the intended chapter-first behavior and removed the stale adjacent-chapter packing language.
5. Added regression coverage for nested same-page outline entries and top-level same-page ambiguity handling.

Key Decisions:
- Chapter segmentation is now explicitly based on top-level outline entries, not every TOC bookmark.
- Nested subsection bookmarks remain valid source metadata but do not create independent chapter chunks.
- Same-page ambiguity is only treated as fatal at the top-level chapter boundary, not for nested outline entries.

Current State:
- E7-04 is aligned with the approved chapter-first behavior and works on the `Curse of Strahd` outline shape.
- Prep-focused verification and the full repo gate both pass.

Next Steps:
1. Treat E7-04 as complete and stable input for E7-05.
2. Reuse the corrected `chapter-index.json` and `chunk-plan.json` contract in downstream chunk-to-markdown work.

Recorded by: codex (gpt-5)

Session: 2026-06-16 - E7-04 Chunk Planning Implemented
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-16

Work Completed:
1. Added TOC-driven chunk planning primitives in `src/gm_kit/pdf_convert/prep/chunking.py` with chapter-first section modeling, fixed 10-page fallback splits, and deterministic chunk serialization.
2. Extended prep analysis artifact paths to include `chapter-index.json` and `chunk-plan.json` and wired a new `prep.plan-chunks.build-chunk-plan` registry step into the prep orchestrator.
3. Updated prep manifest finalization so chunk artifacts are recorded only when they actually exist, preserving the "only when chunking is needed" contract.
4. Added unit coverage for TOC parsing, small-document no-op planning, chapter chunk emission, oversized section splitting, and prep orchestrator chunk-plan emission.

Key Decisions:
- Chunk planning remains chapter-first and does not merge chunks back into a single markdown document by default.
- Chunk artifacts are emitted only when the document exceeds the 10-page budget and are omitted for smaller documents.
- Front matter and appendices are included whenever the TOC exposes them.

Current State:
- E7-04 implementation is complete and verified.
- Repo-wide CI-equivalent checks pass after the chunk-planning wiring.

Next Steps:
1. Hand off to the next Epic 7 feature (`E7-05`).
2. If needed, review the generated chunk plan contract against later conversion steps.

Recorded by: codex (gpt-5)

Session: 2026-06-16 - E7-04 Design and Plan Written
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-16

Work Completed:
1. Wrote the E7-04 Superpowers design doc at `specs/e7-04-chapter-segmentation-chunk-planning/superpowers-design.md`.
2. Wrote the E7-04 implementation plan at `specs/e7-04-chapter-segmentation-chunk-planning/superpowers-plan.md`.
3. Anchored the feature on TOC-driven chapter indexing with a fixed 10-page fallback for oversized sections.
4. Confirmed that front matter and appendices stay in scope whenever the TOC exposes them.

Key Decisions:
- Emit `chapter-index.json` and `chunk-plan.json` only when chunking is needed.
- Keep chunk planning prep-side only and do not merge chunks back into a single document by default.
- Treat TOC order as authoritative for all chapter and chunk boundaries.

Current State:
- E7-04 has an approved design and a concrete implementation plan.
- No code changes for E7-04 have started yet.

Next Steps:
1. Choose `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement E7-04.
2. Start with the chunking models and TOC parsing task.

Recorded by: codex (gpt-5)
