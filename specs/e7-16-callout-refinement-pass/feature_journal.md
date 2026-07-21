Session: 2026-07-11 - E7-16 Feature Start
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-11

Work Completed:
1. Created the E7-16 feature folder and canonical feature journal in the new worktree.
2. Confirmed the feature scope is the optional agent-based callout refinement pass.
3. Added the E7-16 backlog entry as the next Epic 7 item.

Key Decisions:
- E7-16 is separate from E7-15 callout detection and hint generation.
- The feature will use a skip flag and capability gate so refinement remains optional.
- The worktree is the source of truth for this feature.

Current State:
- The new E7-16 worktree exists at `/home/todd/Dev/gm-kit/.worktrees/e7-16-callout-refinement-pass`.
- The backlog entry has been added in the new worktree, but no design or plan has been drafted yet.

Next Steps:
1. Draft the E7-16 design in the new feature folder.
2. Write the implementation plan for the refinement pass.
3. Keep all subsequent work inside the E7-16 worktree checkout.

Recorded by: Codex

Session: 2026-07-20 - Prep-specific mock handoff
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-20

Work Completed:
1. Replaced the generic conversion handoff path with a prep-specific mock-agent script for `analyze-and-prep-pdf`.
2. Wired `just analyze-homebrewery-with-mock-agent-handoff` to run the prep-specific mock refinement flow directly.
3. Added focused unit tests for the new prep handoff helper and validated the end-to-end Homebrewery run.

Key Decisions:
- The prep mock handoff should call `refine_callout_proposals(...)` directly rather than reuse the conversion live-handoff harness.
- The just target should stay prep-specific so it does not imply a generic conversion-style agent loop.
- Worktree execution should remain the default; the script now resolves `.python-version` by walking upward until it finds the repo root.

Current State:
- `just analyze-homebrewery-with-mock-agent-handoff` now runs the prep flow, pauses for refinement, applies the mock refinement adapter, writes `annotation-refined-proposals.json`, and resumes successfully.
- Focused tests for the new script and existing prep refinement/orchestrator helpers are passing.
- Broader repo cleanup, lingering worktree diffs, and table-refinement follow-up items remain open.

Next Steps:
1. Review the generated prep artifacts from the new handoff flow if needed.
2. Decide whether the prep mock handoff should also cover table refinement in a later pass.
3. Continue the broader repo cleanup and selective commit/review work.

Recorded by: Codex

Session: 2026-07-21 - Prep handoff verified, next work queued
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-21

Work Completed:
1. Confirmed the prep-specific mock-agent handoff flow is working from the just target.
2. Added a backlog item for slash-command/prompt/script coverage plus skills-based agent integration.
3. Recorded the next follow-up work as skip-page validation, slash-command testing, and skills integration discussion.

Key Decisions:
- The next analyze-command validation should focus on skip-page behavior before widening scope further.
- Slash-command artifacts and the skills-vs-command agent integration topic should be tracked as a separate backlog item rather than folded into the current prep refinement work.

Current State:
- `just analyze-homebrewery-with-mock-agent-handoff` now runs the prep-specific mock refinement loop successfully.
- The backlog now includes a dedicated item for analyze slash-command artifacts and skills-based agent integration.
- Skip-page behavior, slash-command generation, and skills integration remain unimplemented.

Next Steps:
1. Review and test the skip-page feature.
2. Create and test the analyze slash-command/prompt artifacts.
3. Discuss and design the skills-based agent integration follow-up.

Recorded by: Codex

Session: 2026-07-14 - Two-Mode Refinement Contract Finalized
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-14

Work Completed:
1. Reframed the refinement design around two explicit modes: `mock` and `handoff`.
2. Updated the implementation plan so `mock` completes inline while `handoff` writes a request artifact and pauses for an external response.
3. Kept the integration coverage aligned with the actual Homebrewery handoff test file.

Key Decisions:
- `mock` is the CLI convenience / CI mode and should not require a resume cycle.
- `handoff` is the outer-agent mode and should use the request/response pause-resume flow.
- The mock object remains useful both inline and as the response generator for handoff tests.

Current State:
- The design and plan now reflect the final two-mode contract.
- Existing code and tests already largely match this shape; only documentation needed to be realigned.

Next Steps:
1. Let the user review the updated design/plan wording.
2. If approved, continue with any final cleanup or commit steps that remain.

Recorded by: Codex

Session: 2026-07-13 - Handoff Harness Regression Completed
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-13

