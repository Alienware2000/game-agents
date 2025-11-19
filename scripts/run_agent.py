# scripts/run_agent.py
from games.gridworld.core import GridWorld
from agent.tools import Tools
from agent.rule_based import AgentLoop

def main():
    env = GridWorld()

    # Show initial world
    print("=== INITIAL OBS ===")
    first = env.observe()
    for line in first["grid"]:
        print(line)
    print("player:", first["player"])
    print("inventory:", first["inventory"])
    print("goal:", first["goal"])
    print("===================\n")

    tools = Tools(env)
    loop = AgentLoop(tools, max_steps=40)
    result = loop.run()

    print("\n=== LAST 10 STEPS ===")
    for h in result["history"][-10:]:
        print(h)

    print("\nFINAL:")
    print("steps:", result["steps"])
    print("player:", result["observation"]["player"])
    print("inventory:", result["observation"]["inventory"])
    print("goal_done:", result["observation"]["goal_done"])

if __name__ == "__main__":
    main()
