from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None  # Fixed: Mark as Optional

db = Database()

async def connect_to_mongo():
    """Connect to MongoDB and initialize the client"""
    db.client = AsyncIOMotorClient(settings.MONGODB_URI)
    await db.client.admin.command('ping')  # Test connection
    print("Connected to MongoDB")

async def close_mongo_connection():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")

def get_database():
    """Get database instance"""
    if not db.client:
        raise RuntimeError("MongoDB client not initialized")
    return db.client[settings.DB_NAME]

def get_user_collection():
    """Get users collection"""
    return get_database().users  # Better than get_collection()

def get_artwork_collection():
    """Get artworks collection"""
    return get_database().artworks

def get_wallet_collection():
    """Get wallets collection"""
    return get_database().wallets