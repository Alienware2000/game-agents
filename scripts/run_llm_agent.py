import json
import os
from typing import Dict, Any

from groq import Groq
from openai import OpenAI

from games.gridworld.core import GridWorld
from agent.tools import Tools

SYSTEM_PROMPT = """
You are an agent playing a simple grid-based game.

World:
- You see a 2D grid of characters.
- "#" are walls (impassable).
- "." are empty floor.
- "C" is coal on the floor.
- "S" is a stick on the floor.

Player:
- You know your current position as (row, col).
- You cannot walk through walls.
- The grid uses the same row/col indexing as the 'player' field.

Inventory:
- You can pick up items you stand on.
- You can craft new items from your inventory if a recipe exists.

Goal:
- Your ONLY goal is to craft at least 1 torch.
- Recipe: torch = 1 coal + 1 stick.

TOOLS YOU CAN USE (choose exactly ONE per turn):
- move(direction: "up" | "down" | "left" | "right")
- pickup()
- craft(item: string, qty: int)

STRICT ACTION RULES (YOU MUST OBEY THESE):
1. You are NOT allowed to call pickup() unless the character UNDER YOU
   in the grid is "C" or "S".
2. If you are standing on "C" or "S", you SHOULD call pickup() immediately.
3. If your inventory already has at least 1 "coal" and 1 "stick",
   you SHOULD call craft("torch", 1).
4. If there is no item under you, you MUST choose a move() action, never pickup().
5. You have a limited number of steps. Do not waste steps repeating the same
   useless action.

Response format:
- Always respond with a single JSON object, no extra text.
- Shape: {"tool": "<name>", "args": {...}}.
- If no args are needed, use an empty object: {"tool": "pickup", "args": {}}.
"""

def format_observation(obs: Dict[str, Any]) -> str:
    """Turn the obsercation into a human-readable string for the LLM."""
    lines = "\n".join(obs["grid"])
    player = obs["player"]
    inventory = obs["inventory"]
    goal = obs["goal"]
    goal_done = obs["goal_done"]
    return f"""grid: 

{lines}

player: {player}
inventory: {inventory}
goal: {goal}
goal_done: {goal_done} """

def llm_plan(client: Groq, obs: Dict[str, Any]) -> Dict[str, Any]:
    """Ask the LLM what tool to call next, given the current observation."""
    obs_text = format_observation(obs)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Here is the latest observation:\n\n{obs_text}\n\nPick ONE tool to call the next to make progress toward the goal. Respond ONLY with a JSON object.",
        }
    ]

    # Call the model (adjust model name if needed)
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.0
    )

    content = resp.choices[0].message.content
    # content should be JSON like: {"tool": "move", "args": {"direction": "right"}}

    try:
        action = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: if the model adds extra text, try to recover minimal JSON
        # For now, just raise so you can see what's happening.
        raise RuntimeError(f"Model did not return valid JSON: {content}")
    
    # Basic validation
    if "tool" not in action or "args" not in action:
        raise RuntimeError(f"Model response missing 'tool' or 'args': {action}")
    
    return action

def reflex_action(obs: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Simple hard-coded reflexes that run before the LLM:
    - If the player is standing on C or S, always pickup().
    - (Optional later) If inventory has coal + stick, craft a torch.
    """
    grid = obs["grid"]
    player = obs["player"]
    inventory = obs["inventory"]

    row = player["row"]
    col = player["col"]

    # Defensive check: make sure row/col are in range
    if 0 <= row < len(grid) and 0 <= col < len(grid[row]):
        tile = grid[row][col]
    else:
        tile = "."

    # Reflex 1: standing on an item? Always pick it up.
    if tile in ("C", "S"):
        return {"tool": "pickup", "args": {}}

    # (Optional Reflex 2: auto-craft when ready)
    # if inventory.get("coal", 0) >= 1 and inventory.get("stick", 0) >= 1 and inventory.get("torch", 0) < 1:
    #     return {"tool": "craft", "args": {"item": "torch", "qty": 1}}

    return None  # no reflex triggered


def dispatch(tools: Tools, action: Dict[str, Any]) -> Dict[str, Any]:
    """Map the LLM-chose tool to your actual environment tools."""
    name = action["tool"]
    args = action.get("args", {})

    if name == "move":
        return tools.move(**args)
    if name == "pickup":
        return tools.pickup()
    if name == "craft":
        return tools.craft(**args)
    if name == "observe":
        return tools.observe()
    
    return {"ok": False, "error": f"unknown tool {name}"}

def enforce_action_constraints(obs: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce hard rules on what actions are allowed in this state.
    If the LLM suggests something illegal or useless, replace it with a safe fallback.
    """
    grid = obs["grid"]
    player = obs["player"]
    inventory = obs["inventory"]

    row = player["row"]
    col = player["col"]

    if 0 <= row < len(grid) and 0 <= col < len(grid[row]):
        tile = grid[row][col]
    else:
        tile = "."

    name = action.get("tool")
    args = action.get("args", {})

    # Rule 1: Cannot pickup if not standing on C or S
    if name == "pickup" and tile not in ("C", "S"):
        # Fallback: force a move instead of wasting a turn
        # For now, just move right as a simple heuristic.
        return {"tool": "move", "args": {"direction": "right"}}

    # Rule 2: Cannot craft torch if we don't have coal + stick
    if name == "craft":
        if not (inventory.get("coal", 0) >= 1 and inventory.get("stick", 0) >= 1):
            # Again, force a simple move instead
            return {"tool": "move", "args": {"direction": "right"}}

    # Otherwise, allow the action
    return action


def main():
    # 1. Setup LLM client
    client = Groq(api_key=os.environ["GROQ_API_KEY"]) # reads GROQ_API_KEY from environment

    # 2. Setup environment + tools
    env = GridWorld()
    tools = Tools(env)

    # 3. Initial observation
    obs = env.observe()

    print("=== INITIAL WORLD ===")
    print(format_observation(obs))
    print("======================\n")

    max_steps = 30
    history = []

    for step in range(max_steps):
        if obs.get("goal_done"):
            print(f"Goal already done at step {step}!")
            break

        print(f"\n=== STEP {step} ===")

        # 1) Check for reflex actions first
        action = reflex_action(obs)
        if action is not None:
            print("Reflex chose action:", action)
        else:
            # 2) Fall back to LLM planning
            try:
                action = llm_plan(client, obs)
                print("LLM chose action:", action)
            except Exception as e:
                print("Error in LLM planning:", e)
                break


        # 3) Enforce hard constraints on the chosen action
        action = enforce_action_constraints(obs, action)
        print("Action after constraints:", action)

        # 4) Dispatch the chosen action
        result = dispatch(tools, action)
        print("Result:", result)

        history.append({"action": action, "result": result})

        # 5) Get new observation after action
        obs = env.observe()
        print("New observation:")
        print(format_observation(obs))

        if obs.get("goal_done"):
            print(f"\n🎉 Goal achieved at step {step + 1}!")
            break

    print("\n=== FINAL STATE ===")
    print(format_observation(obs))
    print("Steps taken:", len(history))

if __name__ == "__main__":
    main()
