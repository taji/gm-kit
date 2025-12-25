Contains my notes regarding how Spec-kit actually works.  There are pieces of the spec-kit code base that I've included with my own annoatations. 

# The three basic processes

## 1) Install spec-kit python package via uv and configure the specify command for bash/powershell.  

Uv will download and install:

- The specify_cli package folder to ```~/.local/share/uv/tools/specify-cli/lib/python*/site-packages/specify_cli/``` (a package directory with __init__.py and other modules, not a single .py file).
- The bash invoked ```specify``` python file to ```~/.local/share/uv/tools/specify-cli/bin/specify```. This is a short python file (without the .py extension, but with a shebang to run it), that basically wraps the logic in the specify_cli folder.   
- A symlink is created in ~/.local/bin/specify that points to ```specify``` under ```uv/tools/etc```. 
    ```specify -> ~/.local/share/uv/tools/specify-cli/bin/specify```
        i.  This allows the command to be invoked from anywhere as .local/share is included in the OS PATH.
    
I think that's the entirety of uv's responsibilities.

## 2) Initialize a project by running the specify command as ```specify init <folder name>```

This will install the following folders and logic into the project folder (based on the OS and coding agent selected):

- <agent folder>/prompts/ (or commands/, or similar): 
    - each coding agent has a different location for the prompts:
        - for opencode the location is ```<project folder>/.opencode/command```
        - for codex the location is ```<project folder>/.codex/prompts```
    - the prompt files: are the specific slash commands invoked inside the coding agent.  Here is the list of prompt markdown files installed by ```specify init```:
        - speckit.constitution.md
        - speckit.specify.md (invoked as /specify in the coding agent)
        - speckit.clarify.md (same)
        - speckit.plan.md                 
        - speckit.tasks.md
        - speckit.taskstoissues.md
        - speckit.analyze.md

- <project folder>.specify/memory/
    - constitution.md (contains the core principles the agent is supposed follow when spec-ing a new feature)
- <project folder>.specify/scripts/<bash or ps>/ (invoked by the agent on behalf of the /slash command/prompts listed above). 
    - create-new-feature.sh
    - setup-plan.sh
    - check-prerequisites.sh
    - update-agent-context.sh
    - common.sh
- <project folder>.specify/templates (simple template files that are populated with the arguments provided by the script files above).
    - spec-template.md
    - checklist-template.md
    - plan-template.md
    - tasks-template.md
    - agent-file-template.md
 
More on these files below. 

Note that once the project is initialized the specify bash/ps command is no longer used for the project.

## Invoke the different slash commands in the coding agent to groom features

Here are the specific slash commands invoked inside the coding agent. Each slash command below has a corresponding markdown stored in the coding agents configureation.  Here is the list of prompt markdown files installed by ```specify init```:
    - /speckit.constitution : invoked to establish rules spec-kit will follow when grooming and implementing new features. 
        - rules are written to the ```.specify/constitution.md file (see below)```. 
    - /speckit.specify : invoked to create a new "first pass" feature spec.
        - spec is written to the ```<feature folder>/spec.md``` spec.md file.
    - /speckit.clarify : invoked to clarify any unknowns in the first pass spec.  
        - Unknowns are caused by insufficient details during the specify phase (this is normal). 
        - The agent queries the user to clarify any unknowns and then updates the spec.
        - By the time this phase is complete the spec.md file should be ~90% complete. 
    - /speckit.checklist (optional) : creates a check list for the user to follow and verify to ensure the spec is detailed enough to plan and implement.
    - /speckit.plan : invoked to create detailed plans and design detailes from the specs.md file. 
        - plans are written to the plan.md file along with research.md, quickstart.md, etc. (TODO: add details here):
    - /speckit.tasks
        - invoked to break the plan down into discrete tasks and then create a schedule of execution for the tasks. 
            - the schedule is optimized to run certain tasks in parallel. This is the development speed gain that spec-kit provides.
    - /speckit.taskstoissues.md
        - TODO: figure out what this does and document it.
    - speckit.analyze.md                   
        - figure out what this does and document it.

It's important to note that these files are markdown to be consumed by the coding agent.  They are not scripts/code/etc.  But they do instruct the agent on invoking the scripts listed below.

- <project folder>./specify/memory
    - constitution.md (contains the core principles the agent is supposed to follow when spec-ing a new feature). This file is the only file updated by the agent 
- <project folder>./specify/scripts/<bash or ps>/
    - This folder contains the bash or powershell scripts invoked by the agent on behalf of the /slash command/prompts listed above. 
    - When the slash command is invoked, the agent follows the prompts above to build a set of arguments that are passed into the corresponding script file.
    - It infers or deduces the proper arguments based on slash command prompt above.   
    - the scripts correspond to the the prompts above:
        - create-new-feature.sh:  invoked by the speckit.specify command above
        - setup-plan.sh: invoked by speckit.plan command above
        - check-prerequisites.sh: (TODO)
        - update-agent-context.sh: (TODO)
        - common.sh (common logic to the other scripts in this folder)
- <project folder>./specify/templates
    - These are simple template files that are populated with the arguments provided by the script file above.
        - spec-template.md
        - checklist-template.md
        - plan-template.md
        - tasks-template.md
        - agent-file-template.md
   
So as an example if we invoke /specify with a prompt of "create a todo list app in angular", this is the process of creating the spec.md file:

1. The prompt is passed to the agent along with the context and instructions in the ```speckit.specify.md``` file.
2. The agent considers the context and prompt and builds a list of arguments for the ```create-new-featuere.sh``` script.
3. The script is invoked which takes the arguments and populates them into the ```spec-template.md``` template to create the spec.md.

So it's ```/spec (invoked by user)  ==> Analysis (by agent) => Arguments for script (by agent) ==> Script invoked (by agent) ==> template rendered using args (by script) ==> spec.md.```

Note that this process is a first pass at creating spec.md. It provides the structure needed in the spec.md file so that the agent can 1) revise the spec directly later as needed and 2) refer to the spec.md file as it creates the plan.md, tasks.md file, etc as the process continues.

All of the other /slash commands follow this same pattern: prompt and instructions => create arguments => render template.