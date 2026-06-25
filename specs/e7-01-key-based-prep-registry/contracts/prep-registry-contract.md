# Contract: Prep Registry Foundation (E7-01)

## Scope
Internal contract for registry definitions and startup validation behavior.

## Phase Definition Contract
- Required fields:
  - `phase_key` (string, unique)
  - `order` (integer, unique)
  - `display_name` (string)

## Step Definition Contract
- Required fields:
  - `step_key` (string, unique)
  - `phase_key` (string, must reference registered phase)
  - `order` (integer, unique within `phase_key`)
  - `handler_ref` (string import/call reference)
  - `handler_policy` (`required` | `optional`)
  - `display_name` (string)

## Startup Validation Contract
- Validate all handlers at startup.
- Required handler failure:
  - Startup fails with actionable, sanitized error.
- Optional handler failure:
  - Step disabled with status `DISABLED_OPTIONAL`.
  - Warning emitted including disable reason (sanitized).

## Logging/Display Contract
- Runtime identity keys remain `phase_key` / `step_key`.
- Display alias default format is `phaseOrder.stepOrder`.
- Display alias must not be used as orchestration identity.

## Security/Privacy Contract
- Validation and startup logs/errors must not expose:
  - secrets/tokens/credentials
  - sensitive absolute local filesystem paths
