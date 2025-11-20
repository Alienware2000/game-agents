"""
Shared helper functions for agent loops.

These functions are intentionally backend-agnostic:
they only care about the *observation* dictionary and the *action* dict.

They do NOT reach into GridWorld or MCP directly.
"""

from typing import Dict, Any, Optional, List


def find_items_in_grid(grid: List[str]) -> List[Dict[str, Any]]:
    """
    Scan the grid (list of strings) and return a list of items
    with their types and positions.

    Example return value:
        [
            {"type": "coal", "row": 1, "col": 4},
            {"type": "stick", "row": 3, "col": 1}
        ]
    """
    items: List[Dict[str, Any]] = []
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == "C":
                items.append({"type": "coal", "row": r, "col": c})
            elif ch == "S":
                items.append({"type": "stick", "row": r, "col": c})
            elif ch == "K":
                items.append({"type": "key", "row": r, "col": c})
            elif ch == "D":
                items.append({"type": "door", "row": r, "col": c})
    return items

def attach_memory(
        obs: Dict[str, Any],
        last_action: Optional[Dict[str, Any]],
        last_result: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Attach short-term memory field into the observation.

    This lets the LLM see what happened on the previous step.
    """
    obs["last_action"] = last_action
    obs["last_result"] = last_result
    return obs

def format_observation(obs: Dict[str, Any]) -> str:
    """
    Turn the observation dict into a human-readable string for the LLM.

    This is where we:
    - render the ASCII grid
    - show player + inventory
    - compute items_in_world using find_items_in_grid
    - show goal + memory (last_action/last_result)
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

def reflex_action(obs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Simple hard-coded reflexes that run before the LLM:

    - If the plyer is standing on C or S, always pickup().
    - (Optional later) if inventory has coal + stick, craft a torch.

    Returns:
        - an action dict: {"tool": "...", "args": {...}} if a reflex fires
        - None if no reflex should be applied
    """
    grid = obs["grid"]
    player = obs["player"]
    inventory = obs["inventory"] # kept for future reflexes

    row = player["row"]
    col = player["col"]

    # Defensive check: make sure row/col are in range
    if 0 <= row < len(grid) and 0 <= col < len(grid[row]):
        tile = grid[row][col]
    else:
        tile = "."
    
    # Reflex 1: standing on an item? Always pick it up.
    # Works for both GridWorld (C, S) and KeyDoorWorld (K).
    if tile in ("C", "S", "K"):
        return {"tool": "pickup", "args": {}}
    
    # (Optional Reflex 2: auto-craft when ready)
    if inventory.get("coal", 0) >= 1 and inventory.get("stick", 0) >= 1 and inventory.get("torch", 0) < 1:
         return {"tool": "craft", "args": {"item": "torch", "qty": 1}}
    
    # Reflex 2: in KeyDoorWorld, if we are standing on the door tile
    # and we already have the key, auto-open the door.
    if tile == "D" and inventory.get("key", 0) >= 1:
        return {"tool": "open_door", "args": {}}

    return None # no reflex triggered

def suggest_direction_toward_target(
        player: Dict[str, int],
        target: Dict[str, int]
) -> str:
    """
    Given player {"row": r, "col": c} and target {"row": tr, "col": tc},
    return a direction string ("up"/"down"/"left"/"right") that moves the
    player one step closer to the target in Manhattan distance.

    This is a tiny navigation helper; the LLM still decides WHICH item to chase
    and WHEN to craft. This just helps with the low-level step.
    """

    row = player["row"]
    col = player["col"]
    tr = target["row"]
    tc = target["col"]

    dr = tr - row
    dc = tc - col

    # Already on the target tile
    if dr == 0 and dc == 0:
        # Arbitrary default; usually overridden by pickup()
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
    Enforce hard rules on what action are allowed in this state.

    If the LLM suggests something illegal or useless, we replace it with a 
    safe fallback.

    Also:
    - use items_in_world and suggest_direction_toward_target
      to steer move() actions toward the nearest useful item.
    - Avoid repeating blocked moves in the same direction.
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
    # GridWorld items: C (coal), S (stick)
    # KeyDoorWorld item: K (key)
    if name == "pickup" and tile not in ("C", "S", "K"):
        # Turn this into a move; we'll refine the direction below.
        name = "move"
        args = {"direction": "right"}  # temporary default
        action = {"tool": name, "args": args}

    # -------- Rule 2: Cannot craft torch without coal + stick --------
    if name == "craft":
        if not (inventory.get("coal", 0) >= 1 and inventory.get("stick", 0) >= 1):
            name = "move"
            args = {"direction": "right"}  # temporary default
            action = {"tool": name, "args": args}

    # -------- Move toward the nearest relevant item --------
    if name == "move":
        # 1) Decide what we need next
        items_in_world = find_items_in_grid(grid)
        goal = obs.get("goal", {})
        goal_action = goal.get("action")

        target_type = None

        if goal_action == "craft":
            # GridWorld mode: get coal then stick
            if inventory.get("coal", 0) < 1:
                target_type = "coal"
            elif inventory.get("stick", 0) < 1:
                target_type = "stick"
            else:
                target_type = None  # we already have everything we need to craft
    
        elif goal_action == "unlock":
            #KeyDoorWorld mode: get key, then go to door
            if inventory.get("key", 0) < 1:
                target_type = "key"
            else:
                target_type = "door"
                
        # 2) Find nearest item of that type (if any)
        target_item = None
        if target_type is not None:
            candidates = [it for it in items_in_world if it["type"] == target_type]
            if candidates:
                def manhattan(it: Dict[str, Any]) -> int:
                    return abs(it["row"] - row) + abs(it["col"] - col)

                target_item = min(candidates, key=manhattan)

        # 3) If we have a target, override direction with a purposeful step
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
            blocked_dir = args.get("direction")
            # Naive heuristic: pick a different direction
            for d in ["up", "left", "right", "down"]:
                if d != blocked_dir:
                    args["direction"] = d
                    action = {"tool": "move", "args": args}
                    break

    return action