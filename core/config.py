from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Database
    MONGODB_URL: str = "mongodb+srv://aiprojects789:IP1NwVwaBM0TosQI@drm.cmnzpag.mongodb.net/art_drm?"
    DATABASE_NAME: str = "artdrm_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Blockchain
    WEB3_PROVIDER_URL: str = "https://eth-sepolia.g.alchemy.com/v2/hnme_NBd2tOrddwow5UZv"
    CONTRACT_ADDRESS: str = "0xA07F45FE615E86C6BE90AD207952497c6F23d69d"
    DEMO_MODE: bool = False
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    PINATA_API_KEY: str = "15d20f41a94ec41765cb"
    PINATA_SECRET_API_KEY: str = "5f18bb2ce12f5d2976a133c036bae4b7263eacb548e77af57e4a6ad9792993fd"

    NFT_STORAGE_API_KEY: Optional[str] = None
    WEB3_STORAGE_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()