from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb+srv://aiprojects789:IP1NwVwaBM0TosQI@drm.cmnzpag.mongodb.net/"  
    DB_NAME: str = "art_drm_local"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Add these with empty defaults for local development
    IPFS_API_KEY: str = ""
    IPFS_API_SECRET: str = ""
    WEB3_PROVIDER_URL: str = "https://polygon-rpc.com" 
    CONTRACT_ADDRESS: str = "0x0000000000000000000000000000000000000000"
    class Config:
        env_file = ".env"
        extra = "ignore"  

settings = Settings()