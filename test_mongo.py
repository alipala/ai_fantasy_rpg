# test_mongo.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from db.client import MongoDBClient  # Add this import

load_dotenv()

# Your existing MongoDB connection test
try:
    client = MongoClient(os.getenv('MONGODB_URI'))
    dbs = client.list_database_names()
    print("Connected to MongoDB. Available databases:", dbs)
except Exception as e:
    print("MongoDB connection error:", e)

# Your existing data fetch test
try:
    db = client['fantasy_game']
    print("\nAll stored images:")
    print(list(db.completion_images.find()))
except Exception as e:
    print("Error storage problem error:", e)

# Add new tests using MongoDBClient
print("\n=== Testing MongoDBClient Features ===")

try:
    mongo_client = MongoDBClient()
    
    # Test indexes
    print("\nIndexes in completion_images collection:")
    print(mongo_client.completion_images.index_information())
    
    # Test recent completions
    print("\nMost recent 5 completions:")
    recent = mongo_client.get_recent_completions(limit=5)
    for completion in recent:
        print(f"- {completion['character_name']} in {completion['world_name']} ({completion['created_at']})")
    
    # Test cleanup (commented out for safety)
    # Uncomment these lines when you want to test cleanup
    # count = mongo_client.cleanup_old_images(days_old=60)
    # print(f"\nCleaned up {count} old records")
    
    mongo_client.close()
    
except Exception as e:
    print(f"Error testing MongoDBClient features: {e}")

print("\n=== Testing Complete ===")