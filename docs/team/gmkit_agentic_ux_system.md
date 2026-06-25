# gmkit Agentic UX System

## 1. Purpose

This document defines the architecture, data model, and interaction patterns for the **gmkit Agentic UX System**.

The system enables:
- Collaborative editing of a clue-map model
- Real-time synchronization across multiple clients
- Integration with an AI agent via MCP (Model Context Protocol)
- Local-first operation with no required cloud dependencies

This document is intended to:
- Guide implementation
- Serve as input to spec-kit workflows
- Provide a stable architectural reference

---

## 2. System Overview

The gmkit Agentic UX System is a **local-first, event-driven, multi-client system** with an AI agent participating as a reactive collaborator.

### Key Capabilities

- Real-time UI updates across multiple browser contexts
- Action-driven state updates
- Agent-triggered reasoning based on meaningful changes
- Separation of UI, orchestration, and computation layers

---

## 3. Architectural Principles (Normative)

### 3.1 Local-First
- The system MUST operate without external cloud services
- All state MUST be stored locally

### 3.2 Single Source of Truth
- The database MUST be the canonical state
- UI state MUST be derived from the database

### 3.3 Action-Driven State
- All mutations MUST occur via actions
- Direct mutation outside actions MUST NOT occur

### 3.4 Event Propagation
- All state changes MUST propagate via events
- Clients MUST subscribe to updates

### 3.5 Agent as Participant
- The agent MUST NOT be event-driven
- The agent MUST be triggered via explicit tool calls

### 3.6 Separation of Concerns
- UI MUST NOT directly manipulate persistent storage
- MCP server MUST mediate all persistent operations
- Python layer MUST handle computation only

---

## 4. System Components

```
                ┌──────────────────────────┐
                │   MCP Server (Node.js)   │
                │                          │
                │  - MCP tools             │
                │  - Event bus             │
                │  - WebSocket server      │
                └──────────┬───────────────┘
                           │
                           ▼
                      SQLite DB

        ┌────────────┴────────────┐
        ▼                         ▼

 ┌──────────────┐        ┌──────────────┐
 │ UX App       │        │ MCP App      │
 │ (Vue/Pinia)  │        │ (iframe)     │
 └──────────────┘        └──────────────┘

                           │
                           ▼
                   AI Agent (MCP Client)

                           │
                           ▼
                 Python gmkit Engine
```

---

## 5. Data Model (Normative)

### 5.1 Clue Map

```json
{
  "nodes": [
    { "id": "clue1", "type": "clue", "label": "Bloody Knife" }
  ],
  "edges": [
    { "from": "clue1", "to": "suspectA", "type": "implicates" }
  ]
}
```

### 5.2 Action Schema

```json
{
  "type": "ADD_CLUE",
  "payload": { "id": "clue1", "label": "Bloody Knife" },
  "meta": {
    "source": "user",
    "timestamp": 1234567890,
    "id": "uuid"
  }
}
```

### 5.3 Event Schema

```json
{
  "event": "CLUE_ADDED",
  "data": {},
  "meta": {}
}
```

---

## 6. State Management Model

- Use Vue with Pinia
- All updates MUST occur through store actions
- Components MUST NOT mutate state directly

---

## 7. Synchronization Model

### Outbound

```
User → UI Action → Store → Effect → MCP Tool → DB
```

### Inbound

```
DB → Event → WebSocket → Client → Store Action → UI Update
```

---

## 8. Agent Integration Model

```
DB Change
   ↓
MCP App receives update
   ↓
Effect determines significance
   ↓
tools/call → agent
```

---

## 9. Event & Action System

- Actions MUST include metadata.source
- Prevent feedback loops
- Agent-originated actions MUST NOT retrigger agent

---

## 10. Database Design

- SQLite
- Tables: nodes, edges, optional events

---

## 11. MCP Server Design

- Expose tools (get_clue_map, update_clue_map)
- Persist actions
- Emit events
- Manage WebSocket connections

---

## 12. Python Integration Contract

Example:

```
uv run gmkit generate-pdf
```

- Input: JSON or CLI args
- Output: file path or JSON

---

## 13. End-to-End Flows

### User Update

```
User → UI → Action → MCP → DB → Event → UI + MCP App
```

### Agent Update

```
Agent → MCP Tool → DB → Event → UI
```

### External Sync

```
Tab A → DB → Event → Tab B → UI Update
```

### Agent Trigger

```
Event → MCP App → tools/call → Agent
```

---

## 14. Concurrency & Consistency

- Start with last-write-wins
- Add versioning later

---

## 15. Deployment Model

Requires:
- Node.js
- Python
- Local DB

---

## 16. Risks & Tradeoffs

- Dual runtime complexity
- Event storms
- Agent over-triggering

---

## 17. Future Extensions

- Event sourcing
- Multi-user sync
- Agent intent actions

---

## 18. Appendix

### Example MCP Tool

```json
{
  "name": "update_clue_map",
  "input": {
    "actions": []
  }
}
```
