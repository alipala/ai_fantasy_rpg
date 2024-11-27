from pydantic import BaseModel
from typing import Dict, List

class GameState(BaseModel):
    world: Dict
    current_location: Dict
    inventory: Dict[str, int]
    history: List[Dict]
    
    def to_string(self):
        return f"""
        World: {self.world.get('name')}
        Location: {self.current_location.get('name')}
        Inventory: {self.inventory}
        """
    
    def update_inventory(self, item_updates):
        for update in item_updates:
            name = update['name']
            change = update['change_amount']
            
            if name not in self.inventory:
                self.inventory[name] = 0
            self.inventory[name] += change
            
            if self.inventory[name] <= 0:
                del self.inventory[name]

    def add_to_history(self, action, response):
        self.history.append({
            'action': action,
            'response': response
        })