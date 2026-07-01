Session: 2026-07-01 - Prep artifact naming audit started
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-07-01

Work Completed:
1. Identified `prep-guidance.input.json` as the primary naming mismatch in the prep artifact set.
2. Added the E7-05a backlog story for the defaults rename and broader artifact naming audit.
3. Started the code and documentation rename from `prep-guidance.input.json` to `prep-guidance.defaults.json`.

Key Decisions:
- Use `prep-guidance.defaults.json` for generated prep defaults and reserve reviewed/resolved files for downstream contracts.
- Rename the prep runtime path field to `guidance_defaults` so the code matches the file name.

Current State:
- Runtime prep code, selected tests, and active design docs are partially updated to the new defaults naming.
- Remaining work is to finish the repo-wide reference sweep, run verification, and update any broken imports or assertions.

Next Steps:
1. Finish replacing remaining `prep-guidance.input.json` references in tests, docs, and feature artifacts.
2. Run the targeted test subset for prep contracts and orchestrator behavior.
3. Update the journal with the final rename outcome.

Recorded by: Codex

Session: 2026-07-01 - E7-05a backlog status closed
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-07-01

Work Completed:
1. Marked `E7-05a` complete in `BACKLOG.md`.
2. Confirmed the prep defaults rename is already present in runtime code, tests, and user-facing docs.

Key Decisions:
- Treat the naming audit as complete and move on to the substantive `E7-05` guidance/proposal feature.

Current State:
- `E7-05a` is now closed at the backlog level.
- The repo still contains historical references to the old filename only in migration context.

Next Steps:
1. Start `E7-05` work on the guidance/proposal system.

Recorded by: Codex

Session: 2026-07-01 - Naming audit handoff tightened
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-07-01

Work Completed:
1. Reworded the E7-05a backlog story so it centers on the prep defaults artifact naming audit.
2. Kept the historical `prep-guidance.input.json` references only where they describe the migration itself.
3. Confirmed the active runtime, tests, and user guide now use `prep-guidance.defaults.json`.

Key Decisions:
- Preserve the old filename only in historical/migration context.
- Treat the renamed defaults artifact as the canonical generated seed going forward.

Current State:
- The naming audit story is cleanly scoped and the active repo text uses the new defaults naming.
- No additional runtime changes are required for the rename.

Next Steps:
1. Start the next Epic 7 feature or, if desired, continue with any further artifact-name cleanup.

Recorded by: Codex

Session: 2026-07-01 - Prep artifact defaults rename completed
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-07-01

Work Completed:
1. Renamed the prep defaults artifact from `prep-guidance.input.json` to `prep-guidance.defaults.json` in the runtime artifact path model, orchestrator, handlers, and prep exports.
2. Updated the prep unit tests and user guide to reflect the new filename and the `guidance_defaults` path field.
3. Aligned the active E7-05 and E7-06 design docs with the renamed defaults artifact.

Key Decisions:
- Keep `prep-guidance.resolved.json` and `prep-guidance.reviewed.json` unchanged; the rename only applies to the generated defaults seed.
- Keep the rename local to prep artifact naming rather than widening the contract to a new review schema.

Current State:
- Runtime code and targeted prep tests are passing with the renamed defaults artifact.
- `just lint` passes; `just typecheck` still fails on an unrelated pre-existing `phase7.py` mypy issue.

Next Steps:
1. Decide whether to carry the `defaults` naming through any remaining historical docs/journals.
2. Reconcile the broader repo docs or backlog if you want the old `input` name removed everywhere, including historical references.

Recorded by: Codex