Work Completed:
1. Added a unit regression that simulates the full handoff loop: request artifact, mock response artifact, and resume completion.
2. Cleaned up the prep orchestrator’s pause exception handling and import ordering.
3. Re-ran the focused prep tests and lint checks successfully.

Key Decisions:
- The prep-side vision handoff is now testable end-to-end with a simple mock response flow.
- The request artifact remains the outer boundary; the response artifact remains the resume input.

Current State:
- The refinement handoff path, request artifact, and resume flow are all covered by tests.
- The current mock still serves CI/offline validation, while the handoff contract is explicit in the workspace.

Next Steps:
1. Decide whether the new handoff contract is stable enough to keep as-is.
2. If yes, commit the E7-16 worktree changes.

Recorded by: Codex

Session: 2026-07-13 - Handoff Mode Wired Into Prep
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-13

Work Completed:
1. Added a `handoff` refinement mode that writes a refinement request artifact and pauses prep before review finalization.
2. Wired `resume_prep()` to complete prep after a response artifact is written.
3. Added regression coverage for the pause/resume handoff and verified the request artifact appears in a real fixture run.

Key Decisions:
- The prep command now has an explicit external-handoff path for vision refinement instead of relying only on inline mock behavior.
- The request artifact is the visible boundary for the outer agent or harness; the response artifact is the resume signal.

Current State:
- `GMKIT_CALL_OUT_REFINEMENT_MODE=handoff` produces `annotation-refinement-request.json` and leaves prep incomplete until a response artifact is supplied.
- Focused tests and lint are green after the pause/resume wiring.

Next Steps:
1. Decide whether to document the new handoff mode in the user guide or keep it internal for now.
2. If desired, run a full end-to-end handoff simulation with a mock response artifact.

Recorded by: Codex

Session: 2026-07-13 - Refinement Handoff Request Artifact Added
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-13

Work Completed:
1. Added `annotation-refinement-request.json` to the prep artifact contract so the refinement handoff is represented explicitly in the workspace.
2. Kept `annotation-refined-proposals.json` as the response-side artifact produced by the current mock path.
3. Updated tests and manifest expectations to account for the new request artifact.

Key Decisions:
- The refinement workflow now exposes a visible request artifact even while the mock path answers inline for CI.
- The request artifact is the right first step toward a later true pause/resume handoff.

Current State:
- The Homebrewery fixture run now produces the new request artifact under `prep/annotation-refinement/`.
- Focused unit tests and a targeted lint pass are green.

Next Steps:
1. Decide whether to commit the current prep contract shape as-is.
2. If more alignment is wanted, add an explicit pause/resume path in a follow-up change.

Recorded by: Codex

Session: 2026-07-13 - Handoff Model Aligned With Convert
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-13

Work Completed:
1. Updated the E7-16 backlog entry to require the same pause/resume handoff shape used by the conversion pipeline.
2. Rewrote the E7-16 design around an explicit request/response artifact flow instead of a backend adapter call.
3. Added a backlog TODO to propagate that same handoff pattern into conversion later so both flows stay aligned.

Key Decisions:
- The orchestrator should request vision help, exit cleanly, and resume from a returned refinement artifact rather than calling a backend directly.
- The test harness should emulate the outer agent by intercepting the request, writing the response, and resuming the orchestrator.

Current State:
- E7-16 now matches the convert-style handoff model.
- The design is cleaner and less brittle than the backend-adapter approach.
- The mock refinement docs still stand, but the orchestration contract now centers on external handoff rather than internal backend selection.

Next Steps:
1. Update the implementation to match the new request/response handoff contract.
2. Re-run the focused refinement tests after the code change.
3. If stable, commit the E7-16 worktree changes.

Recorded by: Codex

Session: 2026-07-13 - Mock Refinement Limits Documented
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-13

Work Completed:
1. Updated the mock callout refinement docstring to state that it is a low-fidelity proxy for the real agent.
2. Tightened the E7-16 design text so the mock is explicitly documented as a temporary, deterministic fallback for CI and flow validation.

Key Decisions:
- The mock should be described as rough on purpose so no one mistakes it for the real refinement path.
- Its job is to keep the analyze flow moving and prove the refinement artifact contract, not to model production-quality geometry correction.

Current State:
- The code and design now agree that the mock is a low-fidelity proxy and not a production substitute.
- The proof-of-flow refined PDF remains available for visual review.

Next Steps:
1. Run a focused regression check on the E7-16 refinement tests if needed.
2. Decide whether to commit the worktree changes now or after one more manual review.

Recorded by: Codex

Session: 2026-07-13 - Manual Refinement Proof Artifact
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-13

