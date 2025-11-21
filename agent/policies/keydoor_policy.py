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

def intent_to_action_keydoor(obs: Dict[str, Any], intent_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate a high-level intent for KeyDoorWorld into a concrete tool call.

    The intent_obj is expected to have:
        {
          "intent": "go_to_key" | "pickup_key" | "go_to_door" | "unlock_door",
          "reason": "..."
        }

    Returns an action dict of the form:
        {"tool": "<name>", "args": {...}}
    """

    intent = intent_obj.get("intent")
    player = obs["player"]
    grid = obs["grid"]
    inventory = obs["inventory"]

    items = find_items_in_grid(grid)
    key_tiles = [it for it in items if it["type"] == "key"]
    door_tiles = [it for it in items if it["type"] == "door"]

    row = player["row"]
    col = player["col"]

    on_door_tile = any(
        it["type"] == "door" and it["row"] == row and it["col"] == col
        for it in items
    )

    # Helper to choose a direction toward some target list
    def move_toward_first(target_list):
        if not target_list:
            # If we somehow have no target, default to a harmless move.
            return {"tool": "move", "args": {"direction": "right"}}
        target = target_list[0]
        direction = suggest_direction_toward_target(player, target)
        return {"tool": "move", "args": {"direction": direction}}

    # ---- Intent cases -----------------------------------------------------

    if intent == "go_to_key":
        return move_toward_first(key_tiles)

    if intent == "pickup_key":
        return {"tool": "pickup", "args": {}}

    if intent == "go_to_door":
        return move_toward_first(door_tiles)

    if intent == "unlock_door":
        # Safety: if we are not actually on the door, treat this as "go_to_door".
        if not on_door_tile or inventory.get("key", 0) <= 0:
            return move_toward_first(door_tiles)
        return {"tool": "open_door", "args": {}}

    # Fallback: unknown intent -> harmless move
    return {"tool": "move", "args": {"direction": "right"}}