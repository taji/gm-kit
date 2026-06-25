Session: 2026-06-18 - E7-05 Feature Start
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Restored Epic 7 context from `BACKLOG.md` and the latest E7-04 feature journal entries.
2. Confirmed E7-04 is the direct baseline for E7-05, specifically the corrected `chapter-index.json` and `chunk-plan.json` prep contracts.
3. Established the initial E7-05 scope around prep guidance artifacts plus machine-readable annotation proposal generation.

Key Decisions:
- E7-05 should start from the approved Epic 7 backlog description and the stabilized E7-04 prep contracts.
- `feature_journal.md` is created before any E7-05 design or implementation work, per repo rules.

Current State:
- E7-05 context is restored and ready for brainstorming/design.
- No E7-05 design doc, plan, or implementation changes exist yet.

Next Steps:
1. Clarify the intended role of `prep-guidance.input.json` versus `prep-guidance.resolved.json`.
2. Define the annotation proposal artifact shape for `table`, `callout`, and `skip` labels.
3. Write `specs/e7-05-guidance-annotation-proposal-system/superpowers-design.md` after design approval.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-05 Implemented and Verified
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Added prep guidance/proposal contracts, artifact paths, deterministic proposal helpers, and resolved-guidance normalization for E7-05.
2. Wired E7-05 runtime steps into the prep registry and orchestrator to emit `prep-guidance.input.json`, `annotation-proposals.json`, and `prep-guidance.resolved.json`.
3. Kept `annotation-proposals.json` as raw proposal evidence and `prep-guidance.resolved.json` as the authoritative downstream artifact.
4. Expanded focused prep tests across contracts, handlers, artifact paths, and orchestrator behavior.
5. Ran focused prep verification plus the full repo gate (`just all_ci_actions`) and resolved the Bandit SHA-1 finding by marking the proposal hash as non-security usage.

Key Decisions:
- Proposal IDs are deterministic hashes of stable proposal content, including metadata, so distinct stable proposals do not collide.
- Appendix-style full-page skip proposals are limited to trailing appendix chunks rather than any trailing single-page chunk sequence.
- The optional visual artifact `annotated-prep.pdf` remains reserved in artifact paths and manifest inventory but is not emitted yet in E7-05.

Current State:
- E7-05 implementation is complete and locally verified.
- Focused prep checks pass, full repo CI actions pass, and the prep runtime now emits the E7-05 machine-readable guidance artifacts.

Next Steps:
1. Resume with E7-06 user revision flow for annotation proposals and visual review/edit support.
2. Decide whether `annotated-prep.pdf` should first appear in E7-06 or later once the revision UX is defined.
3. If desired, do a manual sample run of `analyze-and-prep-pdf` against a representative large document to inspect the new prep artifacts.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-05 Task 4 Final Quality Review
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Reviewed the Task 4 prep wiring and scoped unit tests for concrete correctness, maintainability, typing, and test-quality issues.
2. Verified the current implementation is internally consistent across `orchestrator.py`, `handlers.py`, `__init__.py`, and the scoped tests.
3. Found no remaining issues in the reviewed scope that are worth fixing before merge.

Key Decisions:
- Treat this review as approval because the remaining tradeoffs in the scoped files are either intentional or too minor to justify churn now.

Current State:
- E7-05 Task 4 scoped files are review-clean and suitable to merge based on the requested quality bar.

Next Steps:
1. Proceed with merge or broader feature-level validation as needed.
2. If desired later, tighten a few internal tests only when the prep orchestrator behavior changes materially.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-05 Tasks 1 and 2 Completed
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Implemented `AnnotationProposal`, `PrepGuidanceInput`, and `PrepGuidanceResolved` in `src/gm_kit/pdf_convert/prep/contracts.py`.
2. Added focused unit coverage in `tests/unit/pdf_convert/prep/test_guidance_contracts.py`, including round-trip, validation, provenance, and JSON-serializability checks.
3. Extended prep artifact path definitions in `src/gm_kit/pdf_convert/prep/analysis_artifacts.py` for `prep-guidance.input.json`, `annotation-proposals.json`, `prep-guidance.resolved.json`, and `annotated-prep.pdf`.
4. Updated `tests/unit/pdf_convert/prep/test_analysis_artifacts.py` to cover the new E7-05 artifact paths plus the empty-`pdf_stem` rejection edge case.
5. Ran focused `pytest`, `ruff`, and `mypy` checks for both completed tasks and resolved review findings from spec and code-quality passes.

