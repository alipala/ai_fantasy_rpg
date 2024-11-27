# agents/inventory_manager.py
from crewai import Agent
from together import Together
from typing import List, Dict

class InventoryManagerAgent:
    def __init__(self, api_key):
        self.client = Together(api_key=api_key)
        self.agent = Agent(
            role='Inventory Manager',
            goal='Manage player inventory and item interactions',
            backstory='Expert at managing game items and inventory systems',
            allow_delegation=False
        )
    
    def detect_inventory_changes(self, current_inventory: Dict[str, int], action_result: str) -> List[Dict]:
        """Detect inventory changes based on action results."""
        system_prompt = """Analyze the game action result and detect any inventory changes.
        Only include items that were clearly gained or lost in the narrative.
        Return changes in JSON format."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Current inventory: {current_inventory}\nAction result: {action_result}"}
        ]
        
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=messages,
            temperature=0
        )
        
        try:
            # Parse the response to get inventory changes
            return self._parse_inventory_changes(response.choices[0].message.content)
        except Exception as e:
            print(f"Error parsing inventory changes: {e}")
            return []
    
    def _parse_inventory_changes(self, response: str) -> List[Dict]:
        """Parse the LLM response into structured inventory changes."""
        try:
            # Basic parsing of the response
            changes = []
            if "add" in response.lower():
                items = [item.strip() for item in response.split("add")[1].split("remove")[0].split(",")]
                for item in items:
                    if item:
                        changes.append({"name": item, "change_amount": 1})
            if "remove" in response.lower():
                items = [item.strip() for item in response.split("remove")[1].split(",")]
                for item in items:
                    if item:
                        changes.append({"name": item, "change_amount": -1})
            return changes
        except Exception:
            return []

    def can_use_item(self, inventory: Dict[str, int], item_name: str) -> bool:
        """Check if an item can be used based on inventory."""
        return item_name in inventory and inventory[item_name] > 0

    def get_item_description(self, item_name: str) -> str:
        """Get a description for a specific item."""
        system_prompt = """Generate a brief, engaging description for a fantasy game item.
        Keep it under 2 sentences."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Describe the item: {item_name}"}
        ]
        
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=messages
        )
        
        return response.choices[0].message.content