Session: 2026-06-18 - E7-06 Feature Start
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Restored E7-06 scope from `BACKLOG.md` and the E7-05 completed handoff context.
2. Created the E7-06 feature folder and feature journal.
3. Began reviewing existing CLI interaction patterns and prep artifact contracts to ground the E7-06 design.

Key Decisions:
- E7-06 will build directly on the finalized E7-05 guidance/proposal artifacts rather than redefining them.
- The E7-06 review flow must distinguish interactive review from non-interactive auto-accept/bypass behavior in machine-readable artifacts.

Current State:
- E7-06 context is restored and the feature folder is initialized.
- Design work is in progress; no E7-06 implementation changes exist yet.

Next Steps:
1. Inspect current prompt/CLI interaction patterns in the prep and conversion code.
2. Define the E7-06 artifact updates and review state transitions.
3. Write `specs/e7-06-annotation-review-ux-skip-intent-capture/superpowers-design.md`.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-07 Deferred Pending Prep Split
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Reviewed the current Epic 7 contract boundary for `pdf-convert` versus prep-produced artifacts.
2. Confirmed that tables and callouts should be migrated into prep/review flows before hard-gating conversion.
3. Agreed to defer E7-07 until the prep-side split stories are completed and the handoff contract is stable.
4. Identified the next work as separate prep stories for tables and callouts, followed by the conversion gate.

Key Decisions:
- E7-07 is a consumer/gate story and should not finalize while the prep artifact contract is still changing.
- Tables and callouts need their own prep-side stories first so the conversion gate has a fixed contract to enforce.
- Keep the conversion gate focused on validating and consuming prep outputs rather than defining them.

Current State:
- E7-07 is intentionally deferred.
- The next Epic 7 work should be prep-side producer stories before returning to the conversion gate.

Next Steps:
1. Draft the E7-06a/E7-06b prep-side stories for tables and callouts.
2. Resume E7-07 only after those prep artifacts and review/update flows are settled.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-06 Workflow Split Implemented and Docs Aligned
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Implemented the split prep/revise workflow for E7-06 so prep now exits after producing baseline review artifacts and a separate `revise-prep-guidance` command writes `prep-guidance.reviewed.json`.
2. Added the reviewed-guidance path plumbing and effective-guidance loader so the repo can prefer reviewed guidance when it is present.
3. Updated the E7-06 `superpowers-design.md` and `superpowers-plan.md` to remove stale finalize terminology and reflect the revised command split.
4. Kept the feature backlog and tests aligned with the new baseline-resolved versus reviewed-guidance artifact model.

Key Decisions:
- Prep should remain file-backed and non-blocking: generate artifacts, exit, and let revision happen in a separate command.
- `prep-guidance.resolved.json` is the baseline prep output; `prep-guidance.reviewed.json` is the user-reviewed artifact.
- Superpowers workflow docs should live inside the feature folder rather than in the tool default locations.

Current State:
- The E7-06 implementation and documentation are consistent with the split workflow.
- Downstream conversion still needs to be wired to actively consume reviewed guidance if that behavior is not already in place.

Next Steps:
1. Decide whether E7-06 is complete as-is or whether the conversion consumer should be updated in a follow-up feature.
2. If the consumer wiring is needed, update the conversion orchestration to load reviewed guidance first and then verify the change end-to-end.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-06 Prep/Revised Workflow Implemented
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Reworked the prep workflow so `analyze-and-prep-pdf` now emits review artifacts and baseline resolved guidance, then exits without pausing for resume.
2. Added the separate `revise-prep-guidance` command, which reads edited review artifacts and writes `prep-guidance.reviewed.json`.
3. Added `load_effective_prep_guidance` for choosing reviewed guidance when present and updated artifact-path plumbing to include the reviewed file.
4. Updated CLI wiring and unit coverage for the new command, artifact paths, manifest behavior, and review-helper flow.
5. Ran the focused prep/CLI tests, `ruff`, `mypy`, and the full `just all_ci_actions` gate successfully.

