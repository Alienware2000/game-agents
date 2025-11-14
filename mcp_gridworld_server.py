"""
MCP server that exposes our GridWorld game as tools.

This lets an LLM-powered host (ChatGPT, Claude, etc.)
call:
    - observe()
    - move(direction)
    - pickup()
    - craft(item, qty)
over the Model Context Protocol.
"""

from typing import Dict, Any

from mcp.server.fastmcp import FastMCP # official MCP Python SDK
from games.gridworld.core import GridWorld

# 1) Create the MCP server instance.
#    The name is what hosts will see when they list servers.
mcp = FastMCP("game-agents-gridworld")

# 2) Create a single Gridworld instance for this server process.
#    For now, we keep it simple: one world per server.
env = GridWorld()

# 3) Expose tools
# Each @mcp.tool() function becomes a callable MCP tool
# with a JSON schema inferred from type hints and docstrings.

@mcp.tool()
def observe() -> Dict[str, Any]:
    """
    Get the current observation of the GridWorld.

    Returns a dictionary with:
        - grid: list of strings (each a row)
        - player: {'row': int, 'col': int}
        - inventory: {item_name: count}
        - goal: description of the current goal
        - goal_done: bool indicating whether the goal is satisfied
    """
    return env.observe()

@mcp.tool()
def move(direction: str) -> Dict[str, Any]:
    """
    Move the player in the given direction.

    direction:
        One of "up", "down", "left", "right".

    Returns a result dict from env.move(), typically:
        - ok: bool
        - error: optional string if move is blocked
        - player: updated position if successful
    """
    return env.move(direction)

@mcp.tool()
def pickup() -> Dict[str, Any]:
    """
    Pick up an item at the player's current position, if any.

    Returns a dict, e.g.:
        - ok: bool
        - picked: name of the item picked up (if any)
        - inventory: updated inventory snapshot
    """
    return env.pickup()

@mcp.tool()
def craft(item: str, qty: int = 1) -> Dict[str, Any]:
    """
    Craft an item from the player's inventory, if a recipe exists.

    Arguments:
        item: name of the item to craft (e.g., "torch")
        qty: how many to craft (default 1)

    Returns a dict, e.g.:
        - ok: bool
        - crafed: {item_name: qty} on success
        - inventory: updated inventory
        - goal_done: whether the goal has been satisfied
    """
    return env.craft(item=item, qty=qty)

# 4) Entrypoint.
# When this file is run directly (e.g., via `mcp dev`),
# start the MCP server event loop.
if __name__ == "__main__":
    mcp.run()