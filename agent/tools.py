from typing import Dict
from games.gridworld.core import GridWorld
from games.keydoor.core import KeyDoorWorld

class Tools:
    def __init__(self, env: GridWorld):
        self.env = env

    def observe(self) -> Dict:
        return self.env.observe()

    def move(self, direction: str) -> Dict:
        return self.env.move(direction)
    
    def pickup(self) -> Dict:
        return self.env.pickup()
    
    def craft(self, item: str, qty: int = 1) -> Dict:
        return self.env.craft(item, qty)

class KeyDoorTools:
    """
    Tools wrapper for the KeyDoorWorld environment.

    This mirrors the GridWorld Tools class:
    - Same method naming style
    - Same return conventions (dicts with 'ok', 'error', etc.)
    - Keep agents consistent across different worlds
    """

    def __init__(self, env: KeyDoorWorld):
        self.env = env

    def observe(self) -> Dict:
        return self.env.observe()
    
    def move(self, direction: str) -> Dict:
        return self.env.move(direction)
    
    def pickup(self) -> Dict:
        return self.env.pickup()
    
    def open_door(self) -> Dict:
        return self.env.open_door()