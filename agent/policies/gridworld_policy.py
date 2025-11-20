from typing import Dict, Any, Optional

from agent.loop import find_items_in_grid, suggest_direction_toward_target

def reflex_action(obs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Gridworld specific reflexes.

    - If the player is standing on C or S, always pickup().
    - Optional: could auto craft when inventory has coal + stick.
    """
    grid = obs["grid"]
    player = obs["player"]
    inventory = obs["inventory"] # kept for future reflexes

    row = player["row"]
    col = player["col"]

    if 0 <= row < len(grid) and 0 <= col < len(grid[row]):
        tile = grid[row][col]
    else:
        tile = "."

    # Reflex 1: standing on an item tile? Always pick it up.
    if tile in ("C", "S"):
        return {"tool": "pickup", "args": {}}
    
    # Example future reflex:
    # if inventory.get("coal", 0) >= 1 and inventory.get("stick", 0) >= 1 and inventory.get("torch", 0) < 1:
    #   return {"tool": "craft", "args": {"item": "torch", "qty": 1}}

    return None

def enforce_action_constraints(obs: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gridworld specific hard constraints and small navigation heuristics.

    - Do not pickup unless on C or S.
    - Do not craft without enough coal + stick.
    - Nudge move() actions toward coal first, then stick.
    - Avoid repeating the same blocked move direction.
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

    # Rule 1: cannot pickup if not standing on C or S
    if name == "pickup" and tile not in ("C", "S"):
        name = "move"
        args = {"direction": "right"}  # temporary default
        action = {"tool": name, "args": args}

    # Rule 2: cannot craft torch without coal + stick
    if name == "craft":
        has_coal = inventory.get("coal", 0) >= 1
        has_stick = inventory.get("stick", 0) >= 1
        if not (has_coal and has_stick):
            name = "move"
            args = {"direction": "right"}  # temporary default
            action = {"tool": name, "args": args}

    # Rule 3: move toward the nearest relevant item (coal then stick)
    if name == "move":
        items_in_world = find_items_in_grid(grid)

        target_type = None
        if inventory.get("coal", 0) < 1:
            target_type = "coal"
        elif inventory.get("stick", 0) < 1:
            target_type = "stick"
        else:
            target_type = None  # ready to craft

        target_item = None
        if target_type is not None:
            candidates = [it for it in items_in_world if it["type"] == target_type]
            if candidates:
                def manhattan(it: Dict[str, Any]) -> int:
                    return abs(it["row"] - row) + abs(it["col"] - col)

                target_item = min(candidates, key=manhattan)

        if target_item is not None:
            best_dir = suggest_direction_toward_target(player, target_item)
            args["direction"] = best_dir
            action = {"tool": "move", "args": args}

    # Rule 4: do not repeat a blocked move in the same direction
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
            for d in ["up", "left", "right", "down"]:
                if d != blocked_dir:
                    args["direction"] = d
                    action = {"tool": "move", "args": args}
                    break

    return action