Work Completed:
1. Ran the Homebrewery prep fixture in the E7-16 worktree and verified the current mock-backed refinement flow.
2. Wrote a separate proof-of-flow artifact at `tmp/homebrewery-prep/prep/annotated-prep-agent-refined.pdf`.
3. Wrote a companion manual refinement JSON artifact at `tmp/homebrewery-prep/prep/annotation-refined-proposals-agent.json`.

Key Decisions:
- The environment here does not expose a separate live vision-agent backend, so the new artifact is a manual refinement proxy rather than a real agent invocation.
- The proof artifact keeps the baseline `annotated-prep.pdf` intact and writes the revised bbox to a separate file, which is the right shape for validating downstream value.

Current State:
- The prep fixture run still produces the refinement hints, refined proposal JSON, and annotated review PDF.
- The new proof-of-flow PDF shows the same callout with an expanded bbox, and the companion JSON records the revised geometry.
- The real external-agent integration remains unimplemented.

Next Steps:
1. Review the new proof artifact and decide whether the manual refinement proxy is sufficient as a validation step.
2. If yes, commit the E7-16 worktree changes.
3. If not, define the real vision-agent integration point for a later feature.

Recorded by: Codex

Session: 2026-07-12 - E7-16 Adapter Boundary Extracted
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-12

Work Completed:
1. Extracted the refinement backend into explicit adapter classes and a factory selector.
2. Kept the prep orchestrator unchanged while threading the adapter through the existing refinement helper.
3. Added tests for adapter selection, injected-agent refinement, and the existing prep integration path.

Key Decisions:
- The mock refinement logic now lives behind `MockCalloutRefinementAgent` instead of being embedded in the orchestration helper.
- `VisionCalloutRefinementAgent` exists as a placeholder for the future real backend, but the current default path remains deterministic and local.
- The refinement contract still centers on crop entries and decisions; only the backend implementation is swappable.

Current State:
- The refinement backend is now explicitly adapter-based.
- All targeted tests for the E7-16 slice pass.

Next Steps:
1. Decide whether to replace the placeholder vision adapter with a real image-capable agent hook in a later feature.
2. Review whether the `annotation-refined-proposals.json` name should stay canonical.
3. Re-run broader prep checks only if the missing private fixture issue is resolved.

Recorded by: Codex

Session: 2026-07-11 - E7-16 Refinement Adapter Next Step
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-11

Work Completed:
1. Described how the current mock refinement logic can be swapped for a real agent-backed implementation.
2. Identified the stable contract boundary: crop entries and refinement decisions remain fixed, while the agent implementation becomes injectable.

Key Decisions:
- The orchestrator should not need to change again for the agent swap.
- The agent backend should be isolated behind a small `CalloutRefinementAgent`-style adapter so the mock and real implementations share the same contract.

Current State:
- The current mock refinement path is working and validated in the worktree.
- The next implementation slice is to replace the internal mock function with an explicit adapter/factory boundary.

Next Steps:
1. Extract the mock refinement logic into an explicit adapter interface.
2. Add a real-agent placeholder implementation or factory hook.
3. Keep the existing tests green while changing only the refinement backend boundary.

Recorded by: Codex

Session: 2026-07-11 - E7-16 Optional Refinement Pass Wired
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-11

Work Completed:
1. Added the `--skip-callout-refinement` CLI option and threaded it through the prep orchestrator.
2. Implemented a local mock refinement pass that tightens eligible callout bboxes from padded crops rendered from the source PDF.
3. Wrote refined callout proposals to `annotation-refined-proposals.json` and taught render/review guidance to prefer them when present.
4. Added tests for the CLI flag, crop manifest, refinement decisions, and refined review flow.

Key Decisions:
- The refinement pass is still source-PDF based and remains separate from `annotated-prep.pdf`.
- Skip behavior removes stale refined-proposal output so a disabled run cannot reuse older geometry.
- The initial refinement implementation is deterministic and local; it stands in for the future image-capable agent integration.

Current State:
- The optional refinement pass now runs during prep when not skipped and when refinement crops exist.
- Refined proposals are consumed by both the annotated review PDF and reviewed guidance generation.
- Focused prep and integration tests pass; the broader prep suite still has unrelated private-fixture gaps outside this change.

Next Steps:
1. Review whether the mock refinement behavior and artifact filename should be renamed before broader rollout.
2. Decide whether to add a dedicated agent-backed refinement adapter in a later feature.
3. If desired, run the broader prep suite after the private fixture issue is resolved.

Recorded by: Codex

