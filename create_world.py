import os
from dotenv import load_dotenv, find_dotenv
import json
from agents.world_builder import WorldBuilderAgent

def load_env():
    _ = load_dotenv(find_dotenv())

def get_together_api_key():
    load_env()
    together_api_key = os.getenv("TOGETHER_API_KEY")
    return together_api_key

def create_initial_world():
    """Create the initial world structure with start message."""
    api_key = get_together_api_key()
    world_builder = WorldBuilderAgent(api_key)
    
    try:
        # Generate the basic world
        world = world_builder.generate_world(
            "cities built on massive beasts known as Colossi"
        )

        # Generate kingdoms
        kingdoms = world_builder.generate_kingdoms(world)
        world['kingdoms'] = kingdoms

        # For each kingdom, generate towns
        for kingdom_name, kingdom in kingdoms.items():
            print(f"\nGenerating towns for {kingdom_name}...")
            towns = world_builder.generate_towns(world, kingdom)
            kingdom['towns'] = towns

            # For each town, generate NPCs
            for town_name, town in towns.items():
                print(f"Generating NPCs for {town_name}...")
                npcs = world_builder.generate_npcs(world, kingdom, town)
                town['npcs'] = npcs

        # Add starting character and message
        # Pick first town's first NPC as the player character
        first_kingdom = list(kingdoms.values())[0]
        first_town = list(first_kingdom['towns'].values())[0]
        player_character = list(first_town['npcs'].values())[0]

        # Create start message
        start_message = f"""You are {player_character['name']}, {player_character['description']} 
        You stand in the midst of {first_town['name']}, {first_town['description']}"""
        
        world['start'] = start_message

        return world

    except Exception as e:
        print(f"Error creating world: {str(e)}")
        return None

def save_world(world, filename):
    """Save world data to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(world, f, indent=2)
        print(f"World saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving world: {str(e)}")
        return False

def load_world(filename):
    """Load world data from a JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"World file {filename} not found")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding {filename}")
        return None

def main():
    # Create shared_data directory if it doesn't exist
    os.makedirs('../shared_data', exist_ok=True)
    
    world_file = '../shared_data/YourWorld.json'
    
    # Check if world file exists
    if os.path.exists(world_file):
        print(f"World file {world_file} already exists. Loading existing world...")
        world = load_world(world_file)
        if not world:
            print("Error loading existing world. Creating new world...")
            world = create_initial_world()
    else:
        print("Creating new world...")
        world = create_initial_world()
    
    if world:
        save_world(world, world_file)
        
        # Print world summary
        print("\nWorld Summary:")
        print(f"World Name: {world['name']}")
        print(f"Description: {world['description']}")
        print("\nKingdoms:")
        for kingdom_name, kingdom in world['kingdoms'].items():
            print(f"\n- {kingdom_name}")
            print(f"  Description: {kingdom['description'][:100]}...")
            print("  Towns:")
            for town_name, town in kingdom['towns'].items():
                print(f"    - {town_name}")
                print("    NPCs:")
                for npc_name in town['npcs'].keys():
                    print(f"      * {npc_name}")
    else:
        print("Failed to create or load world")

if __name__ == "__main__":
    main()