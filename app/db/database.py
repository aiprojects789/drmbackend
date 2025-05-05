import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

def create_mongo_client():
    return AsyncIOMotorClient(
        settings.MONGODB_URL,
        tlsCAFile=certifi.where(),
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=30000
    )

client = create_mongo_client()
db = client.get_database()

async def init_db():
    try:
        await client.admin.command('ping')
        print("Successfully connected to MongoDB Atlas")
        
        # Create indexes (now using async properly)
        await db.users.create_index([("email", 1)], unique=True)
        await db.artworks.create_index([("ipfs_hash", 1)], unique=True)
    except Exception as e:
        print(f"Database connection error: {e}")
        # Application will continue running without indexes