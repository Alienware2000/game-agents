from games.gridworld.core import GridWorld

# Initialize environment
env = GridWorld(size=10)

def print_view(ob):
    print("\n".join(ob["grid"]))
    p = ob["player"]
    print(f"player: ({p['row']}, {p['col']})")
    print("-"*16)

for d in ["right", "right", "down", "down", "left", "up"]:
    print_view(env.observe())
    out = env.move(d)
    print(d, out)

print_view(env.observe())