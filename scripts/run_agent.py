from games.gridworld.core import GridWorld
from agent.tools import Tools
from agent.loop import AgentLoop

env = GridWorld()
t = Tools(env)
loop = AgentLoop(t, max_steps=10)

plan = [
    {"tool":"move","args":{"direction":"right"}},
    {"tool":"move","args":{"direction":"right"}},
    {"tool":"move","args":{"direction":"down"}},
    {"tool":"observe"}
]

result = loop.run(plan)
print("steps:", result["steps"])
print("final player:", result["observation"]["player"])
print("last 2 actions:")
for h in result["history"][-2:]:
    print(h)

