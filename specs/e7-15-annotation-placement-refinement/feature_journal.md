Session: 2026-07-10 - E7-15 implementation pass
--------------------------------------------------------
Branch: e7-15-annotation-placement-refinement
Date: 2026-07-10

Work Completed:
1. Migrated prep guidance defaults from JSON to YAML and updated the artifact path to `prep-guidance.defaults.yml`.
2. Added `prep/callout_detection.py` to detect callout regions from PDF text anchors and wire those proposals into prep generation.
3. Added unit and integration coverage for detector behavior, Homebrewery bbox refinement, and updated prep orchestration tests.

Key Decisions:
- Keep user-authored prep defaults in YAML while leaving generated contracts as JSON.
- Detect callout regions from PDF text geometry instead of image-count heuristics.
- Preserve OCR fallback as out of scope for this feature.

Current State:
- `just test`, `just lint`, `just typecheck`, `pytest --cov=src`, `pip-audit`, and `bandit -r src` all passed in the worktree.
- The new Homebrewery-updated fixture is present in the worktree and the integration test verifies the refined bbox intersects the GM Note anchor.

Next Steps:
1. Update user-facing docs and backlog references to reflect the YAML defaults and text-anchor callout detection.
2. Review whether any remaining prep docs still describe the old image-based callout behavior.
3. Commit the feature work once docs are reconciled.

Recorded by: Codex

Session: 2026-07-11 - Homebrewery Temp Fixtures Removed
--------------------------------------------------------
Branch: e7-15-annotation-placement-refinement
Date: 2026-07-11

Work Completed:
1. Switched the Homebrewery callout bbox integration test to the canonical `The Homebrewery - NaturalCrit.pdf` fixture.
2. Removed the temporary `The Homebrewery - NaturalCrit-updated.pdf` and `The Homebrewery - NaturalCrit-callout-reference.pdf` files from the worktree.
3. Re-ran the focused integration test to confirm the canonical fixture still exercises the callout bbox refinement path.

Key Decisions:
- The canonical Homebrewery fixture should be the single source of truth for the callout bbox regression test.
- Temporary fixture variants are no longer needed once the canonical PDF carries the updated content and TOC.

Current State:
- The integration test now points at `The Homebrewery - NaturalCrit.pdf`.
- The temporary PDFs are deleted from the worktree and the focused integration test passes.

Next Steps:
1. Keep using the canonical Homebrewery fixture for future callout bbox checks.
2. Commit the fixture cleanup with the rest of the worktree changes when ready.

Recorded by: Codex

Session: 2026-07-11 - Homebrewery Fixtures Reconciled
--------------------------------------------------------
Branch: e7-15-annotation-placement-refinement
Date: 2026-07-11

Work Completed:
1. Replaced `The Homebrewery - NaturalCrit - Without TOC.pdf` with the updated Homebrewery render.
2. Rebuilt `The Homebrewery - NaturalCrit.pdf` from the updated render while preserving the original embedded TOC.
3. Verified the with-TOC fixture still has an embedded outline while the without-TOC fixture does not.

Key Decisions:
- Both Homebrewery fixture PDFs must remain content-equivalent except for the embedded TOC outline.
- The updated render becomes the canonical source content for both fixture variants.

Current State:
- The Homebrewery fixtures in the worktree now reflect the updated PDF content.
- The with-TOC fixture retains 23 TOC entries; the without-TOC fixture has none.

Next Steps:
1. Re-run any fixture-sensitive tests if you want to validate the Homebrewery updates end-to-end.
2. Commit the fixture regeneration with the rest of the worktree changes when ready.

Recorded by: Codex

Session: 2026-07-11 - Refinement Hint Artifact Added
--------------------------------------------------------
Branch: e7-15-annotation-placement-refinement
Date: 2026-07-11

Work Completed:
1. Added `annotation-refinement-hints.json` to the prep artifact inventory in the worktree baseline.
2. Kept the callout detector behavior unchanged while recording multi-block overexpansions as structured JSON hints.
3. Updated the prep tests and reran the Call of Cthulhu fixture to confirm the warning hints are emitted in the worktree output.

