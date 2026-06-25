Session: 2026-04-01 - E7-01 Specify Run and Initial Spec Draft
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-04-01

Work Completed:
1. Created new feature branch and spec folder via Spec-Kit create-new-feature script (`010-key-based-prep-registry`).
2. Added first-pass E7-01 specification content to `specs/e7-01-key-based-prep-registry/spec.md` using the canonical prompt seed from `BACKLOG.md`.
3. Locked canonical prep phase key names in the spec and captured registry requirements, edge cases, and measurable success criteria.

Key Decisions:
- Keep phase + step concepts, but use stable key identity and explicit `order` values as runtime authority.
- Keep display numbering as log/UI alias only (not orchestration identity).
- Scope E7-01 to registry foundation only; defer command-level and conversion integration details to later Epic 7 features.

Current State:
- `specs/e7-01-key-based-prep-registry/spec.md` exists with a complete first-pass draft.
- No revision pass has been performed yet (per session constraint).
- Backlog now contains Epic 7 decomposition and E7-01 canonical prompt seed.

Next Steps:
1. Review `specs/e7-01-key-based-prep-registry/spec.md` for gaps/ambiguities in a follow-up session (no edits required today).
2. Run `/speckit.clarify` on E7-01 after review to capture unresolved decisions.
3. Continue to `/speckit.plan` once spec clarifications are accepted.

Recorded by: codex (gpt-5)

Session: 2026-06-12 - Task 3 Final Code-Quality Re-Review
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-12

Work Completed:
1. Re-reviewed the Task 3 prep registry runtime, package export surface, and unit-test support files after the follow-up test and cleanup pass.
2. Verified the previously flagged gaps were addressed with direct coverage for `disabled_optional_steps`, `get_handler()`, and display-alias stability assertions.
3. Re-ran the focused runtime unit tests for `tests/unit/pdf_convert/prep/test_registry_runtime.py` and confirmed they pass.

Key Decisions:
- Treat this session as a final quality assessment only; no production or test code changes were made.
- Accept the lightweight `tests/unit/pdf_convert/prep/support.py` helper as reasonable test support for Task 3 in its current scope.

Current State:
- Task 3's registry runtime and targeted tests are internally consistent and the previously noted follow-up gaps appear closed.
- Focused runtime coverage now includes the public accessors and insertion-order alias expectations called out in the earlier review.
- Focused runtime tests currently pass (`21 passed`).

Next Steps:
1. Proceed to the next planned E7-01 task unless broader cross-package review is desired.
2. If a final implementation gate is needed, run the full project quality pipeline before merge.

Recorded by: codex (gpt-5)

Session: 2026-06-12 - Superpowers Implementation Plan for E7-01
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-12

Work Completed:
1. Used the approved Superpowers design to create a new implementation plan for E7-01.
2. Scoped the plan to a prep-only registry package that remains separate from the current numeric conversion pipeline.
3. Chose a focused implementation layout under `src/gm_kit/pdf_convert/prep/` with dedicated runtime, type, and validation files plus prep-specific unit tests.
4. Wrote the new plan to `specs/e7-01-key-based-prep-registry/superpowers-plan.md`.

Key Decisions:
- The E7-01 implementation should create a new prep package instead of modifying the current conversion `PhaseRegistry`.
- Handler reference validation should use a deterministic `module.path:callable_name` format.
- E7-01 implementation remains foundation-only and does not add CLI entrypoints, prep artifact contracts, or migration glue.

Current State:
- `specs/e7-01-key-based-prep-registry/superpowers-design.md` is the approved design artifact for E7-01.
- `specs/e7-01-key-based-prep-registry/superpowers-plan.md` is now the active implementation plan artifact.
- No implementation work has started yet under the new Superpowers plan.

Next Steps:
1. Choose an execution mode for `specs/e7-01-key-based-prep-registry/superpowers-plan.md`.
2. Prefer `superpowers:subagent-driven-development` if available; otherwise use `superpowers:executing-plans`.
3. Implement the plan task-by-task and record the resulting code/test changes in this journal.

Recorded by: codex (gpt-5)

Session: 2026-06-12 - Superpowers Design Draft for E7-01
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-12

