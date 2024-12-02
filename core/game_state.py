from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from .puzzle_state import PuzzleProgress, TaskProgress
import json
import logging

class GameState(BaseModel):
    world: Dict
    current_location: Dict
    inventory: Dict[str, int]
    history: List[Dict]
    puzzle_progress: Optional[PuzzleProgress] = None
    
    def to_string(self):
        return f"""
        World: {self.world.get('name')}
        Location: {self.current_location.get('name')}
        Inventory: {self.inventory}
        """
    
    def validate_transaction(self, item: str, cost: int) -> bool:
        """Validate if a transaction is possible."""
        if 'gold' not in self.inventory:
            return False
        return self.inventory['gold'] >= cost

    def process_transaction(self, item: str, cost: int) -> bool:
        """Process a purchase transaction."""
        if self.validate_transaction(item, cost):
            self.inventory['gold'] -= cost
            self.inventory[item] = self.inventory.get(item, 0) + 1
            return True
        return False

    def update_inventory(self, changes: List[Dict[str, Any]]) -> bool:
        """Update inventory with validation."""
        old_inventory = self.inventory.copy()
        
        for change in changes:
            item_name = change['name']
            amount = change['amount']
            
            if item_name not in self.inventory and amount < 0:
                return False
                
            new_count = self.inventory.get(item_name, 0) + amount
            if new_count < 0:
                return False
                
            if new_count == 0:
                del self.inventory[item_name]
            else:
                self.inventory[item_name] = new_count
                
        return True

    def load_character_inventory(self, character_name: str):
        """Load character's starting inventory."""
        try:
            with open('shared_data/paste.txt', 'r') as f:
                inventory_data = json.load(f)
                character_items = inventory_data['inventories'].get(character_name, [])
                self.inventory = {item: 1 for item in character_items}
        except Exception as e:
            logging.error(f"Error loading character inventory: {e}")
            self.inventory = {}

    def add_to_history(self, action: str, response: str):
        """Add action and response to history."""
        self.history.append({
            'action': action,
            'response': response
        })

    def initialize_puzzle(self, character_name: str, world_data: Dict):
        """Initialize puzzle state for the character"""
        try:
            with open('shared_data/puzzle_data.json', 'r') as f:
                puzzle_data = json.load(f)
                world_name = self.world['name']
                
                if (world_name in puzzle_data['world_puzzles'] and 
                    character_name in puzzle_data['world_puzzles'][world_name]['characters']):
                        
                    char_puzzle = puzzle_data['world_puzzles'][world_name]['characters'][character_name]
                    world_puzzle = puzzle_data['world_puzzles'][world_name]
                    
                    self.puzzle_progress = PuzzleProgress(
                        main_puzzle=world_puzzle['main_puzzle'],
                        solution_requirements=world_puzzle['solution_requirements'],
                        total_tasks=len(char_puzzle['role_tasks']),
                        completed_tasks=0,
                        tasks={
                            task['task_id']: TaskProgress(**task, completed=False)
                            for task in char_puzzle['role_tasks']
                        }
                    )
                    
                    print(f"Puzzle initialized for {character_name}")
                    return True
                    
        except Exception as e:
            print(f"Error initializing puzzle: {e}")
        return False
            
    def attempt_task(self, task_id: str) -> Optional[str]:
        """Attempt to complete a task and return reward if successful"""
        if not self.puzzle_progress:
            return None
            
        if self.puzzle_progress.can_perform_task(task_id, self.inventory):
            return self.puzzle_progress.complete_task(task_id)
            
        return None