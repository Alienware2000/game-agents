from typing import Dict, List
from agent.tools import Tools

class AgentLoop:
    def __init__(self, tools: Tools, max_steps: int = 20):
        self.t = tools
        self.max_steps = max_steps

    def run(self) -> Dict:
        # plan is a list like [{"tool":"move","args":{"direction":"right"}}, ...]
        obs = self.t.observe()
        history = []
        steps = 0

        while steps < self.max_steps:
            action = self._plan(obs, steps)
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
    
    def _plan(self, obs: Dict, step: int) -> Dict:
        dirs = ["right", "right", "down", "down", "left", "up"]
        d = dirs[step % len(dirs)]
        return {"tool": "move", "args": {"direction": d}}