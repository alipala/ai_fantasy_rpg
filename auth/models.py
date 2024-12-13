# auth/models.py
from datetime import datetime
from typing import Optional, List
from pymongo import ASCENDING
from db.client import MongoDBClient

class UserModel:
    def __init__(self):
        self.client = MongoDBClient()
        self.users = self.client.db['users']
        self.user_completions = self.client.db['user_completions']
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create required indexes"""
        # User indexes
        self.users.create_index([("google_id", ASCENDING)], unique=True)
        self.users.create_index([("email", ASCENDING)], unique=True)
        
        # User completions index
        self.user_completions.create_index([
            ("user_id", ASCENDING),
            ("created_at", ASCENDING)
        ])

    def create_user(self, google_data: dict) -> str:
        """Create new user from Google OAuth data"""
        user = {
            'google_id': google_data['sub'],
            'email': google_data['email'],
            'name': google_data['name'],
            'picture': google_data.get('picture'),
            'created_at': datetime.utcnow(),
            'last_login': datetime.utcnow()
        }
        
        result = self.users.update_one(
            {'google_id': google_data['sub']},
            {'$set': user},
            upsert=True
        )
        
        if result.upserted_id:
            return str(result.upserted_id)
        
        user = self.users.find_one({'google_id': google_data['sub']})
        return str(user['_id'])

    def get_user(self, google_id: str) -> Optional[dict]:
        """Get user by Google ID"""
        user = self.users.find_one({'google_id': google_id})
        if user:
            user['_id'] = str(user['_id'])
        return user

    def add_completion(self, user_id: str, completion_id: str):
        """Link completion image to user"""
        self.user_completions.insert_one({
            'user_id': user_id,
            'completion_id': completion_id,
            'created_at': datetime.utcnow()
        })

    def get_user_completions(self, user_id: str, limit: int = 10) -> List[dict]:
        """Get user's completion images"""
        return list(
            self.user_completions.find({'user_id': user_id})
            .sort('created_at', -1)
            .limit(limit)
        )

    def close(self):
        """Close MongoDB connection"""
        self.client.close()