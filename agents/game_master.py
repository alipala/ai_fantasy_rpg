from crewai import Agent
from together import Together
from core.game_state import GameState
from langchain.chat_models.base import BaseChatModel
from typing import List, Dict, Any
from pydantic import BaseModel, Field

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
    def __init__(self, api_key):
        try:
            self.client = Together(api_key=api_key)
            self.chat_model = CustomTogetherModel(together_client=self.client)
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

    def process_action(self, action: str, game_state: GameState) -> str:
        system_prompt = """You are an AI Game master. Generate the next story event based on:
        1. Player's current location and surroundings
        2. Available NPCs and their characteristics
        3. Current inventory items
        4. Recent action history
        
        Keep responses engaging but concise (2-3 sentences).
        Use second person present tense.
        Include opportunities for inventory interaction.
        If an item is used from inventory, indicate this with [USED_ITEM:item_name] at the start of the response."""
        
        context = f"""Current location: {game_state.current_location['name']}
        Description: {game_state.current_location['description']}
        Inventory: {game_state.inventory}
        Recent history: {game_state.history[-3:] if game_state.history else 'None'}
        Action: {action}"""
        
        try:
            # Check if action is using an item
            item_used = None
            if action.lower().startswith('use '):
                item_name = action[4:].strip()
                if item_name in game_state.inventory and game_state.inventory[item_name] > 0:
                    game_state.inventory[item_name] -= 1
                    if game_state.inventory[item_name] == 0:
                        del game_state.inventory[item_name]
                    item_used = item_name

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ]
            
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-3-70b-chat-hf",
                messages=messages,
                temperature=0.7
            )
            
            result = response.choices[0].message.content
            if item_used:
                result = f"[USED_ITEM:{item_used}] {result}"
            
            return result
        except Exception as e:
            print(f"Error processing action: {str(e)}")
            return "Something went wrong. Please try again."