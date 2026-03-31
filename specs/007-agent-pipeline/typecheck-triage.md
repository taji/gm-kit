# Typecheck Triage (2026-03-04)

Scope: `just typecheck` failures after E4-07b integration updates.

Status summary:
- Total errors: 23
- Files affected: 8

## Priority Order (lowest risk -> highest impact)

## 1) `src/gm_kit/pdf_convert/agents/errors.py` (1 error)
- Error:
  - line 23: implicit optional default (`output: dict = None`)
- Fix:
  - change signature to `output: dict[str, object] | None = None`
  - keep `self.output = output or {}`

## 2) `src/gm_kit/pdf_convert/phases/phase3.py` (1 error)
- Error:
  - line 1011: returns `Any` from `fitz` page_count
- Fix:
  - cast result: `count = int(doc.page_count)`
  - return `count`

## 3) `src/gm_kit/pdf_convert/agents/token_preflight.py` (5 errors)
- Errors:
  - lines 56/68/71/79/81: assigning `str` into dict inferred as `int | None`
- Root cause:
  - `result` dict inferred too narrowly from initial keys/values.
- Fix:
  - annotate result explicitly with wider value type, e.g.:
    - `result: dict[str, int | bool | str | None] = {...}`
    - OR introduce a small `TypedDict` for the function return shape.

## 4) `src/gm_kit/pdf_convert/agents/evaluator.py` (2 errors)
- Errors:
  - lines 20/24: returning `Any` from registry access wrappers
- Fix:
  - explicitly annotate `_rubrics` in `RubricRegistry.__init__` as `dict[str, StepRubric]`
  - ensure `all_rubrics()` returns typed copy.

## 5) `src/gm_kit/pdf_convert/agents/contracts.py` (1 error)
- Error:
  - line 58: `load_schema()` returns `Any` from `json.load`
- Fix:
  - cast loaded schema:
    - `schema = cast(dict[str, Any], json.load(f))`
  - keep function return type `dict[str, Any]`.

## 6) `src/gm_kit/pdf_convert/agents/dispatch.py` (1 error)
- Error:
  - line 119: `build_agent_command()` returns `Any`
- Root cause:
  - config dict is untyped and list concatenation pulls `Any`.
- Fix:
  - type dispatch table and config values, or cast args:
    - `args = cast(list[str], config["args"])`
    - `cmd: list[str] = [str(config["cli"]), *args]`

## 7) `src/gm_kit/pdf_convert/phases/phase9.py` (6 errors)
- Errors:
  - lines 260/267/270/282/293/314: “Cannot call function of unknown type”
- Root cause:
  - heterogeneous builder list; `builder` not typed callable to mypy.
- Fix:
  - define a typed callable protocol/alias for builders, or dispatch builders directly in each branch.
  - simplest path: avoid `steps_to_execute` builder tuple and call each builder in explicit per-step branch.

## 8) `src/gm_kit/pdf_convert/agents/registry.py` (6 errors)
- Errors:
  - lines 129-134: `defn[...]` values inferred as `object` passed to typed dataclass fields.
- Root cause:
  - `STEP_DEFINITIONS` dict lacks typed structure.
- Fix:
  - define `TypedDict` for step definition shape.
  - annotate `STEP_DEFINITIONS: dict[str, StepDefinitionDict]`.
  - then `defn["phase"]`, etc. become correctly typed.

## Suggested execution sequence
1. Fix `errors.py`, `phase3.py` (quick wins).
2. Fix `token_preflight.py` and `contracts.py`.
3. Fix `evaluator.py` and `dispatch.py`.
4. Fix `registry.py` typed dict.
5. Fix `phase9.py` builder typing (likely the only non-trivial refactor).
6. Re-run `just typecheck`.

## Validation command
```bash
UV_CACHE_DIR=/tmp/uvcache just typecheck
```
