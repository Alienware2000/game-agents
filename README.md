# 🧠 Game Agents — A Learning Sandbox for Agentic Development

**Game Agents** is my personal sandbox for learning **agentic development from first principles**.  
Instead of relying on pre-built frameworks, I am building everything from scratch — the worlds, the tools, the agent loops, the planners, and later the MCP server that will make the agent portable across environments.

The long-term goal is to master agentic thinking and agentic engineering across *any* domain:  
games, embedded systems, robotics, productivity, business automation, and beyond.

This project uses games as a fun and visual way to explore agent capabilities, decision-making, perception, and tool usage.

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
- This milestone lifts the project from a local Python simulation to a **portable, externally-controllable agent environment**.

### 🧠 Why This Matters
With MCP integration:
- The GridWorld becomes a **first-class tool provider** for any LLM or agent capable of MCP.
- Tools are now described using **schema**, which lets the LLM understand how to call them.
- The environment operates like a real API — the same pattern used by:
  - ChatGPT/Claude tool calling
  - Cursor Agents
  - Voyager / Minecraft agents
  - Web automation tools
  - Robotics/IoT control systems

GridWorld is now “LLM-ready,” meaning any Large Language Model can reason about the world, choose actions, and call the tools through the protocol.

This is the exact architecture modern agentic systems are built on.

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
  - Foundation laid for LLM-driven agent planning (Milestone 5)

(Upcoming)  
- **Milestone 5:** LLM Planner Agent (LLM-controlled decision-making)  
- **Milestone 6:** Second Game World (Pygame or custom design)

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

MCP is the bridge between “game logic” and “AI agent intelligence.”

---

## 🌟 Why This Project Exists

I want to deeply understand:
- how agents perceive, plan, and act  
- how to design tool interfaces and action spaces  
- how to build portable, general agents that can operate across domains  
- how to scale from toy worlds → complex games → hardware → real-world tasks  

This repository is a living journey toward **agentic mastery**, built one small, clear milestone at a time.

---

