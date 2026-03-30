import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "library_db")

client = AsyncIOMotorClient(MONGODB_URL)
database = client[MONGODB_DB_NAME]

async def get_db():
    yield database
