from typing import Dict, Any, Optional

from agent.loop import find_items_in_grid, suggest_direction_toward_target


def reflex_action(obs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    KeyDoorWorld specific reflexes.

    - If the player is standing on K, auto pickup().
    - If the player is standing on D and has the key, auto open_door().
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

    # Standing on key? Always pick it up.
    if tile == "K":
        return {"tool": "pickup", "args": {}}

    # Standing on door with key in inventory? Open it.
    if tile == "D" and inventory.get("key", 0) >= 1:
        return {"tool": "open_door", "args": {}}

    return None


def enforce_action_constraints(obs: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
    """
    KeyDoorWorld specific constraints and navigation:

    - Do not pickup unless standing on K.
    - Only open_door when standing on D and holding the key.
    - Move toward key first, then toward door.
    - Avoid repeating blocked moves.
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

    # Rule 1: cannot pickup if not standing on K
    if name == "pickup" and tile != "K":
        name = "move"
        args = {"direction": "right"}  # temporary default
        action = {"tool": name, "args": args}

    # Rule 2: cannot open_door unless standing on D with key in inventory
    if name == "open_door":
        has_key = inventory.get("key", 0) >= 1
        if (tile != "D") or (not has_key):
            name = "move"
            args = {"direction": "right"}  # temporary default
            action = {"tool": name, "args": args}

    # Rule 3: guide movement toward "key" first, then "door"
    if name == "move":
        items_in_world = find_items_in_grid(grid)

        if inventory.get("key", 0) < 1:
            target_type = "key"
        else:
            target_type = "door"

        target_item = None
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
