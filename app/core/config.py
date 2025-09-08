import os
from typing import List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    MONGODB_URI: str = "mongodb+srv://aiprojects789:IP1NwVwaBM0TosQI@drm.cmnzpag.mongodb.net/"
    DB_NAME: str = "art_drm_local"

    # JWT / Security
    JWT_SECRET_KEY: str = "default-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Blockchain
    WEB3_PROVIDER_URL: str = "https://eth-sepolia.g.alchemy.com/v2/hnme_NBd2tOrddwow5UZv"
    CONTRACT_ADDRESS: str = "0xA07F45FE615E86C6BE90AD207952497c6F23d69d"
    DEMO_MODE: bool = False

    # CORS - Handle comma-separated string from environment
    ALLOWED_ORIGINS_STR: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Parse ALLOWED_ORIGINS from comma-separated string"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_STR.split(',') if origin.strip()]

    # IPFS / Pinata
    PINATA_API_KEY: Optional[str] = None
    PINATA_SECRET_API_KEY: Optional[str] = None
    NFT_STORAGE_API_KEY: Optional[str] = None
    WEB3_STORAGE_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"  

settings = Settings()
