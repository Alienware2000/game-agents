# 🧠 Game Agents — A Learning Sandbox for Agentic Development

**Game Agents** is my personal sandbox for learning **agentic development from first principles**.  
Instead of relying on pre-built frameworks, I am building everything from scratch — the worlds, the tools, the agent loops, the planners, and the MCP server that makes the agent portable across environments.

The long-term goal is to master agentic thinking and agentic engineering across *any* domain:  
games, embedded systems, robotics, productivity, business automation, and beyond.

This project uses games as a fun and visual way to explore agent capabilities, decision-making, perception, and tool usage.

---

# 🌍 Multiple Worlds Now Supported

The project now supports **multiple independent game worlds**, each representing a different agentic challenge:

### ✔️ GridWorld  
The original environment:
- 10×10 grid  
- coal + stick items  
- inventory  
- crafting  
- goal: craft a torch  

### ✔️ KeyDoorWorld (NEW — Milestone 8)  
A second, fully independent world:
- player must locate a **Key (K)**  
- pick it up  
- find the **Door (D)**  
- unlock it  
- no crafting, simpler inventory  
- goal: `{"action": "unlock", "item": "door"}`

This milestone demonstrates the scalability of the architecture and introduces multi-world agent loops.

More worlds will be added in future milestones.

---

# 🧱 Milestone 9 — World-Specific Policy Modules (NEW)

### ✔️ Completed

- Added `agent/policies/gridworld_policy.py`  
- Added `agent/policies/keydoor_policy.py`  
- Moved **world-specific reflexes + constraints** out of `agent/loop.py`  
- `agent/loop.py` is now **fully world-agnostic**  
- LLM planners automatically import the correct policy module based on world type  
- Architecture now scales elegantly to:
  - many environments  
  - richer rule sets  
  - cleaner division between shared logic & world logic  

This was a major cleanup milestone that makes future worlds, tools, and agents dramatically easier to implement.

---

## 🛰️ Milestone 4 — MCP Integration (Tool Server Architecture)

### ✔️ Completed

- **Built `mcp_gridworld_server.py`**, turning the entire GridWorld into an **MCP-compliant tool server**.
- Exposed the environment’s capabilities as MCP tools:
  - `observe()`
  - `move(direction)`
  - `pickup()`
  - `craft(item, qty)`
- **Integrated FastMCP**, the official Python Model Context Protocol SDK.
- **Verified schemas and tool contracts** through the MCP Inspector GUI.
- Successfully:
  - launched the MCP server via STDIO transport  
  - connected using the Inspector  
  - invoked tools manually  
  - observed live world updates  
  - picked up items and crafted using MCP calls  

This milestone lifts the project from a local Python simulation to a **portable, externally-controllable agent environment**.

> **Note:** The MCP server exposes the GridWorld as tools.  
> Initially, the LLM planner ran in a separate script and called the environment directly.  
> Later milestones route the planner’s tool use *through* MCP as well.

### 🧠 Why This Matters

With MCP integration:

- The GridWorld becomes a **first-class tool provider** for any LLM or agent capable of MCP.
- Tools are now described using **schemas**, which lets the LLM understand how to call them.
- The environment operates like a real API — the same pattern used by:
  - ChatGPT / Claude tool calling  
  - Cursor agents  
  - Voyager / Minecraft-style agents  
  - Web automation tools  
  - Robotics / IoT control systems  

GridWorld is now “LLM-ready,” meaning any Large Language Model can reason about the world, choose actions, and call tools through a protocol.

This is the exact architecture modern agentic systems are built on.

---

## 🤖 Milestone 5 — LLM Planner Agent (Structured Observations + Tool Use, Direct Python)

### ✔️ Completed

- Implemented `scripts/run_llm_agent.py`, a **LLM-driven control loop**:
  - Uses an LLM (via Groq / OpenAI-compatible APIs) to choose actions.
  - The agent **never touches the GridWorld directly** — it only acts through tools:
    - `move(direction)`
    - `pickup()`
    - `craft(item, qty)`.
- Designed a clean **observe → plan → act → repeat** loop:
  - Environment returns a structured observation (`grid`, `player`, `inventory`, `goal`, `goal_done`).
  - We format this into a prompt and ask the LLM which tool to call next.
- Added **preprocessed perception** for the LLM:
  - `items_in_world = [{"type": "coal", "row": ..., "col": ...}, ...]`
  - This gives the model an object-level view of the world instead of forcing it to “read” ASCII art.
