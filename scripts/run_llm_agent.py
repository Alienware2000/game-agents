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

def find_items_in_grid(grid: list[str]) -> list[Dict[str, Any]]:
    """
    Scan the grid and return a list of items with their types and positions.
    This is 'preprocessed perception' for the LLM, so it doesn't have to
    infer positions from ASCII itself.
    """
    items = []
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == "C":
                items.append({"type": "coal", "row": r, "col": c})
            elif ch == "S":
                items.append({"type": "stick", "row": r, "col": c})

    return items

def attach_memory(obs: Dict[str, Any],
                  last_action: Dict[str, Any] | None,
                  last_result: Dict[str, Any] | None) -> Dict[str, Any]:
    obs["last_action"] = last_action
    obs["last_result"] = last_result
    return obs

def format_observation(obs: Dict[str, Any]) -> str:
    """Turn the observation into a human-readable string for the LLM."""
    lines = "\n".join(obs["grid"])
    player = obs["player"]
    inventory = obs["inventory"]
    goal = obs["goal"]
    goal_done = obs["goal_done"]

    # New: short-term memory of what just happened
    last_action = obs.get("last_action")
    last_result = obs.get("last_result")

    # New: structured objects list, computed from the grid
    items_in_world = find_items_in_grid(obs["grid"])

    return f"""grid: 

{lines}

player: {player}
inventory: {inventory}
items_in_world: {items_in_world}
goal: {goal}
goal_done: {goal_done}
last_action: {last_action}
last_result: {last_result} 
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

def suggest_direction_toward_target(player: Dict[str, int],
                                    target: Dict[str, int]) -> str:
    """
    Given player {"row": r, "col": c} and target {"row": tr, "col": tc},
    return a direction string ("up"/"down"/"left"/"right") that moves
    the player one step closer to the target in Manhattan distance.

    This is a tiny navigation helper; the LLM still decides WHICH item
    to chase and WHEN to craft. This just helps with the low-level "step".
    """
    row = player["row"]
    col = player["col"]
    tr = target["row"]
    tc = target["col"]

    # Compute differences
    dr = tr - row
    dc = tc - col

    # If we are already on the target, direction doesn't really matter.
    # We'll just choose an arbitrary direction (it should be overridden
    # by pickup() anyway if we're standing on an item).
    if dr == 0 and dc == 0:
        return "up"

    # Prioritize the axis with the larger absolute difference.
    if abs(dr) >= abs(dc):
        # Move vertically toward target
        if dr < 0:
            return "up"
        else:
            return "down"
    else:
        # Move horizontally toward target
        if dc < 0:
            return "left"
        else:
            return "right"


def enforce_action_constraints(obs: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce hard rules on what actions are allowed in this state.
    If the LLM suggests something illegal or useless, replace it with a safe fallback.

    NEW: If the LLM chooses move(), we use items_in_world and suggest_direction_toward_target
    to steer the movement toward the nearest useful item (coal or stick).
    """
    grid = obs["grid"]
    player = obs["player"]
    inventory = obs["inventory"]
    last_result = obs.get("last_result")
    last_action = obs.get("last_action") or {}

    row = player["row"]
    col = player["col"]

    if 0 <= row < len(grid) and 0 <= col < len(grid[row]):
        tile = grid[row][col]
    else:
        tile = "."

    name = action.get("tool")
    args = action.get("args", {})

    # -------- Rule 1: Cannot pickup if not standing on C or S --------
    if name == "pickup" and tile not in ("C", "S"):
        # Fallback: force a move instead of wasting a turn.
        # We'll refine the direction below using the target logic.
        name = "move"
        args = {"direction": "right"}  # temporary default
        action = {"tool": name, "args": args}

    # -------- Rule 2: Cannot craft torch without coal + stick --------
    if name == "craft":
        if not (inventory.get("coal", 0) >= 1 and inventory.get("stick", 0) >= 1):
            # Not ready to craft torch yet → turn this into a move()
            name = "move"
            args = {"direction": "right"}  # temporary default
            action = {"tool": name, "args": args}

    # -------- NEW: Move toward the nearest relevant item --------
    if name == "move":
        # 1) Decide what we need next
        items_in_world = find_items_in_grid(grid)

        target_type = None
        if inventory.get("coal", 0) < 1:
            target_type = "coal"
        elif inventory.get("stick", 0) < 1:
            target_type = "stick"
        else:
            target_type = None  # we already have everything; LLM can choose craft

        # 2) Find nearest item of that type (if any)
        target_item = None
        if target_type is not None:
            candidates = [it for it in items_in_world if it["type"] == target_type]
            if candidates:
                # Find the candidate with minimal Manhattan distance
                def manhattan(it):
                    return abs(it["row"] - row) + abs(it["col"] - col)
                target_item = min(candidates, key=manhattan)

        # 3) If we have a target, override the direction with a purposeful step
        if target_item is not None:
            best_dir = suggest_direction_toward_target(player, target_item)
            args["direction"] = best_dir
            action = {"tool": "move", "args": args}

    # -------- Rule 3: Don't repeat a blocked move in the same direction --------
    if (
        last_result is not None
        and last_result.get("ok") is False
        and last_result.get("error") == "move blocked"
        and name == "move"
    ):
        last_tool = last_action.get("tool")
        last_args = last_action.get("args", {})
        if last_tool == "move" and last_args.get("direction") == args.get("direction"):
            # Naive heuristic: pick a different direction than the blocked one
            blocked_dir = args.get("direction")
            for d in ["up", "left", "right", "down"]:
                if d != blocked_dir:
                    args["direction"] = d
                    action = {"tool": "move", "args": args}
                    break

    # Return the (possibly modified) action
    return action


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
