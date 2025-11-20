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

    Supports both:
      - GridWorld: "C" (coal), "S" (stick)
      - KeyDoorWorld: "K" (key), "D" (door)
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
        
