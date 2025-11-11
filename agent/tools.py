from typing import Dict
from games.gridworld.core import GridWorld

class Tools:
    def __init__(self, env: GridWorld):
        self.env = env

    def observe(self) -> Dict:
        return self.env.observe()

    def move(self, direction: str) -> Dict:
        return self.env.move(direction)
    