Work Completed:
1. Restarted E7-01 under the Superpowers brainstorming workflow using the canonical prompt seed from `BACKLOG.md`.
2. Confirmed that E7-01 should remain strictly foundation-only, with no command skeleton, migration shim, or runtime integration work pulled in from later Epic 7 features.
3. Reused previously settled E7-01 technical decisions as baseline defaults for the new workflow.
4. Wrote the new Superpowers design document to `specs/e7-01-key-based-prep-registry/superpowers-design.md`.

Key Decisions:
- E7-01 remains limited to typed registry definitions, ordering rules, display alias behavior, handler validation policy, logging metadata contract, and tests.
- Existing Spec-Kit E7-01 artifacts remain historical reference material and are not the active design source of truth for the restarted workflow.
- The Superpowers design file is now the active design artifact for E7-01 pending user review.

Current State:
- `specs/e7-01-key-based-prep-registry/superpowers-design.md` exists with the first Superpowers-based E7-01 design draft.
- The draft reflects the backlog scope and preserved baseline decisions from the earlier E7-01 work.
- Planning has not started yet; waiting for user review and approval of the written design document.

Next Steps:
1. User reviews `specs/e7-01-key-based-prep-registry/superpowers-design.md`.
2. Apply any requested design edits.
3. After approval, create `specs/e7-01-key-based-prep-registry/superpowers-plan.md` using the Superpowers planning workflow.

Recorded by: codex (gpt-5)


Session: 2026-06-12 - Backlog-Aligned Feature Folder Rename
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-12

Work Completed:
1. Updated `AGENTS.md` to define the preferred feature-folder naming convention as `specs/<backlog-feature-id>-<short-slug>/` for Epic 7 and later work.
2. Renamed the E7-01 feature folder from `specs/010-key-based-prep-registry/` to `specs/e7-01-key-based-prep-registry/`.
3. Updated path references inside the E7-01 feature artifacts so the renamed folder is now the canonical path.

Key Decisions:
- `BACKLOG.md` feature IDs are now the source of truth for Epic 7+ feature-folder names.
- Historical branch-name references inside older artifacts remain unchanged because they reflect the actual branch used during those earlier sessions.
- The canonical E7-01 feature folder is now `specs/e7-01-key-based-prep-registry/`.

Current State:
- Repo guidance now supports backlog-aligned feature-folder naming for Epic 7 and later features.
- E7-01 artifacts now live under `specs/e7-01-key-based-prep-registry/`.
- The next Superpowers-generated design and plan files for E7-01 should be created in this renamed folder.

Next Steps:
1. Start the E7-01 Superpowers brainstorming flow using the canonical prompt seed in `BACKLOG.md`.
2. Write the new design to `specs/e7-01-key-based-prep-registry/superpowers-design.md`.
3. After design approval, generate `specs/e7-01-key-based-prep-registry/superpowers-plan.md`.

Recorded by: codex (gpt-5)

Session: 2026-06-12 - Repo Guidance Updated for Superpowers Cutover
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-12

Work Completed:
1. Updated `AGENTS.md` to make Superpowers the active workflow for new feature work in this repository.
2. Added explicit repository instructions requiring Superpowers-generated design and plan docs to live inside each feature folder instead of Superpowers' default `docs/superpowers/` locations.
3. Standardized the preferred Superpowers artifact filenames as `superpowers-design.md` and `superpowers-plan.md` under `specs/<feature-name>/`.
4. Updated `README.md` workflow guidance to replace the active Spec-Kit instructions with Superpowers-oriented feature creation guidance while preserving Spec-Kit materials as historical references.

Key Decisions:
- Feature-local artifact storage is now a repository rule, not just an implementation preference.
- Superpowers artifact filenames should remain distinct from legacy `spec.md` and `plan.md` files to avoid ambiguity during migration.
- Existing Spec-Kit docs stay in the repo for historical context until the Epic 7 pilot proves the replacement workflow cleanly.

Current State:
- Repo-level agent guidance now directs future agents to keep Superpowers design and plan files in `specs/<feature-name>/`.
- `README.md` now reflects the Superpowers-first workflow for new feature work.
- E7-01 remains the pilot feature for re-specification under Superpowers.

Next Steps:
1. Start E7-01 over with the Superpowers brainstorming flow using the canonical prompt seed in `BACKLOG.md`.
2. Write the new design to `specs/e7-01-key-based-prep-registry/superpowers-design.md`.
3. After design approval, generate `specs/e7-01-key-based-prep-registry/superpowers-plan.md` and use that as the implementation source of truth.

