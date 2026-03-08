# AGENTS.md (Context file for AI Agents)

This file defines the standards, conventions, and expectations for AI-assisted development on this project.

## Git Hygiene

- When renaming or moving tracked files, use `git mv` so history and rename detection stay intact.

## Feature Journal

Each feature — whether formally specced in spec-kit or informally described — has a `feature_journal.md` in its spec folder. The journal is the canonical, agent-agnostic record of progress for that feature.

### When to create one

Create `specs/<feature-name>/feature_journal.md` at the very start of any feature work, before writing any code or spec content. If the `specs/<feature-name>/` directory does not exist yet, create it.

### Entry format

Each session appends a new entry to the bottom of the file. Use this structure:

```
Session: <YYYY-MM-DD> - <Short descriptive title>
--------------------------------------------------------
Branch: <branch-name>
Date: <YYYY-MM-DD>

Work Completed:
1. <What was actually done this session>
2. ...

Key Decisions:
- <Architectural or design choices made, with rationale>

Current State:
- <Point-in-time snapshot of where things stand right now>

Next Steps:
1. <What a new agent should do first>
2. ...

Recorded by: <agent-name>
```

Keep entries factual and brief. **Next Steps** is the most important field for handoffs — it should be specific enough that a new agent can start immediately without re-reading the whole journal.

### Agent handoff

When starting a session on an in-progress feature, read the feature's `feature_journal.md` before doing anything else — specifically the most recent entry's **Current State** and **Next Steps**. It is the fastest way to restore context across agent switches, compacted context windows, or resumed sessions.

At the end of every session, append a new entry recording what you did, any decisions made, the current state, and what comes next. Include your agent name in `Recorded by`.

### Lifecycle

The journal is a living document during feature development. Once the feature is complete and merged, leave it in place as a historical record. It does not need to be pruned, compacted, or loaded in future sessions — it is self-contained to the feature.

<!-- GENERATED:SPEC_KIT_GUIDELINES_START -->

- Merge each feature's `spec/<feature>/quickstart.md` into `docs/user/user-guide.md`; keep `user-guide.md` canonical. Reconcile overlaps and ensure new flows do not duplicate or conflict with existing behavior. Mark the feature's quickstart items as **SYNCED** in `BACKLOG.md` once merged.
- Validate new feature behavior against `user-guide.md`. If you find conflicts or missing guidance, record the issues in the feature's `spec.md` as "needs clarification" and pause until resolved.
- Propagate design changes from `spec/<feature>/plan.md`, `spec/<feature>/research.md`, and `spec/<feature>/data-model.md` into `ARCHITECTURE.md`. Keep `ARCHITECTURE.md` canonical.
- After syncing, mark the relevant `plan.md`, `research.md`, and `data-model.md` sections as "synced to ARCHITECTURE.md" and leave the files intact.
- After each merge, prompt the user to review older specs against `docs/user/user-guide.md` and older design docs against `ARCHITECTURE.md`; report any discrepancies so the user can guide revisions.

<!-- GENERATED:SPEC_KIT_GUIDELINES_END -->

<!-- GENERATED:AGENT_CONTEXT_PYTHON_START -->

## Python CLI conventions

The project is a **Python command-line utility**, not a web service, so the guidelines below focus on CLI-appropriate quality, security, and maintainability.

---

## 📦 Project Overview for Agents

This repository contains a Python CLI tool managed with:

