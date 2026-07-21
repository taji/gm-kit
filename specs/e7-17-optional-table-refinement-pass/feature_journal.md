Session: 2026-07-15 - E7-17 Feature Start
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-15

Work Completed:
1. Added the E7-17 backlog story for an optional table refinement pass.
2. Created the E7-17 feature folder and initial feature journal.
3. Began drafting the design and implementation plan around the existing callout refinement pattern.

Key Decisions:
- E7-17 should reuse the same pause/revise/resume shape established for callouts.
- The feature should compare the current table workflow to the callout workflow and only close the gaps.
- Table detection itself is not being redesigned unless the comparison exposes a concrete mismatch.

Current State:
- The E7-17 feature folder now exists under `specs/e7-17-optional-table-refinement-pass/`.
- No code changes have been made yet for table refinement.
- The current worktree branch is still the E7-16 branch, so the feature artifacts are being created in-place for now.

Next Steps:
1. Finish the E7-17 design document.
2. Finish the E7-17 implementation plan.
3. Reconcile the table workflow with the callout handoff shape before touching code.

Recorded by: Codex

Session: 2026-07-21 - Table review mode clarified
--------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-21

Work Completed:
1. Clarified that the E7-17 table refinement pass supports both user review and optional agent-assisted refinement.
2. Confirmed the default workflow is user review of the annotated prep PDF, with agent review available for automation or handoff.

Key Decisions:
- User review remains the default refinement path.
- Agent review is optional and should be treated as an automation mode rather than the only supported path.
- The feature should preserve the same review/revise/resume contract regardless of whether the reviewer is the user or an agent.

Current State:
- E7-17 is still a planned feature with design and plan artifacts in place.
- The next step is to implement the table refinement flow so it matches the clarified review modes.

Next Steps:
1. Implement the table refinement flow to support the clarified user/agent review modes.
2. Add or update tests to cover both default user review and optional agent-assisted refinement.
3. Commit and push the updated feature journal once implementation begins.

Recorded by: Codex

Session: 2026-07-17 - Table crop rule baseline
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-17

Work Completed:
1. Agreed on a generic first-pass rule for table cropping: start at the detected table top and extend to the next heading/title or the end of the page.
2. Clarified that two-column tables should expand to the next left-column heading boundary, while one-column tables should stop at the next heading in the same column.
3. Confirmed the rule should be layout-driven rather than content-driven, and should be refined later if needed.

Key Decisions:
- Table detection should stop on the next clear heading/title boundary rather than trying to infer specific row contents.
- Column-aware stopping is required so full-width and single-column tables are both captured cleanly.
- The baseline rule should remain generic and avoid hard-coded document-specific text.

Current State:
- The table refinement design has a stable baseline crop rule.
- Implementation work is still paused; no code changes were made in this session.

Next Steps:
1. Implement the column-aware crop rule in the table detector.
2. Run the annotated Homebrewery and CoC fixtures to verify the rule does not regress the current good cases.
3. Tighten the detector only if the new baseline still misses table boundaries in a generic way.

Recorded by: Codex

Session: 2026-07-17 - Span-level table trim
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-17

Work Completed:
1. Added span-aware trimming for table regions so merged blocks can stop at heading-like lines inside the same extracted block.
2. Switched table annotation fill color to the fixture-matched light blue instead of cyan.
3. Re-ran Homebrewery and CoC prep analyses and verified the generated annotated PDFs.

Key Decisions:
- Homebrewery’s `Images` section is now trimmed out of the table bbox even though it lives in the same extracted text block as the table.
- The CoC page 16 table did not change from span trimming; it still stops at the same body boundary and does not yet include the later rows.
- Span-level trimming is the correct mechanism for mixed table/heading blocks; content-specific row labels remain off-limits.

Current State:
- Homebrewery table annotation now ends before the `Images` section and still preserves the `Weapons Table` title.
- CoC page 16 remains truncated after the `Moderate` row; pages 29 and 31 are unchanged.
- Both annotated PDFs are regenerated in the worktree tmp directory.

Next Steps:
1. Decide whether to keep refining the CoC page 16 generic continuation rule or leave it for the agent review path.
2. If we keep iterating, run the focused fixture checks again after the next detector change.

Recorded by: Codex

Session: 2026-07-17 - Annotated table rule set
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-17

Work Completed:
1. Replaced the table detector prototype with a layout-based rule set derived from the annotated Homebrewery and CoC fixtures.
2. Added integration coverage that validates the detector against the annotated table fixtures and asserts the expected table pages.
3. Kept the shared prep review flow intact while preserving table-specific cyan annotations.

Key Decisions:
- Table detection now requires compact row/column structure, a real table title or title-like first line, and repeated row fragments before a region is accepted.
- The detector rejects prose-heavy blocks and credits/copyright-style blocks instead of promoting them into tables.
- Homebrewery and CoC annotated fixtures are now the validation targets for this pass.