Recorded by: codex (gpt-5)

Session: 2026-06-12 - Superpowers Migration Assessment for E7-01
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-12

Work Completed:
1. Verified that the `superpowers@openai-curated` plugin is installed and enabled for Codex in `.codex/config.toml`.
2. Read the installed Superpowers workflow guidance for `brainstorming`, `writing-plans`, and `executing-plans` to determine expected artifact locations and workflow order.
3. Compared Superpowers defaults against the existing `specs/e7-01-key-based-prep-registry/` layout and the repo's current Spec-Kit-oriented documentation and conventions.
4. Produced a migration recommendation for Epic 7 that preserves `BACKLOG.md` and `feature_journal.md`, keeps E7-01 in its existing feature folder, and treats prior Spec-Kit artifacts as historical inputs rather than deleting them immediately.

Key Decisions:
- Reuse `specs/e7-01-key-based-prep-registry/` for E7-01 instead of moving Epic 7 artifacts to Superpowers' default `docs/superpowers/` paths.
- Treat the existing E7-01 `spec.md`/`plan.md`/related Spec-Kit outputs as archived reference material during the transition, not as the active workflow source of truth.
- Use `BACKLOG.md` as the canonical Epic 7 scope source and `feature_journal.md` as the canonical handoff log during the migration.
- Defer repo-wide deletion or retirement of Spec-Kit files until the Superpowers-based E7-01 pilot is complete and the replacement workflow is stable.

Current State:
- Superpowers is available for use in Codex and its default workflow expects design docs under `docs/superpowers/specs/` and plans under `docs/superpowers/plans/`, but those defaults can be overridden by project preference.
- The repository still contains substantial active documentation that assumes Spec-Kit is the primary workflow (`README.md`, `docs/team/project-overview.md`, `docs/team/speckit_guidelines.md`, prompt-template docs, and historical feature journals).
- E7-01 is still the correct migration pilot because implementation has not started and the existing artifact set is still planning-stage only.

Next Steps:
1. Update repo guidance to declare Superpowers as the active workflow for new Epic 7 work while preserving existing Spec-Kit artifacts as historical references.
2. Decide the exact file naming/location convention for Superpowers-generated design and plan artifacts within `specs/e7-01-key-based-prep-registry/` to avoid ambiguous overlap with existing `spec.md` and `plan.md`.
3. Re-spec E7-01 from the canonical prompt seed in `BACKLOG.md` using the Superpowers brainstorming flow, with the existing E7-01 spec files used only as reference context.
4. After the new E7-01 design is approved, generate the new implementation plan with Superpowers and only then decide what older Spec-Kit files should be marked superseded or archived more explicitly.

Recorded by: codex (gpt-5)

Session: 2026-04-02 - Epic 7 Alignment + Skills/MCP Backlog Expansion
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-04-02

Work Completed:
1. Aligned `specs/e7-01-key-based-prep-registry/spec.md` with updated Epic 7 constraints:
   - Added non-normative "Current Implementation References" pointing to existing conversion/orchestrator/state/agent-step files to anchor migration context.
   - Added FR-017/FR-018 and SC-005 for execution-category support and E4-07a-i logging parity support.
2. Updated Epic 7 in `BACKLOG.md` to include:
   - explicit Code/Agent/User execution category map
   - explicit requirement to follow E4-07a-i logging structure with deterministic test assertions
3. Added Epic 8 in `BACKLOG.md` for `gmkit init` migration from prompts/commands to skills (Codex/Claude/OpenCode/Qwen), including research, installer architecture, dev registration/debug workflow, Gemini compatibility, and validation matrix.
4. Added Epic 9 in `BACKLOG.md` for Agentic UX System implementation planning, referencing `docs/team/gmkit_agentic_ux_system.md` as canonical design input.

Key Decisions:
- Keep `gmkit init` as the central installation orchestrator for skills + future MCP + MCP app wiring.
- Treat E4-08a as superseded; Epic 7 is canonical for prep-first pipeline scope.
- Keep E7-01 as registry foundation only (no full implementation in this session).
- Preserve Code-first default for Epic 7 while allowing targeted Agent-assisted handlers and interactive User review steps.

