"""
Tiny manual tester for KeyDoorWorld.

Allows you to:
- See the grid with walls, key (K), door (D)
- Move with WASD-style commands
- Run 'pickup' to pick up the key
- Run 'open' to open the door (if you have the key and are at the door)

This is purely for human testing and understanding
no LLMs involved.
"""

from games.keydoor.core import KeyDoorWorld

def render_observation(obs: dict) -> None:
    """
    Pretty-print the observation:
    - grid with the player drawn as 'P'
    - inventory
    - goal
    - goal_done
    """

    grid = obs["grid"]
    player = obs["player"]
    inventory = obs["inventory"]
    goal = obs["goal"]
    goal_done = obs["goal_done"]

    # Turn grid strings into mutable lists so we can overlay the player
    grid_chars = [list(row) for row in grid]

    pr = player["row"]
    pc = player["col"]

    # Only overlay if in bounds (defensive programming)
    if 0 <= pr < len(grid_chars) and 0 <= pc < len(grid_chars[0]):
        grid_chars[pr][pc] = "P"

    # Print the grid
    print("\n === KeyDoorWorld ===")
    for row_chars in grid_chars:
        print("".join(row_chars))

    # Print extra info
    print(f"\nPlayer position: (row={pr}, col={pc})")
    print(f"Inventory: {inventory}")
    print(f"Goal: {goal}")
    print(f"Goal done? {goal_done}")
    print("======================\n")

def main() -> None:
    # Create the world
    world = KeyDoorWorld(size=10)

    print("Manual KeyDoorWorld tester.")
    print("Commands:")
    print("   w = move up")
    print("   s = move down")
    print("   a = move left")
    print("   d = move right")
    print("   pickup = pick up key (if on the key)")
    print("   open = open the door (if on door and have key)")
    print("   q = quite\n")

    while True:
        obs = world.observe()
        render_observation(obs)

        if obs["goal_done"]:
            print("🎉 Goal achieved! The door is open. Exiting.")
            break

        cmd = input("Enter command (w/a/s/d, pickup, open, q): ").strip().lower()

        if cmd == "q":
            print("Exiting.")
            break

        # Map simple keys to directions
        if cmd in ("w", "a", "s", "d"):
            if cmd == "w":
                direction = "up"
            elif cmd == "s":
                direction = "down"
            elif cmd == "a":
                direction = "left"
            else:
                direction = "right"
            
            result = world.move(direction)
            print(f"Result: {result}")
        
        elif cmd == "pickup":
            result = world.pickup()
            print(f"Result: {result}")
        
        elif cmd == "open":
            result = world.open_door()
            print(f"Result: {result}")
        
        else:
            print("Unknown command. Please use w/a/s/d, pickup, open or q.")

if __name__ == "__main__":
    main()