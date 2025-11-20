import json
import os
from typing import Dict, Any

from groq import Groq

from games.gridworld.core import GridWorld
from agent.tools import Tools
from agent.loop import (
    attach_memory,
    format_observation,
)
from agent.policies import gridworld_policy as policy

SYSTEM_PROMPT = """
You are an agent playing a simple grid-based game.

World:
- You see a 2D grid of characters.
- "#" are walls (impassable).
- "." are empty floor.
- "C" is coal on the floor.
- "S" is a stick on the floor.
- You are ALSO given a parsed list `items_in_world`, which contains entries like {"type": "coal", "row": 1, "col":4}. Use this list to reason about where to move to reach items.

Movement strategy:
- If you do not have at least 1 coal in your inventory, your first priority is to move
  toward the nearest coal in items_in_world.
- If you already have coal but no stick, move toward the nearest stick.
- To move toward a target at (target_row, target_col), compare it with your current
  position (row, col) and choose a move that reduces the Manhattan distance:
  |target_row - row| + |target_col - col|.
- Example: if target_row < row, moving "up" moves you closer in the row dimension.
  If target_col > col, moving "right" moves you closer in the column dimension.

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
6. If last_result shows that your previous move was blocked (e.g. {"ok": false, "error": "move blocked"}), you MUST choose a different direction next time. Do NOT keep repeating a blocked move.
7.You have a limited number of steps. Do not waste steps repeating the same useless action.

Response format:
- Always respond with a single JSON object, no extra text.
- Shape: {"tool": "<name>", "args": {...}}.
- If no args are needed, use an empty object: {"tool": "pickup", "args": {}}.
"""

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


def main():
    # 1. Setup LLM client
    client = Groq(api_key=os.environ["GROQ_API_KEY"]) # reads GROQ_API_KEY from environment

    # 2. Setup environment + tools
    env = GridWorld()
    tools = Tools(env)

    # 3. Initial observation
    obs = env.observe()

    # Short-term memory of what happened on the previous step
    last_action: Dict[str, Any] | None = None
    last_result: Dict[str, Any] | None = None

    # Attach memory before printing the initial world
    obs = attach_memory(obs, last_action, last_result)

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

        # Attach memory into obs so reflex + LLM both see it
        obs = attach_memory(obs, last_action, last_result)

        # 1) Check for reflex actions first (Gridworld policy)
        action = policy.reflex_action(obs)
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
        action = policy.enforce_action_constraints(obs, action)
        print("Action after constraints:", action)

        # 4) Dispatch the chosen action
        result = dispatch(tools, action)
        print("Result:", result)

        history.append({"action": action, "result": result})

        # Update short-term memory
        last_action = action
        last_result = result

        # 5) Get new observation after action
        obs = env.observe()
        # attach memory BEFORE printing so logs show it
        obs = attach_memory(obs, last_action, last_result)

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
