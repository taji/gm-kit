Session: 2026-06-20 - E7-07 Feature Start
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-20

Work Completed:
1. Created the E7-07 feature folder and journal scaffold.
2. Captured the conversion gating problem as a prep-artifact consumption story.
3. Established the initial policy direction: fail fast for missing prep artifacts, fall back from reviewed to baseline prep outputs.

Key Decisions:
- Conversion should prefer reviewed prep artifacts when they exist, but remain automatable by falling back to baseline prep outputs.
- Missing prep roots or required baseline artifacts should fail conversion up front rather than halfway through.

Current State:
- E7-07 is identified as the next Epic 7 story.
- No spec or implementation content has been written yet.

Next Steps:
1. Draft the E7-07 design around artifact discovery, fallback, and fail-fast behavior.
2. Confirm which prep artifacts are mandatory for conversion startup.
3. After design approval, write the implementation plan.

Recorded by: codex (gpt-5)

Session: 2026-06-20 - E7-07 Prep-Gated Conversion Implementation
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-20

Work Completed:
1. Added prep artifact resolution helpers and prep artifact validation support.
2. Switched `pdf-convert` startup to consume prep preflight data when present and fall back to baseline analysis when prep artifacts are absent.
3. Updated Phase 0 to bootstrap missing metadata and preflight artifacts, and Phase 7 to emit baseline `prep-guidance.resolved.json` for downstream phases.
4. Updated unit and integration tests for the new prep-backed flow and verified lint, typecheck, coverage, and repo tests.

Key Decisions:
- `pdf-convert` remains usable as the end-to-end command; it prefers prep artifacts but regenerates baseline outputs when they are missing.
- Phase 7 now writes baseline prep guidance into the `prep/` workspace so later phases can consume table regions without requiring a separate prep run.
- Reviewed prep guidance still overrides baseline guidance when present.

Current State:
- E7-07 implementation is complete and verified.
- `just lint`, `just typecheck`, `just test`, and `pytest --cov=src` all pass.

Next Steps:
1. Review the updated E7-07 design and implementation against the backlog wording.
2. Decide whether to keep the bootstrap fallback as the final conversion behavior or tighten it further in a follow-up story.

Recorded by: codex (gpt-5)

Session: 2026-06-20 - E7-07 Prep-Gated Conversion Implementation
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-20

Work Completed:
1. Added prep artifact resolution helpers and prep artifact validation support.
2. Switched `pdf-convert` startup to consume prep preflight data when present and fall back to baseline analysis when prep artifacts are absent.
3. Updated Phase 0 to bootstrap missing metadata and preflight artifacts, and Phase 7 to emit baseline `prep-guidance.resolved.json` for downstream phases.
4. Updated unit and integration tests for the new prep-backed flow and verified the repo quality pipeline.

Key Decisions:
- `pdf-convert` remains usable as the end-to-end command; it prefers prep artifacts but regenerates baseline outputs when they are missing.
- Phase 7 now writes baseline prep guidance into the `prep/` workspace so later phases can consume table regions without requiring a separate prep run.
- Reviewed prep guidance still overrides baseline guidance when present.

Current State:
- E7-07 implementation is complete and verified.
- `just lint`, `just typecheck`, `just test`, and `pytest --cov=src` all pass.

Next Steps:
1. Review the updated E7-07 design and implementation against the backlog wording.
2. Decide whether to keep the bootstrap fallback as the final conversion behavior or tighten it further in a follow-up story.

Recorded by: codex (gpt-5)

Session: 2026-06-20 - E7-07 Plan Draft
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-20

Work Completed:
1. Wrote the E7-07 implementation plan in the feature folder using the Superpowers plan format.
2. Broke the work into prep artifact resolution, startup gating, phase consumer alignment, and docs updates.
3. Kept legacy `gm_callout_config_file` removal explicitly out of scope.

Key Decisions:
- Conversion startup should fail fast on missing prep workspace or required baseline prep artifacts.
- Reviewed prep guidance should override baseline guidance when available, but the baseline path must still work for automation.

Current State:
- The feature now has both a design and an implementation plan.
- No E7-07 code has been changed yet.

Next Steps:
1. Review `specs/e7-07-convert-gating-prep-artifact-consumption/superpowers-plan.md`.
2. If the plan looks right, start implementation using subagent-driven development or executing-plans.

Recorded by: codex (gpt-5)

Session: 2026-06-20 - E7-07 Design Draft
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-20

Work Completed:
1. Drafted the E7-07 conversion gating design around fail-fast startup validation and reviewed-to-baseline prep guidance fallback.
2. Defined the baseline prep artifact contract and the single reviewed override currently in scope.
3. Clarified that legacy `gm_callout_config_file` removal is out of scope for this feature.