Current State:
- The Homebrewery annotated fixture yields one table proposal on page 2.
- The CoC annotated fixture yields three table proposals on pages 16, 29, and 31.
- Focused prep tests and ruff checks pass for the touched files.

Next Steps:
1. Run the broader prep regression slice if we want more confidence beyond the focused fixture tests.
2. Decide whether to merge this detector shape into the remaining table work or keep refining the optional edge cases later.

Recorded by: Codex

Session: 2026-07-16 - Added post-merge workflow cleanup TODO
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-16

Work Completed:
1. Added `E7-18. Post-Merge Workflow Directory Cleanup` to `BACKLOG.md`.
2. Captured the requested repo migration cleanup for after the analyze work is merged.

Key Decisions:
- The cleanup should happen after the current analyze/prep work is complete and merged.
- The repo should keep the backlog-aligned folder naming convention while moving from `specs/` to `work-items/`.

Current State:
- The backlog now contains a dedicated cleanup TODO for the Superpowers migration.
- No rename or uninstall work has been performed yet.

Next Steps:
1. Finish the current analyze/prep work before attempting the repository-wide cleanup.
2. Then rename the feature root, remove Spec-Kit leftovers, and normalize the Superpowers filenames.

Recorded by: Codex

Session: 2026-07-16 - Unified table and callout review pass
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-16

Work Completed:
1. Updated the E7-17 design and plan so table annotations use cyan and share one review PDF with callouts.
2. Clarified that revise/update should capture both table and callout corrections in a single review pass.

Key Decisions:
- The user reviews one annotated PDF for both annotation types instead of separate table and callout review cycles.
- Table annotations should remain machine-identifiable as `ap-...-table` while using cyan only as a visual cue.

Current State:
- The E7-17 design and plan now describe one shared review/repair pass.
- Implementation has not started yet.

Next Steps:
1. Inspect the current table and callout prep code paths to identify the shared render/resume boundary.
2. Implement the shared review PDF emission and related artifact wiring.
3. Add or update tests to cover the unified review flow.

Recorded by: Codex

Session: 2026-07-16 - Added dual-mode analyze command TODO
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-16

Work Completed:
1. Added `E7-19. Dual-Mode Analyze Command Entry Points` to `BACKLOG.md`.
2. Captured the requirement for both unattended analyze/prep runs and agent-driven pause/resume runs.

Key Decisions:
- The analyze entry point should support a no-pause unattended mode and a prompt-driven agent mode.
- The underlying analysis logic should remain shared so only orchestration differs between the two modes.

Current State:
- The backlog now records the dual-mode CLI entry-point TODO.
- No implementation work has been started for this behavior.

Next Steps:
1. Keep finishing the current table refinement work before implementing the CLI split.
2. When ready, define the exact just targets and agent prompt contract for the two modes.

Recorded by: Codex

Session: 2026-07-16 - Table pattern review paused
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-16

Work Completed:
1. Reviewed the annotated Homebrewery and CoC table fixtures supplied by Todd.
2. Confirmed the key table pattern examples include a full-width two-column table, narrower single-column tables, and stat-block style tables.
3. Agreed to resume later with a layout-driven detector that uses aligned rows/columns instead of title words.

Key Decisions:
- Table detection should not depend on the presence of the word "table" in titles.
- Page boundaries remain hard table boundaries; cross-page tables will be treated as separate proposals.
- The first-pass detector should prioritize aligned column structure and row regularity, with the annotated fixtures serving as the pattern reference set.

Current State:
- The table refinement design remains valid, but implementation of the tighter detector is paused until the next session.
- The annotated fixture PDFs are available for future review and tuning.

Next Steps:
1. Reopen the E7-17 table detector implementation.
2. Encode the observed table patterns into the first-pass detector.
3. Verify against the annotated Homebrewery and CoC fixtures before broadening scope.

Recorded by: Codex

Session: 2026-07-17 - Column-aware table continuation fix
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-17

Work Completed:
1. Tightened the table detector so continuation decisions use the current block instead of the title block as the column anchor.
2. Relaxed the stop rule so intervening numeric/table cells can remain part of the same table region even when the text column shifts.
3. Added a regression assertion that the CoC page-16 table region includes the later damage rows.

Key Decisions:
- Full-width and multi-column tables should be treated as one region as long as the layout still reads as table content.
- Column mismatch alone is not enough to end a table region when the next block still looks like a table cell.
- The detector should stop on real prose/heading boundaries, not on the internal structure of the table itself.

Current State:
- The table detector now includes the later CoC page-16 rows instead of stopping after the Moderate row.
- Homebrewery still trims before the Images section, and the table color remains the fixture-matched light blue.
- Focused regression tests and Ruff checks pass on the touched files.