Current State:
- E7-01 spec exists and is materially aligned with current backlog direction.
- Epic 7 has explicit execution ownership and logging expectations.
- Epic 8 and Epic 9 are now represented in backlog as high-level programs ready for decomposition/specification.
- No `/speckit.clarify` run yet in this session.

Next Steps:
1. Start next session by running `/speckit.clarify` for E7-01 (`specs/e7-01-key-based-prep-registry/spec.md`).
2. After clarify outputs are accepted, proceed to `/speckit.plan` for E7-01.
3. Begin decomposition/specification sequence for Epic 8 starting with E8-01 (skills capability + integration research).
4. Keep Epic 9 high-level for now; decompose after Epic 8 migration direction is stabilized.

Recorded by: codex (gpt-5)

Session: 2026-04-03 - Clarify x2 + Plan + Tasks Generation
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-04-03

Work Completed:
1. Ran `/speckit.clarify` twice for E7-01 and integrated clarifications directly into `spec.md`.
2. Added/expanded functional requirements for ordering policy, display numbering, handler policy validation, optional-handler disable semantics, and startup diagnostics security sanitization.
3. Ran `/speckit.plan` and generated Phase 0/1 artifacts:
   - `plan.md`
   - `research.md`
   - `data-model.md`
   - `contracts/prep-registry-contract.md`
   - `quickstart.md`
4. Ran `/speckit.tasks` and generated `tasks.md` with 34 dependency-ordered tasks organized by user story and phase.
5. Confirmed MVP implementation scope as Setup + Foundational + US1.

Key Decisions:
- `order` is integer-only.
- Phase ordering uses phase-level `order`; step ordering is per-phase.
- Duplicate phase order and duplicate per-phase step order fail validation.
- All handlers validated at startup.
- Required handler failures fail startup; optional handler failures become `DISABLED_OPTIONAL` with explicit reason.
- Handler policy must be explicit per step (`required|optional`), never inferred.
- Display alias default is `phaseOrder.stepOrder` via formatter abstraction; key identity remains authoritative.
- Validation/log output must sanitize secrets and sensitive absolute local paths.

Current State:
- E7-01 spec is fully clarified for planning and implementation.
- Planning artifacts are complete and present under `specs/e7-01-key-based-prep-registry/`.
- `tasks.md` is generated and ready for execution sequencing.

Next Steps:
1. Run `/speckit.checklist` for `specs/e7-01-key-based-prep-registry/spec.md` and review checklist output.
2. If checklist passes, begin implementation using `tasks.md` in phase order (MVP: Phase 1 + Phase 2 + US1).

Recorded by: codex (gpt-5)

Session: 2026-04-03 - Requirements Checklist Generation (Post-Tasks)
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-04-03

Work Completed:
1. Ran `/speckit.checklist` after spec clarification, planning, and task generation.
2. Generated strict-depth requirements-quality checklist at `specs/e7-01-key-based-prep-registry/checklists/requirements.md`.
3. Produced 34 checklist items (`CHK001`-`CHK034`) covering completeness, clarity, consistency, acceptance quality, scenario/edge-case coverage, non-functional requirements, dependencies, and ambiguity checks.

Key Decisions:
- Checklist is treated as a pre-implementation quality gate for requirements (not implementation testing).
- Current implementation should pause until checklist items are reviewed and resolved in spec/planning artifacts as needed.

Current State:
- E7-01 spec, plan, research, data model, contract, tasks, and checklist artifacts now all exist under `specs/e7-01-key-based-prep-registry/`.
- Checklist has not yet been resolved item-by-item.

Next Steps:
1. Resolve all items in `specs/e7-01-key-based-prep-registry/checklists/requirements.md`.
2. Update `spec.md`/`plan.md` (and related artifacts if needed) for each accepted checklist finding.
3. Re-review checklist status, then begin implementation from `tasks.md` MVP path (Phase 1 + Phase 2 + US1).

Recorded by: codex (gpt-5)

Session: 2026-04-03 - Checklist Resolution Pass 1
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-04-03

Work Completed:
1. Loaded `spec.md`, `plan.md`, and `checklists/requirements.md` and started checklist resolution.
2. Resolved and checked off obvious checklist items; updated checklist status to 30 resolved / 4 open.
3. Updated `spec.md` with explicit actionable-error content requirement:
   - Added `FR-009e` (minimum error content includes failing key, failure class, remediation hint).

Key Decisions:
- Proceed with mixed resolution strategy: auto-resolve obvious checklist items first, then handle unresolved items one-by-one with user decisions.

