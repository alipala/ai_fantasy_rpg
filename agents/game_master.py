from crewai import Agent
from together import Together
from core.game_state import GameState
from langchain.chat_models.base import BaseChatModel
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
import logging
import random
from db.client import MongoDBClient

class CustomTogetherModel(BaseChatModel):
    client: Any = Field(default=None)
    model_name: str = Field(default="meta-llama/Llama-3-70b-chat-hf")

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, together_client, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'client', together_client)

    @property
    def _llm_type(self) -> str:
        return "together"

    def _generate(self, messages: List[Dict[str, Any]], stop: List[str] | None = None) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages]
        )
        return response.choices[0].message.content

    def _call(self, messages: List[Dict[str, Any]], stop: List[str] | None = None) -> str:
        return self._generate(messages, stop)

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model": self.model_name}

class GameMasterAgent:
    def __init__(self, api_key, openai_api_key):
        try:
            # Initialize Together client
            self.client = Together(api_key=api_key)
            self.chat_model = CustomTogetherModel(together_client=self.client)
            self.openai_client = OpenAI(api_key=openai_api_key)
            self.agent = Agent(
                role='Game Master',
                goal='Manage game flow and player interactions',
                backstory='Expert at creating engaging game narratives',
                allow_delegation=True,
                llm=self.chat_model
            )
        except Exception as e:
            print(f"Error initializing agent: {str(e)}")
            raise

    def generate_initial_story_image(self, character: str, location: Dict, world: Dict) -> Optional[Dict]:
        """Generate an image for the initial story scene"""
        try:
            # Craft a detailed prompt based on the character and location
            prompt = (
                f"A wide establishing shot of {character} exploring {location['name']} "
                f"in the fantasy world of {world['name']}. {location['description']} "
                "Epic fantasy game art style with dramatic lighting and cinematic composition."
            )
            
            # Generate image using OpenAI's DALL-E
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            
            if response.data:
                return {
                    'url': response.data[0].url,
                    'type': 'establishing_shot',
                    'context': {
                        'character': character,
                        'location': location['name'],
                        'world': world['name']
                    }
                }
                
        except Exception as e:
            print(f"Initial story image generation error: {e}")
            return None

    def _find_matching_task(self, action: str, available_tasks: List) -> Optional[Any]:
        """Find matching task based on action description."""
        action_words = set(action.lower().split())
        
        for task in available_tasks:
            task_words = set(task.description.lower().split())
            # Check for significant word overlap
            if len(task_words.intersection(action_words)) >= 2:
                logging.info(f"Found matching task: {task.description}")
                return task
                
            # Check for item usage matching required item
            if action.lower().startswith('use '):
                item_name = action[4:].strip().lower()
                if item_name in task.required_item.lower():
                    return task
                    
        logging.info("No matching task found")
        return None

    def _verify_required_items(self, required_items: List[str], inventory: Dict) -> bool:
        logging.info(f"Verifying items: {required_items}")
        return all(item in inventory and inventory[item] > 0 for item in required_items)

    def _consume_items(self, items: List[str], inventory: Dict) -> None:
        logging.info(f"Consuming items: {items}")
        for item in items:
            if item in inventory:
                inventory[item] -= 1   
   
    def _process_item_use(self, item_name: str, game_state: GameState) -> str:
        """Process use of an item and return the result."""
        # Check if this action matches any pending tasks
        if game_state.puzzle_progress:
            available_tasks = game_state.puzzle_progress.get_available_tasks(game_state.inventory)
            
            for task in available_tasks:
                if task.required_item == item_name:
                    reward = game_state.attempt_task(task.task_id)
                    if reward:
                        return f"Task completed: {task.description}. Received: {reward}"
        
        # Generic item use response
        return f"You use the {item_name}. Nothing special happens."

    def process_action(self, action: str, game_state: GameState) -> str:
        try:
            # Check for examine/inspect actions first
            if any(word in action.lower() for word in ['examine', 'inspect', 'look', 'check']):
                return self._generate_contextual_hints(game_state)
                
            # Handle item usage
            if action.lower().startswith('use '):
                item_name = action[4:].strip()
                return self._process_item_use(item_name, game_state)
            
            # Try to match with puzzle tasks if puzzle exists
            puzzle_response = None
            if game_state.puzzle_progress:
                available_tasks = game_state.puzzle_progress.get_available_tasks(game_state.inventory)
                matching_task = self._find_matching_task(action, available_tasks)
                
                if matching_task:
                    required_items = matching_task.required_item.split(', ')
                    if self._verify_required_items(required_items, game_state.inventory):
                        self._consume_items(required_items, game_state.inventory)
                        reward = game_state.attempt_task(matching_task.task_id)
                        if reward:
                            puzzle_response = f"Task completed: {matching_task.description}. Received: {reward}"
                            if game_state.puzzle_progress.is_puzzle_solved():
                                puzzle_response += "\n\nCongratulations! You have solved the puzzle and saved the realm!"
                            return puzzle_response

            # If no puzzle match or no puzzle exists, generate contextual response
            location_name = game_state.current_location.get('name', 'this area')
            location_desc = game_state.current_location.get('description', '')
            
            system_prompt = f"""You are the Game Master of a fantasy RPG game. Current context:
            Location: {location_name}
            Description: {location_desc}
            Available items: {', '.join(game_state.inventory.keys())}
            Last action: {action}
            
            Respond in character as a game master, providing an engaging response to the player's action.
            Keep response under 3 sentences. Include references to the location and available items when relevant."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": action}
            ]
            
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-3-70b-chat-hf",
                messages=messages,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Error in process_action: {str(e)}")
            return "Something unexpected happened. Please try a different action."
        
    def _generate_contextual_hints(self, game_state: GameState) -> str:
        if not game_state.puzzle_progress:
            return "You observe your surroundings carefully, but notice nothing unusual."
            
        available_tasks = game_state.puzzle_progress.get_available_tasks(game_state.inventory)
        if not available_tasks:
            return "The area seems peaceful for now."
            
        hints = []
        locations = {
            'anchor': "You notice concerning instability in the nearby floating islands' anchor points.",
            'crystal': "Ethereal crystals pulse with mysterious energy, seeming to respond to the realm's stability.",
            'structure': "The supporting structures around you show signs of magical strain.",
            'repair': "Various mechanisms appear to need maintenance and careful attention.",
            'measurement': "You spot subtle variations in the magical field strengths that might need measuring.",
            'defense': "The magical barriers protecting key areas seem to need reinforcement."
        }
        
        for task in available_tasks[:2]:
            for keyword, hint in locations.items():
                if keyword in task.description.lower() and hint not in hints:
                    hints.append(hint)
                    break
                    
        for item in game_state.inventory:
            if any(item.lower() in task.required_item.lower() for task in available_tasks):
                hints.append(f"Your {item} might be useful in addressing some of these issues.")
                
        if not hints:
            return "You sense that your skills and tools could be put to good use here."
            
        return " ".join(hints)

    def generate_examples(self, context: str, location: Dict, game_state: GameState) -> List[str]:
        examples = set()
        
        environmental_actions = [
            f"Examine {location['name'].lower()}",
            f"Inspect the area", 
            "Look around carefully"
        ]
        examples.add(random.choice(environmental_actions))
        
        if game_state.puzzle_progress:
            available_tasks = game_state.puzzle_progress.get_available_tasks(game_state.inventory)
            if available_tasks:
                for task in available_tasks[:2]:
                    if task.required_item in game_state.inventory:
                        examples.add(f"Use {task.required_item}")
        
        if 'npcs' in location:
            npc = random.choice(list(location['npcs'].values()))
            examples.add(f"Talk to {npc['name']}")
            
        example_list = list(examples)
        if len(example_list) < 3:
            example_list.extend([
                "Look around",
                "Check inventory",
                "View tasks"
            ])
        return example_list[:4]
    
    def _generate_system_prompt(self, game_state: GameState) -> str:
        """Generate context-aware system prompt."""
        location = game_state.current_location.get('name', 'this area')
        character = game_state.character.get('name', 'Adventurer') if isinstance(game_state.character, dict) else 'Adventurer'
        
        return f"""You are the Game Master for a fantasy RPG. Current context:
        - Location: {location}
        - Character: {character}
        - Available items: {', '.join(game_state.inventory.keys())}
        
        Respond in character as a game master, providing rich narrative responses
        while tracking game state and puzzle progress. Keep responses under 3 sentences."""

    def _generate_action_context(self, action: str, game_state: GameState) -> str:
        """Generate context for processing player actions."""
        return f"""Current action: {action}
        Location: {game_state.current_location.get('description', '')}
        Inventory: {game_state.inventory}
        Latest history: {game_state.history[-1] if game_state.history else 'None'}"""
    
    def generate_completion_image(self, game_state: GameState) -> Optional[Dict]:
        """Generate a final image capturing the player's journey and achievements"""
        try:
            # Build story summary and generate image as before
            story_summary = self._build_story_summary(game_state)
            character_name = game_state.character.get('name')
            
            if not character_name:
                logging.error("Character name not found in game state")
                return None
                
            prompt = f"A grand epic fantasy scene showing {character_name} in {game_state.world['name']} " \
                    f"after saving the realm. {story_summary}"
            
            try:
                # Generate image using OpenAI's DALL-E
                response = self.openai_client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    n=1,
                    size="1024x1024",
                    quality="hd",
                    style="vivid"
                )
                
                if response.data:
                    image_url = response.data[0].url
                    
                    # Initialize MongoDB client
                    mongo_client = MongoDBClient()
                    
                    # Store image data and get game_id
                    game_id = mongo_client.store_completion_image(
                        image_url=image_url,
                        puzzle_text=game_state.puzzle_progress.main_puzzle if game_state.puzzle_progress else "",
                        world_name=game_state.world['name'],
                        character_name=character_name
                    )
                    
                    # Close MongoDB connection
                    mongo_client.close()
                    
                    return {
                        'url': image_url,
                        'game_id': game_id,
                        'type': 'completion_shot',
                        'context': {
                            'character': character_name,
                            'world': game_state.world['name'],
                            'achievements': self._get_achievement_summary(game_state)
                        }
                    }
                        
            except Exception as e:
                logging.error(f"DALL-E image generation error: {e}")
                return None
                    
        except Exception as e:
            logging.error(f"Completion image generation error: {str(e)}")
            return None

    def _build_story_summary(self, game_state: GameState) -> str:
        """Build a narrative summary from the game history"""
        try:
            # Get character name safely
            character_name = game_state.character.get('name', 'the hero')
            
            key_moments = []
            task_descriptions = set()
            
            # Analyze game history for key moments and completed tasks
            for entry in game_state.history:
                if "completed" in entry.get('response', '').lower():
                    key_moments.append(entry['response'])
                    
                # Extract task descriptions
                if game_state.puzzle_progress:
                    for task in game_state.puzzle_progress.tasks.values():
                        if task.completed and task.description not in task_descriptions:
                            task_descriptions.add(task.description)
            
            # Build the summary
            summary = f"Throughout their journey, {character_name} "
            
            # Add task achievements
            if task_descriptions:
                task_list = list(task_descriptions)
                if len(task_list) > 1:
                    summary += f"{', '.join(task_list[:-1])}, and {task_list[-1]}. "
                else:
                    summary += f"{task_list[0]}. "
            
            # Add world-specific context
            world_contexts = {
                "Etherion": "stabilizing the floating islands",
                "Mechanica": "restoring the great clockwork",
                "Aquaria": "healing the coral kingdoms",
                "Ignisia": "harmonizing the volcanic networks"
            }
            
            if game_state.world['name'] in world_contexts:
                summary += f"Their efforts succeeded in {world_contexts[game_state.world['name']]}. "
            
            return summary
        except Exception as e:
            logging.error(f"Error building story summary: {e}")
            return "completed their epic quest and saved the realm."


    def _get_achievement_summary(self, game_state: GameState) -> List[str]:
        """Get a list of major achievements from the game"""
        achievements = []
        
        if game_state.puzzle_progress:
            # Add completed tasks as achievements
            for task in game_state.puzzle_progress.tasks.values():
                if task.completed:
                    achievements.append(task.title)
            
            # Add overall completion if puzzle is solved
            if game_state.puzzle_progress.is_puzzle_solved():
                achievements.append(f"Saved {game_state.world['name']}")
                
        return achievements