Key Decisions:
- The worktree remains the source of truth for E7-15.
- Overexpansion warnings should be persisted as structured JSON hints, but the detector itself should stay on the working baseline path.
- The root repo drift was intentionally discarded rather than merged back in.

Current State:
- `analyze-and-prep-pdf` in the worktree now writes `annotation-refinement-hints.json` alongside the proposal JSON.
- The Call of Cthulhu rerun still reports the same two overexpansion warnings and now stores them in the hint artifact.
- Targeted prep tests are passing after the worktree-only change.

Next Steps:
1. Keep working in the worktree checkout only.
2. Decide whether any additional user-facing documentation should mention the new hint artifact.

Recorded by: Codex

Session: 2026-07-10 - Annotation Styling Verified
--------------------------------------------------------
Branch: e7-15-annotation-placement-refinement
Date: 2026-07-10

Work Completed:
1. Verified the smaller right-aligned FreeText label style on the Homebrewery fixture.
2. Reran the full analyze flow on both Homebrewery and CoC fixtures.
3. Confirmed both fixtures still generate editable annotations and the detector warnings remain limited to the same expected multi-block callouts.

Key Decisions:
- Keep the smaller, right-aligned annotation text style; it improves readability without changing the underlying annotation workflow.
- Leave the current detector warnings in place because they document the rare over-expansion cases without blocking prep.

Current State:
- Homebrewery remains at 1 callout annotation and CoC remains at 18 callout annotations after rerun.
- The callout review artifacts are still editable and visually usable in the PDF viewers we checked.

Next Steps:
1. No immediate code changes are required unless the user wants to tighten the two CoC multi-block expansions later.
2. Proceed to the next Epic 7 item or close out this review work as requested.

Recorded by: Codex

Session: 2026-07-10 - FreeText Text Placement Tweaks
--------------------------------------------------------
Branch: e7-15-annotation-placement-refinement
Date: 2026-07-10

Work Completed:
1. Reduced the rendered FreeText annotation font size from 10pt to 6pt.
2. Switched the annotation text alignment to right-justified so the label sits away from the underlying PDF text.
3. Re-ran the Homebrewery prep flow and confirmed the regenerated annotated PDF still produces a single callout annotation.

Key Decisions:
- The yellow box geometry can remain imperfect; the text placement is the part that matters for readability.
- A smaller, right-aligned label is sufficient for the current review workflow.

Current State:
- Homebrewery prep still generates one callout annotation and the annotation text is now less intrusive.
- The CoC fixture behavior is unchanged from the prior detector update.

Next Steps:
1. Have the user inspect the new Homebrewery annotated PDF and confirm the text placement improvement.
2. Only revisit bbox geometry if the user still finds the text too close to the underlying content.

Recorded by: Codex

Session: 2026-07-10 - Callout Fallback Warnings
--------------------------------------------------------
Branch: e7-15-annotation-placement-refinement
Date: 2026-07-10

Work Completed:
1. Reworked callout detection to grow proposals from text blocks in reading order, stopping at column breaks or large vertical gaps.
2. Added a line-level phrase-only fallback path for missed anchors and wired warning output into the prep analysis command.
3. Added regression tests for the CoC multi-note page and for the phrase-only fallback path.

Key Decisions:
- Block-level detection is the primary path because it matches the callout layout in the fixture better than the old line-only span growth.
- Phrase-only fallback should remain available for missed anchors so users can manually expand the short annotation in their PDF editor.
- Warning output belongs in the prep command flow, not only in returned artifacts.

Current State:
- `detect_callout_proposals()` still returns the raw proposal list, while `detect_callout_proposals_with_warnings()` exposes the warning summary for the prep command.
- The CoC fixture still yields 4 callout proposals on page 19 and the targeted prep/integration tests are passing.

Next Steps:
1. Re-run the full prep-oriented checks if you want broader confidence beyond the targeted slices.
2. Decide whether the warning summary should also be persisted as an artifact, or if console output is enough.
3. Continue with the next Epic 7 item once this review flow is accepted.

Recorded by: Codex

Session: 2026-07-10 - Callout BBox Tightened
--------------------------------------------------------
Branch: e7-15-annotation-placement-refinement
Date: 2026-07-10

