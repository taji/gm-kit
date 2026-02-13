# AGENTS.md (Context file for AI Agents)

This file defines the standards, conventions, and expectations for AI-assisted development on this project.

## Git Hygiene

- When renaming or moving tracked files, use `git mv` so history and rename detection stay intact.

<!-- GENERATED:MEMORY_GUIDELINES_START -->

Follow these steps for each interaction:

1. User Identification:
   - You should assume that you are interacting with default_user
   - If you have not identified default_user, proactively try to do so.

2. Memory Retrieval:
   - Always begin your chat by saying only "Remembering..." and immediately call a memory read (e.g., `aim_read_graph`) to load all relevant information from your knowledge graph before writing anything else.
   - Always refer to your knowledge graph as your "memory".
   - If the memory read was not executed, state that explicitly and retry the read before answering.

3. Memory
   - While conversing with the user, be attentive to any new information that falls into these categories:
     a) Basic Identity (age, gender, location, job title, education level, etc.)
     b) Behaviors (interests, habits, etc.)
     c) Preferences (communication style, preferred language, etc.)
     d) Goals (goals, targets, aspirations, etc.)
     e) Relationships (personal and professional relationships up to 3 degrees of separation)

5. Progress tracking (Backlog → memory)
   - When reading or updating BACKLOG.md, create or refresh memory entities for each epic/feature with status (COMPLETED/DRAFT/PARTIAL/NOT SPECCED), key blockers, and next steps (e.g., E1-03 CLI surface mismatch + missing dry-run/logging tests; E1-04 Cardinal palette gap; E1-05 Xvfb/Zenity modal blocks test enablement; E1-09 pending CLI rename). Keep this detail out of the BACKLOG title; record it as lines under the feature.
   - Record spec folder links and doc-sync state per epic (quickstart synced to docs/user/user-guide.md, plan/research/data-model synced to ARCHITECTURE.md). Note pending sync actions and the file that must be updated/marked **SYNCED** in BACKLOG.md. When a feature has a spec folder, include it directly in the BACKLOG feature title, using the format shown in E2-02 (e.g., `### E2-02. Installation and Walking Skeleton **[FEATURE, COMPLETED as specs/002-installer-skeleton/spec.md]**`), and put doc-sync state on its own line under the feature.
   - On any status change or newly discovered blocker, immediately update memory with observations and relations to the epic entity (e.g., `E1-03` relates to `specs/001-cli-fxp-conversion`, `docs/user/user-guide.md`).
   - If `docs/user/user-guide.md` or `ARCHITECTURE.md` conflicts with a spec, add a "needs clarification" note in the spec file and capture that unresolved item in memory until resolved.

4. Memory Update:
   - If any new information was gathered during the interaction, update your memory as follows:
     a) Create entities for recurring organizations, people, and significant events
     b) Connect them to the current entities using relations
     c) Store facts about them as observations

<!-- GENERATED:MEMORY_GUIDELINES_END -->

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