Key Decisions:
- Prep now stays deterministic and non-interactive; review is a separate follow-up command instead of a pause/resume checkpoint.
- `prep-guidance.resolved.json` is the baseline prep output; `prep-guidance.reviewed.json` is the reviewed artifact written only after revision.
- The reviewed artifact path is discoverable through the prep artifact manifest once `revise-prep-guidance` runs.

Current State:
- The code and tests now match the revised workflow docs.
- The conversion pipeline still does not actively consume reviewed guidance in a downstream phase; the new loader is in place for the next feature or follow-up wiring pass.

Next Steps:
1. Wire conversion to prefer reviewed guidance when present.
2. Move on to the next Epic 7 feature once the conversion consumer hook is ready.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-06 Workflow Reframed
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Reframed E7-06 from a pause/resume review loop into a prep → revise → convert workflow.
2. Updated `BACKLOG.md` to describe prep producing review artifacts, a separate revision step, and conversion consuming reviewed guidance when present.
3. Revised `superpowers-design.md` and `superpowers-plan.md` to standardize on `prep-guidance.reviewed.json` as the reviewed artifact and to treat `prep-guidance.resolved.json` as the baseline prep output.

Key Decisions:
- Prep now ends cleanly after generating review artifacts and guidance instructions.
- The reviewed artifact name will be `prep-guidance.reviewed.json`.
- Automation can skip the revision step and convert directly from the baseline resolved guidance.

Current State:
- The feature docs now describe the split workflow, but the code still reflects the earlier prep-side review flow.
- A future implementation pass will need to realign the prep and conversion code with the revised docs.

Next Steps:
1. Update the implementation plan for the revise command and reviewed-guidance consumer.
2. Decide whether to keep the current prep review code as a temporary implementation or replace it before continuing.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-06 Review Runtime Wired
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Wired the prep runtime to include the E7-06 review phase and finalization phase in the default registry.
2. Added `handle_seed_annotation_review`, `handle_render_annotated_prep_pdf`, and `handle_finalize_reviewed_guidance`, and updated `handle_generate_annotation_proposals` to keep raw proposal evidence immutable.
3. Expanded artifact publishing to include `annotation-review.edits.json` and `annotated-prep.pdf`.
4. Added focused unit coverage for review seeding, review finalization, runtime registry/export wiring, and the renderer save-failure path.
5. Ran the focused prep tests, `ruff check`, `mypy`, and the full `just all_ci_actions` gate successfully after fixing a Bandit false positive in the skip-range parser.

Key Decisions:
- Review edits are seeded as file-backed artifacts and finalized into `prep-guidance.resolved.json` using the same prep workspace subtree.
- Raw annotation proposals remain evidence-only; final resolved guidance is regenerated from the review artifact rather than from the proposal writer.
- Skip-range capture is parsed during finalization so explicit page skips and review-edited skip intent merge before resolved guidance is written.

Current State:
- E7-06 runtime wiring is in place and verified across unit, integration, lint, typecheck, and security gates.
- The prep workflow now emits review artifacts during the standard prep run.

Next Steps:
1. Move to the next Epic 7 feature or any follow-up review workflow adjustments.
2. If interactive pause/resume behavior is still desired, layer it on top of the current review artifact pipeline in a separate pass.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-06 Task 3 Review Helpers
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Added review-handler unit coverage for review edit seeding, proposal application, final resolved guidance, and annotated PDF rendering.
2. Implemented `build_annotation_review_edits`, `apply_review_edits_to_proposals`, `build_final_resolved_guidance`, and `render_annotated_prep_pdf` in `handlers.py`.
3. Kept skip precedence deterministic: explicit full-page skips merge into resolved pages, region skips populate `skip_regions`, and overlapping table/callout regions are excluded.
4. Verified the new helpers with targeted `pytest`, `ruff check`, and `mypy` runs.

Key Decisions:
- Review edits now default to empty decision state and derive review status from the requested review mode.
- Final resolved guidance treats omitted explicit skip pages as an empty list and only includes table/callout proposals that survive skip precedence.
- Annotated PDF rendering stays lightweight: rectangle overlays plus stable proposal ID/label stamps.

