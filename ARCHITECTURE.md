# Game Agents – Architecture Overview

This repo is a learning sandbox for **agentic development**, built from first principles.

There are now **three architecture layers**, plus support for **multiple worlds**.

---

# 1. Worlds

All game worlds live under `games/`.

Each world contains **only game logic**, no AI code:

### `games/gridworld/core.py`
- 10×10 grid with walls & items  
- player movement  
- inventory system  
- pickup & crafting  
- torch recipe  
- goal: craft 1 torch  

### `games/keydoor/core.py`
- new world type  
- contains a key (`K`) and a door (`D`)  
- player must pick up the key and unlock the door  
- no crafting  
- simpler inventory  
- goal: `{"action": "unlock", "item": "door"}`

Worlds are intentionally isolated — swapping worlds should not affect the agent code.

---

# 2. Tool Backends

These wrap a world into a set of callable actions.

### 2.1 Python Tools
`agent/tools.py`  

A lightweight wrapper exposing:
- `observe()`
- `move(direction)`
- `pickup()`
- `craft(...)`
- (world-specific tools e.g. `open_door()`)

Used by:
- `scripts/run_llm_agent.py`
- `scripts/run_llm_agent_keydoor.py`

### 2.2 MCP Server
`mcp_gridworld_server.py`

Uses **FastMCP** to expose GridWorld as an MCP tool provider.

This enables:
- remote control  
- LLM-over-MCP agents  
- compatibility with ChatGPT / Claude tool calling  

Currently implemented for GridWorld.  
A KeyDoorWorld MCP server will be added later.

---

# 3. Agent Loops & Shared Helper Layer

### 3.1 Shared helper functions

`agent/loop.py` is the core “agent brain” support module.

It contains world-agnostic utilities:
- `find_items_in_grid`
- `format_observation`
- `attach_memory`
- `reflex_action`
- `enforce_action_constraints`
- `suggest_direction_toward_target`

Both GridWorld and KeyDoorWorld agents use this file.

### 3.2 LLM Planner (Python Backend)

`scripts/run_llm_agent.py`  
`scripts/run_llm_agent_keydoor.py`

- Requests LLM actions  
- Applies reflexes + constraints  
- Dispatches tool calls  
- Updates memory and observation  

### 3.3 LLM-over-MCP Planner

`scripts/run_llm_agent_mcp.py`

- Uses MCP instead of Python methods  
- Demonstrates full production-style separation:
  LLM → MCP → Environment

---

# 4. Directory Evolution & Future Refactor

As the project gained a second world, the following became clear:

- reflexes and constraints differ per-world  
- world-specific logic should not live in a shared helper module  
- scalability requires separating:
  - *shared logic*
  - *world-specific “policies”*

**Upcoming refactor (Milestone 9):**

```
agent/policies/
    gridworld_policy.py
    keydoor_policy.py
```

Each policy module will define:
- `reflex_action()`
- `enforce_action_constraints()`

This keeps `agent/loop.py` clean and world-agnostic.

---

# 5. Older Utilities

Kept for learning history:

- `agent/rule_based.py`
- `scripts/run_agent.py`
- `scripts/run.py`
- `scripts/test_tools_smoke.py`

These trace the evolution from Milestones 0 → 3B.

---

# 6. Milestones

See README.md for a full ordered milestone list.

This `ARCHITECTURE.md` documents how the pieces fit together in the final structure.