Next Steps:
1. Run the annotated fixture analyzes again to confirm the visual output still matches expectations.
2. If the CoC table boundary is now correct visually, decide whether any additional refinement is worth the complexity.
3. Commit the table-detector and regression-test updates once the visual review is complete.

Recorded by: Codex

Session: 2026-07-17 - Table refinement crops added
---------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-17

Work Completed:
1. Added table refinement crop generation alongside the existing callout refinement flow.
2. Wrote table-specific review artifacts: `annotation-table-refinement-request.json` and `annotation-table-refinement-inputs.json`.
3. Updated the prep artifact manifest and unit tests to include the new table review files.
4. Verified the B2 fixture now emits table crop PNGs in `annotation-refinement/crops/`.

Key Decisions:
- Table crops should live in the same shared `annotation-refinement/crops/` directory as callout crops so the review surface stays in one place.
- Table proposals are reviewed as a separate artifact stream, even though they reuse the same crop directory.
- The table review path is capture-only for now; the full agent-driven correction flow can be added later.

Current State:
- B2 now produces 11 table crop images plus the existing callout crop images.
- The prep manifest includes the new table-refinement artifacts.
- Focused unit tests and Ruff checks pass.

Next Steps:
1. Inspect the new B2 table crop PNGs to confirm they match the problematic tables you identified.
2. Decide whether the table review step needs a dedicated agent handoff or if capture-only is sufficient for the next milestone.
3. If the crop set looks good, update any remaining docs or backlog notes and commit the work.

Recorded by: Codex

Session: 2026-07-17 - Crop filename prefixes and wider table crops
-------------------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-17

Work Completed:
1. Prefixed refinement crop filenames with their type: `callout-...` and `table-...`.
2. Expanded table crops with a larger default crop margin so review images include more context.
3. Updated the table crop test to expect the prefixed filename and the larger crop window.

Key Decisions:
- Crop filenames should encode the proposal type so file explorer sorting makes review easier.
- Table crops need larger margins than callouts so the AI can better judge missing lower rows and surrounding structure.
- The shared crop directory remains the same; only the filenames now distinguish the proposal type.

Current State:
- Focused tests and Ruff checks pass after the filename and crop expansion updates.
- B2 still emits both callout and table refinement artifacts, now with clearer file naming.
- The next useful check is visual review of the new crop sizes on Homebrewery and B2.

Next Steps:
1. Rerun the prep analyze command on Homebrewery and B2 if you want to visually verify the larger crops.
2. Review the new `callout-*` and `table-*` crop files in `annotation-refinement/crops/`.
3. Decide whether table/callout handoff should be formally unified or left capture-only for now.

Recorded by: Codex

Session: 2026-07-17 - Callout crop expansion for review context
---------------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-17

Work Completed:
1. Expanded callout review crops beyond the proposal bbox so continuation blocks remain visible to the reviewer.
2. Kept table crops on the wider context path and preserved the `callout-` / `table-` filename prefixes.
3. Re-ran the Homebrewery fixture after clearing the prep output to verify the updated callout crop was regenerated.

Key Decisions:
- Callout review crops should include the following text block(s) when they remain in the same column and within the continuation gap.
- The crop image should provide more visual context than the raw bbox so the reviewer can judge whether the callout boundary is too tight.
- Filename prefixes remain the primary way to distinguish callout and table crops in the shared review folder.

Current State:
- Homebrewery now emits a `callout-*` crop that is taller than the bbox and better captures the continuation text.
- Focused unit tests and Ruff still pass after the crop expansion change.
- The next check is whether the same crop rule remains acceptable on B2 before any further tuning.

Next Steps:
1. Review the new Homebrewery callout crop visually and confirm the extra context is sufficient.
2. Apply the same review pass to B2 only if the Homebrewery crop looks correct.
3. If needed, tune the continuation gap or heading stop logic rather than reverting to bbox-only crops.

Recorded by: Codex

Session: 2026-07-17 - Final crop review completed
--------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-17

Work Completed:
1. Reran the Homebrewery and CoC prep flows after the latest crop-expansion changes.
2. Confirmed the generated callout and table crop images are visually acceptable for review.
3. Verified the new crop naming convention and expanded crop regions are working as intended.

Key Decisions:
- The current crop expansion and filename prefixing are good enough for the first-pass refinement flow.
- No additional tuning is needed before moving on from callout/table capture.
- The existing warnings for a small number of multi-block callouts can remain as review guidance.

Current State:
- Homebrewery and CoC both produce usable `callout-*` and `table-*` crop images in `annotation-refinement/crops/`.
- The table and callout refinement artifacts are in place and validated by manual review.
- The first-pass crop work for callouts and tables is effectively complete.

Next Steps:
1. Commit the current worktree changes once you are ready.
2. If desired, decide whether to add the actual agent-driven crop response/resume flow for table refinement later.
3. Otherwise, move on to the next backlog item or cleanup task.

Recorded by: Codex
