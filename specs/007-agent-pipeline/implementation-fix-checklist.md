# E4-07b Implementation Fix Checklist (Spec Conformance)

Purpose: Close the remaining gaps between `specs/007-agent-pipeline/spec.md` and current code implementation.

Scope references:
- `specs/007-agent-pipeline/spec.md:143` (FR-010)
- `specs/007-agent-pipeline/spec.md:144` (FR-011)
- `specs/007-agent-pipeline/spec.md:147` (FR-014)

## 1) Replace Phase 7 step 7.7 placeholder

- [x] Implement real agent execution for step `7.7` in `src/gm_kit/pdf_convert/phases/phase7.py`.
- [x] Remove placeholder `SKIPPED` path (`"integration pending"` message).
- [x] Wire actual inputs from prior phase artifacts (extracted text + workspace context), then call runtime.
- [x] Persist step output artifact(s) expected by downstream step `8.7`.
- [x] Ensure failure handling follows FR-010 criticality behavior (no silent unresolved stub skip).

Acceptance checks:
- [x] `7.7` returns SUCCESS/WARNING/ERROR based on runtime outcome, not stub SKIPPED.
- [x] `7.7` outputs are consumable by step `8.7`.

## 2) Replace Phase 8 step 8.7 placeholder

- [x] Implement real agent execution for step `8.7` in `src/gm_kit/pdf_convert/phases/phase8.py`.
- [x] Remove placeholder `SKIPPED` path (`"integration pending"` message).
- [x] Load table-detection artifacts from `7.7`, perform expected image handoff/cropping flow, and execute agent step.
- [x] Ensure in-place markdown edit + metadata/output handling matches design expectations.
- [x] Ensure degraded continuation behavior is explicit and aligned with FR-010.

Acceptance checks:
- [x] `8.7` no longer reports placeholder skip when inputs exist.
- [x] Downstream phases receive expected post-8.7 markdown/state.

## 3) Replace Phase 9 placeholders for 9.4 and 9.5

- [x] Implement builders and runtime calls for `9.4` and `9.5` in `src/gm_kit/pdf_convert/phases/phase9.py`.
- [x] Remove `None` builders and generic `"Integration pending"` SKIPPED behavior.
- [x] Feed each step the required phase artifacts and schema-valid payloads.
- [x] Keep `9.1` as no-op per spec (already intended).
- [x] Ensure FR-010 behavior for retry/escalation/degraded continuation is preserved.

Acceptance checks:
- [x] `9.4` and `9.5` execute with real inputs and structured outcomes.
- [x] No unresolved placeholder skip remains for `9.2-9.5, 9.7-9.8`.

## 4) Update tests to enforce non-stub behavior

- [x] Add/update unit tests for phases 7/8/9 to fail if `7.7`, `8.7`, `9.4`, or `9.5` return placeholder SKIPPED messages.
- [ ] Add/update integration coverage for end-to-end step handoff (`7.7 -> 8.7 -> 9.4/9.5`).
- [x] Update/extend contract tests where needed for payload shape and artifact expectations.

Acceptance checks:
- [ ] Tests assert these steps are integrated paths, not stubs.
- [ ] Relevant tests pass under `just test-unit` (and integration suite if included for this feature).

## 5) Align tracking docs after code fixes

- [x] Mark corresponding tasks complete in `specs/007-agent-pipeline/tasks.md` (`T061`, `T062`, `T063`).
- [x] Append an implementation entry in `specs/007-agent-pipeline/feature-implementation-journal.txt` with what changed and validation run.
- [x] If behavior/design details changed, sync `plan.md` notes accordingly.

Acceptance checks:
- [x] Tasks and journal reflect completed implementation status.
- [x] No contradiction remains between spec, tasks, and code.