Key Decisions:
- Conversion should fail fast if the prep workspace or required baseline artifacts are missing.
- Reviewed prep guidance should override baseline guidance when present; otherwise baseline guidance remains authoritative.

Current State:
- E7-07 design is drafted in the feature folder.
- No implementation plan or code changes have been made for E7-07 yet.

Next Steps:
1. Review `specs/e7-07-convert-gating-prep-artifact-consumption/superpowers-design.md`.
2. Confirm whether the artifact contract matches the intended conversion startup behavior.
3. After approval, write the implementation plan.

Recorded by: codex (gpt-5)

Session: 2026-06-20 - E7-07 Prep-Gated Conversion Implementation
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-20

Work Completed:
1. Added prep artifact resolution helpers and prep artifact validation support.
2. Switched `pdf-convert` startup to consume prep preflight data when present and fall back to baseline analysis when prep artifacts are absent.
3. Updated Phase 0 to bootstrap missing metadata and preflight artifacts, and Phase 7 to emit baseline `prep-guidance.resolved.json` for downstream phases.
4. Updated unit and integration tests for the new prep-backed flow and verified lint, typecheck, coverage, and repo tests.

Key Decisions:
- `pdf-convert` remains usable as the end-to-end command; it prefers prep artifacts but regenerates baseline outputs when they are missing.
- Phase 7 now writes baseline prep guidance into the `prep/` workspace so later phases can consume table regions without requiring a separate prep run.
- Reviewed prep guidance still overrides baseline guidance when present.

Current State:
- E7-07 implementation is complete and verified.
- `just lint`, `just typecheck`, `just test`, and `pytest --cov=src` all pass.

Next Steps:
1. Review the updated E7-07 design and implementation against the backlog wording.
2. Decide whether to keep the bootstrap fallback as the final conversion behavior or tighten it further in a follow-up story.

Recorded by: codex (gpt-5)

Session: 2026-06-20 - E7-07 Docs Aligned to Bootstrap Behavior
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-20

Work Completed:
1. Updated the E7-07 backlog entry to describe prep-first conversion with bootstrap fallback instead of fail-fast gating.
2. Aligned the E7-07 design and plan text with the shipped behavior: reviewed guidance is preferred, baseline guidance is the fallback, and missing baseline prep outputs are bootstrapped when needed.
3. Re-checked the feature docs for leftover fail-fast wording and removed the mismatch.

Key Decisions:
- The canonical conversion behavior is prep-first with bootstrap fallback, not strict fail-fast startup.
- Reviewed prep guidance remains optional and should continue to override baseline guidance when it exists.

Current State:
- E7-07 code and docs now describe the same behavior.
- No code changes were needed for this pass.

Next Steps:
1. Review the updated E7-07 backlog/design/plan text for any remaining wording preferences.
2. Move on to the next feature or follow-up cleanup if needed.

Recorded by: codex (gpt-5)

Session: 2026-06-20 - E7-07 Shared Backlog Wording Cleanup
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-20

Work Completed:
1. Updated the Epic 7 shared backlog constraints to describe prep-first conversion with bootstrap fallback instead of hard-fail prep gating.
2. Reworded the E7-07 backlog entry so it matches the implemented conversion contract.
3. Confirmed the remaining `fail fast` wording in the backlog is limited to the intentional missing-TOC recovery story.

Key Decisions:
- The top-level Epic 7 contract should describe prep-first bootstrap behavior, not strict missing-prep failure.
- The missing-TOC story remains a separate intentional fail-fast case.

Current State:
- The Epic 7 backlog language now matches the shipped E7-07 behavior.
- No code changes were needed for this pass.

Next Steps:
1. Review the updated Epic 7 backlog wording if you want further tone or policy adjustments.
2. Continue with the next feature or cleanup item.

Recorded by: codex (gpt-5)

Session: 2026-06-20 - E7-07 Active-Doc Cleanup Pass
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-20

Work Completed:
1. Renamed the remaining bootstrap-related plan wording so it no longer implied fail-fast prep gating.
2. Verified the active E7-07 design, plan, and backlog now describe prep-first bootstrap fallback consistently.
3. Left the historical journal entries unchanged and limited the cleanup to the active authoritative docs.

Key Decisions:
- Historical journal entries remain as a record of how the policy evolved.
- Active design/plan/backlog text should reflect the shipped bootstrap behavior, not the earlier fail-fast drafts.

Current State:
- E7-07 active docs are consistent.
- The only remaining fail-fast language in Epic 7 backlog is the intentional missing-TOC recovery case.

Next Steps:
1. Review the updated wording if you want any final tone changes.
2. Move on to the next feature or cleanup task.

Recorded by: codex (gpt-5)
