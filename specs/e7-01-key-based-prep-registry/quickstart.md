# Quickstart: E7-01 Key-Based Prep Registry Foundation

## Goal
Implement key-based prep registry foundations for `gmkit analyze-and-prep-pdf` orchestration.

## 1. Implement registry models
1. Add typed phase/step definition models in `src/gm_kit/pdf_convert/` (prep-oriented module).
2. Add validation rules for:
   - phase order uniqueness
   - step order uniqueness per phase
   - required handler policy field
   - valid phase references

## 2. Implement startup validation
1. Add handler import/bind validation at startup.
2. Fail fast for required handler failures.
3. Disable optional handlers with status `DISABLED_OPTIONAL` and warning reason.

## 3. Implement display mapping
1. Add generated display alias mapping with default `phaseOrder.stepOrder` format.
2. Ensure runtime identity remains key-based.

## 4. Logging alignment
1. Ensure emitted metadata can support E4-07a-i style phase/step logging structure.
2. Sanitize diagnostics to avoid secrets/sensitive absolute paths.

## 5. Tests
1. Add unit tests for ordering determinism and insertion behavior.
2. Add unit tests for startup validation behavior (required vs optional handlers).
3. Add unit tests for display mapping and `DISABLED_OPTIONAL` representation.
4. Add tests for log/error sanitization constraints.
