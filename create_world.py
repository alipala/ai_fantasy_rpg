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

def create_initial_worlds():
   """Create multiple world structures."""
   api_key = get_together_api_key()
   world_builder = WorldBuilderAgent(api_key)
   
   world_concepts = {
       "Kyropeia": "cities built on massive beasts known as Colossi",
       "Etheria": "floating islands drifting through eternal twilight",
       "Mechanica": "steam-powered clockwork cities marching across brass deserts"
   }
   
   try:
       worlds = {}
       for world_name, concept in world_concepts.items():
           print(f"\nGenerating world: {world_name}...")
           world = world_builder.generate_world(concept)
           
           print("Generating kingdoms...")
           kingdoms = world_builder.generate_kingdoms(world)
           world['kingdoms'] = kingdoms

           for kingdom_name, kingdom in kingdoms.items():
               print(f"\nGenerating towns for {kingdom_name}...")
               towns = world_builder.generate_towns(world, kingdom)
               kingdom['towns'] = towns

               for town_name, town in towns.items():
                   print(f"Generating NPCs for {town_name}...")
                   npcs = world_builder.generate_npcs(world, kingdom, town)
                   town['npcs'] = npcs
                   
                   # Create start message for first town in first kingdom only
                   if not world.get('start'):
                       first_npc = list(town['npcs'].values())[0]
                       world['start'] = f"""Welcome to {world['name']}! You begin your journey in {town['name']}, {town['description']} Your guide is {first_npc['name']}, {first_npc['description']}"""

           worlds[world_name] = world

       return worlds

   except Exception as e:
       print(f"Error creating worlds: {str(e)}")
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
   os.makedirs('shared_data', exist_ok=True)
   
   world_file = 'shared_data/game_world.json'
   
   # Check if world file exists
   if os.path.exists(world_file):
       print(f"World file {world_file} already exists. Loading existing worlds...")
       worlds = load_world(world_file)
       if not worlds:
           print("Error loading existing worlds. Creating new worlds...")
           worlds = create_initial_worlds()
   else:
       print("Creating new worlds...")
       worlds = create_initial_worlds()
   
   if worlds:
       save_world(worlds, world_file)
       
       # Print worlds summary
       for world_name, world in worlds.items():
           print(f"\nWorld: {world_name}")
           print(f"Description: {world['description'][:100]}...")
           for kingdom_name, kingdom in world['kingdoms'].items():
               print(f"\n- {kingdom_name}")
               for town_name, town in kingdom['towns'].items():
                   print(f"  * {town_name}")
                   print(f"    NPCs: {', '.join(town['npcs'].keys())}")
   else:
       print("Failed to create or load worlds")

if __name__ == "__main__":
   main()