- Introduced **short-term memory** in the observation:
  - `last_action`
  - `last_result`
  - This lets the LLM see whether the last move failed (e.g. `"move blocked"`) and adjust.
- Implemented **action constraints & safety checks**:
  - Block illegal or useless actions (e.g. `pickup()` when nothing is under the player).
  - Prevent repeated blocked moves (do not keep walking into a wall).
  - Ensure `craft("torch", 1)` is only called when there is at least one `coal` and one `stick`.
- Added a small helper policy, `suggest_direction_toward_target`, that:
  - Looks at `player` vs `items_in_world`
  - Suggests a direction that reduces Manhattan distance to the next needed item
  - Is used as a *fallback / nudge* when the LLM keeps getting stuck

### 🧩 What This Milestone Shows

- How to wrap a simple grid world in **tool-like actions** and let an LLM decide which to call.
- How to combine:
  - LLM **flexibility** (choosing tools, reacting to results)
  - with **guardrails** (constraints, reflex rules, fallback heuristics).
- How to build up an agent loop **incrementally**:
  1. Pure rule-based planner (M3B).
  2. LLM planner with raw grid.
  3. LLM planner with structured perception + memory + constraints.

At this stage, the LLM planner talks to the environment directly via Python, while MCP exposes the same tools over a protocol.

---

## 🌐 Milestone 6 — LLM-over-MCP (Agent Uses MCP Server as Tool Backend)

### ✔️ Completed

- Implemented `scripts/run_llm_agent_mcp.py`, a **LLM agent that controls GridWorld through MCP** instead of calling Python methods directly.
- The agent loop now:
  - Calls the MCP tool **`gridworld.observe`** to get the latest world state.
  - Formats a structured observation (including `items_in_world`, `last_action`, `last_result`).
  - Asks the LLM to pick the next tool to call.
  - Maps the chosen tool to an MCP tool name:
    - `gridworld.observe`
    - `gridworld.move`
    - `gridworld.pickup`
    - `gridworld.craft`
  - Sends the tool call via MCP and receives the result.
  - Updates memory and repeats until the goal is achieved or steps are exhausted.
- Reuses the same:
  - **reflex rules** (auto-pickup on items),
  - **action constraints** (legal actions only),
  - and navigation helper (`suggest_direction_toward_target`),  
  now sitting on top of an **MCP-based tool backend**.

### 🧠 Why This Matters

- The GridWorld is now a **remote environment reached entirely via a protocol**.
- The agent behaves like a real LLM app client:
  - it doesn’t “reach into” the game’s internals,
  - it only sees observations and calls tools over MCP.
- This mirrors how:
  - ChatGPT tools,
  - Claude tools,
  - and other agent hosts  
    interact with external systems.
- This milestone is the full **“LLM-over-MCP”** pattern:  
  an LLM planner driving a tool-exposed environment through a standard protocol.

---

## 🧱 Milestone 7 — Agent Architecture Cleanup

### ✔️ Completed (optional class wrapper not required)

- Created the unified **agent brain utility layer** in `agent/loop.py`:
  - `find_items_in_grid`
  - `format_observation`
  - `attach_memory`
  - `reflex_action`
  - `suggest_direction_toward_target`
  - `enforce_action_constraints`
- Both LLM agents now share the same logic.
- Clear separation of concerns:
  - `games/` = environment  
  - `agent/` = agent brain + tools  
  - `scripts/` = agent loops / runners  
  - `mcp_*.py` = protocol servers  

The milestone is done.  
The optional `class Agent:` wrapper can be added later if needed.

---

# 🔑 Milestone 8 — Second Game World: KeyDoorWorld (NEW)

### ✔️ Completed

- Added `games/keydoor/core.py`
- Fully independent logic:
  - Key tile (`K`)
  - Door tile (`D`)
  - Inventory with `"key"`
  - `open_door()` tool
  - Goal completion via unlocking
- Added `scripts/run_llm_agent_keydoor.py`
- Reused the entire agent loop architecture with minimal changes
- Verified LLM-driven unlocking works end-to-end

This milestone proves that the architecture is scalable and supports **multi-world agents**.

---

## 🏁 Milestone Summary (Project Progress)

A concise list of all milestones completed so far in this project:

- **Milestone 0:** Tiny World + Tiny Agent  
  - Built a minimal 10×10 GridWorld  
  - Added player movement and an `observe()` method  
  - Implemented the first observe → act loop

- **Milestone 1:** Tools Interface  
  - Created a `Tools` class exposing `observe` and `move`  
  - Enforced separation between agent and environment  
  - Prepared foundation for MCP-style tool contracts