Key Decisions:
- Proposal provenance is enforced at the contract layer via `metadata.source` with allowed values `code`, `ai`, and `hybrid`.
- Proposal metadata and resolved-region extra fields must be JSON-safe before they are serialized to prep artifacts.
- Empty `pdf_stem` values are treated as invalid input rather than silently collapsing to the `source` fallback artifact name.

Current State:
- E7-05 Tasks 1 and 2 are implemented, locally validated, and review-clean.
- The prep package now has the contract and artifact-path foundation needed for proposal generation and resolved-guidance writing.

Next Steps:
1. Implement Task 3 in `src/gm_kit/pdf_convert/prep/handlers.py` and `tests/unit/pdf_convert/prep/test_guidance_handlers.py`.
2. Add deterministic proposal generation plus normalization into `PrepGuidanceResolved`.
3. Review Task 3 with the same spec-first, quality-second loop before wiring orchestrator integration.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-05 Plan Written
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Read the approved E7-05 design and mapped the implementation onto the existing prep package boundaries.
2. Wrote the E7-05 implementation plan to `specs/e7-05-guidance-annotation-proposal-system/superpowers-plan.md`.
3. Broke implementation into prep contract models, artifact-path expansion, proposal-generation helpers, prep runtime wiring, and final verification/handoff.
4. Kept the plan aligned with the existing prep architecture by routing work through `contracts.py`, `analysis_artifacts.py`, `handlers.py`, and `orchestrator.py`.

Key Decisions:
- Keep E7-05 inside the current prep package rather than creating a new subsystem.
- Treat `prep-guidance.resolved.json` as authoritative and raw proposals as separate evidence artifacts.
- Use focused prep tests plus the full repo gate as the implementation verification standard.

Current State:
- E7-05 now has both an approved design and a written implementation plan.
- No implementation work has started yet.

Next Steps:
1. Choose execution mode for the E7-05 plan.
2. Implement the plan task-by-task, starting with guidance/proposal contract tests.

Recorded by: codex (gpt-5)

Session: 2026-06-18 - E7-05 Design Written
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-18

Work Completed:
1. Restored the E7-05 backlog scope from `BACKLOG.md` and the direct E7-04 handoff context from the latest feature journal entries.
2. Clarified the relationship between `prep-guidance.input.json`, raw proposal artifacts, and `prep-guidance.resolved.json`.
3. Established that annotation proposals should use a shared base JSON schema for `table`, `callout`, and `skip`, with both full-page and region `skip` support.
4. Defined `prep-guidance.resolved.json` as the only authoritative downstream guidance/annotation contract.
5. Wrote the approved E7-05 design document to `specs/e7-05-guidance-annotation-proposal-system/superpowers-design.md`.

Key Decisions:
- Raw annotation proposals are JSON evidence artifacts, not the PDF itself.
- `annotated-prep.pdf` is optional and visual only; it is not authoritative machine input.
- User revision of visual annotations is anticipated but deferred to E7-06.
- Proposal provenance should be first-class metadata (`code`, `ai`, or `hybrid`).

Current State:
- E7-05 now has an approved design document.
- No implementation work has started.

Next Steps:
1. Write `specs/e7-05-guidance-annotation-proposal-system/superpowers-plan.md`.
2. Review the written design doc with the user before planning if any design changes are needed.
3. After plan approval, implement E7-05 task-by-task.

Recorded by: codex (gpt-5)
