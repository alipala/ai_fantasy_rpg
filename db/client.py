# db/client.py

from pymongo import MongoClient, ASCENDING
from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client['fantasy_game']
        self.completion_images = self.db['completion_images']
        
        # Create indexes during initialization
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure required indexes exist"""
        existing_indexes = self.completion_images.index_information()
        
        if "game_id_1" not in existing_indexes:
            self.completion_images.create_index(
                [("game_id", ASCENDING)], 
                unique=True,
                background=True
            )
            
        if "created_at_1" not in existing_indexes:
            self.completion_images.create_index(
                [("created_at", ASCENDING)],
                background=True
            )

    def store_completion_image(self, 
                             image_url: str,
                             puzzle_text: str,
                             world_name: str,
                             character_name: str) -> str:
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
        """Retrieve completion image data by game_id"""
        return self.completion_images.find_one({'game_id': game_id})

    def get_recent_completions(self, limit: int = 10) -> List[Dict]:
        """Get most recent completion images"""
        return list(
            self.completion_images.find()
            .sort("created_at", -1)
            .limit(limit)
        )

    def cleanup_old_images(self, days_old: int = 30) -> int:
        """Remove image records older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        result = self.completion_images.delete_many(
            {"created_at": {"$lt": cutoff_date}}
        )
        return result.deleted_count

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()