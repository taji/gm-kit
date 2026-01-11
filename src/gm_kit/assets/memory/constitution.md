# GM-Kit Constitution (Summary)

Placeholder: this will be replaced with the default GM-Kit constitution wording
(schema validation, artifact formats, campaign tone, etc.).

- Use Spec-Kit prompts and local templates to generate repeatable GM artifacts.
- Prefer deterministic, idempotent commands; no network access after install.
- Validate inputs and provide clear, actionable errors.
- Support prioritized agents (claude, codex-cli, gemini, qwen) with correct paths and formats.
- Keep outputs portable (Markdown/TOML), cross-platform scripts (bash + PowerShell).
- Favor test-first development with pytest + pexpect; validate CLI contracts and integration flows.
