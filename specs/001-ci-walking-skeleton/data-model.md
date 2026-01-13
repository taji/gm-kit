# Data Model: CI Pipeline for Walking Skeleton

This feature introduces no persistent data model. CI artifacts are ephemeral and limited to workflow outputs.

## Entities

- **CI Workflow**: The pipeline definition for PR validation; includes a Linux job.
- **CI Job**: An execution unit (e.g., Linux quality gates, parity check).
- **Parity Output**: Generated files used to compare bash vs PowerShell outputs.

## Relationships

- CI Workflow contains CI Jobs.
- Parity Output is produced by a CI Job and compared within the same job.

## Validation Rules

- Parity Output comparisons must be file-content based.
- Missing PowerShell on Linux must trigger install attempt; failure to run parity is a CI failure.
