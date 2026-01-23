---
description: Create or update the feature specification from a natural language feature description.
handoffs: 
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify specification requirements
    send: true
---
<!-- 
JTG ANALYSIS: ABOVE: Front-matter metadata for the agent runtime (not user-facing). It labels the command and declares handoffs to plan/clarify; `send: true` can **trigger an automatic next-step invocation** in some runtimes.  (So it can provide context but also it can automate the next step in the speckit-process).
-->

<!-- JTG ANALYSIS How does the $ARGUMENTS variable get processed?  This isn't a script, so how does it work? -->

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/speckit.specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `$ARGUMENTS` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, do this:

<!-- JTG ANALYSIS: Steps 1 and 2 determine the setup variables needed to complete the remaining steps (so generate a short feature name, a branch name and a folder name, so that the agent can call the script below (step 2.d) to create the folder artifacts (so the git branch, the folders, subfolders and files). 
-->

1. **Generate a concise short name** (2-4 words) for the branch:
   - Analyze the feature description and extract the most meaningful keywords
   - Create a 2-4 word short name that captures the essence of the feature
   - Use action-noun format when possible (e.g., "add-user-auth", "fix-payment-bug")
   - Preserve technical terms and acronyms (OAuth2, API, JWT, etc.)
   - Keep it concise but descriptive enough to understand the feature at a glance
   - Examples: <!-- JTG: Examples are the E in SCOPE -->
     - "I want to add user authentication" → "user-auth"
     - "Implement OAuth2 integration for the API" → "oauth2-api-integration"
     - "Create a dashboard for analytics" → "analytics-dashboard"
     - "Fix payment processing timeout bug" → "fix-payment-timeout"

2. **Check for existing branches before creating new one**:

   a. First, fetch all remote branches to ensure we have the latest information:

      ```bash
      git fetch --all --prune
      ```

   b. Find the highest feature number across all sources for the short-name:
      - Remote branches: `git ls-remote --heads origin | grep -E 'refs/heads/[0-9]+-<short-name>$'`
      - Local branches: `git branch | grep -E '^[* ]*[0-9]+-<short-name>$'`
      - Specs directories: Check for directories matching `specs/[0-9]+-<short-name>`

   c. Determine the next available number:
      - Extract all numbers from all three sources
      - Find the highest number N
      - Use N+1 for the new branch number

   <!-- 
   JTG ANALYSIS: This is the first step that actually generates an artifact (branches, files, folders, etc).
   -->
   d. Run the script `.specify/scripts/bash/create-new-feature.sh --json "$ARGUMENTS"` with the calculated number and short-name:
      - Pass `--number N+1` and `--short-name "your-short-name"` along with the feature description
      - Bash example: `.specify/scripts/bash/create-new-feature.sh --json "$ARGUMENTS" --json --number 5 --short-name "user-auth" "Add user authentication"`
      - PowerShell example: `.specify/scripts/bash/create-new-feature.sh --json "$ARGUMENTS" -Json -Number 5 -ShortName "user-auth" "Add user authentication"`

   <!-- 
   JTG ANALYSIS: Note that for multiple complex steps, the steps are listed and then **IMPORTANT** clarifying instructions are addded to ensure precision for ALL of the steps. I'm wondering if this "multiple-steps-and-then-clarifying-statements"  approach is used later as well. 
   -->

   **IMPORTANT**:
   - Check all three sources (remote branches, local branches, specs directories) to find the highest number
   - Only match branches/directories with the exact short-name pattern
   - If no existing branches/directories found with this short-name, start with number 1
   - You must only ever run this script once per feature
   - The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for
   - The JSON output will contain BRANCH_NAME and SPEC_FILE paths
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot")

<!-- 
JTG ANALYSIS: This next step 3 primes the agent to know how to render the template later.  I imagine this will be essential when generating campaign artifacts from prompts.
-->

3. Load `.specify/templates/spec-template.md` to understand required sections.

4. Follow this execution flow:

    1. Parse user description from Input
       If empty: ERROR "No feature description provided"
    2. Extract key concepts from description
       Identify: actors, actions, data, constraints
       <!-- 
         JTG ANALYSIS: How does this short "Identify" command establish such complexity? ANSWER: See this next item (3), it's similar to the **IMPORTANT** block above. It clarifies to the agent how to provide the complex and nuanced detail required for the later steps.
         Codex note: This is the "intent + guardrails" pattern — step 2 states the intent (identify actors/actions/data/constraints), while step 3 supplies guardrails for ambiguity (defaults, clarification thresholds, and limits) so the model can execute the intent without over-asking or over-guessing.

         Short answer: there isn’t a magic tool that “writes the perfect prompt,” but the best
         teams use a small set of practices and lightweight scaffolds that behave like a tool.

         Keep instructions short but reliable.
         - Bound ambiguity: The “max 3 clarifications” rule (below) avoids analysis‑paralysis and forces
            defaults. That’s the key to keeping prompt length from exploding.
         - Priority heuristics: The ordering (scope > security > UX > technical) lets the model
            resolve conflicts without extra user input.

         Practical “tooling” people use:

         - Prompt lint checklists (manual): verify each step has a success condition, a failure
            condition, and an ambiguity rule.
         - Template‑first drafting: start with a minimal outline, then add constraints only
            where real failures appear.
         - Iterative tuning with examples: run 5–10 real prompts, track where the model
            deviates, and add only the constraints that fix those failure modes.
      -->
    3. For unclear aspects:
       - Make informed guesses based on context and industry standards
       - Only mark with [NEEDS CLARIFICATION: specific question] if:
         - The choice significantly impacts feature scope or user experience
         - Multiple reasonable interpretations exist with different implications
         - No reasonable default exists
       - **LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**
       - Prioritize clarifications by impact: scope > security/privacy > user experience > technical details
         <!-- 
         JTG ANALYSIS: It's crazy that the agent is instructed to  limit needed clarifications to only 3, especially when you look at the priortization. All of these concerns are important, but you are only going to get 3 out of 4? How does this even work?  
         -->
    4. Fill User Scenarios & Testing section
       If no clear user flow: ERROR "Cannot determine user scenarios"
       <!--
         JTG ANALYSIS: 
          
         CRITICAL POINT: Note that the "if" statement above is the "exit on error" path that fails to completely create the spec.  By this step, key concepts, actors, actions, data and constraints should be established, all uncertainties identified, if it can't create a user story, it fails out.
         
         Additionally, here is an example output from this step:

         ---          
         
         ## User Scenarios & Testing *(mandatory)*

         ### User Story 1 - Install GM-Kit and Initialize Project (Priority: P1)

         Contributors install GM-Kit using uv and run "gmkit init" to set up scripts and prompts for the walking skeleton, enabling basic slash command functionality.

         **Why this priority**: This is the core uv-based install and initializer that provides the foundation for all subsequent GM-Kit usage.

         **Independent Test**: Can be fully tested by installing GM-Kit, running gmkit init, and verifying the correct files are created in the temp workspace.

         **Acceptance Scenarios**:

         1. **Given** uv is installed, **When** contributor runs `uv tool install gmkit-cli`, **Then** GM-Kit is installed with the gmkit command available in PATH and no network dependencies required after installation.
         2. etc.

         ---

         QUESTION: How does it know the format of this section? ANSWER: From the newly copied spec-template.md file from step 3 above.
      -->
    5. Generate Functional Requirements
       Each requirement must be testable
       Use reasonable defaults for unspecified details (document assumptions in Assumptions section)
       <!-- 
         JTG ANALYSIS: Same question for this example functional requirements block:
         
         ---
         ### Functional Requirements

         - **FR-001**: System MUST install GM-Kit CLI tool using uv with cross-platform artifacts (symlinks/shims for PATH access).
         - **FR-002**: System MUST provide gmkit init command that accepts required temp path and optional agent/OS parameters. 
         - etc.
         
         ---

         ANSWER: From the same spec-template.md file 
      -->

    6. Define Success Criteria
       Create measurable, technology-agnostic outcomes
       Include both quantitative metrics (time, performance, volume) and qualitative measures (user satisfaction, task completion)
       Each criterion must be verifiable without implementation details
       <!-- 
         JTG ANALYSIS: Same question for this example Success Criteria block:
         
         ---
         ## Success Criteria *(mandatory)*

         ### Measurable Outcomes

         - **SC-001**: Contributors can install GM-Kit with uv in under 5 minutes and invoke gmkit command from terminal.
         - etc.

         ---

         ANSWER: From the same spec-template.md file.
      -->

    7. Identify Key Entities (if data involved)
    <!-- 
      JTG ANALYSIS: Note Same question for this Key Entities block:
      ### Key Entities *(include if feature involves data)*

      - **Coding Agent**: Type of AI assistant (claude, codex-cli, gemini, qwen) determining prompt location and file format. Agents must be pre-installed and accessible.
      - claude: .claude/commands/ with .md files
      - codex-cli: .codex/prompts/ with .md files  
      - gemini: .gemini/commands/ with .toml files
      - qwen: .qwen/commands/ with .toml files
      - **Operating System**: Target platform (macos/linux, windows) determining script type.
      - **Temp Workspace**: File system location for generated scripts, templates, and memory files.
      - **Script File**: Executable file (bash or PowerShell) that processes slash command arguments.
      - **Prompt File**: Agent-specific instruction file for slash command behavior.
      - **Template File**: Markdown template for generating output files.
      - **Greeting File**: Sequenced markdown file containing processed greetings.
      
      ANSWER:  From the same spec-template.md file.

    -->
    8. Return: SUCCESS (spec ready for planning)


<!-- 
JTG ANALYSIS: This next step is where the template file is replaced with it's rendered self (generated by AI, not a script).
-->

5. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.

6. **Specification Quality Validation**: After writing the initial spec, validate it against quality criteria:

   <!-- 
   JTG ANALYSIS: NOTE how at this point the agent will generate a separate checklist file and that it's distinctly different than the one generated by the speckit.checklist command?  The spec is validated against this checklist by the agent in step b below, and it does the work of checking completed items and raising any incomplete items to the user so that every item can ultimately be checked.  

   The speckit.checklist command does not automatically self validate the gnerated checklist against the spec/plan/task, so it's important that users prompt the agent to  do so after invoking the speckit.checklist command.
   -->
   a. **Create Spec Quality Checklist**: Generate a checklist file at `FEATURE_DIR/checklists/requirements.md` using the checklist template structure with these validation items:

      ```markdown
      # Specification Quality Checklist: [FEATURE NAME]
      
      **Purpose**: Validate specification completeness and quality before proceeding to planning
      **Created**: [DATE]
      **Feature**: [Link to spec.md]
      
      ## Content Quality
      
      - [ ] No implementation details (languages, frameworks, APIs)
      - [ ] Focused on user value and business needs
      - [ ] Written for non-technical stakeholders
      - [ ] All mandatory sections completed
      
      ## Requirement Completeness
      
      - [ ] No [NEEDS CLARIFICATION] markers remain
      - [ ] Requirements are testable and unambiguous
      - [ ] Success criteria are measurable
      - [ ] Success criteria are technology-agnostic (no implementation details)
      - [ ] All acceptance scenarios are defined
      - [ ] Edge cases are identified
      - [ ] Scope is clearly bounded
      - [ ] Dependencies and assumptions identified
      
      ## Feature Readiness
      
      - [ ] All functional requirements have clear acceptance criteria
      - [ ] User scenarios cover primary flows
      - [ ] Feature meets measurable outcomes defined in Success Criteria
      - [ ] No implementation details leak into specification
      
      ## Notes
      
      - Items marked incomplete require spec updates before `/speckit.clarify` or `/speckit.plan`
      ```

   b. **Run Validation Check**: Review the spec against each checklist item:
      - For each item, determine if it passes or fails
      - Document specific issues found (quote relevant spec sections) 
      <!-- JTG ANALYSIS: Q: Where does this get documnnted?  We need to verify this.
           A: The issues are documented in the requirements.md file (which contains the checklist) under the Notes section at the bottom of the requirements.md file and also under any NEEDS CLARIFICATION sections in the spec.md file. Note that as these issues get resolved, the agent will remove these issues from requirements.md and the spec.md files. 
      -->

   c. **Handle Validation Results**:

      - **If all items pass**: Mark checklist complete and proceed to step 6 <!-- JTG ANALYSIS: this is the loop's happy path exit point. But it's a bit confusing.  How do you proceed backwards?  Shouldn't this say "Proceed to Step 7" (rather than 6?).  If six is correct it will go into an infinite loop.  I've posted this as a bug here: https://github.com/github/spec-kit/issues/1509 -->

      - **If items fail (excluding [NEEDS CLARIFICATION])**:
        1. List the failing items and specific issues <!--JTG ANALYSIS:  This listing of failing checklist items means it is presented to the user in the terminal. -->
        2. Update the spec to address each issue
        3. Re-run validation until all items pass (max 3 iterations)
        4. If still failing after 3 iterations, document remaining issues in checklist notes and warn user  <!--JTG:  Note it's a warning and the agent proceeds to the the CLARIFCATION markers -->

      - **If [NEEDS CLARIFICATION] markers remain**:
        1. Extract all [NEEDS CLARIFICATION: ...] markers from the spec
        2. **LIMIT CHECK**: If more than 3 markers exist, keep only the 3 most critical (by scope/security/UX impact) and make informed guesses for the rest
        3. For each clarification needed (max 3), present options to user in this format:

           ```markdown
           ## Question [N]: [Topic]  <!--JTG ANALYSIS: NOTE - N stands for the item number -->
           
           **Context**: [Quote relevant spec section]
           
           **What we need to know**: [Specific question from NEEDS CLARIFICATION marker]
           
           **Suggested Answers**:
           
           | Option | Answer | Implications |
           |--------|--------|--------------|
           | A      | [First suggested answer] | [What this means for the feature] |
           | B      | [Second suggested answer] | [What this means for the feature] |
           | C      | [Third suggested answer] | [What this means for the feature] |
           | Custom | Provide your own answer | [Explain how to provide custom input] |
           
           **Your choice**: _[Wait for user response]_
           ```

        4. **CRITICAL - Table Formatting**: Ensure markdown tables are properly formatted:
           - Use consistent spacing with pipes aligned
           - Each cell should have spaces around content: `| Content |` not `|Content|`
           - Header separator must have at least 3 dashes: `|--------|`
           - Test that the table renders correctly in markdown preview <!-- JTG ANALYSIS: Note that this instruction is poorly worded. There is no testing utility that could verify this.  It's just a best practice instruction that forces the agent to infer an equivalent insight into how to format the table. -->
        5. Number questions sequentially (Q1, Q2, Q3 - max 3 total)
        6. Present all questions together before waiting for responses
        7. Wait for user to respond with their choices for all questions (e.g., "Q1: A, Q2: Custom - [details], Q3: B")
        8. Update the spec by replacing each [NEEDS CLARIFICATION] marker with the user's selected or provided answer
        9. Re-run validation after all clarifications are resolved

   d. **Update Checklist**: After each validation iteration, update the checklist file with current pass/fail status

7. Report completion with branch name, spec file path, checklist results, and readiness for the next phase (`/speckit.clarify` or `/speckit.plan`).

**NOTE:** The script creates and checks out the new branch and initializes the spec file before writing.

## General Guidelines <!-- JTG ANALYSIS: Note that these guidelines cover the entirety of this prompt and in filling out the spec.md template -->

## Quick Guidelines

- Focus on **WHAT** users need and **WHY**.
- Avoid HOW to implement (no tech stack, APIs, code structure).
- Written for business stakeholders, not developers.
- DO NOT create any checklists that are embedded in the spec. That will be a separate command.

### Section Requirements

- **Mandatory sections**: Must be completed for every feature <!-- JTG ANALYSIS: This refers to some sections in the spec.md template that are marked mandatory -->
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation

When creating this spec from a user prompt:

1. **Make informed guesses**: Use context, industry standards, and common patterns to fill gaps
2. **Document assumptions**: Record reasonable defaults in the Assumptions section
3. **Limit clarifications**: Maximum 3 [NEEDS CLARIFICATION] markers - use only for critical decisions that:
   - Significantly impact feature scope or user experience
   - Have multiple reasonable interpretations with different implications
   - Lack any reasonable default
4. **Prioritize clarifications**: scope > security/privacy > user experience > technical details
5. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
6. **Common areas needing clarification** (only if no reasonable default exists):
   - Feature scope and boundaries (include/exclude specific use cases)
   - User types and permissions (if multiple conflicting interpretations possible)
   - Security/compliance requirements (when legally/financially significant)

**Examples of reasonable defaults** (don't ask about these): <!-- JTG ANALYSIS: Note these specific examplees of what to auto assume when creating the spec -->

- Data retention: Industry-standard practices for the domain
- Performance targets: Standard web/mobile app expectations unless specified
- Error handling: User-friendly messages with appropriate fallbacks
- Authentication method: Standard session-based or OAuth2 for web apps
- Integration patterns: RESTful APIs unless specified otherwise

### Success Criteria Guidelines

Success criteria must be:

1. **Measurable**: Include specific metrics (time, percentage, count, rate)
2. **Technology-agnostic**: No mention of frameworks, languages, databases, or tools
3. **User-focused**: Describe outcomes from user/business perspective, not system internals
4. **Verifiable**: Can be tested/validated without knowing implementation details

**Good examples**:

- "Users can complete checkout in under 3 minutes"
- "System supports 10,000 concurrent users"
- "95% of searches return results in under 1 second"
- "Task completion rate improves by 40%"

**Bad examples** (implementation-focused):

- "API response time is under 200ms" (too technical, use "Users see results instantly")
- "Database can handle 1000 TPS" (implementation detail, use user-facing metric)
- "React components render efficiently" (framework-specific)
- "Redis cache hit rate above 80%" (technology-specific)
