import json
import os
from typing import Dict, Any

from groq import Groq

from games.keydoor.core import KeyDoorWorld
from agent.tools import KeyDoorTools
from agent.loop import (
    attach_memory,
    format_observation,
)
from agent.policies import keydoor_policy as policy

SYSTEM_PROMPT = """
You are an agent playing a simple key-and-door puzzle game on a 2D grid.

World:
- You see a 2D grid of characters.
- "#" are walls (impassable).
- "." are empty floor.
- "K" is a key on the floor.
- "D" is a locked door.
- You are ALSO given a parsed list `items_in_world`, which contains entries like {"type": "key", "row": 2, "col": 3} or {"type": "door", "row": 8, "col": 8}.
  Use this list to reason about where to move to reach the key and the door.

Player:
- You know your current position as (row, col).
- You cannot walk through walls.
- The grid uses the same row/col indexing as the 'player' field.

Inventory:
- You can pick up the key when you are standing on it.
- The inventory contains "key": 0 or 1, representing whether you hold the key.

Goal:
- Your ONLY goal is to open the door.
- To do this, you must:
  1) Move to the tile with the key ("K") and pick it up.
  2) Move to the tile with the door ("D").
  3) Call open_door() while standing on the door tile and holding the key.

TOOLS YOU CAN USE (choose exactly ONE per turn):
- move(direction: "up" | "down" | "left" | "right")
- pickup()
- open_door()

STRICT ACTION RULES (YOU MUST OBEY THESE):
1. You are NOT allowed to call pickup() unless the character UNDER YOU
   in the grid is "K".
2. If you are standing on "K", you SHOULD call pickup() immediately.
3. You CANNOT open the door unless:
   - you are standing on the "D" tile, AND
   - your inventory has key == 1.
4. If you are not on "K" or "D", you MUST choose a move() action, never pickup()
   and never open_door().
5. You have a limited number of steps. Do not waste steps repeating the same
   useless action.
6. If last_result shows that your previous move was blocked
   (e.g. {"ok": false, "error": "move blocked"}), you MUST choose a different
   direction next time. Do NOT keep repeating a blocked move.

Movement strategy:
- Before you have the key:
  - Move toward the nearest key in items_in_world (type == "key").
- After you have the key:
  - Move toward the door tile in items_in_world (type == "door").
- To move toward a target at (target_row, target_col), compare it with your current
  position (row, col) and choose a move that reduces the Manhattan distance:
  |target_row - row| + |target_col - col|.

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
            "content": (
                "Here is the latest observation:\n\n"
                f"{obs_text}\n\n"
                "Pick ONE tool to call next to make progress toward the goal. "
                "Respond ONLY with a JSON object."
            )
        }
    ]

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.0
    )

    content = resp.choices[0].message.content

    try:
        action = json.loads(content)
    except json.JSONDecodeError:
        raise RuntimeError(f"Model did not return valid JSON: {content}")
    
    if "tool" not in action or "args" not in action:
        raise RuntimeError(f"Model response missing 'tool' or 'args': {action}")
    
    return action

def dispatch(tools: KeyDoorTools, action: Dict[str, Any]) -> Dict[str, Any]:
    """Map the LLM-chosen tool to the actual KeyDoorWorld tools."""
    name = action["tool"]
    args = action.get("args", {})

    if name == "move":
        return tools.move(**args)
    if name == "pickup":
        return tools.pickup()
    if name == "open_door":
        return tools.open_door()
    if name == "observe":
        return tools.observe()
    
    return {"ok": False, "error": f"unkwnon tool {name}"}

def main():
    # 1. Setup LLM client
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    # 2. Setup environment + tools
    env = KeyDoorWorld()
    tools = KeyDoorTools(env)

    # 3. Initial observation
    obs = env.observe()

    last_action: Dict[str, Any] | None = None
    last_result: Dict[str, Any] | None = None

    # Attach memory before printing the initial world
    obs = attach_memory(obs, last_action, last_result)

    print("=== INITIAL KEYDOOR WORLD ===")
    print(format_observation(obs))
    print("==========================\n")

    max_steps = 30
    history = []

    for step in range(max_steps):
        if obs.get("goal_done"):
            print(f"Goal already done at step {step}!")

        print(f"\n=== STEP {step} ===")

        # Ensure observation contains last_action/last_result
        obs = attach_memory(obs, last_action, last_result)

        # 1) Check reflex_actions first
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
        obs = attach_memory(obs, last_action, last_result)

        print("New observation:")
        print(format_observation(obs))
        
        if obs.get("goal_done"):
            print(f"\n🎉 Goal achieved at step {step + 1}!")
            break

        print("\n=== FINAL STATE (KEYDOOR) ===")
        print(format_observation(obs))
        print("Steps taken:", len(history))

if __name__ == "__main__":
    main()