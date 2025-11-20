# Game Agents – Architecture Overview

This repository is a learning environment for **agentic development from first principles**.  
The architecture is intentionally simple, transparent, and extensible, allowing multiple game worlds,
multiple tool backends, and multiple styles of LLM agents to coexist.

The project is now structured into **four major layers**:

1. Worlds  
2. Tool Backends  
3. Agent Logic (Shared & World-Specific)  
4. Agent Runners (Python & MCP)

Below is the complete, accurate description of how the current system works.

---

# 1. Worlds (`games/`)

Worlds contain **only game logic** and define the rules of each environment.

They do *not* contain:
- LLM logic  
- planning  
- policies  
- MCP code  

They simply expose Python methods such as `observe()`, `move()`, `pickup()`, etc.

## 1.1 GridWorld (`games/gridworld/core.py`)
The original environment:
- 10×10 grid with walls  
- Items: coal (`C`), stick (`S`)  
- Inventory system  
- Crafting: `torch = coal + stick`  
- `pickup()`, `craft()`, `move()`  
- Goal: craft a torch  

## 1.2 KeyDoorWorld (`games/keydoor/core.py`)
The second environment:
- Key tile (`K`)  
- Door tile (`D`)  
- Inventory contains a single field `"key"`  
- Player must:
  1. Walk to the key  
  2. Pick it up  
  3. Walk to the door  
  4. Unlock it via `open_door()`  
- Goal: `{"action": "unlock", "item": "door"}`  

Worlds follow the same interface but define their own rules internally.

---

# 2. Tool Backends (`agent/` and MCP servers)

Tool backends expose world actions in a **tool-callable** format.
They convert the world into something an LLM can interact with.

There are two types: Python direct tools and MCP-exposed tools.

## 2.1 Python Tools (`agent/tools.py`)
This file wraps a world instance and exposes:

- `observe()`
- `move(direction)`
- `pickup()`
- `craft(item, qty)` (GridWorld only)
- `open_door()` (KeyDoorWorld only)

Python tools are used by:
- `scripts/run_llm_agent.py`  
- `scripts/run_llm_agent_keydoor.py`

These are simple wrappers — no agent logic lives here.

## 2.2 MCP Tool Server (`mcp_gridworld_server.py`)
Exposes the **GridWorld** tools via the **Model Context Protocol** using FastMCP.

Tools registered:
- `gridworld.observe`
- `gridworld.move`
- `gridworld.pickup`
- `gridworld.craft`

This allows:
- ChatGPT
- Claude
- Assistant API
- External LLM agents

…to control the world over a protocol instead of Python imports.

(A KeyDoorWorld MCP server can be added at any time using the same pattern.)

---

# 3. Agent Logic

Agent logic is split into **shared utilities** and **world-specific policies**.

## 3.1 Shared Logic (`agent/loop.py`)
This file contains **world-agnostic** utilities that support every agent:

- `format_observation()`  
- `attach_memory()`  
- structured observation creation  
- LLM prompt helpers  
- memory injection  
- common utilities used by all planners  

Importantly, **Milestone 9 removed all world-specific rules** from this file.

It is now truly universal.

## 3.2 World-Specific Policy Modules (`agent/policies/`)
This was Milestone 9 — and it fundamentally improved scalability.

Each world now has its own file:

- `agent/policies/`
  - gridworld_policy.py
  - keydoor_policy.py

Each policy implements two key functions:

### `reflex_action(obs)`
- Auto-pickup logic  
- Crafting reflexes (GridWorld)  
- Auto-unlock (KeyDoorWorld) if conditions are met  

### `enforce_action_constraints(obs, action)`
- Validity checks  
- Block illegal actions  
- Fix actions the LLM suggested incorrectly  
- Improve navigation or avoid repeated mistakes

These policy modules are the “rules of the world,” separate from the shared logic.

The LLM planner loads the correct module based on which world is running.

---

# 4. Agent Runners (`scripts/`)

Agent runners are the actual loops that:

1. Call `tools.observe()`  
2. Format observation  
3. Apply policy reflexes  
4. Ask the LLM to choose an action  
5. Apply constraints  
6. Perform the action  
7. Update memory  
8. Repeat until goal achieved or steps exhausted

There are three main runners:

## 4.1 Direct Python LLM Agent (GridWorld)
`scripts/run_llm_agent.py`  
Uses:
- Python tools  
- Shared helper logic  
- GridWorld policy  

This is the simplest LLM agent.

## 4.2 Direct Python LLM Agent (KeyDoorWorld)
`scripts/run_llm_agent_keydoor.py`  
Same architecture, but loads KeyDoorWorld + its policy module.

Proves multi-world scalability.

## 4.3 LLM-over-MCP Agent
`scripts/run_llm_agent_mcp.py`  
Uses:
- MCP tools instead of Python methods  
- Same agent loop  
- Same policy and helper layers  

This is the "realistic" production-style architecture:
LLM → MCP → Environment.

---

# 5. Directory Structure Overview

For clarity, the repo now conceptually looks like this:

- `games/`
  - `gridworld/`
    - core.py
  - `keydoor/`
    - core.py

- `agent/`
  - tools.py
  - loop.py
  - `policies/`
    - gridworld_policy.py
    - keydoor_policy.py

- `scripts/`
  - run_llm_agent.py
  - run_llm_agent_keydoor.py
  - run_llm_agent_mcp.py

- mcp_gridworld_server.py


This layout is clean, scalable, and ready for many more worlds.

---

# 6. How the Layers Fit Together

**World (game rules)**  
↓  
**Tools (API surface for actions)**  
↓  
**Policy (world-specific constraints + reflexes)**  
↓  
**Shared helpers (LLM formatting, memory, observation shaping)**  
↓  
**Agent Loop (choose action, run step)**  
↓  
**LLM models (external — Groq / API)**

This modularity allows:

- many worlds  
- many planners  
- many backends  
- multiple visualization layers (e.g., upcoming Pygame UI)

…without breaking the architecture.

---

# 7. Next Steps in Architecture

Future milestones will extend this architecture naturally:

- Intent Planner (M10)
- Pygame front-end (M11)
- Multi-world unified agent (M12)
- Real-game integrations (M13)

This document will evolve as the system grows, but the core abstraction boundaries are already strong and stable.
