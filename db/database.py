import email
from enum import unique
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def connect_to_mongo():
    try:
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db.database = db.client[settings.DATABASE_NAME]
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    try:
        # Users collection indexes
        await db.database.users.create_index("wallet_address", unique=True)
        await db.database.users.create_index([("email", 1)], unique=True, sparse=True)
        
        # Artworks collection indexes  
        await db.database.artworks.create_index("token_id", unique=True)
        await db.database.artworks.create_index("creator_address")
        await db.database.artworks.create_index("owner_address")
        
        # Licenses collection indexes
        await db.database.licenses.create_index("token_id")
        await db.database.licenses.create_index("licensee_address")
        await db.database.licenses.create_index("license_id", unique=True)
        
        # Transactions collection indexes
        await db.database.transactions.create_index("tx_hash", unique=True)
        await db.database.transactions.create_index("from_address")
        await db.database.transactions.create_index("to_address")
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")

def get_database():
    return db.database