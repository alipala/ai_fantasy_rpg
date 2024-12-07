# db/models.py
from typing import TypedDict
from datetime import datetime

class CompletionImage(TypedDict):
    game_id: str
    image_url: str
    puzzle_text: str
    world_name: str
    character_name: str
    created_at: datetime