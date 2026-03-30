import os
from pymongo import MongoClient

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "library_db")

client = MongoClient(MONGODB_URL)
database = client[MONGODB_DB_NAME]

def get_db():
    return database
