from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

db = Database()

async def connect_to_mongo():
    """Connect to MongoDB only if not already connected"""
    if db.client is not None and db.db is not None:
        return  # Already connected

    try:
        db.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=50,
            socketTimeoutMS=30000,
            connectTimeoutMS=30000,
            serverSelectionTimeoutMS=5000
        )
        await db.client.admin.command('ping')
        db.db = db.client[settings.DB_NAME]
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        raise RuntimeError("Database connection failed") from e


async def close_mongo_connection():
    """Close MongoDB connection gracefully"""
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed")
        db.client = None
        db.db = None

def get_db() -> AsyncIOMotorDatabase:
    if db.db is None:
        raise RuntimeError("MongoDB not initialized - call connect_to_mongo() first")
    return db.db

def get_user_collection():
    """Get users collection with validation"""
    return get_db().users

def get_artwork_collection():
    """Get artworks collection with validation"""
    return get_db().artworks

def get_wallet_collection():
    """Get wallets collection with validation"""
    return get_db().wallets