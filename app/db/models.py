from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, Field, StringConstraints, ConfigDict
from enum import Enum

class UserRole(str, Enum):
    ARTIST = "artist"
    ADMIN = "admin"
    USER = "user"

class UserBase(BaseModel):
    email: EmailStr = Field(description="Used for authentication")
    username: Annotated[str, StringConstraints(
        min_length=3, 
        max_length=50, 
        pattern=r"^[a-zA-Z0-9_]+$"
    )] = Field(description="Public display name")
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = Field(default=UserRole.ARTIST)

    model_config = ConfigDict(
        populate_by_name=True,  # Replaces allow_population_by_field_name
        str_strip_whitespace=True
    )

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserInDB(UserBase):
    id: str = Field(..., alias="_id")
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    wallet_address: Optional[str] = None

class UserOut(BaseModel):
    id: str = Field(..., alias="_id")
    email: EmailStr
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    wallet_address: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    username: Optional[Annotated[str, StringConstraints(
        min_length=3, 
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$"
    )]] = None

class ArtworkBase(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    ipfs_hash: str = Field(description="CID of the uploaded artwork")
    blockchain_tx: str = Field(description="Transaction hash of NFT minting")
    price: float = Field(..., gt=0)
    royalty_percentage: float = Field(..., ge=0, le=50)

class ArtworkCreate(ArtworkBase):
    pass

class ArtworkInDB(ArtworkBase):
    id: str = Field(..., alias="_id")
    artist_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_verified: bool = False

    model_config = ConfigDict(populate_by_name=True)

class WalletBase(BaseModel):
    address: Annotated[str, StringConstraints(pattern=r"^0x[a-fA-F0-9]{40}$")]
    balance: float = Field(default=0.0, ge=0)

class WalletInDB(WalletBase):
    id: str = Field(..., alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    private_key: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
    user_id: Optional[str] = None
    exp: Optional[datetime] = None