- **uv** for dependency management, environment resolution, and execution
- **just** for task orchestration (until uv's task runner stabilizes)
- **pytest** for testing
- **ruff**, **black**, **isort** for linting and formatting
- **mypy** for static typing
- **bandit** and **uv audit** for security scanning

Agents must follow the procedures below when implementing or modifying code.

---

# ✅ Quality Guidelines

## 1. Unit Tests Required for All New Code
- When you implement a new function, class, or feature, you **must add unit tests**.
- Place tests in the `tests/` directory, using pytest conventions.
 - Regression-test harness guidance lives in `tests/README.md` (add a unit test whenever an integration anomaly requires a code change).

## 2. Maintain and Expand Existing Tests
- When modifying existing code, update any affected tests.
- Before completing a task, ensure all tests pass:

```bash
just test
```

## 3. Code Coverage
Run coverage after completing any task:

```bash
pytest --cov=src
```

Maintain or improve project coverage. If coverage drops, add tests.

## 4. Linting and Style Consistency
Linting & formatting are enforced with:

- **ruff** (linting)
- **black** (formatting)
- **isort** (import ordering)

Run these before concluding work:

```bash
just lint
just format
just format-imports
```

Fix all issues automatically where possible.

## 4.5 Test Naming Convention
- Name pytest functions with the pattern `test_<Subject>__should_<ExpectedOutcome>__when_<Condition>`.
- Keep the subject descriptive (e.g., `surgebench_cli`), the expected outcome explicit (e.g., `should_emit_error_modal`), and the condition clear (e.g., `when_invalid_vcv_file`).
- Apply consistently across unit and integration tests so logs clearly show intent when tests pass/fail.

## 4.6 Test Boundary Rules
- **Unit tests** (`tests/unit/`) must not spawn subprocesses, use network calls, or depend on real fixture assets beyond `tmp_path`; mock/stub external libraries and I/O.
- **Integration tests** (`tests/integration/`) may use subprocesses, real fixture files, and cross-module workflows.
- Unit tests for CLI parsing should use `typer.testing.CliRunner` and mock orchestration/service layers.
- Assertions must be unconditional (`assert`, no `if` guards around expected artifacts/results).
- Error-path tests should assert exact error text and exact exit behavior.

## 5. Type Checking
Use MyPy to enforce typing standards:

```bash
just typecheck
```

All modified or added code must pass MyPy.

## 6. Cyclomatic Complexity Guidelines
Complexity is tracked using **Ruff's mccabe plugin** to maintain code readability for both humans and AI agents.

### Complexity Thresholds
- **A (1-5)**: Simple - acceptable
- **B (6-10)**: Acceptable - no action needed
- **C (11-15)**: Warning - consider refactoring if function grows
- **D (16-20)**: High - should be refactored when convenient
- **E (21-35)**: Very High - must be refactored (see exceptions below)
- **F (35+)**: Extreme - must be refactored immediately

### Check Complexity
Complexity is automatically checked during `just lint` via Ruff's C90 (mccabe) rule. The current threshold is **max-complexity = 20** (E-grade threshold).

```bash
# Run linting (includes complexity check via Ruff)
just lint

# To suppress complexity warnings for a specific function
def my_function():  # noqa: C901
    """This function has high complexity but is acceptable."""
    pass
```

### When to Allow High Complexity
Complexity violations are acceptable in these cases:
- **Purely sequential steps** with no branching (just long procedural code)
- **Single large `execute()` methods** that orchestrate multiple steps (when extracted to step methods)
- **External library wrappers** that must match library interfaces
- **Agent steps** (10.2, 10.3, etc.) that are intentionally stubbed

### When to Refactor
Require refactoring when:
- Deep nesting (>3 levels of conditionals/loops)
- Multiple responsibilities in one function (violates SRP)
- High branch count with interdependent conditions
- Poor testability due to complexity
- Functions exceed 100 lines (secondary indicator)

### Current High Complexity (For Reference)
These functions currently have E-grade complexity and should be refactored in future:
- `phase3.py:execute()` - 31 complexity (extract step methods)
- `phase3.py:_analyze_footer_watermarks()` - 33 complexity
- `phase3.py:_analyze_icon_fonts()` - 29 complexity
- `phase4.py:execute()` - 38 complexity (extract text extraction loop)
- `phase5.py:execute()` - 65 complexity (extract step methods)
- `phase7.py:execute()` - 82 complexity (extract detection methods)
- `orchestrator.py` - various methods need extraction

**Note**: Complexity violations will fail the build during `just lint`. Use `# noqa: C901` comments sparingly for functions that legitimately need high complexity.

---

# 🔐 Security Guidelines

Even though this is a CLI tool (not a web service), security remains important.

## 1. Dependency Vulnerability Audit
After adding or updating dependencies, run:

```bash
uv audit
```

Resolve or document any reported vulnerabilities.

## 2. Static Code Security Scan
Use Bandit to detect unsafe coding patterns:

```bash
bandit -r src
```

Fix or justify all Bandit warnings.

## 3. Avoid Unsafe Python Features
Agents must not introduce:

- `eval()` or `exec()`
- `pickle` (use JSON, msgpack, or `yaml.safe_load`)
- `yaml.load` (must use `yaml.safe_load`)
- `subprocess` with `shell=True` unless absolutely required and documented
- unsafe temp file handling

## 4. Input-Handling Safety
Even CLI arguments may be untrusted.

For any feature handling user paths or file content:

- validate paths
- avoid path traversal (`../`) issues
- sanitize data passed to subprocesses

---

# 📁 Project Workflow for Agents

## Always use uv for execution:
```bash
uv run --python "$(cat .python-version)" --extra dev --editable -- <command>
```

## Always use Just for task orchestration:
```bash
just <task>
```

## Recommended AI workflow:
1. Implement code
2. Write/update tests
3. Run the full quality pipeline:

```bash
just format
just format-imports
just lint
just typecheck
just test
uv audit
bandit -r src
```

4. Confirm all checks pass
5. Submit changes

---

# 📝 Documentation Guidelines

- Update `README.md` or docstrings for new features.
- Add examples for new CLI commands or flags.
- Keep inline comments minimal but clear.

---

# 🤖 Commit Guidelines for AI Assistants

All commits must be:

- Atomic
- Well-described
- Paired with tests
- Passing all quality & security checks

Example commit message:

```
Add feature X to module Y, including tests and updated CLI handler
```

---

# 🏁 Completion Requirements for All AI Tasks

A task is “complete” only when:

- All tests pass
- Code coverage meets or exceeds requirements
- Linting and formatting pass
- Type checking passes
- Security scans show no unresolved issues
- Documentation reflects new changes
- The implementation adheres to project architecture and style guidelines

<!-- GENERATED:AGENT_CONTEXT_PYTHON_END -->

## Active Technologies
- Python 3.13.7 + typer, rich, uv, pytest, ruff, black, isort, mypy, bandit (001-ci-walking-skeleton)
- N/A (CI configuration only) (001-ci-walking-skeleton)
- Python 3.13.7 + typer, rich, PyMuPDF (fitz), pymarkdownlnt (006-code-pdf-pipeline)
- Files on local workspace (.state.json, per-phase artifacts, manifests) (006-code-pdf-pipeline)
- Local files in conversion workspace (JSON, markdown, prompt artifacts) (007-agent-pipeline)
- Python 3.8+ (constitution mandate), running on 3.13.7 + typer, rich, PyMuPDF/fitz, jsonschema (contract validation) (007-agent-pipeline)
- Local files in conversion workspace (JSON contracts, markdown artifacts, prompt templates as Python modules) (007-agent-pipeline)

## Recent Changes
- 001-ci-walking-skeleton: Added Python 3.13.7 + typer, rich, uv, pytest, ruff, black, isort, mypy, bandit
