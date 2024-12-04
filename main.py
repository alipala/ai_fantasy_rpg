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
from typing import List, Dict

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

def display_worlds_info(worlds):
    """Display information about the created worlds."""
    print("\n=== Worlds Information ===")
    for world_name, world in worlds.items():
        print(f"\nWorld: {world_name}")
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
    print("\n=== Worlds Creation Complete ===")

def initialize_worlds():
    """Initialize or load the game worlds."""
    world_file = 'shared_data/game_world.json'
    os.makedirs('shared_data', exist_ok=True)

    # First try to load existing worlds
    if os.path.exists(world_file):
        logging.info("Loading existing worlds...")
        try:
            with open(world_file, 'r') as f:
                worlds_data = json.load(f)
                if 'worlds' in worlds_data:  # Check if it has the correct structure
                    logging.info("Successfully loaded existing worlds")
                    return worlds_data['worlds']
        except Exception as e:
            logging.error(f"Error loading worlds: {e}")

    # Only generate new worlds if loading fails
    logging.info("Creating new worlds...")
    api_key = os.getenv('TOGETHER_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if not api_key or not openai_api_key:
        logging.error("API_KEYs not found")
        raise ValueError("API_KEYs not found")

    world_builder = WorldBuilderAgent(api_key)
    try:
        worlds = world_builder.generate_worlds()  # Your world generation logic
        
        # Save the newly generated worlds
        with open(world_file, 'w') as f:
            json.dump({'worlds': worlds}, f, indent=2)
            
        return worlds
    except Exception as e:
        logging.error(f"Error creating worlds: {e}")
        raise

def load_character_inventory(character_name):
    try:
        with open('shared_data/inventory.json', 'r') as f:
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

def generate_examples(self, context: str, location: Dict, game_state: GameState) -> List[str]:
    examples = set()
    
    # Add environmental actions
    environmental_actions = [
        f"Examine {location['name'].lower()}",
        f"Inspect the area",
        "Look around carefully"
    ]
    examples.add(random.choice(environmental_actions))
    
    # Add inventory-based suggestions
    if game_state.puzzle_progress:
        available_tasks = game_state.puzzle_progress.get_available_tasks(game_state.inventory)
        if available_tasks:
            for task in available_tasks[:2]:
                if task.required_item in game_state.inventory:
                    examples.add(f"Use {task.required_item}")
    
    # Add NPC interactions
    if 'npcs' in location:
        npc = random.choice(list(location['npcs'].values()))
        examples.add(f"Talk to {npc['name']}")
    
    return list(examples)[:4]


# Initialize worlds and agents
try:
    print("Initializing game worlds...")
    worlds = initialize_worlds()
    if worlds:
        logging.info(f"Loaded {len(worlds)} worlds")
    else:
        logging.error("Failed to load or generate worlds")
        raise ValueError("No worlds available")
    
    logging.info("Initializing game agents...")
    api_key = os.getenv('TOGETHER_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY') 
    game_master = GameMasterAgent(
        api_key,
        openai_api_key=openai_api_key)
    
    # Initialize game state
    game_state = None  # Will be initialized when character is selected
    
except Exception as e:
    logging.critical(f"Critical error during initialization: {str(e)}")
    raise

def extract_keywords(text):
    """Extract key elements from response text"""
    keywords = {
        'npcs': [],
        'items': [],
        'locations': [],
        'actions': []
    }
    
    # Extract NPCs (names and titles)
    npc_matches = re.findall(r'([A-Z][a-z]+ [A-Z][a-z]+|the [a-z]+ [a-z]+)', text)
    keywords['npcs'] = list(set(npc_matches))
    
    # Extract items
    item_matches = re.findall(r'(?:the |a |an )([a-z]+ [a-z]+)', text.lower())
    keywords['items'] = list(set(item_matches))
    
    # Extract locations
    loc_matches = re.findall(r'(?:at |in |near |by )(?:the )?([a-z]+ [a-z]+)', text.lower())
    keywords['locations'] = list(set(loc_matches))
    
    return keywords

def process_regular_action(action):
    # Existing action processing logic
    response = game_master.process_action(action, game_state)
    return jsonify({
        'response': response,
        'puzzle_progress': game_state.puzzle_progress.dict() if game_state.puzzle_progress else None,
        'inventory': game_state.inventory,
        'puzzle_solved': False
    })

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/world-info')
def world_info():
    world_file = 'shared_data/game_world.json'
    try:
        with open(world_file, 'r') as f:
            worlds = json.load(f)
            print("Serving worlds data:", worlds)  # Debug log
            return jsonify(worlds)
    except Exception as e:
        logging.error(f"Error loading worlds: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/start-game', methods=['POST'])
def start_game():
    try:
        # Get request data
        data = request.json
        character_name = data.get('character')
        world_name = data.get('world')
        kingdom_name = data.get('kingdom')
        
        # Load character inventory
        character_inventory = load_character_inventory(character_name)
        
        # Load puzzle data
        puzzle_data = None
        try:
            with open('shared_data/puzzle_data.json', 'r') as f:
                world_puzzles = json.load(f)['world_puzzles']
                if world_name in world_puzzles and character_name in world_puzzles[world_name]['characters']:
                    puzzle_data = world_puzzles[world_name]['characters'][character_name]
        except Exception as e:
            logging.error(f"Error loading puzzle data: {e}")
        
        # Find world data
        world = None
        with open('shared_data/game_world.json', 'r') as f:
            worlds_data = json.load(f)
            world = worlds_data['worlds'].get(world_name)
        
        if not world:
            raise ValueError(f"World {world_name} not found")
            
        # Find character's town or select random town
        kingdom = world['kingdoms'].get(kingdom_name)
        if not kingdom:
            raise ValueError(f"Kingdom {kingdom_name} not found")
            
        character_town = None
        character_data = None
        
        # Search for character in towns
        for town in kingdom['towns'].values():
            if character_name in town['npcs']:
                character_town = town
                character_data = town['npcs'][character_name]
                break
                
        if not character_town:
            # Fallback to random town if character's town not found
            character_town = random.choice(list(kingdom['towns'].values()))
            
        if not character_data:
            raise ValueError(f"Character {character_name} not found")
        
        # Initialize game state
        global game_state
        game_state = GameState(
            world=world,
            current_location=character_town,
            inventory=character_inventory,
            history=[],
            character={
                'name': character_name,
                'description': character_data['description']
            }
        )
        
        # Initialize puzzle if data exists
        if puzzle_data:
            game_state.initialize_puzzle(character_name, worlds_data)
            logging.info(f"Initialized puzzle for {character_name}")
            print(f"Initialized puzzle progress: {game_state.puzzle_progress}")
        
        # Create initial welcome message
        welcome_message = (
            f"Welcome to {world['name']}! You are {character_name} in "
            f"{character_town['name']}. {character_town['description']}"
        )
        
        if game_state.puzzle_progress:
            welcome_message += f"\n\nYour Quest: {game_state.puzzle_progress.main_puzzle}"
        
        # Generate initial story image
        try:
            initial_image = game_master.generate_initial_story_image(
                character=character_name,
                location=character_town,
                world=world
            )
        except Exception as e:
            logging.error(f"Image generation error: {e}")
            initial_image = None
            
        # Prepare location-specific items based on world
        location_items = []
        if "Ignisia" in world_name:
            location_items = ["Fire-resistant cloak", "Magma compass"]
        elif "Aquaria" in world_name:
            location_items = ["Water breathing charm", "Pearl compass"]
        elif "Mechanica" in world_name:
            location_items = ["Clockwork assistant", "Steam-powered toolkit"]
        elif "Terranova" in world_name:
            location_items = ["Nature's blessing stone", "Living compass"]
        elif "Etheria" in world_name:
            location_items = ["Ethereal crystal", "Void compass"]
            
        # Add location items to inventory if any
        if location_items:
            for item in location_items:
                character_inventory[item] = character_inventory.get(item, 0) + 1
        
        # Create response
        response = {
            'location': {
                'name': character_town['name'],
                'description': character_town['description'],
                'npcs': character_town['npcs']
            },
            'inventory': character_inventory,
            'message': welcome_message,
            'character': {
                'name': character_name,
                'description': character_data['description']
            },
            'world': {
                'name': world['name'],
                'description': world['description']
            },
            'puzzle_progress': game_state.puzzle_progress.dict() if game_state.puzzle_progress else None
        }
        
        # Add initial image if generation was successful
        if initial_image:
            response['initial_image'] = initial_image
            
        # Log successful game start
        logging.info(f"Game started for character {character_name} in {world_name}")

        print("Starting game with character:", character_name)
        print("Puzzle progress initialized:", game_state.puzzle_progress)
        
        return jsonify(response)
        
    except ValueError as ve:
        logging.error(f"Validation error in start_game: {str(ve)}")
        return jsonify({'error': str(ve)}), 400
        
    except Exception as e:
        logging.error(f"Error in start_game: {str(e)}")
        return jsonify({'error': "Failed to start game. Please try again."}), 500
    
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
    logging.info(f"Processing action: {action}")
    
    try:
        response = None
        puzzle_progress = None
        puzzle_solved = False
        completion_image = None
        
        # Check for puzzle completion
        if hasattr(game_state, 'puzzle_progress') and game_state.puzzle_progress:
            available_tasks = game_state.puzzle_progress.get_available_tasks(game_state.inventory)
            matching_task = None
            
            # Match action with available tasks
            for task in available_tasks:
                task_keywords = set(task.description.lower().split())
                action_keywords = set(action.lower().split())
                if len(task_keywords.intersection(action_keywords)) >= 2:
                    matching_task = task
                    break
            
            if matching_task:
                reward = game_state.attempt_task(matching_task.task_id)
                if reward:
                    response = f"Task completed: {matching_task.description}. Received: {reward}"
                    puzzle_progress = game_state.puzzle_progress.dict()
                    puzzle_solved = game_state.puzzle_progress.is_puzzle_solved()
                    
                    if puzzle_solved:
                        # Only add completion message first
                        response += "\n\nCongratulations! You have solved the puzzle and saved the realm!"
                    
        # Regular game action processing if no task completed
        if not response:
            response = game_master.process_action(action, game_state)
            
        # Create base response data
        response_data = {
            'response': response,
            'inventory': game_state.inventory,
            'location': game_state.current_location['name'],
            'puzzle_progress': puzzle_progress,
            'puzzle_solved': puzzle_solved,
            'available_tasks': [
                {
                    'id': task.task_id,
                    'title': task.title,
                    'description': task.description
                }
                for task in game_state.puzzle_progress.get_available_tasks(game_state.inventory)
            ] if hasattr(game_state, 'puzzle_progress') and game_state.puzzle_progress else []
        }
        
        # Add completion context if puzzle is solved
        if puzzle_solved:
            response_data['character'] = {
                'name': game_state.character['name'],
                'description': game_state.character['description']
            }
            response_data['world'] = {
                'name': game_state.world['name'],
                'description': game_state.world['description']
            }
            
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f"Error processing action: {str(e)}"
        logging.error(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/generate-completion', methods=['POST'])
def generate_completion():
    try:
        completion_image = game_master.generate_completion_image(game_state)
        if completion_image:
            return jsonify({
                'completion_image': completion_image,
                'success': True
            })
        return jsonify({'success': False}), 404
    except Exception as e:
        logging.error(f"Error generating completion image: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-examples', methods=['POST'])
def generate_examples():
    try:
        data = request.json
        context = data.get('context', '')
        
        examples = set()
        
        # Get available puzzle tasks
        if hasattr(game_state, 'puzzle_progress') and game_state.puzzle_progress:
            available_tasks = game_state.puzzle_progress.get_available_tasks(game_state.inventory)
            
            # Add simplified versions of available tasks
            for task in available_tasks:
                # Extract key action from task
                task_words = task.description.lower().split()
                key_verbs = {'use', 'activate', 'defend', 'lead', 'coordinate', 'establish', 'rally', 'create'}
                
                for verb in key_verbs:
                    if verb in task_words:
                        # Create simplified action based on verb and required item
                        if task.required_item != 'All items':
                            action = f"{verb.title()} {task.required_item}"
                            examples.add(action)
                            break
            
            # Add inventory-based suggestions
            for item in game_state.inventory:
                if any(task.required_item == item for task in available_tasks):
                    examples.add(f"Use {item}")
        
        # Add contextual actions
        keywords = extract_keywords(context)
        if keywords['npcs']:
            examples.add(f"Talk to {random.choice(keywords['npcs'])}")
        
        if keywords['locations']:
            examples.add(f"Explore {random.choice(keywords['locations'])}")
            
        # Always include some general actions
        general_actions = ["Look around", "Check inventory", "View current tasks"]
        examples.add(random.choice(general_actions))
        
        # Convert to list and limit size
        example_list = list(examples)[:4]
        
        # If we have active tasks but no task-related examples, add one
        if available_tasks and not any('use' in ex.lower() for ex in example_list):
            task = random.choice(available_tasks)
            hint = f"Try using {task.required_item}"
            example_list[0] = hint
        
        return jsonify({'examples': example_list})
        
    except Exception as e:
        logging.error(f"Error generating examples: {e}")
        return jsonify({'examples': ['Look around', 'Talk', 'Explore']})
    

if __name__ == '__main__':
    print("\n=== Game Ready to Start ===")
    print("\nAccess the game at http://localhost:5000")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', debug=True, port=port)