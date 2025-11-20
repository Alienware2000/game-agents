from typing import Dict, Tuple, List

# Type alias for coordinates (row, col)
Coord = Tuple[int, int]

# Tile constants (similar style to GridWorld)
TITLE_EMPTY = "."
TITLE_WALL = "#"
TITLE_PLAYER = "P" # we track player separately but keep this for completeness
TITLE_KEY = "K"
TITLE_DOOR = "D"

class KeyDoorWorld:
    def __init__(self, size: int = 10):
        """Simple world: player must pick up a key and open a door"""
        self.size = size

        # Base grid: empty tiles
        self.grid: List[List[str]] = [
            [TITLE_EMPTY for _ in range(size)] for _ in range(size)
        ]

        # Add walls around the border (same as GridWorld)
        for i in range(size):
            self.grid[0][i] = TITLE_WALL
            self.grid[size - 1][i] = TITLE_WALL
            self.grid[i][0] = TITLE_WALL
            self.grid[i][size - 1] = TITLE_WALL
        
        # Player start position (inside the walls)
        self.player: Coord = (1, 1)

        # Key and door positions (Tweakable)
        self.key_pos: Coord = (2, 3)
        self.door_pos: Coord = (size - 2, size - 2) # e.g. bottom-right inside walls

        # Inventory: track whether we have the key
        self.inventory: Dict[str, int] = {"key": 0}

        # Door state
        self.door_open: bool = False

        # Goal structure (mirrows GridWorld style)
        self.goal = {"action": "unlock", "item": "door"}

    # ---------------- Internal Helpers ----------------------

    def _in_bounds(self, r: int, c: int) -> bool:
        """Check if (r, c) is inside the grid."""
        return 0 <= r < self.size and 0 <= c < self.size
    
    def _is_free(self, r: int, c: int) -> bool:
        """
        A tile is free if:
        - it's inside the grid AND
        - it's not a wall.
        The door tile is walkable; the "locked" behavior is handled by open_door().
        """
        return self._in_bounds(r, c) and self.grid[r][c] != TITLE_WALL
    
    def _goal_done(self) -> bool:
        """The goal is done when the door has been opened."""
        return self.door_open
    
    # ---------------- Public API: environment actions & observations ----------------------
    def observe(self) -> Dict:
        """
        Build an observation similar to GridWorld.observe():
        - 'grid': list of strings with walls, key, door, empty floor
        - 'player': {row, col}
        - 'inventory': {"key": or 1}
        - 'goal': goal dict
        - ' goal_done': bool
        """
        view: List[str] = []

        for row in range(self.size):
            line = ""

            for col in range(self.size):
                pos = (row, col)

                # Walls from the underlying grid
                if self.grid[row][col] == TITLE_WALL:
                    line += TITLE_WALL
                
                # Key (only if it hasn't been picked up yet)
                elif self.key_pos is not None and pos == self.key_pos:
                    line += TITLE_KEY

                # Door (regardless of open/closed; logic handled elsewhere)
                elif pos == self.door_pos:
                    line += TITLE_DOOR

                # Everything else is empty floor
                else:
                    line += TITLE_EMPTY
                
            view.append(line)

        return {
            "grid": view,
            "player": {"row": self.player[0], "col": self.player[1]},
            "inventory": dict(self.inventory),
            "goal": self.goal,
            "goal_done": self._goal_done()
        }

    def move(self, direction: str) -> Dict:
        """
        Move the player one tile in the given direction.
        Returns a dict with:
        - ok: bool
        - error: message (if any)
        - player: new postion (on success)
        """

        dir_map = {
            "up": (-1, 0),
            "down": (1, 0),
            "left": (0, -1),
            "right": (0, 1)
        }

        if direction not in dir_map:
            return {"ok": False, "error": f"bad {direction}"}
        
        dr, dc = dir_map[direction]
        r, c = self.player
        new_r, new_c = r + dr, c + dc

        # Can't walk through walls or outside grid
        if not self._is_free(new_r, new_c):
            return {"ok": False, "error": "move blocked"}
        
        # Update player postion
        self.player = (new_r, new_c)
        return {"ok": True, "player": {"row": new_r, "col": new_c}}
    
    def pickup(self) -> Dict:
        """
        Pick up the key if the player is standing on it.
        - On success: inventory['key] becomes 1, key disappears from the map.
        """
        if self.key_pos is None:
            return {"ok": False, "error": "nothing to pickup"}
        
        if self.player != self.key_pos:
            return {"ok": False, "error": "nothing to pickup"}
        
        # Take the key
        self.key_pos = None
        self.inventory["key"] = 1

        return {
            "ok": True,
            "picked": "key",
            "inventory": dict(self.inventory)
        }
    
    def open_door(self) -> Dict:
        """
        Open the door if:
        - the player is standing on the door tile, and 
        - the player has the key.
        """
        if self.player != self.door_pos:
            return {"ok": False, "error": "not at the door"}
        
        if self.inventory.get("key", 0) < 1:
            return {"ok": False, "error": "door locked (no key)"}
        
        if self.door_open:
            # Already opened; not really an error, but nothing to do.
            return {"ok": True, "door_open": True, "goal_done": self._goal_done()}
        
        # Open the door and mark goal as done
        self.door_open = True
        return {"ok": True, "door_open": True, "goal_done": self._goal_done()}
    
    def reset(self) -> None:
        """Reset the world to its initial configuration."""
        self.player = (1, 1)
        self.key_pos = (2, 3)
        self.door_pos = (self.size - 2, self.size - 2)
        self.inventory = {"key": 0}
        self.door_open = False