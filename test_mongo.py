from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

try:
    client = MongoClient(os.getenv('MONGODB_URI'))
    dbs = client.list_database_names()
    print("Connected to MongoDB. Available databases:", dbs)
except Exception as e:
    print("MongoDB connection error:", e)


try:
    db = client['fantasy_game']
    print(list(db.completion_images.find()))
except Exception as e:
    print("Eror storage problem error:", e)