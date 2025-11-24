# Contract: Manual Structure Audit

1. **Snapshot Command**
   - Run `ls -a` (or `tree -L 1` when available) at repo root.
   - Paste the raw output into the PR description or planning note.

2. **Checklist Items**
   - `[ ] planning/`
   - `[ ] specs/`
   - `[ ] src/`
   - `[ ] README.md`
   - `[ ] .gitignore`
   - `[ ] pyproject.toml`
   - `[ ] uv.lock`
   - `[ ] .python-version`
   - `[ ] temp-resources/ (ignored)`
   - `[ ] spec-kit/ (ignored)`

3. **Verification Rules**
   - Each checklist item must indicate **present/missing** and note remediation steps if missing.
   - Audit must be re-run after modifying README or `.gitignore`.
   - Results must be included in every PR touching docs/structure.
