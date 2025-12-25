# Spec-Kit Prompt Templates for GM-Kit Slash Commands

Purpose: Provide reusable feature prompts for `/speckit.specify` when adding new GM-Kit slash commands. These templates focus on prompt/script/template installation and output artifact behavior (no uv installer work).

Use one of the templates below based on the output pattern:
- Template A: Create new folder/file outputs
- Template B: Append a new section inside an existing notes file

Replace bracketed placeholders before running `/speckit.specify`.

Definitions:
- **Agent folder**: The agent-specific directory where prompt files are installed.

Agent folder mapping (extend over time):
| Agent | Prompt folder |
| --- | --- |
| opencode | `<project folder>/.opencode/command` |
| codex-cli | `<project folder>/.codex/prompts` |
| claude | `<project folder>/.claude/commands` |
| gemini | `<project folder>/.gemini/commands` |
| copilot | `<project folder>/.github/agents` |
| cursor-agent | `<project folder>/.cursor/commands` |
| qwen | `<project folder>/.qwen/commands` |
| windsurf | `<project folder>/.windsurf/workflows` |
| kilocode | `<project folder>/.kilocode/rules` |
| auggie | `<project folder>/.augment/rules` |
| codebuddy | `<project folder>/.codebuddy/commands` |
| roo | `<project folder>/.roo/rules` |
| q/Amazon Q | `<project folder>/.amazonq/prompts` |
| amp | `<project folder>/.agents/commands` |
| shai | `<project folder>/.shai/commands` |

---

## Template A: New Folder/File Output Command

Feature description:
Deliver a new GM-Kit slash command `/gmkit.[command]` that creates a new folder and notes file for [artifact name]. The `gmkit init` command must install the following artifacts:

1) Prompt file:
   - Path: `<project folder>/<agent folder>/prompts/gmkit.[command].md`

2) Script file:
   - Path: `<project folder>/.gmkit/scripts/<bash or ps>/[script_name].sh` (or `.ps1` on Windows)

3) Template file:
   - Path: `<project folder>/.gmkit/templates/[template_name].md`

The command generates output at:
- `<project folder>/[parent folder]/<name>/<notes file>.md`

Behavior:
- The prompt instructs the agent to gather required arguments, then invoke the script with those arguments.
- The script fills the template with arguments and writes the output file.
- Output folders are created as needed.

Success looks like:
- `gmkit init` installs the prompt/script/template files in the correct locations.
- Running `/gmkit.[command]` produces `<project folder>/[parent folder]/<name>/<notes file>.md` with the provided inputs.
- Re-running the command with the same name does not destroy existing data (idempotent behavior is explicit in the spec).

Example (campaign):
- Command: `/gmkit.campaign`
- Prompt: `<project folder>/<agent folder>/prompts/gmkit.campaign.md`
- Script: `<project folder>/.gmkit/scripts/<bash or ps>/create_campaign.sh`
- Template: `<project folder>/.gmkit/templates/campaign-template.md`
- Output: `<project folder>/campaigns/<campaign_name>/campaign_notes.md`

---

## Template B: Append Section in Existing Notes File

Feature description:
Deliver a new GM-Kit slash command `/gmkit.[command]` that appends a new section to an existing notes file. The `gmkit init` command must install the following artifacts:

1) Prompt file:
   - Path: `<project folder>/<agent folder>/prompts/gmkit.[command].md`

2) Script file:
   - Path: `<project folder>/.gmkit/scripts/<bash or ps>/[script_name].sh` (or `.ps1` on Windows)

3) Template file:
   - Path: `<project folder>/.gmkit/templates/[template_name].md`

The command targets an existing notes file:
- `<project folder>/campaigns/<campaign_name>/scenarios/<scenario_name>/scenario_notes.md`

Behavior:
- The prompt instructs the agent to gather required arguments, then invoke the script with those arguments.
- The script fills the template and appends a new section to the target notes file.
- The section includes a clear heading and is appended without overwriting other content.

Success looks like:
- `gmkit init` installs the prompt/script/template files in the correct locations.
- Running `/gmkit.[command]` appends a new section to the target notes file.
- Re-running the command appends a new section without overwriting existing sections.

Example (NPC section):
- Command: `/gmkit.npc`
- Prompt: `<project folder>/<agent folder>/prompts/gmkit.npc.md`
- Script: `<project folder>/.gmkit/scripts/<bash or ps>/create_npc.sh`
- Template: `<project folder>/.gmkit/templates/npc-template.md`
- Target: `<project folder>/campaigns/<campaign_name>/scenarios/<scenario_name>/scenario_notes.md`
