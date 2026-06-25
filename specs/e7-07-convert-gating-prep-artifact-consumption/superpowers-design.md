# E7-07 Convert Gating + Prep Artifact Consumption Design

**Goal:** Make `gmkit pdf-convert` consume prep artifacts when available, prefer reviewed prep guidance when present, and bootstrap missing baseline prep outputs so the legacy conversion command still works end-to-end.

## Decision
Use **prep-first artifact resolution** at conversion startup, then keep **phase-level artifact resolution** for the actual data each phase consumes.

That gives us one clean conversion entry point:
- if prep artifacts already exist, conversion consumes them directly
- if prep artifacts are missing, conversion bootstraps baseline metadata and preflight outputs from the source PDF so the command remains usable
- if reviewed prep artifacts exist, conversion prefers them
- if reviewed prep artifacts are absent, conversion falls back to baseline prep outputs

## Architecture
Add a small prep-artifact resolution layer in conversion startup that knows how to locate the prep workspace and resolve the effective artifact set for a source PDF. The conversion orchestrator uses that resolver before running phases, so it can prefer prep outputs, bootstrap baseline artifacts when needed, and still fail clearly if bootstrap cannot produce a usable baseline.

The resolver should not invent reviewed artifacts or change review semantics. Its job is to select the best available artifact for each logical input and make the baseline bootstrap behavior explicit. Reviewed guidance becomes an override of baseline guidance; everything else remains baseline-only unless a later feature introduces a reviewed variant.

## Artifact Contract
The conversion side should treat these prep outputs as the baseline contract when they already exist:
- `prep/prep-manifest.json`
- `prep/metadata.json`
- `prep/toc-extracted.txt`
- `prep/chapter-index.json`
- `prep/chunk-plan.json` when chunking was required
- `prep/prep-guidance.resolved.json`
- `prep/preprocessed/<pdf-stem>-no-images.pdf` when the prep workflow produced it

Reviewed prep artifacts, when present, should override baseline equivalents:
- `prep/prep-guidance.reviewed.json` overrides `prep/prep-guidance.resolved.json`

I am assuming no separate reviewed artifacts for chapter index, chunk plan, or no-images PDF in this feature. Those remain deterministic prep outputs, not review outputs.

## Data Flow
1. `pdf-convert` starts and resolves the prep workspace from the conversion output directory.
2. The resolver checks that the baseline prep workspace exists and contains the required files for conversion startup.
3. The conversion pipeline loads the effective guidance contract by preferring `prep-guidance.reviewed.json` when it exists, otherwise `prep-guidance.resolved.json`.
4. Conversion phases continue to consume prep data through the existing prep-aware loaders and phase inputs.
5. Phases that need guidance or annotations keep using the resolved prep contract; they do not rediscover tables or callouts themselves.

## Error Handling
Missing prep workspace should not block conversion outright; the conversion command may bootstrap baseline metadata and preflight outputs from the source PDF before the first phase runs.

Error messages should be explicit and actionable:
- name the missing file when bootstrap is not possible
- distinguish between a missing baseline artifact and a reviewed artifact that is simply unavailable
- explain that reviewed guidance is optional while baseline guidance is authoritative for automation

If reviewed prep guidance is absent, that is not an error. The system should fall back to baseline guidance without warning.

If the baseline prep guidance exists but is malformed, fail at startup with a conversion error that points at the bad artifact.

## Implementation Boundaries
This feature should touch the conversion startup path, not the legacy discovery logic in Phase 7/8.

In scope:
- startup resolution of prep workspace inputs and effective guidance
- reviewed-versus-baseline prep guidance selection
- conversion-side bootstrap of baseline metadata/preflight outputs when prep artifacts are absent
- conversion-side error messaging and CLI plumbing
- tests for reviewed fallback, malformed prep guidance, and bootstrap fallback behavior

Out of scope:
- removing `gm_callout_config_file` from Phase 7/8
- changing callout discovery or formatting internals
- redesigning prep generation itself

## Testing Strategy
Add unit tests that cover:
- conversion fails immediately when the prep workspace is missing
- conversion fails immediately when a required baseline prep file is missing
- reviewed guidance is preferred when both reviewed and baseline guidance exist
- baseline guidance is used when reviewed guidance is absent
- malformed prep guidance surfaces a clear error

Keep the tests focused on the startup resolver and the phase payloads that consume prep guidance. Do not add integration tests for unrelated phases unless the new gating path changes behavior there directly.
