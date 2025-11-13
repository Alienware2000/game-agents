from typing import Dict, List
from agent.tools import Tools

class AgentLoop:
    def __init__(self, tools: Tools, max_steps: int = 20):
        self.t = tools
        self.max_steps = max_steps

    def run(self) -> Dict:
        # plan is a list like [{"tool":"move","args":{"direction":"right"}}, ...]
        obs = self.t.observe()
        history: List[Dict] = []
        steps = 0

        while steps < self.max_steps:
            action = self._plan(obs, steps)
            result = self._dispatch(action)
            history.append({"action": action, "result": result})
            obs = self.t.observe()
            steps += 1

            if obs.get("goal_done"):
                break
        
        return {"steps": steps, "observation": obs, "history": history}
    
    def _dispatch(self, action: Dict) -> Dict:
        name = action["tool"]
        args = action.get("args", {})
        if name == "move":
            return self.t.move(**args)
        if name == "pickup":
            return self.t.pickup()
        if name == "craft":
            return self.t.craft(**args)
        if name == "observe":
            return {"ok": True, "observation": self.t.observe()}
        
        return {"ok": False, "error": f"unknown tool {name}"}
    
    def _plan(self, obs: Dict, step: int) -> Dict:
        # If goal is done, just observe (no-op)
        if obs.get("goal_done"):
            return {"tool": "observe"}

        # Basic info from observation
        grid = obs["grid"]
        pr, pc = obs["player"]["row"], obs["player"]["col"]
        inv = obs["inventory"]

        # What resources do we still need? Do we need coal or stick? 
        need_coal = inv.get("coal", 0) < 1
        need_stick = inv.get("stick", 0) < 1

        # Scan grid for visible item locations
        coal_locs = []
        stick_locs = []

        for r, line in enumerate(grid):
            for c, ch in enumerate(line):
                if ch == "C":
                    coal_locs.append((r, c))
                if ch == "S":
                    stick_locs.append((r, c)) 

        # Navigation helper
        def move_toward(src, dst):
            sr, sc = src; dr, dc = dst
            if sr < dr: return {"tool": "move", "args": {"direction": "down"}}
            if sr > dr: return {"tool": "move", "args": {"direction": "up"}}
            if sc < dc: return {"tool": "move", "args": {"direction": "right"}}
            if sc > dc: return {"tool": "move", "args": {"direction": "left"}}
            return None  # already there
        
        # 1) If we still need coal, go to coal and pick it up
        if need_coal:
            # If we SEE coal
            if coal_locs:
                target = coal_locs[0]

                # If we're not standing on it, walk toward it
                if (pr, pc) != target:
                    nxt = move_toward((pr, pc), target)
                    if nxt: return nxt

                # If already on it -> pick it up
                return {"tool": "pickup"}
            
            directions = ["right", "down", "left", "up"]
            return {"tool": "move", "args": {"direction": directions[step % 4]}}
        
        # If we still need stick, go to stick and pick it up
        if need_stick:
            if stick_locs:
                target = stick_locs[0]

                if (pr, pc) != target:
                    nxt = move_toward((pr, pc), target)
                    if nxt: return nxt

                return {"tool": "pickup"}
            
            # Stick not visible? explore
            return {"tool": "move", "args": {"direction": ["right","down","left","up"][step % 4]}}

        # 3) If both items collected → craft
        return {"tool": "craft", "args": {"item": "torch", "qty": 1}}
