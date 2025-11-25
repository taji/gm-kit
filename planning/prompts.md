# GM-Kit Feature Prompts (Arcane Library Edition)

Use these `/speckit.specify` prompts to translate the active epics in `planning/project-overview.md` into executable specs. Prompts are grouped and ordered by those epics so the workflow remains: prompts → specs → plans → tasks → implementation. Replace references to legacy combat/social/exploration artifacts; Arcane Library schemas are the new source of truth.

---

## ✅ Epic 1 — Repository Setup & Governance (completed)

### ✅ 1) Repo Bootstrap (README + .gitignore + Structure Audit)
Feature description:
Scaffold a minimal README describing GM-Kit’s Arcane Library mission, add a `.gitignore` that excludes `temp-resources/` and `spec-kit/`, and then audit the folder structure and included files to verify the project is ready to push to gihtub. Include instructions for keeping the README synced with planning docs.

Success looks like: a repo that is ready for PRs, ignores transient analysis folders and is ready for python development.

### ✅ 2) Development Lifecycle Documentation
Feature description:
Add contributor documentation that explains the enforced workflow: todos (as epics) → prompts → specs → /plan → tasks → implementation → validation. Highlight how prompts are stored, how specs reference planning artifacts, and where status lives. Include guidance for capturing decisions in Obsidian and syncing back.

Success looks like: anyone can trace a shipped change back to the originating todo epic.

### ⚠️ 3) Testing Strategy (deferred)
Feature description:
Define how to unit or integration test the MCP. Cover minimal walking tests (CLI dry runs, mock agents) and outline where automated scripts live. Specify pass/fail gates that block shipping (e.g., failing CLI smoke test).

Success looks like: a practical testing rubric the team can run locally before each PR.

## Epic 2 — Development Environment & Walking Skeleton

### 6) Knowledge-Graph MCP Experiment (Optional)
Feature description:
Spec an experiment that wires a knowledge-graph MCP into the workflow to compare against vendor-provided session distillers. Outline evaluation metrics and fallback plans if the integration adds friction.

Success looks like: documented learnings on whether the knowledge graph improves Arcane Library outputs.

NOTE: The developer will install the mcp and configure it. Use the context at this link in both codex and opencode to ensure it's working correctly: https://github.com/modelcontextprotocol/servers/tree/main/src/memory (See SYSTEM PROMPT section in the readme, note we are using Cheezy's recommended knowledge graph mcp rather than the Memory mcp)

### 7) Walking Skeleton MCP + Tests
Feature description:
Build a “hello world” MCP command that exercises the CLI stack end-to-end, includes a minimal test harness, and proves that code/test/watch loops work. This skeleton becomes the template for later commands.

Success looks like: a passing test plus documentation on how to extend the skeleton for new features.

### 8) Multi-Agent Installation Flow
Feature description:
Document and/or script the installation experience for Codex and OpenCode agents (and note what changes for others). Highlight how the init process handles agent folders safely and how updates are applied.

Success looks like: new contributors can onboard to both agents without guesswork.

### 9) PDF→Markdown Feature (First Post-Init Command)
Feature description:
Plan the very first feature after init: the PDF-to-Markdown converter. Capture dependencies, CLI surface, early acceptance tests, and how it will integrate with later Arcane Library formatting work.

Success looks like: a locked-in scope for the converter so subsequent tasks can hang off it.

---

## Epic 3 — Spec-Kit Architecture Analysis

### 10) Spec-Kit Repo Deep Dive
Feature description:
Download the upstream spec-kit repo and catalogue how commands, templates, and scripts are organized. Include notes on versioning, template prefixes, and how prompts feed specs.

Success looks like: a concise reference document stored in `planning/` that captures the structural learnings.

### 11) Constitution → Gate Mapping
Feature description:
Trace how Spec-Kit’s constitution articles produce gates like the “Simplicity Gate” and “Anti-Abstraction Gate.” Clarify what “No future-proofing” truly enforces and how those checks can be adapted for GM-Kit.

Success looks like: actionable guidance for crafting GM-Kit checklists based on upstream doctrine.

### 12) MCP Flow Walkthrough (Specify → Clarify → Plan → Execute)
Feature description:
Describe, with screenshots or transcripts, how each Spec-Kit phase behaves today when building a feature. Focus on checklists, clarifying questions, and artifact outputs so we can mirror or adapt them.

Success looks like: the team can answer “why does Spec-Kit ask for this gate?” with evidence.

### 13) Guardrails & Cross-Platform Considerations
Feature description:
Identify what guardrails are necessary when GM-Kit becomes its own MCP: how to ensure cross-platform CLI compatibility, how to warn about licensed content, and how to steer AI agents away from unsafe behaviors.

Success looks like: a list of guardrails ready to be codified into specs and templates.

---

## Epic 4 — PDF → Markdown Research & Pipelines

### 14) Research Plan Across Three Module Formats
Feature description:
Define the research matrix: DMsGuild two-column, Call of Cthulhu, and Werewolf 5E samples. Outline success criteria, manual review steps, and how findings will be recorded.

Success looks like: a reproducible study plan for evaluating conversion quality across systems.

