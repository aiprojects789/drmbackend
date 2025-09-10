from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
# DB_NAME = os.getenv("DB_NAME", "image_dedupe_db")
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]