Session: 2026-07-11 - E7-16 Source Crop Preparation Implemented
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-11

Work Completed:
1. Added `prep/refinement.py` to render padded callout crops from the original source PDF.
2. Wired `handle_generate_annotation_proposals()` to write an `annotation-refinement/annotation-refinement-inputs.json` manifest and cropped PNGs for callouts flagged by multi-block traversal hints.
3. Added unit tests proving the crop helper renders source-PDF imagery and writes an empty manifest when no hints are present.
4. Updated artifact-path and orchestrator expectations to include the new refinement manifest.

Key Decisions:
- The refinement input images come from the source PDF, not `annotated-prep.pdf`.
- The crop manifest is produced during analyze so later agent refinement can consume it without re-rendering the PDF.
- The first implementation slice does not yet invoke an agent; it prepares the image inputs and manifest for the later refinement pass.

Current State:
- The prep pipeline now emits source-PDF callout refinement crops alongside the existing hint artifact.
- Focused tests and the integration callout bbox regression test pass.
- Two unrelated prep unit tests still fail when run as a broad suite because the private Call of Cthulhu fixture PDF is absent in this worktree environment.

Next Steps:
1. Add the actual optional refinement execution path that consumes the crop manifest.
2. Decide how to gate that pass behind the skip flag and image-capability check.
3. Re-run the prep slice once the missing private fixture is restored or excluded from the broad suite.

Recorded by: Codex

Session: 2026-07-11 - E7-16 Refinement Image Contract Clarified
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-11

Work Completed:
1. Clarified that the refinement agent should inspect crops rendered from the original source PDF, not the annotated review PDF.
2. Updated the design to require crop padding so the callout background, border, and nearby context remain visible.
3. Updated the plan to reflect the source-image contract and the padded crop requirement.

Key Decisions:
- Refinement images must come from the source PDF to avoid circular dependency on the review overlay.
- Crops must include enough padding to expose fill color and other visual cues that influence geometry refinement.

Current State:
- The E7-16 design and plan now explicitly require source-PDF crops for the refinement pass.
- No implementation code has changed yet.

Next Steps:
1. Review the crop-padding language for any further tightening.
2. Implement the image rendering helper and refinement orchestration in the E7-16 worktree.
3. Add tests that prove the agent sees the source-PDF crop contract.

Recorded by: Codex

Session: 2026-07-11 - E7-16 Design and Plan Drafted
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-11

Work Completed:
1. Drafted `superpowers-design.md` for the optional callout refinement pass.
2. Drafted `superpowers-plan.md` with implementation slices, tests, and commit targets.
3. Kept the worktree-local backlog entry and feature folder as the source of truth for E7-16.

Key Decisions:
- The refinement pass runs only after the code-first callout detector and only for proposals flagged by multi-block traversal hints.
- The pass is optional, with an explicit skip flag and an image-capability gate.
- The raw detection evidence must remain separate from any refined geometry so the original detector output is preserved.
- Automated tests will use a mock agent rather than a live paid agent.

Current State:
- The E7-16 design and plan artifacts now exist in the feature folder.
- No implementation code has been changed yet for the refinement pass.

Next Steps:
1. Review the design and plan for any naming or artifact-shape adjustments before coding.
2. Implement the refinement helper and orchestration wiring in the E7-16 worktree.
3. Add unit and integration coverage for skip, capability-gate, and mock-agent behavior.

Recorded by: Codex

Session: 2026-07-14 - Handoff renders annotated PDF before pause
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-14

Work Completed:
1. Moved annotated PDF rendering before the handoff pause in prep callout refinement.
2. Updated unit and integration tests to require `annotated-prep.pdf` in handoff mode.
3. Reran the Homebrewery prep flow in handoff mode, wrote a refined bbox proposal, and resumed successfully.
4. Verified the regenerated FreeText annotation directly in the PDF and confirmed it is yellow, semi-transparent, and properly sized.

Key Decisions:
- The handoff flow must leave a reviewable `annotated-prep.pdf` on disk before pausing.
- Manual outer-agent refinement continues to use `annotation-refined-proposals.json` as the response artifact.

Current State:
- The handoff run completes the prep-side PDF render before pausing.
- The Homebrewery fixture now produces a usable annotated PDF for manual review.
- The refined callout bbox is stable and the resume path completes successfully.

Next Steps:
1. Decide whether to commit the updated handoff behavior now.
2. If continuing, run any broader repo checks needed for final confidence.
3. Then hand off for manual review or move to the next E7 item.

Recorded by: Codex

Session: 2026-07-14 - Added table refinement follow-up story
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-14