Current State:
- `specs/e7-01-key-based-prep-registry/checklists/requirements.md` has four unresolved items:
  - `CHK025` (empty phase behavior)
  - `CHK027` (import vs bind failure distinction)
  - `CHK031` (performance requirement-level criterion)
  - `CHK034` (definition of sensitive absolute local paths)
- Next unresolved question was prepared for `CHK025` but not finalized.

Next Steps:
1. Resume with `CHK025` decision:
   - Option set currently proposed (A/B/C) with recommendation for conditional behavior by required/optional phase policy.
2. Resolve `CHK027`, `CHK031`, and `CHK034` in sequence and update spec/checklist.
3. Re-check checklist for full closure and record final readiness before implementation starts.

Recorded by: codex (gpt-5)
Session: 2026-06-12 - Task 3 Code Quality Review
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-12

Work Completed:
1. Reviewed Task 3 implementation files for the prep registry runtime, package exports, and unit-test support helpers.
2. Cross-checked the implementation against the E7-01 Superpowers Task 3 plan requirements and file-structure expectations.
3. Ran the focused runtime unit tests in `tests/unit/pdf_convert/prep/test_registry_runtime.py` and confirmed they pass.

Key Decisions:
- Treat the review as implementation assessment only; no production code changes were made in this session.
- Record follow-up test coverage gaps as review feedback rather than expanding scope during the review.

Current State:
- Task 3 remains cleanly isolated under `gm_kit.pdf_convert.prep` and does not touch the numeric conversion pipeline.
- Focused runtime tests currently pass (`18 passed`).
- Review feedback identifies a small number of test-coverage gaps around public runtime accessors and alias-stability assertions.

Next Steps:
1. Decide whether to add follow-up tests for `get_handler()`, `disabled_optional_steps`, and explicit display-alias stability after inserted steps.
2. If desired, document whether the extra `tests/unit/pdf_convert/prep/support.py` helper file should be considered part of the accepted Task 3 structure.
3. Continue with the next planned E7-01 task or address the review feedback before moving on.

Recorded by: codex (gpt-5)

Session: 2026-06-12 - Task 4 Package Export and E7-01 Implementation Handoff
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-12

Work Completed:
1. Completed the top-level `gm_kit.pdf_convert` package surface for the prep foundation by binding and exporting `prep` from `src/gm_kit/pdf_convert/__init__.py`.
2. Recorded the completed E7-01 implementation scope to date, including the prep modules added under `src/gm_kit/pdf_convert/prep/`: `__init__.py`, `registry.py`, `registry_errors.py`, and `registry_types.py`.
3. Captured the implemented validation and ordering behavior: canonical phase-key enforcement, deterministic `order` sorting, stable display alias numbering derived from insertion order, handler reference validation/sanitization, and required-vs-optional step handling including disabled optional steps.
4. Recorded the prep-focused unit-test surface added for E7-01: `tests/unit/pdf_convert/prep/test_registry_types.py`, `tests/unit/pdf_convert/prep/test_registry_validation.py`, `tests/unit/pdf_convert/prep/test_registry_runtime.py`, plus `tests/unit/pdf_convert/prep/support.py`.

Key Decisions:
- Keep E7-01 foundation-only: `gm_kit.pdf_convert.prep` is now available from the top-level package surface, but CLI wiring, command orchestration, and prep artifact contracts remain owned by later Epic 7 tasks.
- Preserve the separation between the new prep registry runtime and the existing numeric conversion pipeline so E7-02 and E7-03 can integrate intentionally instead of via implicit compatibility shims.
- Treat the current export change as a package-surface completion step, not as evidence that prep execution is user-facing yet.

Current State:
- E7-01 now exposes `gm_kit.pdf_convert.prep` from the top-level package surface and has an implementation journal entry covering the foundation work delivered across Tasks 1-4.
- The prep registry surface remains a reusable foundation package with typed definitions, validation helpers, and runtime ordering/access behavior covered by prep-specific unit tests.
- Later Epic 7 work still owns CLI command skeletons, runtime wiring into conversion flows, and any prep artifact contract/output definitions.

