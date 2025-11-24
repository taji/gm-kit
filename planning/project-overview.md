# GM-Kit: Arcane Library Prep Toolkit

GM-Kit is a spec-driven toolkit built with Spec-Kit's MCP workflow that helps Game Masters restructure adventures into Kelsey Dionne's Arcane Library format. The project now centers on producing concise, Obsidian-friendly Markdown packets that follow Arcane Library schemas rather than bespoke combat/social/exploration templates.

## Vision
- Convert any scenario (PDFs, prior notes, or scratch ideas) into Arcane Library style prep the GM can trust at the table.
- Keep prep lightweight: todos → prompts → specs → plans → tasks → implementation is the required workflow across every improvement.
- Stay system-agnostic: reference Stat Sources or provenance instead of embedding mechanics.
- Ensure everything round-trips through Obsidian with predictable names, YAML frontmatter, and relative links.
- Produce tooling that works across Codex/OpenCode/Gemini/etc. via symlink-friendly layouts and MCP-first commands.

## Arcane Library Standard
Arcane Library one-page beats are the canonical schema:
- **Frontmatter packet**: Synopsis, Background, Word to the GM (boilerplate), and Pacing/Transitions guidance.
- **Intro Page**: Title, plot hooks, linked Character Cards for hooks, and transitions.
- **Encounters (per page)**: Title, Approaching the location, Developments (problems/twists), Dramatic Question, Challenge/Social resolution (combat or skill challenge framing), Character Cards (links), GM Guidance (links or errata), Transition pointers.
- **Character Cards**: condensed NPC briefs that fuse goals, leverage, appearance, and secrets.
- **Optional V2**: dungeon maps treated as linked room pages, with each room adopting the encounter schema and hyperlinks back to map pins.

All new tooling, prompts, and scripts must target these artifacts so the GM never has to juggle incompatible schemas.

## Current Epics (from `planning/TODOS.md`)
1. **Repository Setup**: initialize README/.gitignore (ignore `temp-resources/` and `spec-kit/`), document the lifecycle (todos → prompts → specs → plans → tasks → implement), validate repo layout with AI, design MCP unit/integration test strategy, and figure out symlink strategy so multiple AI agents can share the repo.
2. **Development Environment & Walking Skeleton**: author startup scripts (`uv run/test` helpers), optionally integrate the knowledge-graph MCP for comparison, build a walking-skeleton MCP with tests, wire fast update loops with the Obsidian vault, and ship installation flows for Codex and OpenCode. The first post-init feature must be the PDF-to-Markdown converter.
3. **Spec-Kit Architecture Analysis**: study the upstream repo in detail (constitution → gates/checklists → command phases), answer open questions about where the gates originate, and produce a knowledge write-up that explains how Spec-Kit’s MCP logic works and what guardrails GM-Kit inherits.
4. **PDF → Markdown Research & Implementation**: evaluate both AI-direct and CLI-driven conversion approaches across DMsGuild, Call of Cthulhu, and Werewolf 5E layouts; determine required command-line tools vs Python libs; solve heading detection, box text treatment (`>`), and verification flows; aim for markdown that mirrors the hierarchy with images added in v2.
5. **Prompt & Schema Overhaul (Arcane Library)**: replace old pillar prompts, integrate Arcane Library schemas, revise PDF-conversion prompts based on findings, spec the MVP in Spec-Kit, convert Skyhorn Lighthouse (both variants) and Temple of the Basilisk Cult, and analyze schema coverage so the Arcane Library templates stay grounded in real data.
6. **Version 2 Dungeon & Flow Extensions**: expand the schema so every dungeon room can become a one-page encounter, wire maps to linked Markdown, investigate Obsidian plugin support, and craft AI prompts that revise distilled docs and clue-route diagrams using the enhanced schema.

These epics feed directly into prompt ordering, spec drafting, and execution.

## Operating Principles
- Always document provenance/licensing before ingesting third-party content; default outputs to private use.
- Prefer lightweight checklist “unit tests for English” at each stage; use Spec-Kit clarify/analyze/checklist loops to keep artifacts honest.
- Target portable tooling: when CLI dependencies are unavoidable, provide Windows-friendly steps or fall back to Python packages.
- Testing is mandatory: define either MCP unit hooks or integration smoke tests for each feature before shipping.
- Keep guardrails explicit (session-only prep, no rules text, safe handling of AI credentials in agent folders).

GM-Kit’s success is measured by how quickly a GM can pick any scenario, ingest it, and receive Arcane Library formatted prep with confidence across multiple AI agents and platforms.
