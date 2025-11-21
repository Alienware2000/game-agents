"""
Intent-level planning helpers.

This module is responsible for asking the LLM:
    "Given this observation, what HIGH_LEVEL INTENT should we pursue next?

Concrete low-level actions (move/pickup/open_door) are still chosen
by world-specific policy code.
"""

from typing import Dict, Any
import json

from groq import Groq

from agent.loop import format_observation, find_items_in_grid

# ------ KeyDoorWorld intent planner ------

KEYDOOR_SYSTEM_PROMPT = """
You are an intent-level planner for a simple grid-based game called KeyDoorWorld.

World summary:
- The player is on a 2D grid.
- 'K' marks the tile with the key.
- 'D' marks the tile with the locked door.
- The player must first MOVE to the key, PICK IT UP, then MOVE to the door and UNLOCK it.

You do NOT choose low-level tools directly (move, pickup, open_door).
Instead, you output a HIGH-LEVEL INTENT that describes what the agent should try to do next.

You will be given, in the observation:
- `has_key` (True/False)
- `on_key_tile` (True/False)
- `on_door_tile` (True/False)
along with the grid, player position, inventory, and items_in_world.

You MUST treat these booleans as the source of truth.

Allowed intents (choose exactly one):

1. "go_to_key"
   - Use when has_key is False AND on_key_tile is False.
   - Meaning: move in a direction that gets closer to the key.

2. "pickup_key"
   - Use when on_key_tile is True (player is standing on 'K').
   - Meaning: pick up the key into inventory.

3. "go_to_door"
   - Use when has_key is True AND on_door_tile is False.
   - Meaning: move in a direction that gets closer to the door.

4. "unlock_door"
   - Use ONLY when has_key is True AND on_door_tile is True.
   - Meaning: unlock the door.

Hard rules (very important):
- NEVER choose "go_to_door" if has_key is False.
- NEVER choose "unlock_door" unless has_key is True AND on_door_tile is True.
- If these conditions are not satisfied, prefer "go_to_key" or "go_to_door" instead.

You will be given:
- a rendered grid
- the player position
- inventory
- items_in_world (parsed objects for 'key' and 'door')
- has_key, on_key_tile, on_door_tile
- goal + goal_done
- last_action, last_result

Your job:
- Look at the current state (especially has_key / on_key_tile / on_door_tile).
- Decide which ONE of the allowed intents is most appropriate RIGHT NOW.
- Explain briefly why.

Response format (JSON only):
{
  "intent": "<one of: go_to_key | pickup_key | go_to_door | unlock_door>",
  "reason": "<short natural language explanation>"
}

Do NOT return low-level tool calls here.
Do NOT invent new intent names.
"""

def format_intent_observation(obs: Dict[str, Any]) -> str:
    """
    Turn the observation dict into a human-readable string for the LLM.

    We also compute some derived booleans (has_key, on_key_tile, on_door_tile)
    to make reasoning easier and more reliable.
    """
    grid = obs["grid"]
    lines = "\n".join(grid)

    player = obs["player"]
    inventory = obs["inventory"]
    goal = obs["goal"]
    goal_done = obs["goal_done"]

    last_action = obs.get("last_action")
    last_result = obs.get("last_result")

    items_in_world = find_items_in_grid(grid)

    # --- Derived flags for all worlds (mostly useful for KeyDoorWorld) ----
    row = player["row"]
    col = player["col"]

    has_key = inventory.get("key", 0) > 0

    on_key_tile = any(
        it["type"] == "key" and it["row"] == row and it["col"] == col
        for it in items_in_world
    )
    on_door_tile = any(
        it["type"] == "door" and it["row"] == row and it["col"] == col
        for it in items_in_world
    )

    return f"""grid:

{lines}

player: {player}
inventory: {inventory}
items_in_world: {items_in_world}
has_key: {has_key}
on_key_tile: {on_key_tile}
on_door_tile: {on_door_tile}
goal: {goal}
goal_done: {goal_done}
last_action: {last_action}
last_result: {last_result}
"""


def propose_keydoor_intent(client: Groq, obs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ask the LLM to propose a high-level intent for KeyDoorWorld.

    Returns a dict with at least:
        {
            "intent": "...",
            "reason": "..."
        }
    """
    obs_text = format_observation(obs)

    messages = [
        {"role": "system", "content": KEYDOOR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Here is the latest observation of the world:\n\n"
                f"{obs_text}\n\n"
                "Choose ONE intent and respond ONLY with a JSON object."
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
        intent_obj = json.loads(content)
    except json.JSONDecodeError:
        raise RuntimeError(f"Intent planner did not return valid JSON: {content}")
    
    if "intent" not in intent_obj:
        raise RuntimeError(f"Intent planner missing 'intent' field: {intent_obj}")
    
    return intent_obj