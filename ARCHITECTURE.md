# Game Agents – Architecture Overview

This repo is a learning sandbox for **agentic development**.

At a high level there are three layers:

1. **Worlds** – game environments the agent lives in  
2. **Tool backends** – ways to interact with the world (Python / MCP)  
3. **Agent loops** – logic that observes, plans, and acts

---

## 1. Worlds

- `games/gridworld/core.py`  
  Defines the **GridWorld** environment:
  - 10×10 grid with walls, empty floor, and items (`C` for coal, `S` for stick)
  - Player position
  - Inventory and crafting (torch = coal + stick)
  - `observe()`, `move()`, `pickup()`, `craft()`
  - `goal` and `goal_done` for task completion

This layer knows **nothing** about LLMs or MCP. It is just game logic.

---

## 2. Tool Backends

Two ways to expose the same environment as tools:

### 2.1 Python tools

- `agent/tools.py`

Wraps a `GridWorld` instance with simple Python methods:

- `Tools.observe()`
- `Tools.move(direction)`
- `Tools.pickup()`
- `Tools.craft(item, qty)`

These are used by Python-based agents like `scripts/run_llm_agent.py`.

### 2.2 MCP server

- `mcp_gridworld_server.py`

Uses **FastMCP** to expose GridWorld as **MCP tools**:

- `gridworld.observe`
- `gridworld.move`
- `gridworld.pickup`
- `gridworld.craft`

This lets external LLM hosts and MCP clients control the same world over a protocol.

---

## 3. Agent Loops

There are two main agent entrypoints:

### 3.1 LLM planner over Python tools

- `scripts/run_llm_agent.py`

Key ideas:

- Calls `env.observe()` (via `Tools`) to get a structured observation:
  - `grid`, `player`, `inventory`, `goal`, `goal_done`
- Adds:
  - `items_in_world` (parsed objects like coal/stick positions)
  - `last_action`, `last_result` (short-term memory)
- Sends this to an LLM with a **system prompt** that explains:
  - the world
  - the available tools (`move`, `pickup`, `craft`)
  - rules for valid actions
- LLM responds with a JSON action:
  - `{"tool": "...", "args": {...}}`
- Before executing, the code applies:
  - **reflex rules** (auto `pickup` when on an item)
  - **constraints** (block illegal actions, avoid repeating blocked moves)
  - **navigation helper** `suggest_direction_toward_target` to move toward coal/stick

This agent talks **directly** to GridWorld through Python code.

### 3.2 LLM planner over MCP

- `run_llm_agent_mcp.py`

Same high-level logic as above, but:

- Uses **MCP client** to call tools:
  - `gridworld.observe`
  - `gridworld.move`
  - `gridworld.pickup`
  - `gridworld.craft`
- Still:
  - formats a structured observation
  - uses reflex rules and constraints
  - lets the LLM pick actions in JSON

The agent now behaves like a **real LLM app client**:
it never calls `GridWorld` methods directly, only MCP tools.

---

## 4. Older utilities

- `agent/loop.py`  
  Earlier, simpler loop experiments from the first milestones.

- `scripts/run_agent.py`, `scripts/run.py`, `scripts/test_tools_smoke.py`  
  Older scripts used to test the environment and tools. Still useful for debugging.

---

## 5. Milestones (High Level)

See `README.md` for the human-friendly milestone story.

This `ARCHITECTURE.md` is the “map” of how the code fits together.