- **Milestone 2:** Agent Loop with Trivial Planner  
  - Added a `_plan()` method  
  - Enabled the first autonomous behavior  
  - Agent executes actions selected at runtime (not hardcoded scripts)

- **Milestone 3A:** Pickup, Inventory, Crafting, and Goal System  
  - Added items on the grid (coal, stick)  
  - Implemented `pickup()` and inventory handling  
  - Added crafting (`torch = coal + stick`)  
  - Introduced a goal structure and `goal_done` tracking  
  - Agent successfully completes a multi-step objective

- **Milestone 3B:** Reactive, Perception-Driven Planner  
  - Agent now scans the grid to locate visible items  
  - Moves toward items based on observation (no hardcoded positions)  
  - Picks up required resources and crafts the torch  
  - Fully autonomous, perception-driven behavior

- **Milestone 4:** MCP Integration  
  - Implemented a full MCP tool server around GridWorld  
  - Tools validated with MCP Inspector  
  - Successfully invoked actions (`observe`, `move`, `pickup`, `craft`) through the protocol  
  - World is now externally controllable by LLMs and agent hosts  
  - Foundation laid for LLM-driven planning over MCP

- **Milestone 5:** LLM Planner Agent (Direct Python)  
  - Implemented a Python LLM agent loop in `scripts/run_llm_agent.py`  
  - Uses structured observations (`items_in_world`, `last_action`, `last_result`)  
  - Enforces action constraints and reflex rules to keep the agent safe and efficient  
  - Demonstrates a full LLM-in-the-loop tool-using agent over GridWorld

- **Milestone 6:** LLM-over-MCP  
  - Implemented `scripts/run_llm_agent_mcp.py`  
  - Agent now uses the MCP server as its tool backend  
  - All environment interaction flows through MCP tools  
  - Brings the architecture in line with real-world LLM tool usage patterns

- **Milestone 7:** Agent Architecture Cleanup (Optional class-based design, shared components)
  - Created the unified **agent brain utility layer** in `agent/loop.py`
  - Both LLM agents now share the same logic.
  - Clear separation of concerns
  - The optional `class Agent:` wrapper can be added later if needed.
    
- **Milestone 8:** Second Game World (KeyDoorWorld)
    - Added `games/keydoor/core.py`
    - Fully independent logic
    - Goal completion via unlocking
    - Added `scripts/run_llm_agent_keydoor.py`
    - Reused the entire agent loop architecture with minimal changes
    - Verified LLM-driven unlocking works end-to-end
      
- **Milestone 9:** World-Specific Policy Modules  
  - Extracted world-dependent reflexes + constraints  
  - Introduced `agent/policies/*`  
  - Core agent loop is now clean and fully world-agnostic
      
(Upcoming)
- **Milestone 10:** Intent Planner (true multi-step reasoning for actions)  
- **Milestone 11:** Pygame front-end  
- **Milestone 12:** Multi-world unified agent  
- **Milestone 13:** Integration with real games (Minecraft, Terraria, Stardew-like worlds)

---

## 🌐 What MCP Adds to the Project

MCP transforms the GridWorld from a local Python program into a **remote, tool-based environment** that any agent can connect to.  

This means:

- The world is now a **service** with callable tools.  
- Observations and actions flow through a standard JSON-RPC protocol.  
- The environment is no longer limited to the Python agent loop — LLMs, external clients, or other agents can control it.

This opens the door to:

- **LLM-driven agents** that decide actions based on world observations.  
- Reusable **tool schemas** that multiple agents can share.  
- Plug-and-play integration with future tools, games, and hardware.  
- Multi-game, multi-world agents that operate across entirely different environments.

MCP is the bridge between “game logic” and “AI agent intelligence”.

---

## 🌟 Why This Project Exists

I want to deeply understand:

- how agents perceive, plan, and act  
- how to design tool interfaces and action spaces  
- how to build portable, general agents that can operate across domains  
- how to scale from toy worlds → complex games → hardware → real-world tasks  

This repository is a living journey toward **agentic mastery**, built one small, clear milestone at a time.

---

## 📚 Further Reading and References

Some of the ideas in this project connect to existing work on tool-using and embodied agents:

- **ReAct: Synergizing Reasoning and Acting in Language Models** – early work on letting LLMs interleave reasoning and tool use.  
- **Voyager: An Open-Ended Embodied Agent in Minecraft** – shows how agents can explore, learn skills, and act in a voxel world using tools and a curriculum.  
- **Model Context Protocol (MCP) documentation** – explains how MCP servers expose tools to LLM-based apps.
