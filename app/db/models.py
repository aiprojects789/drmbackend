from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class UserRole(str, Enum):
    artist = "artist"
    admin = "admin"

class User(BaseModel):
    email: str
    hashed_password: str
    wallet_address: Optional[str] = None
    role: UserRole = UserRole.artist
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Artwork(BaseModel):
    title: str
    description: str
    ipfs_hash: str
    creator_email: str
    license_type: str
    token_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_flagged: bool = False