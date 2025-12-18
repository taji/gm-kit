# Using MCP Knowledge Graph

## WHAT IS IT?

From here

https://github.com/shaneholloman/mcp-knowledge-graph


## WHY DO WE NEED IT?

https://youtu.be/khbFT5hOpKk

NOTE:  The youtube video is for a different memory mcp server, but the basic concepts are the same.  The only difference is we use mcp-knowledge-graph instead of neo 4j's memory mpc server because 1) mcp_knowledge_graph does not require the installation of a graph database, 2) simple install with npx, 3) all of the memory files live in the project folder under the .aim subfolder.  4) You can easily create a memory database on a per project basis, as the database uses simple JSONL to record knowledge/memory (JSONL is a list of json objects delimited by a CRLF --so one json object on each line).


## HOW DO I USE IT?

For the most part the scaffolding logic in agent-ready-starter setup up the mcp to be used in codex and/or opencode.

### To verify it's installed in Codex:

- Run codex from the root folder of this project.
- Enter the /mcp command to list the installed mcps.
- You should see mcp_knowledge_graph listed.

To ensure it's tracking your converstations:

- Ask it to read the AGENTS.md file.  
- This will instruct it to retreive memory.  
- From the codex prompt run "aim_list_databases"
- It should indicated the local project database was detected.
 

### To verify in Opencode

- run opencode from the root folder of this project.
- Enter the /status command to list the installed mcps.
- You should see mcp_knowledge_graph listed.

To ensure it's tracking your converstations, follow the codex instructions.



