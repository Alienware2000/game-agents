import os
from typing import Dict, Any

from groq import Groq

from games.keydoor.core import KeyDoorWorld
from agent.tools import KeyDoorTools
from agent.loop import attach_memory
from agent.intent import propose_keydoor_intent, format_intent_observation
from agent.policies.keydoor_policy import (
    reflex_action,
    enforce_action_constraints,
    intent_to_action_keydoor
)

def dispatch(tools: KeyDoorTools, action: Dict[str, Any]) -> Dict[str, Any]:
    """Map an action dict to actual environment calls."""
    name = action["tool"]
    args = action.get("args", {})

    if name == "move":
        return tools.move(**args)
    if name == "pickup":
        return tools.pickup()
    if name == "open_door":
        return tools.open_door()
    
    # Fallback
    return {"ok": False, "error": f"unknown tool {name}"}

def main():
    # 1. LLM client
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    # 2. Environment + tools
    env = KeyDoorWorld()
    tools = KeyDoorTools(env)

    # 3. Initial observation
    obs = env.observe()
    last_action: Dict[str, Any] | None = None
    last_result: Dict[str, Any] | None = None

    print("=== INITIAL KEYDOOR WORLD (INTENT PLANNER) ===")
    print(format_intent_observation(obs))
    print("==============================================\n")

    max_steps = 40
    history = []

    for step in range(max_steps):
        if obs.get("goal_done"):
            print(f"Goal already done at step {step}!")
            break

        print(f"\n=== STEP {step} ===")

        # Attach memory so reflex + intent planner can see it
        obs = attach_memory(obs, last_action, last_result)

        # 1) Reflex first (cheap, local logic)
        action = reflex_action(obs)
        if action is not None:
            print("Reflex chose action:", action)
        else:
            # 2) Intent-level LLM planning
            try:
                intent_obj = propose_keydoor_intent(client, obs)
                print("LLM proposed intent:", intent_obj)

                action = intent_to_action_keydoor(obs, intent_obj)
                print("Mapped intent -> action:", action)
            except Exception as e:
                print("Error in intent planning:", e)
                break
        
        # 3) World-specific constraints
        action = enforce_action_constraints(obs, action)
        print("Action after constraints:", action)

        # 4) Dispatch to environment
        result = dispatch(tools, action)
        print("Result:", result)

        history.append({"action": action, "result": result})

        last_action = action
        last_result = result

        # 5) New observation
        obs = env.observe()
        obs = attach_memory(obs, last_action, last_result)

        print("New observation:")
        print(format_intent_observation(obs))

        if obs.get("goal_done"):
            print(f"\n🎉 Goal achieved at step {step + 1}!")
            break

    print("\n=== FINAL STATE (KEYDOOR, INTENT PLANNER) ===")
    print(format_intent_observation(obs))
    print("Steps taken:", len(history))


if __name__ == "__main__":
    main()