Current State:
- Task 3 is implemented in the owned handler file and covered by a focused unit test file.
- The prep review helpers are not yet wired into the runtime/orchestrator flow.

Next Steps:
1. Wire the new review helpers into the prep runtime when the next task in the E7-06 plan begins.
2. Extend artifact plumbing if the runtime needs to persist or reload review edits.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-06 Plan Written
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Reviewed the approved E7-06 design and mapped it onto the existing prep contracts, handlers, artifact paths, and orchestrator phases.
2. Wrote the implementation plan to `specs/e7-06-annotation-review-ux-skip-intent-capture/superpowers-plan.md`.
3. Broke the work into review contracts, skip parsing, review/finalization helpers, runtime wiring, and final verification/handoff tasks.
4. Kept the plan aligned with the current prep architecture by extending E7-05 artifacts rather than introducing a parallel workflow.

Key Decisions:
- The editable review state will be represented as `annotation-review.edits.json`.
- Interactive review should use a resume-after-edit pattern, while non-interactive mode should finalize with explicit `auto_accept` provenance.
- The final E7-06 writer of `prep-guidance.resolved.json` should enforce skip precedence and become the last authoritative normalization step before conversion.

Current State:
- E7-06 now has both a design doc and an implementation plan.
- No implementation work has started yet.

Next Steps:
1. Choose the E7-06 execution mode.
2. Implement the plan task-by-task, starting with review/edit contracts and guidance input extensions.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-06 Design Written
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Reviewed the E7-06 backlog requirements and the finalized E7-05 artifact model.
2. Inspected existing CLI prompt/resume patterns to keep the review UX aligned with the current Python CLI architecture.
3. Defined the E7-06 review workflow around `annotated-prep.pdf`, a structured review edits artifact, explicit skip range capture, and final resolved-guidance regeneration.
4. Wrote the design document to `specs/e7-06-annotation-review-ux-skip-intent-capture/superpowers-design.md`.

Key Decisions:
- E7-06 should use a file-backed review/resume loop rather than attempting a terminal-native bbox editor.
- Raw proposal evidence stays immutable in `annotation-proposals.json`; user review decisions live in a new `annotation-review.edits.json` artifact.
- `skip` precedence should be enforced during finalization, with full-page skip first and region overlap exclusion second.

Current State:
- E7-06 now has a drafted design grounded in the existing prep runtime and E7-05 artifacts.
- No E7-06 implementation work has started yet.

Next Steps:
1. Review the E7-06 design assumptions, especially the new `annotation-review.edits.json` artifact and the resume-after-edit workflow.
2. Write `specs/e7-06-annotation-review-ux-skip-intent-capture/superpowers-plan.md`.
3. After plan approval, implement skip parsing, review artifact seeding/finalization, and review-phase runtime wiring.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-06 Downstream Consumer Wired
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Wired Phase 9 and Phase 10 to load effective prep guidance from the prep workspace and pass it into the agent payloads used by quality assessment and reporting.
2. Updated the shared step-payload builders so guidance is attached to the agent context without changing the existing required artifact contracts.
3. Added unit coverage proving reviewed guidance is preferred over baseline resolved guidance when both exist.
4. Re-ran the focused phase tests, `ruff check`, `mypy`, and the full `just all_ci_actions` gate successfully.

Key Decisions:
- Downstream conversion consumers should receive guidance as part of agent context, not as a hard dependency on a new file format.
- Reviewed guidance wins over resolved guidance when both are present; baseline resolved guidance remains the fallback.
- Keep the prep artifact loader in the prep package and reuse it from the conversion phases rather than duplicating selection logic.

Current State:
- The downstream conversion pipeline now consumes prep guidance and prefers reviewed guidance when it exists.
- The repo is green after the consumer wiring change.

Next Steps:
1. Move on to the next Epic 7 feature or, if desired, extend E7-07 to hard-gate conversion on required prep artifacts.
2. If E7-07 starts next, update the conversion orchestration and user-facing error handling around missing prep outputs.

Recorded by: codex (gpt-5)
