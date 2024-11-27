import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
from agents.world_builder import WorldBuilderAgent
from agents.game_master import GameMasterAgent
from core.game_state import GameState
import json
from datetime import datetime

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
    # Get API key and check if it exists
    api_key = os.getenv('TOGETHER_API_KEY')
    if not api_key:
        logging.error("TOGETHER_API_KEY not found in environment variables")
        raise ValueError("TOGETHER_API_KEY not found in environment variables")

    try:
        world_builder = WorldBuilderAgent(api_key)
        world = world_builder.build_complete_world(
            concept="cities built on massive beasts known as Colossi"
        )
        save_world(world, world_file)
        logging.info("New world created and saved successfully")
        return world
    except Exception as e:
        logging.error(f"Error creating world: {str(e)}")
        raise

def parse_inventory_changes(response_text: str, current_inventory: dict) -> dict:
    """Parse the response text for inventory changes and update the inventory."""
    new_inventory = current_inventory.copy()
    logging.info(f"Parsing inventory changes from response: {response_text[:100]}...")  # Log first 100 chars
    
    # Look for explicit inventory statements
    if "inventory now" in response_text.lower():
        try:
            # Find the inventory section
            start_idx = response_text.find('{')
            end_idx = response_text.find('}') + 1
            if start_idx != -1 and end_idx != -1:
                inventory_str = response_text[start_idx:end_idx]
                parsed_inventory = eval(inventory_str)
                # Only update if we got a valid dictionary
                if isinstance(parsed_inventory, dict):
                    new_inventory = parsed_inventory
                    logging.info(f"Updated inventory from explicit statement: {new_inventory}")
        except Exception as e:
            logging.error(f"Failed to parse inventory statement: {e}")
    else:
        # Handle item additions
        if "pick up" in response_text.lower():
            for item in ["rock", "sword", "key"]:
                if item in response_text.lower() and "don't have" not in response_text.lower():
                    new_inventory[item] = new_inventory.get(item, 0) + 1
                    logging.info(f"Added item: {item}")
        
        # Handle item removals
        if "throw" in response_text.lower() or "drop" in response_text.lower():
            for item in ["goggles", "rock", "sword"]:
                if item in response_text.lower():
                    if item in new_inventory:
                        del new_inventory[item]
                        logging.info(f"Removed item: {item}")
        
        # Handle purchases (gold spending)
        if "buy" in response_text.lower() and "gold" in response_text.lower():
            try:
                # Look for numbers in the text near "gold"
                import re
                numbers = re.findall(r'\d+', response_text)
                if numbers and 'gold' in new_inventory:
                    cost = int(numbers[0])
                    if new_inventory['gold'] >= cost:
                        new_inventory['gold'] -= cost
                        logging.info(f"Spent {cost} gold")
            except Exception as e:
                logging.error(f"Failed to process gold transaction: {e}")
    
    logging.info(f"Final inventory state: {new_inventory}")
    return new_inventory

def validate_inventory_change(old_inventory: dict, new_inventory: dict) -> bool:
    """Validate that inventory changes are reasonable."""
    # Gold shouldn't increase without explicit reason
    if 'gold' in old_inventory and 'gold' in new_inventory:
        if new_inventory['gold'] > old_inventory['gold']:
            return False
            
    # Basic items shouldn't disappear without explicit action
    basic_items = ['cloth pants', 'cloth shirt']
    for item in basic_items:
        if item in old_inventory and item not in new_inventory:
            return False
            
    return True

# Initialize world and agents
try:
    print("Initializing game world...")
    world = initialize_world()
    display_world_info(world)
    
    logging.info("Initializing game agents...")
    api_key = os.getenv('TOGETHER_API_KEY')
    game_master = GameMasterAgent(api_key)
    
    # Initialize game state with the first kingdom's first town and NPC
    first_kingdom = list(world['kingdoms'].values())[0]
    first_town = list(first_kingdom['towns'].values())[0]
    first_npc = list(first_town['npcs'].values())[0]
    
    game_state = GameState(
        world=world,
        current_location=first_town,
        inventory={
            "cloth pants": 1,
            "cloth shirt": 1,
            "gold": 5
        },
        history=[]
    )
    logging.info("Game state initialized successfully")
    
except Exception as e:
    logging.critical(f"Critical error during initialization: {str(e)}")
    raise

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/')
def home():
    logging.info("Home page accessed")
    try:
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Error rendering template: {e}")
        return str(e), 500

@app.route('/world-info')
def world_info():
    """Endpoint to get world information"""
    return jsonify({
        'name': world['name'],
        'description': world['description'],
        'current_location': game_state.current_location['name']
    })

@app.route('/action', methods=['POST'])
def process_action():
    action = request.json['action']
    logging.info(f"Processing action: {action}")
    
    try:
        if action == 'start game':
            response = f"Welcome to {world['name']}! You are in {game_state.current_location['name']}. {first_npc['description']}"
        else:
            response = game_master.process_action(action, game_state)
        
        # Update inventory based on response
        old_inventory = game_state.inventory.copy()
        new_inventory = parse_inventory_changes(response, old_inventory)
        
        # Validate inventory changes
        if validate_inventory_change(old_inventory, new_inventory):
            game_state.inventory = new_inventory
        else:
            logging.warning("Invalid inventory change detected, keeping old inventory")
            
        game_state.add_to_history(action, response)
        logging.info(f"Action processed successfully: {action}")
        logging.info(f"Current inventory: {game_state.inventory}")
        
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
    print(f"Current Location: {game_state.current_location['name']}")
    print(f"Starting Inventory: {game_state.inventory}")
    print("\nAccess the game at http://localhost:5000")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', debug=True, port=port)

