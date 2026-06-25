Session: 2026-06-19 - E7-06b Feature Start
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-19

Work Completed:
1. Created the E7-06b feature folder and journal scaffold.
2. Captured callout detection as the next prep-side review handoff story after E7-06a.
3. Aligned callout handling with the same prep/review/update pattern used for other Epic 7 artifacts.

Key Decisions:
- Callout detection should move into prep as a reviewable handoff artifact.
- Conversion should consume finalized callout JSON and not rediscover callouts itself.

Current State:
- E7-06b exists as a named backlog item and feature folder.
- No spec or implementation content has been written yet.

Next Steps:
1. Draft the E7-06b spec/design for callout proposal review.
2. Define the exact prep artifact shape for finalized callout decisions.
3. After approval, implement the prep-side callout review workflow.

Recorded by: codex (gpt-5)

Session: 2026-06-19 - Callout-config sweep
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-19

Work Completed:
1. Swept the remaining `gm_callout_config` references across the repo to separate legacy input plumbing from downstream consumption.
2. Confirmed the conversion-side quality check path no longer depends on a standalone callout-config artifact.
3. Left the Phase 0 / CLI / preflight configuration plumbing intact because it still represents user-supplied input wiring.

Key Decisions:
- The prep-guidance contract is now the authoritative downstream source for reviewed callout decisions.
- Legacy config wiring can remain until the actual callout discovery/formatting phases are migrated away from it.

Current State:
- Phase 9 is prep-driven for callout review, while Phase 7/8 still carry the legacy user-input path.
- No further code changes were made in this sweep.

Next Steps:
1. Defer Phase 7/8 callout-config removal to a later story.
2. When revisited, treat it as a separate refactor because it changes the callout discovery/formatting pipeline itself.

Recorded by: codex (gpt-5)

Session: 2026-06-19 - Conversion callout cutover
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-19

Work Completed:
1. Updated Phase 9 callout assessment to consume reviewed prep guidance instead of a separate callout-config input.
2. Changed the step 9.5 payload builder and instruction template to pass `prep_guidance` through the agent contract.
3. Added regression coverage that verifies reviewed callout regions round-trip into the Phase 9 agent payload.
4. Re-ran the focused prep and Phase 9 test slice plus Ruff on the touched files.

Key Decisions:
- Shared prep guidance is the authoritative source for reviewed callout decisions.
- Phase 9 should receive callout context from `prep-guidance.reviewed.json` / resolved prep guidance rather than a callout-specific config artifact.

Current State:
- Prep-side callout review is locked down and downstream Phase 9 now consumes reviewed callout guidance through the shared prep contract.
- Focused tests and lint checks are passing.

Next Steps:
1. Review whether any remaining conversion phases still depend on the old callout-config path.
2. If so, migrate them to the shared prep guidance contract before starting the next feature.

Recorded by: codex (gpt-5)

Session: 2026-06-19 - Prep callout review regression
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-19

Work Completed:
1. Added a callout-specific prep regression test that exercises `run_new_prep()` with callout proposals, annotated PDF output, and final review materialization.
2. Verified `revise_prep_guidance()` finalizes reviewed callout decisions into the shared `prep-guidance.reviewed.json` artifact and updates the shared prep manifest in place.
3. Confirmed the focused prep test slice and Ruff checks pass after the test update.

Key Decisions:
- Kept the review flow anchored on the annotated prep PDF and the shared prep workspace.
- Reused the existing shared prep guidance artifact shape instead of introducing any callout-only manifest.

Current State:
- Prep review coverage now includes a callout-specific regression path in addition to the existing table-oriented coverage.
- The targeted prep workflow tests are green.

Next Steps:
1. Proceed with the remaining E7-06b callout migration work, if any, in the conversion phases.
2. Re-run broader prep/conversion tests only if the callout contract changes again.

Recorded by: codex (gpt-5)

Session: 2026-06-19 - Callout guidance contract lock
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-19

Work Completed:
1. Added regression coverage for `PrepGuidanceResolved.callout_regions` round-tripping with `proposal_id`, `page`, `bbox`, `label`, and JSON-safe extra metadata.
2. Updated the shared prep guidance contract so callout regions require labels and accept `callout_gm` / `callout_read_aloud`.
3. Normalized callout regions in shared prep handlers to emit stable proposal IDs plus explicit callout labels.
4. Updated prep review/guidance tests to expect labeled callout regions and verified the focused prep suite.

Key Decisions:
- Callout regions stay in the shared resolved guidance artifact instead of introducing a new callout-only artifact.
- `callout_gm` is the default normalized label when a proposal does not carry an explicit `callout_label` metadata override.
- Table and skip regions remain unchanged; only callout regions gained label enforcement.

Current State:
- `prep-guidance.resolved.json` now validates callout labels and preserves them during round-trip serialization.
- Shared prep handlers emit labeled callout regions, and the affected prep unit tests are green.

Next Steps:
1. Let the broader prep/conversion suite run if you want extra confidence beyond the focused tests.
2. Carry the same contract shape forward if later E7-06b work needs review UI or downstream consumption changes.

Recorded by: codex (gpt-5)
