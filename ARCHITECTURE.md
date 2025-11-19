# Game Agents – Architecture Overview

This repo is a learning sandbox for **agentic development**.

At a high level there are three layers:

1. **Worlds** – game environments the agent lives in  
2. **Tool backends** – ways to interact with the world (Python / MCP)  
3. **Agent loops & shared helpers** – logic that observes, plans, constrains, and acts

---

## 1. Worlds

- `games/gridworld/core.py`  
  Defines the **GridWorld** environment:
  - 10×10 grid with walls, empty floor, and items (`C` for coal, `S` for stick)
  - Player position
  - Inventory and crafting (torch = coal + stick)
  - `observe()`, `move()`, `pickup()`, `craft()`
  - `goal` and `goal_done` for task completion

This layer knows **nothing** about LLMs, MCP, or any agent.  
It is just game logic.

---

## 2. Tool Backends

These expose the environment as “tools” that an agent can call.

### 2.1 Python tools

- `agent/tools.py`

Wraps a `GridWorld` instance with simple Python-accessible actions:

- `Tools.observe()`
- `Tools.move(direction)`
- `Tools.pickup()`
- `Tools.craft(item, qty)`

Used by Python-based agents such as `scripts/run_llm_agent.py`.

### 2.2 MCP server

- `mcp_gridworld_server.py`

Uses **FastMCP** to expose GridWorld as **MCP tools**:

- `observe`
- `move`
- `pickup`
- `craft`

This allows any MCP-compatible LLM host (ChatGPT, Claude, Assistant API, etc.)  
to control the GridWorld environment over a protocol.

The MCP server is now a **first-class tool provider**.

---

## 3. Agent Loops & Shared Helper Layer

### 3.1 Shared helper functions (core of modern architecture)

- `agent/loop.py`

This file contains all reusable logic shared by *every* agent loop:

- `find_items_in_grid` – preprocessed perception for LLMs  
- `attach_memory` – injects `last_action` and `last_result`  
- `format_observation` – converts env observation into LLM-readable text  
- `reflex_action` – auto-pickup and rule-based reflexes  
- `suggest_direction_toward_target` – tiny navigation helper  
- `enforce_action_constraints` – safety, legality, fallback moves, avoid repeated-blocked moves  

**This is now the canonical “agent brain utility layer.”**  
All agents (Python, MCP, future games, etc.) use these.

### 3.2 LLM planner over Python tools

- `scripts/run_llm_agent.py`

This agent:

- Calls Python `Tools` to interact with GridWorld  
- Requests actions from the LLM using `SYSTEM_PROMPT`  
- Adds memory + structured perception  
- Applies reflexes + constraints  
- Dispatches actions via Python methods (`Tools.move`, `Tools.pickup`, etc.)

This is the “LLM agent with direct Python backend.”

### 3.3 LLM planner over MCP

- `scripts/run_llm_agent_mcp.py`

Same planning logic as above, but:

- Connects to the MCP GridWorld server  
- Calls MCP tools instead of Python methods:
  - `observe`
  - `move`
  - `pickup`
  - `craft`
- Still uses all shared helper functions for:
  - memory
  - constraints
  - navigation
  - reflexes

This agent behaves like a **real production LLM client**, not a Python script calling environment internals.

---

## 4. Older utilities (now mostly superseded)

These remain useful for reference/debugging but are not used in the refactored architecture:

- `agent/rule_based.py`  
- `scripts/run_agent.py`  
- `scripts/run.py`  
- `scripts/test_tools_smoke.py`

They were part of early milestones (0–3B) and show the evolution of the project.

---

## 5. Milestones (High Level)

See `README.md` for the human-friendly milestone story.

This `ARCHITECTURE.md` is the “map” of how the code fits together in the final refactored structure.
