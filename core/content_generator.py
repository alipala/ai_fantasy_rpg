# core/content_generator.py
from typing import Dict, List
from together import Together

class ContentGenerator:
    def __init__(self, api_key: str):
        self.client = Together(api_key=api_key)
    
    def generate_location_description(self, location_type: str, context: Dict) -> str:
        """Generate description for a new location."""
        system_prompt = f"""Create a description for a {location_type} in a fantasy setting.
        Use vivid but concise language. Include notable features and atmosphere.
        Maximum 3 sentences."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context}"}
        ]
        
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=messages
        )
        
        return response.choices[0].message.content
    
    def generate_npc_dialogue(self, npc_info: Dict, context: Dict) -> str:
        """Generate NPC dialogue based on character and context."""
        system_prompt = """Create a short dialogue response for an NPC.
        Stay in character and reference relevant context.
        Maximum 2 sentences."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"NPC: {npc_info}\nContext: {context}"}
        ]
        
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=messages
        )
        
        return response.choices[0].message.content
    
    def generate_quest(self, context: Dict) -> Dict:
        """Generate a new quest based on current game context."""
        system_prompt = """Create a simple quest for a fantasy RPG.
        Include:
        - Title
        - Description
        - Objective
        - Reward
        Keep it concise and achievable."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context}"}
        ]
        
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=messages
        )
        
        # Parse response into quest structure
        quest_text = response.choices[0].message.content
        return self._parse_quest_text(quest_text)
    
    def _parse_quest_text(self, quest_text: str) -> Dict:
        """Parse generated quest text into structured format."""
        try:
            lines = quest_text.split('\n')
            quest = {
                "title": lines[0].replace("Title:", "").strip(),
                "description": lines[1].replace("Description:", "").strip(),
                "objective": lines[2].replace("Objective:", "").strip(),
                "reward": lines[3].replace("Reward:", "").strip()
            }
            return quest
        except Exception:
            return {
                "title": "Mystery Quest",
                "description": quest_text,
                "objective": "Investigate further",
                "reward": "Unknown"
            }