Work Completed:
1. Tightened the callout region collector to read text top-to-bottom and stop after the current note block’s continuation text.
2. Verified the CoC fixture no longer spans multiple Keeper’s Note blocks; the callout bbox now stays within a single note block.
3. Re-ran the prep slice and confirmed lint/typecheck still pass.

Key Decisions:
- Text line ordering should be spatial, not extraction-order driven, before callout region growth.
- A slightly looser continuation gap is acceptable as long as the region no longer absorbs subsequent note blocks.

Current State:
- The CoC fixture now produces 10 callout proposals and the rendered annotations are tighter.
- The Homebrewery fixture remains correct.

Next Steps:
1. If needed, do one more user-visible CoC check to confirm the new bbox feels right in the PDF viewer.
2. Leave table suppression unchanged unless another fixture exposes a regression.

Recorded by: Codex

Session: 2026-07-10 - Table Detection Suppressed When Disabled
--------------------------------------------------------
Branch: e7-15-annotation-placement-refinement
Date: 2026-07-10

Work Completed:
1. Changed prep proposal generation so table proposals are not emitted when `prefer_detect_tables` is false.
2. Updated the prep tests to assert that disabled table detection suppresses table entries in raw proposals and in the final annotation surface.
3. Re-ran the Call of Cthulhu fixture and verified both `annotation-proposals.json` and `annotated-prep.pdf` contain callouts only.

Key Decisions:
- When table detection is disabled, the pipeline should bypass table generation entirely rather than generate and filter later.
- `annotation-proposals.json` remains raw evidence for enabled detectors, but disabled detectors should not leave table artifacts behind.

Current State:
- The CoC fixture now produces 10 callout proposals and 0 table proposals.
- The rendered review PDF also contains only callouts.

Next Steps:
1. Ask the user whether they want to tighten the callout span heuristic next.
2. Keep the current table suppression behavior unless a later fixture shows a need to change it.

Recorded by: Codex

Session: 2026-07-10 - FreeText Renderer Restored
--------------------------------------------------------
Branch: e7-15-annotation-placement-refinement
Date: 2026-07-10

Work Completed:
1. Traced the non-editable black-box regression to `render_annotated_prep_pdf()` still drawing rectangles and stamping text instead of creating real annotations.
2. Restored the renderer to create real `FreeText` annotations with yellow styling and 50% opacity.
3. Updated the renderer regression test to assert the PDF contains a real annotation object and verified the fresh Homebrewery output directly.

Key Decisions:
- Prep review artifacts must be real PDF annotations so the user can edit them in Okular/PDF Studio.
- Border inflation around the annotation is acceptable; the important requirement is that the object remains a real editable annotation with the expected fill/opacity.

Current State:
- The fresh Homebrewery output now contains one editable `FreeText` annotation on page 1.
- PyMuPDF inspection of the saved artifact shows `FreeText`, opacity `0.5`, and yellow annotation styling.

Next Steps:
1. Ask the user to re-open the regenerated Homebrewery output and confirm the annotation is editable in their viewer.
2. Tighten bbox placement further only if the geometry still feels off in the viewer.
3. Leave the unrelated legacy `Phase 2` test failures alone unless the user explicitly wants them addressed.

Recorded by: Codex

Session: 2026-07-11 - Worktree Guidance Captured
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-07-11

Work Completed:
1. Added a worktree-local `GEMINI.md` to document that this feature must stay in the active worktree checkout.
2. Explicitly captured the command rule that validation commands should name the exact checkout they run in.
3. Recorded the policy that the worktree is the source of truth for this feature when it differs from the root repo.

Key Decisions:
- The active feature checkout is `/home/todd/Dev/gm-kit/.worktrees/e7-15-annotation-placement-refinement`.
- Commands and edits for E7-15 should target that checkout unless the user explicitly changes the scope.

Current State:
- The worktree now has local guidance to reduce root-vs-worktree confusion.
- The feature journal reflects the new workspace rule.

Next Steps:
1. Continue feature work in the worktree checkout only.
2. Use the new guidance when giving or running validation commands.

Recorded by: Codex
