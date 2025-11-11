from typing import Dict, List
from agent.tools import Tools

class AgentLoop:
    def __init__(self, tools: Tools, max_steps: int = 20):
        self.t = tools
        self.max_steps = max_steps

    def run(self, plan: List[Dict]) -> Dict:
        # plan is a list like [{"tool":"move","args":{"direction":"right"}}, ...]
        obs = self.t.observe()
        history = []
        steps = 0
        for action in plan:
            if steps >= self.max_steps:
                break
            result = self._dispatch(action)
            history.append({"action": action, "result": result})
            obs = self.t.observe()
            steps += 1
        
        return {"steps": steps, "observation": obs, "history": history}
    
    def _dispatch(self, action: Dict) -> Dict:
        name = action["tool"]
        args = action.get("args", {})
        if name == "move":
            return self.t.move(**args)
        if name == "observe":
            return {"ok": True, "observation": self.t.observe()}
        
        return {"ok": False, "error": f"unknown tool {name}"}