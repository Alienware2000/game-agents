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
        if name == "pickup":
            return self.t.pickup()
        if name == "craft":
            return self.t.craft(**args)
        
        return {"ok": False, "error": f"unknown tool {name}"}
    
    def _plan(self, obs: Dict, step: int) -> Dict:
        # 1) If goal is done, just observe (no-op)
        if obs.get("goal_done"):
            return {"tool": "observe"}
        
        # 2) If we already have resources, craft the torch
        inv = obs.get("inventory", {})
        need_coal = inv.get("coal", 0) < 1
        need_stick = inv.get("stick", 0) < 1

        # Hardcoded coordinates for M3A (we'll remove this crutch in M3B)
        coal_pos = (1, 4)
        stick_pos = (3, 1)
        me = (obs["player"]["row"], obs["player"]["col"])

        def move_toward(src, dst):
            sr, sc = src; dr, dc = dst
            if sr < dr: return {"tool": "move", "args": {"direction": "down"}}
            if sr > dr: return {"tool": "move", "args": {"direction": "up"}}
            if sc < dc: return {"tool": "move", "args": {"direction": "right"}}
            if sc > dc: return {"tool": "move", "args": {"direction": "left"}}
            return None  # already there
        
        # 3) If we still need coal, go to coal and pick it up
        if need_coal:
            if me != coal_pos:
                nxt = move_toward(me, coal_pos)
                if nxt: return nxt
            return {"tool": "pickup"}
        
        # If we still need stick, go to stick and pick it up
        if need_stick:
            if me != stick_pos:
                nxt = move_toward(me, stick_pos)
                if nxt: return nxt
            return {"tool": "pickup"}
        
        return {"tool": "craft", "args": {"item": "torch", "qty": 1}}