Work Completed:
1. Added a new Epic 7 backlog story for an optional table refinement pass that mirrors the callout pause/revise/resume workflow.
2. Scoped the story to compare table prep against callout prep and reuse the same reviewable PDF + revise/update + resume pattern.

Key Decisions:
- Table refinement should follow the same prep-side handoff contract as callouts rather than inventing a separate workflow.
- The new story is intentionally comparison-driven so the implementation can reuse existing prep artifacts and only close the gaps.

Current State:
- `BACKLOG.md` now includes `E7-17. Optional Table Refinement Pass`.
- No implementation work has started for the new table story yet.

Next Steps:
1. If desired, create the feature folder and Superpowers design/plan for E7-17.
2. Otherwise, continue with the current E7-16 handoff work or move to the next Epic 7 item.

Recorded by: Codex

Session: 2026-07-14 - Deferred E7-17 design work
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-14

Work Completed:
1. Added `E7-17. Optional Table Refinement Pass` to `BACKLOG.md`.
2. Sketched the intended scope as a comparison-driven follow-up to the callout refinement workflow.

Key Decisions:
- Table refinement will be deferred until tomorrow.
- The new table story should be developed later as a separate design/plan pass rather than immediately in this session.

Current State:
- The backlog now tracks the table refinement follow-up, but no E7-17 design or plan files have been created yet.
- E7-16 remains committed and complete.

Next Steps:
1. Tomorrow, create the E7-17 feature folder and draft the Superpowers design.
2. Then write the corresponding implementation plan.
3. Compare the current table workflow against the callout handoff flow before making code changes.

Recorded by: Codex

Session: 2026-07-17 - Analyze command completion todos
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-17

Work Completed:
1. Captured the remaining analyze-command work items requested by the user as a structured todo list.
2. Grouped the remaining work around the agent review handoff, page-skip behavior, chunking behavior, and reviewed-artifact resume flow.

Key Decisions:
- The remaining analyze work should stay focused on finishing the current first pass before widening scope further.
- Chunking should be revisited with the goal of simplifying analyze so the same chunk-oriented flow can be used consistently, even for one-page inputs.

Current State:
- The first-pass analyze/prep pipeline is in a good stopping point, but the agent-driven crop review and resume path still need to be completed and verified.
- Page skipping, chunking behavior, and reviewed JSON artifact handoff remain open follow-up items.

Next Steps:
1. Review the current PR/code as it stands now.
2. Implement agent review of cropped images plus resume handling.
3. Test page-skip behavior and confirm chunking still works, including the one-page chunk simplification idea.
4. Add the reviewed JSON artifact flow so convert can consume user-revised prep output.

Recorded by: Codex

Session: 2026-07-17 - Reconciled backlog and journal
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-17

Work Completed:
1. Reconciled the journal with the new E7-16 backlog todo list.
2. Kept the remaining analyze work focused on the current first pass: code review, agent crop review/resume, page skipping, chunking, and reviewed artifact handoff.

Key Decisions:
- The journal and backlog should stay in sync so the remaining work is easy to pick up without re-deriving scope.
- The analyze follow-up work remains an implementation/validation pass rather than a design rewrite.

Current State:
- `BACKLOG.md` and the feature journal now describe the same remaining analyze-command work.
- No additional implementation changes were made in this reconciliation step.

Next Steps:
1. Review the current PR/code as it stands now.
2. Implement agent review of cropped images plus resume handling.
3. Verify page-skip behavior and chunking behavior.
4. Add the reviewed JSON artifact flow for convert.

Recorded by: Codex

Session: 2026-07-17 - Added analyze run modes
--------------------------------------------------------
Branch: e7-16-callout-refinement-pass
Date: 2026-07-17

Work Completed:
1. Added separate `just` targets for analyze mock-inline mode and harness-driven handoff mode.
2. Recorded the remaining work item to test both command paths when time allows.

Key Decisions:
- The mock-inline and handoff flows should be exposed as distinct commands so their behavior is obvious at the terminal.
- Testing for both flows is still pending and should be tracked explicitly rather than assumed complete.

Current State:
- `just analyze-homebrewery-with-cli-mock` explains and runs the inline mock-review flow.
- `just analyze-homebrewery-with-mock-agent-handoff` explains and runs the harness-driven pause/resume flow.
- Both flows still need manual verification.

Next Steps:
1. Review the current PR/code as it stands now.
2. Implement agent review of cropped images plus resume handling.
3. Verify page-skip behavior and chunking behavior.
4. Test both new analyze entry points.

Recorded by: Codex
