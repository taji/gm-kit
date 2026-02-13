# Tests

This folder contains unit and integration tests for the GM-Kit CLI and PDF pipeline.

## Regression Test Harness Pattern

When an integration anomaly requires a code change, add a **unit test** that reproduces the issue.
This keeps regressions localized and makes failures easy to diagnose.

Workflow:
1. Identify the minimal input that triggers the anomaly.
2. Add a unit test in `tests/unit/...` that fails without the fix.
3. Apply the code change.
4. Re-run the unit test and the original integration test.

Guidelines:
- Prefer unit tests over integration tests for regressions.
- Assert exact error messages or output fragments when feasible.
- Use fakes/mocks instead of real PDFs when the failure is logic-only.
- Keep fixtures small and focused if a real PDF is required.

## Naming

Use the standard pattern:
`test_<Subject>__should_<ExpectedOutcome>__when_<Condition>`

## Fixture Setup

- See `tests/fixtures/pdf_convert/README.md` for fixture policy and sources.
- Some third-party PDFs are intentionally not committed for licensing reasons.
- To fetch the B2 integration fixture locally, run:
  - `bash tests/fixtures/pdf_convert/download_b2_fixture.sh`
- To fetch the optional CoC fixture locally, run:
  - `bash tests/fixtures/pdf_convert/download_cofc_fixture.sh`
