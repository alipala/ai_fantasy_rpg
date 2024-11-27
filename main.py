import os
import logging
import re
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
from agents.world_builder import WorldBuilderAgent
from agents.game_master import GameMasterAgent
from core.game_state import GameState
import json
from datetime import datetime
import random

# Set up logging
logging.basicConfig(
    filename=f'game_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__, 
    static_folder='static',  
    template_folder='templates'
)

load_dotenv()

def save_world(world, filename):
    """Save world data to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(world, f, indent=2)
        logging.info(f"World saved to {filename}")
        return True
    except Exception as e:
        logging.error(f"Error saving world: {str(e)}")
        return False

def load_world(filename):
    """Load world data from a JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"World file {filename} not found")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error decoding {filename}")
        return None

def display_world_info(world):
    """Display information about the created world."""
    print("\n=== World Information ===")
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
    print("\n=== World Creation Complete ===")

def initialize_world():
    """Initialize or load the game world."""
    world_file = 'shared_data/game_world.json'
    os.makedirs('shared_data', exist_ok=True)

    if os.path.exists(world_file):
        logging.info("Loading existing world...")
        world = load_world(world_file)
        if world:
            logging.info("Existing world loaded successfully")
            return world

    logging.info("Creating new world...")
    api_key = os.getenv('TOGETHER_API_KEY')
    if not api_key:
        logging.error("TOGETHER_API_KEY not found")
        raise ValueError("TOGETHER_API_KEY not found")

    try:
        world_builder = WorldBuilderAgent(api_key)
        world = world_builder.build_complete_world(
            concept="cities built on massive beasts known as Colossi"
        )
        save_world(world, world_file)
        logging.info("New world created and saved successfully")
        return world
    except Exception as e:
        logging.error(f"Error creating world: {e}")
        raise

def load_character_inventory(character_name):
    try:
        with open('shared_data/paste.txt', 'r') as f:
            data = json.load(f)
            inventory = {}
            char_items = data['inventories'].get(character_name, [])
            
            for item in char_items:
                if item.endswith('gold'):
                    inventory['gold'] = int(item.split()[0])
                else:
                    inventory[item] = 1
            return inventory
    except Exception as e:
        logging.error(f"Error loading character inventory: {e}")
        return {"gold": 10}

def parse_inventory_changes(response_text: str, current_inventory: dict) -> dict:
    """Parse the response text for inventory changes and update the inventory."""
    new_inventory = current_inventory.copy()
    logging.info(f"Parsing inventory changes from response: {response_text[:100]}...")
    
    if "inventory now" in response_text.lower():
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.find('}') + 1
            if start_idx != -1 and end_idx != -1:
                inventory_str = response_text[start_idx:end_idx]
                parsed_inventory = eval(inventory_str)
                if isinstance(parsed_inventory, dict):
                    new_inventory = parsed_inventory
                    logging.info(f"Updated inventory: {new_inventory}")
        except Exception as e:
            logging.error(f"Failed to parse inventory: {e}")

    # Handle purchases
    if "buy" in response_text.lower() and "gold" in response_text.lower():
        try:
            cost = int(re.search(r'\d+', response_text).group())
            if new_inventory.get('gold', 0) >= cost:
                new_inventory['gold'] -= cost
                item = re.search(r'buy (\w+)', response_text.lower()).group(1)
                new_inventory[item] = new_inventory.get(item, 0) + 1
        except Exception as e:
            logging.error(f"Failed to process purchase: {e}")

    return new_inventory

def validate_inventory_change(old_inventory: dict, new_inventory: dict) -> bool:
    """Validate inventory changes."""
    if ('gold' in old_inventory and 'gold' in new_inventory and 
        new_inventory['gold'] > old_inventory['gold']):
        return False
    return True

def generate_examples(response: str, location: dict) -> list:
    """Generate contextual example actions."""
    examples = []
    
    # Location-based examples
    if 'market' in response.lower() or 'shop' in response.lower():
        examples.extend(['Browse goods', 'Check prices', 'Negotiate'])
    elif 'npc' in response.lower() or any(npc in response for npc in location['npcs']):
        examples.extend(['Ask questions', 'Learn more', 'Request help'])
    else:
        examples.extend(['Explore area', 'Talk to locals', 'Check surroundings'])
    
    return examples[:3]  # Return top 3 examples

# Initialize world and agents
try:
    print("Initializing game world...")
    world = initialize_world()
    display_world_info(world)
    
    logging.info("Initializing game agents...")
    api_key = os.getenv('TOGETHER_API_KEY')
    game_master = GameMasterAgent(api_key)
    
    # Initialize game state
    game_state = None  # Will be initialized when character is selected
    
except Exception as e:
    logging.critical(f"Critical error during initialization: {str(e)}")
    raise

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/world-info')
def world_info():
    return jsonify(world)

@app.route('/start-game', methods=['POST'])
def start_game():
    try:
        data = request.json
        character_name = data.get('character')
        kingdom_name = data.get('kingdom')
        
        # Load character inventory
        character_inventory = load_character_inventory(character_name)
        
        # Find character's town or select random town
        kingdom = world['kingdoms'][kingdom_name]
        character_town = None
        for town in kingdom['towns'].values():
            if character_name in town['npcs']:
                character_town = town
                break
        if not character_town:
            character_town = random.choice(list(kingdom['towns'].values()))
        
        # Initialize game state
        global game_state
        game_state = GameState(
            world=world,
            current_location=character_town,
            inventory=character_inventory,
            history=[]
        )
        
        return jsonify({
            'location': character_town,
            'inventory': character_inventory,
            'message': f"Starting game as {character_name} in {character_town['name']}"
        })
        
    except Exception as e:
        logging.error(f"Error starting game: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/load-inventory', methods=['POST'])
def load_inventory():
    try:
        character_name = request.json['character']
        inventory = load_character_inventory(character_name)
        return jsonify({'inventory': inventory})
    except Exception as e:
        logging.error(f"Error loading inventory: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/action', methods=['POST'])
def process_action():
    action = request.json['action']
    logging.info(f"Processing action: {action}")  # Add detailed logging
    
    try:
        response = game_master.process_action(action, game_state)
        old_inventory = game_state.inventory.copy()
        logging.info(f"Old inventory: {old_inventory}")  # Log old inventory
        
        # Process inventory changes
        if 'hand over' in response.lower() or 'spend' in response.lower():
            matches = re.findall(r'(\d+)\s*gold', response.lower())
            if matches:
                cost = int(matches[0])
                if game_state.inventory['gold'] >= cost:
                    game_state.inventory['gold'] -= cost
                    logging.info(f"Spent {cost} gold. New amount: {game_state.inventory['gold']}")
        
        logging.info(f"Response: {response}")  # Log response
        logging.info(f"New inventory: {game_state.inventory}")  # Log new inventory
        
        return jsonify({
            'response': response,
            'inventory': game_state.inventory,
            'location': game_state.current_location['name']
        })
    except Exception as e:
        logging.error(f"Error processing action: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n=== Game Ready to Start ===")
    print("\nAccess the game at http://localhost:5000")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', debug=True, port=port)