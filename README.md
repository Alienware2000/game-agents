# 🧠 Game Agents — A Learning Sandbox for Agentic Development

**Game Agents** is my personal sandbox for learning **agentic development from first principles**.  
Instead of relying on pre-built frameworks, I am building everything from scratch — the worlds, the tools, the agent loops, the planners, and later the MCP server that will make the agent portable across environments.

The long-term goal is to master agentic thinking and agentic engineering across *any* domain:  
games, embedded systems, robotics, productivity, business automation, and beyond.

This project uses games as a fun and visual way to explore agent capabilities, decision-making, perception, and tool usage.

---

## 🎮 Current Milestone: M3 — Reactive, Perception-Driven Agent

### ✔️ Implemented So Far
- **Custom GridWorld environment**
  - 10×10 world, walls, player movement  
  - Items on the ground (coal, stick)  
  - Inventory system  
  - Crafting system (torch = coal + stick)  

- **Tool Interface (`observe`, `move`, `pickup`, `craft`)**
  - Mirrors the structure of an MCP tool contract  
  - Agent interacts *only* through tools, never directly with the world  

- **Agent Loop (observe → plan → act → repeat)**
  - Clean architecture separating agent logic from environment  
  - Deterministic rule-based planner for initial testing  

- **Goal System**
  - Goal: craft 1 torch  
  - Environment tracks `goal_done`  

- **Reactive Planner (M3B)**
  - Agent scans the observed grid for items ("C" / "S")  
  - Moves toward them based on perception  
  - Picks them up and crafts when ready  
  - Fully autonomous, perception-driven behavior

---

## 🔜 Coming Next

### M4 — MCP Integration  
Turn the GridWorld into an **MCP tool server**, making the agent portable and world-agnostic.

### M5 — Second Game World  
Introduce a richer environment (Pygame or a new custom world) and reuse the exact same agent.

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
  - Implemented `pickup()` and an inventory system  
  - Added crafting (`torch = coal + stick`)  
  - Introduced a goal structure and `goal_done` tracking  
  - Agent successfully completes a multi-step objective

- **Milestone 3B:** Reactive, Perception-Driven Planner  
  - Agent now scans the grid to locate visible items  
  - Moves toward items based on observation (no hardcoded positions)  
  - Picks up required resources and crafts the torch  
  - Fully autonomous, perception-driven behavior

(Upcoming)  
- **Milestone 4:** MCP Integration  
- **Milestone 5:** Second Game World (Pygame or custom design)

## 🌟 Why This Project Exists

I want to deeply understand:
- how agents perceive, plan, and act  
- how to design tool interfaces and action spaces  
- how to build portable, general agents that can operate across domains  
- how to scale from toy worlds → complex games → hardware → real-world tasks  

This repository is a living journey toward **agentic mastery**, built one small, clear milestone at a time.

---

