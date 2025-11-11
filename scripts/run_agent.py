# scripts/run_agent.py
from games.gridworld.core import GridWorld
from agent.tools import Tools
from agent.loop import AgentLoop

env = GridWorld()
t = Tools(env)
loop = AgentLoop(t, max_steps=8)
result = loop.run()
print("steps:", result["steps"])
print("final player:", result["observation"]["player"])
