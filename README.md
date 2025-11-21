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

# 🧠 Milestone 10 — Intent Planner (NEW)

### ✔️ Completed

- Introduced **high-level intent planning** on top of world-specific reflexes and navigation.
- Implemented a dedicated `agent/intents/keydoor_intent.py` for KeyDoorWorld.
- The model now reasons at a *goal level*, producing intents such as:
  - `"go_to_key"`
  - `"pickup_key"`
  - `"go_to_door"`
  - `"unlock_door"`
- Added intent-to-action mapping (`intent_to_action_keydoor`) converting intents into concrete tool calls.
- Integrated the intent planner into a new loop:  
  *reflex → intent planner → constraints → dispatch → observe → repeat*.
- Demonstrated **much more stable behavior** in KeyDoorWorld, reducing oscillations and mistaken tool calls.
- This milestone brings the architecture closer to **real agent stacks**:
  - reflex layer (fast, local corrections)
  - intent layer (LLM reasoning)
  - action layer (tools + constraints)
  - environment layer (world-specific game logic)

### 🧩 Why This Matters

In modern agent systems (Voyager, Devin, ReAct-style agents, robotics planners):

- LLMs do *not* choose raw actions every step.
- They choose **intent-level decisions**.
- Lower layers convert those intents into legal, safe, environment-appropriate actions.

This milestone adds that layer and prepares the project for:

- multi-step plan generation  
- planning graphs  
- curriculum learning  
- and higher-level world abstractions.

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

- **Milestone 9:** World-Specific Policy Modules  
  - Extracted world-dependent reflexes + constraints  
  - Introduced `agent/policies/*`  
  - Core agent loop is now clean and fully world-agnostic

- **Milestone 10:** Intent Planner  
  - Added high-level decision-making  
  - Introduced world-specific intent planners  
  - Mapped intents to low-level tools  
  - Improved multi-step reasoning stability 
      
(Upcoming)
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
