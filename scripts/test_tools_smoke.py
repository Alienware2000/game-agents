from games.gridworld.core import GridWorld
from agent.tools import Tools

env = GridWorld()
t = Tools(env)
print(t.observe()["player"])
print(t.move("right"))
print(t.observe()["player"])