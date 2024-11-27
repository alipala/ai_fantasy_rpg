# utils/helpers.py
import os
import json
from typing import Dict, Any
from datetime import datetime

def load_game_data(file_path: str) -> Dict:
    """Load game data from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_game_data(data: Dict, file_path: str) -> bool:
    """Save game data to JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False

def validate_action(action: str) -> bool:
    """Validate if an action is properly formatted."""
    if not action or len(action) > 200:
        return False
    return True

def format_response(response: str) -> str:
    """Format response for game output."""
    return response.strip()

def log_event(event_type: str, data: Any) -> None:
    """Log game events for monitoring."""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "type": event_type,
        "data": data
    }
    
    try:
        with open("game_logs.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Logging error: {e}")

def sanitize_input(user_input: str) -> str:
    """Sanitize user input for safety."""
    # Remove potentially harmful characters
    sanitized = ''.join(char for char in user_input if char.isprintable())
    return sanitized.strip()