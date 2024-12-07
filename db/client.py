# db/client.py
from pymongo import MongoClient, ASCENDING
from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv

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
        
        # Create game_id index if it doesn't exist
        if "game_id_1" not in existing_indexes:
            self.completion_images.create_index(
                [("game_id", ASCENDING)], 
                unique=True,
                background=True
            )
            
        # Create index on created_at for cleanup queries
        if "created_at_1" not in existing_indexes:
            self.completion_images.create_index(
                [("created_at", ASCENDING)],
                background=True
            )

    def cleanup_old_images(self, days_old: int = 30) -> int:
        """
        Remove image records older than specified days
        Returns number of records removed
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        result = self.completion_images.delete_many(
            {"created_at": {"$lt": cutoff_date}}
        )
        return result.deleted_count

    def get_recent_completions(self, limit: int = 10) -> List[Dict]:
        """
        Get most recent completion images
        Args:
            limit: Maximum number of records to return
        Returns:
            List of completion image records
        """
        return list(
            self.completion_images.find()
            .sort("created_at", -1)
            .limit(limit)
        )

    def close(self):
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()