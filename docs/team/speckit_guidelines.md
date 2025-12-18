# Spec-kit Guidelines and Best Practices

# Using Spec-kit

## WHAT IS IT?

From here

https://youtu.be/em3vIT9aUsg

And a deep dive here:

https://www.youtube.com/playlist?list=PL4cUxeGkcC9h9RbDpG8ZModUzwy45tLjb


## WHY DO WE NEED IT?

It solves multiple problems and reduces time to delivery as so:

- It takes on the three roles involved in grooming a feature and/or story in software development projects: product owner/project manager, scrum master and developer.
- It goes further by coordinating all three roles together via the four basic spec-kit commands:  

- /spec -  feature writing and story grooming
- /plan -  exploraton/design/architecture phase),
- /tasks -  break down plans into tasks AND arrange them in the most optimal sequence -- i.e. parallel-ization
- /implement - write the code following the defined task order using the specs, the plans and the task artifacts to ensure properly implemented clean code.

- Because the specification process produces clear instructions for the coding assistant, the assistant can generate code that hews closer to the specification then context driven development can provide. 

## HOW DO I USE IT?

For the most part the scaffolding logic in the agent-ready-starter project sets up the mcp to be used in codex and/or opencode.

### To verify it's installed in Codex:

- Run codex from the root folder of this project.
- Enter the /mcp command to list the installed mcps.
- You should see spec-kit listed.

Also you can ensure the prompts are available:

- In codex run /prompts
- You should see the speckit prompts listed.

### To verify in Opencode

- run opencode from the root folder of this project.
- Enter the /status command to list the installed mcps.
- You should see spec-kit listed.

To the spec-kit commands are available:

- In codex type /speckit
- You should see the speckit commands listed.

## HOW DO I USE IT WELL?

### Prerequisites before adding a new spec:

Code is no longer the source of truth in AI generated applications.  Instead it's the specification. Because of this, we prioritize our specifications to ensure they are DRY/YAGNI/etc. compliant.  So it's important to have a single document that defines the user experience and another that defines the architectural choices of the project.  For this project, the user docs are in the docs/user folder, and the design/architecture details are stored in the ARCHITECTURE.md file.  That way whenever a new spec is created, we can compare the spec against the user docs and the ARCHITECTURE.md to ensure we aren't inadvertantly impacting/breaking/reproducing existing functionality.

Follow these guidelines and ensure your AI follows them as well (TODO:  Integrate these steps into your AGENT.md file, establish a baseline constitution.md file as well, sigh).

- After completing a feature, always merge the generated quickstart.md documentation into your your user-docs folder. 
- In the same way, you need to update ARCHITECTURE.md file with any changes to the design of the application.  Move any details from the spec folder's plan.md, research.md or data-model.md files into the ARCHITECTURE.md. 

> NOTE:  You should perform these steps for any features/archetectural details you've already implemented as well.

## Spec phase

- When adding a new spec, have the AI vet the spec against the user-docs folder.

## Plan phase.

- When adding a new spec, have the AI vet the plan.md, research.md and/or data-model.md file against the ARCHITECTURE.md file.

By adding these checkpoints into the process we ensure:

- the new spec is not duplicating previously completed features, but actually adding value. 
- the new spec not conflict with or override current functionality.
- the new plan is not duplciating previously implemented code, but is instead re-using logic we already have.
- the new plan does not conflict or override current logic in the code.