### 15) AI-Only Conversion Approach
Feature description:
Prompt AI to perform direct conversion of PDFs into Markdown, describing how to manage context limits, heading detection, call-out handling (`>` for box text), and verification loops with the user.

Success looks like: documented steps for when AI alone is sufficient and how to check results.

### 16) CLI/Python Conversion Pipeline
Feature description:
Design the hybrid workflow: CLI utilities (`pdfinfo`, `qpdf`, `pdftohtml`, `pandoc`, `pdfimages`, `ocrmypdf`) vs pure-Python alternatives. Include install guidance for Windows/macOS/Linux and show where AI should clean up the Markdown output.

Success looks like: a spec-ready blueprint for automating conversions portably.

### 17) Heading & Hierarchy Verification Tooling
Feature description:
Create a command that surfaces title snippets from the PDF, allows the AI/user to assign heading levels, and validates whether the Markdown mirrors the PDF’s hierarchy.

Success looks like: fewer mis-leveled headers and a repeatable QA checklist.

### 18) Box Text & Callout Handling
Feature description:
Define how boxed text should appear in Markdown (`>`), how to tag read-aloud vs GM-only notes, and how to preserve their placement relative to body copy.

Success looks like: readable Markdown that keeps the intent of boxed callouts intact.

### 19) Version 2 Image Extraction
Feature description:
Plan the follow-up feature that extracts images, saves them to `images/`, and injects relative links into the Markdown at the correct positions. Include licensing cautions.

Success looks like: a scoped V2 plan that can follow the initial converter work.

---

## Epic 5 — Prompt & Schema Overhaul (Arcane Library)

### 20) Arcane Library Schema Definition
Feature description:
Spec the authoritative schema for Synopsis, Background, Word to the GM, Pacing/Transitions, Intro Page (title, hooks, character cards, transition), and the one-page encounter layout (Approach, Developments, Dramatic Question, Challenge/Social, Character Card links, GM Guidance, Transition). Include guidance for Character Cards themselves.

Success looks like: templates every command will target going forward.

### 21) Prompt Refresh for Spec-Kit
Feature description:
Replace the legacy combat/social/exploration/challenge prompts with new prompts that create Arcane Library-friendly specs. Ensure each prompt ties back to the schema definition.

Success looks like: `/speckit.specify` now seeds Arcane Library work instead of pillar encounters.

### 22) PDF→Markdown Prompt Revisions
Feature description:
Revise the conversion prompts using findings from Epic 4 so they ask better research questions, cite the two approaches, and capture acceptance criteria for each module type.

Success looks like: future specs bake in the lessons learned from the research phase.

### 23) MVP Specification Sweep
Feature description:
Drive a spec that narrows the MVP scope (init scripts + PDF converter + Arcane Library template generation) and sequences work accordingly.

Success looks like: a consensus MVP backlog ready for implementation.

### 24) Scenario Conversion Targets
Feature description:
Plan how to convert both Skyhorn Lighthouse scenarios and Temple of the Basilisk Cult to Markdown, including verification steps, schema mapping, and storage locations.

Success looks like: a checklist the team can run for each conversion candidate.

### 25) Schema Analysis & Refinement
Feature description:
Create a process where AI analyzes converted scenarios, highlights schema gaps, and proposes revisions to the Arcane Library templates. Include a feedback loop for the GM to accept or adjust.

Success looks like: evolving schemas grounded in real module conversions.

### 26) MVP Beta Readiness & CI/CD
Feature description:
Prepare GM-Kit for the first MVP beta release. Stand up a CI/CD pipeline that runs lint/format/type-check (or equivalent quality gates), a minimal smoke conversion (sample PDF → Markdown → Arcane Library outline), and packaging/uv build. Define release/versioning, tagging, and changelog steps; lock prompts/templates used by `/speckit.*`; refresh README to reflect the beta state (what works, known gaps, supported agents, quickstart). Include a release checklist (artifacts, docs, sample outputs, manual QA) and how beta feedback is collected.

Success looks like: a passing pipeline, a repeatable beta release recipe (tag + artifacts + docs), and updated README/prompts ready for beta testers.

---

## Epic 6 — Version 2 Dungeon & Flow Extensions

### 27) V2 Dungeon Room Workflow
Feature description:
Extend the schema to treat each dungeon room as its own encounter page, link map pins to room files, and prompt AI to suggest transitions and clue-routing adjustments. Mention potential Obsidian plugins if relevant.

Success looks like: a ready-to-spec plan for dungeon-heavy adventures once v1 ships.

### 28) Clue-Route Diagram Enhancements
Feature description:
Develop a prompt that guides AI through analyzing the clue-route diagram, recommending revisions, and updating the distilled document to reflect those changes using the Arcane Library schema.

Success looks like: consistent transitions and dramatic questions across the entire adventure.

---

These prompts keep planning, specs, and implementation aligned with the Arcane Library direction and the prioritized todo list. Copy the relevant prompt into `/speckit.specify`, attach `planning/project-overview.md`, and iterate through /clarify → /plan → /implement per Spec-Kit conventions.
