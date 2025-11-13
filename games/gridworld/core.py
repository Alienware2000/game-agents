from typing import Dict, Tuple, List

# Define types for clarity
Coord = Tuple[int, int]
TITLE_EMPTY = "."
TITLE_WALL = "#"
TITLE_PLAYER = "P"
RECIPES = {
    "torch": {"coal": 1, "stick": 1}
}

# Define the GridWorld environment
class GridWorld:
    def __init__(self, size: int = 10):
        self.size = size # Size of the grid
        self.grid = [[TITLE_EMPTY for _ in range(size)] for _ in range(size)] # Initialize empty grid
        
        # Set up walls around the grid
        for i in range(size):
            self.grid[0][i] = TITLE_WALL
            self.grid[size-1][i] = TITLE_WALL
            self.grid[i][0] = TITLE_WALL
            self.grid[i][size-1] = TITLE_WALL

        self.player: Coord = (1, 1) # Starting position of the player
        r, c = self.player
        self.grid[r][c] = TITLE_PLAYER
        self.inventory: Dict[str, int] = {}
        self.items_on_floor = {
            (1, 4) : ["coal"],
            (3, 1) : ["stick"]
        }
        self.goal = {"action": "craft", "item": "torch", "qty": 1}

    # Check if a coordinate is within bounds
    def _in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.size and 0 <= c < self.size
    
    # Check if a coordinate is free (not a wall)
    def _is_free(self, r: int, c: int) -> bool:
        return self._in_bounds(r, c) and self.grid[r][c] != TITLE_WALL
    
    # Observe the current state of the gridworld
    def observe(self) -> Dict:
        view = []
        for row in range(self.size):
            line = ""
            for col in range(self.size):
                if (row, col) == self.player:
                    line += "P"
                elif self.grid[row][col] == "#":
                    line += "#"
                elif (row, col) in self.items_on_floor:
                    # show first item letter
                    line += self.items_on_floor[(row, col)][0][0].upper()
                else:
                    line += "."
                view.append(line)
        return {
            "grid": view,
            "player": {"row": self.player[0], "col": self.player[1]},
            "inventory": dict(self.inventory),
            "goal": self.goal,
            "goal_done": self._goal_done()
        }

    # Move the player in a specified direction
    def move(self, direction: str) -> bool:
        # Define movement deltas
        dir_map = {
            "up": (-1, 0),
            "down": (1, 0),
            "left": (0, -1),
            "right": (0, 1)
        }

        if direction not in dir_map:
            return {"ok": False, "error": f"bad direction {direction}"}
        
        # Calculate new position
        dr, dc = dir_map[direction]
        r, c = self.player
        new_r, new_c = r + dr, c + dc

        if not self._is_free(new_r, new_c):
            return {"ok": False, "error": "move blocked"}
        
        # Update player position
        self.grid[r][c] = TITLE_EMPTY
        self.player = (new_r, new_c)
        self.grid[new_r][new_c] = TITLE_PLAYER
        return {"ok": True, "player": {"row": new_r, "col": new_c}}
    
    # Pick up on object in the environment
    def pickup(self) -> Dict:
        pos = self.player
        items = self.items_on_floor.get(pos, [])
        if not items:
            return {"ok": False, "error": "nothing to pickup"}
        picked = items.pop(0)
        if not items:
            self.items_on_floor.pop(pos, None)
        self.inventory[picked] = self.inventory.get(picked, 0) + 1
        return {"ok": True, "picked": picked, "inventory": dict(self.inventory)}
    
    def _goal_done(self) -> bool:
        g = self.goal
        if g["action"] == "craft":
            return self.inventory.get(g["item"], 0) >= g["qty"]
        return False
    
    # Craft an item
    def craft(self, item: str, qty: int = 1) -> Dict:
        if item not in RECIPES:
            return {"ok": False, "error": f"no recipe for {item}"}
        recipe = RECIPES[item]
        
        # verify resources
        for res, need in recipe.items():
            if self.inventory.get(res, 0) < need * qty:
                return {"ok": False, "error": "insufficient materials"}
        
        # consume
        for res, need in recipe.items():
            self.inventory[res] -= need * qty

        # produce
        self.inventory[item] = self.inventory.get(item, 0) + qty
        return {"ok": True, "crafted": {item: qty}, "inventory": dict(self.inventory), "goal_done": self._goal_done()}

    