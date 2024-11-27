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
    try:
        def __init__(self, api_key):
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

    def process_action(self, action, game_state):
        system_prompt = """You are an AI Game master. Your job is to write what 
        happens next in a player's adventure game.
        Instructions: 
        - Write 1-3 sentences in response
        - Use second person present tense
        - Consider player's inventory and location
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Current state: {game_state.to_string()}\nAction: {action}"}
        ]
        
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=messages
        )
        
        return response.choices[0].message.content