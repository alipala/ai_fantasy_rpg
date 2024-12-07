from pymongo import MongoClient
from datetime import datetime
import uuid
from typing import Optional, Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client['fantasy_game']
        self.completion_images = self.db['completion_images']

    def store_completion_image(self, 
                             image_url: str,
                             world_name: str,
                             character_name: str,
                             puzzle_text: str) -> str:
        """
        Store completion image data in MongoDB
        Returns: game_id (str)
        """
        game_id = str(uuid.uuid4())
        
        image_data = {
            'game_id': game_id,
            'image_url': image_url,
            'puzzle_text': puzzle_text,
            'world_name': world_name,
            'character_name': character_name,
            'created_at': datetime.utcnow()
        }
        
        self.completion_images.insert_one(image_data)
        return game_id

    def get_completion_image(self, game_id: str) -> Optional[Dict]:
        """
        Retrieve completion image data by game_id
        """
        return self.completion_images.find_one({'game_id': game_id})

    def get_all_completion_images(self):
        """
        Retrieve all completion images
        """
        return list(self.completion_images.find().sort('created_at', -1))

    def close(self):
        """
        Close MongoDB connection
        """
        self.client.close()