Next Steps:
1. E7-02 should wire the foundation registry into the analyze/prep command skeleton without changing the canonical key/order contract established here.
2. E7-03 should define artifact contracts and execution/reporting integration on top of the existing prep registry surface rather than extending E7-01 scope.
3. Keep future Epic 7 work aligned with the foundation-only boundary unless the backlog explicitly expands E7-01.

Recorded by: codex (gpt-5)

Session: 2026-06-13 - Task 4 Verification Completion
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-13

Work Completed:
1. Resumed the incomplete E7-01 Task 4 closeout and inspected the prep package surface, runtime files, and prep-specific tests.
2. Fixed the remaining prep-package cleanup items in `src/gm_kit/pdf_convert/prep/__init__.py`, `src/gm_kit/pdf_convert/prep/registry.py`, and `src/gm_kit/pdf_convert/prep/registry_types.py`.
3. Kept enum definitions compatible with the project's broader Python support expectations while resolving the outstanding lint issue on the new prep code.
4. Re-ran focused verification in the project `uv` environment and confirmed the prep package lint, type checks, and prep unit tests all pass.

Key Decisions:
- Treat `uv run --python "$(cat .python-version)" --extra dev --editable -- ...` as the authoritative verification path for this feature work.
- Preserve `str, Enum` for handler enums instead of adopting `StrEnum`, because plain Python 3.10 execution still exists in some local paths and the repo guidance still references broader Python compatibility than 3.11+.

Current State:
- E7-01 Task 4 is now closed with fresh verification evidence.
- Verified commands:
  - `uv run --python "$(cat .python-version)" --extra dev --editable -- ruff check src/gm_kit/pdf_convert/prep tests/unit/pdf_convert/prep src/gm_kit/pdf_convert/__init__.py`
  - `uv run --python "$(cat .python-version)" --extra dev --editable -- mypy src/gm_kit/pdf_convert/prep src/gm_kit/pdf_convert/__init__.py tests/unit/pdf_convert/prep`
  - `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep -q`
- `gm_kit.pdf_convert.prep` remains exported from the top-level package surface and the prep foundation remains isolated from the existing numeric conversion pipeline.

Next Steps:
1. Start E7-02 from the existing prep foundation without changing the key/order contract established in E7-01.
2. If broader repo verification is needed before branch integration, run the full project quality pipeline separately because the worktree contains unrelated in-progress changes.

Recorded by: codex (gpt-5)

Session: 2026-06-13 - E7-01 Audit Gap Closure
--------------------------------------------------------
Branch: 010-key-based-prep-registry
Date: 2026-06-13

Work Completed:
1. Reviewed E7-01 against `BACKLOG.md`, `superpowers-design.md`, `superpowers-plan.md`, and the implemented prep registry surface with fresh verification.
2. Added prep runtime coverage for full canonical phase registration success and non-integer phase/step order rejection in `tests/unit/pdf_convert/prep/test_registry_runtime.py`.
3. Tightened the E7-01 design wording so display alias generation is explicitly derived from validated `order` values and so the logging section clearly describes readable-log support as metadata, not rendered log output.
4. Updated the E7-01 plan file structure to include the existing `tests/unit/pdf_convert/prep/support.py` helper.
5. Removed the malformed partial journal fragment left by the earlier failed shell append.

Key Decisions:
- Treat the E7-01 audit findings as closure work, not as scope expansion: the only required changes were missing test coverage and design/plan wording alignment.
- Keep the implementation unchanged because the newly added audit tests passed immediately; the missing gap was coverage, not runtime behavior.

Current State:
- E7-01 remains foundation-only and now has explicit test coverage for the two audit gaps that were still open.
- Fresh focused verification passed:
  - `uv run --python "$(cat .python-version)" --extra dev --editable -- ruff check src/gm_kit/pdf_convert/prep tests/unit/pdf_convert/prep src/gm_kit/pdf_convert/__init__.py`
  - `uv run --python "$(cat .python-version)" --extra dev --editable -- mypy src/gm_kit/pdf_convert/prep src/gm_kit/pdf_convert/__init__.py tests/unit/pdf_convert/prep`
  - `uv run --python "$(cat .python-version)" --extra dev --editable -- pytest tests/unit/pdf_convert/prep -q`
- Prep-focused suite now passes with `35 passed`.

Next Steps:
1. Start E7-02 from the now-audited E7-01 registry foundation.
2. Keep future prep command and artifact work aligned with the key/order and metadata contracts already established here.

Recorded by: codex (gpt-5)
