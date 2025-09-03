from pydantic import BaseModel, Field, ConfigDict, validator, field_validator,EmailStr,StringConstraints
from typing import Optional, List, Any, Dict,Annotated
from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue
from pydantic import GetCoreSchemaHandler
from web3 import Web3
import uuid
import logging


class UserBase(BaseModel):
    wallet_address: str = Field(..., min_length=42, max_length=42)
    email: Optional[str] = None 
    created_at: Optional[datetime] = None  # Make optional
    updated_at: Optional[datetime] = None  # Make optional
    
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    is_verified: bool = False
    profile_image: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)

    @field_validator('created_at', 'updated_at', mode='before')
    def parse_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(str(v))
        except (TypeError, ValueError):
            return None
    
    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        try:
            return Web3.to_checksum_address(v)
        except ValueError:
            raise ValueError("Invalid Ethereum address")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class UserPublic(UserBase):
    """Public user model with string ID and timestamps"""
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

class User(UserPublic):
    """Main User model that extends UserPublic"""

    id: str = Field(..., alias="_id")
    model_config = ConfigDict(
        populate_by_name=True
    )

class WalletConnectRequest(BaseModel):
    wallet_address: str

class UserRole(str, Enum):
    ARTIST = "artist"
    ADMIN = "admin"
    USER = "user"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class UserEmailRequest(BaseModel):
    email: str


class UserCreate(UserBase):
    wallet_address: str
    password: str = Field(..., min_length=8)
    full_name: str
    

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
    role: Optional[str] = None
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
    role: Optional[str] = Field(None)
    is_active: Optional[bool] = None 
    


from bson import ObjectId
from pydantic import BaseModel
from typing import Any

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> ObjectId:
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError(f"Invalid ObjectId: {v}")

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema):
        """
        Replaces __modify_schema__ in Pydantic v2.
        Makes Swagger/OpenAPI show this field as a string.
        """
        return {
            "type": "string",
            "examples": ["64d2c4e5f12a3b0012345678"]
        }

class ArtworkBase(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    token_id: int
    creator_address: str
    owner_address: str
    metadata_uri: str
    royalty_percentage: int
    is_licensed: bool
    title: str
    description: str
    attributes: dict
    created_at: str
    updated_at: str

    class Config:
        validate_by_name = True       # renamed from allow_population_by_field_name
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ArtworkCreate(ArtworkBase):
    pass

class ArtworkInDB(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    token_id: int
    creator_address: str
    owner_address: str
    metadata_uri: str
    royalty_percentage: int
    is_licensed: bool
    title: str
    description: str
    attributes: Dict
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}

    @classmethod
    def validate_document(cls, doc):
        try:
            return cls.model_validate(doc)
        except Exception as e:
            print(f"Skipping invalid artwork: {e} | Raw doc: {doc}")
            return None


# --- Public-facing Model ---
class ArtworkPublic(BaseModel):
    id: str = Field(..., description="String representation of MongoDB _id")
    token_id: int
    creator_address: str
    owner_address: str
    metadata_uri: str
    royalty_percentage: int
    is_licensed: bool
    title: str
    description: str
    attributes: Dict
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db_model(cls, db_model: ArtworkInDB):
        data = db_model.model_dump(by_alias=True, exclude_none=True)
        data["id"] = str(data["_id"])
        return cls(**data)
# --- Artwork Update Model ---
class ArtworkUpdate(BaseModel):
    owner_address: Optional[str] = Field(
        None, min_length=42, max_length=42,
        pattern=r"^0x[a-fA-F0-9]{40}$",
        description="New owner's Ethereum address"
    )
    is_licensed: Optional[bool] = None
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    updated_at: Optional[datetime] = None


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



class SaleConfirmation(BaseModel):
    tx_hash: str
    token_id: int
    buyer_address: str
    seller_address: str
    sale_price: str

    class Config:
        # This allows the model to be created from JSON/dict
        from_attributes = True
class TransactionType(str, Enum):
    REGISTER = "REGISTER"
    GRANT_LICENSE = "GRANT_LICENSE"
    REVOKE_LICENSE = "REVOKE_LICENSE"
    TRANSFER = "TRANSFER"
    ROYALTY_PAYMENT = "ROYALTY_PAYMENT"
    SALE = "SALE"

class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    
class TransactionCreate(BaseModel):
    tx_hash: str = Field(..., min_length=66, max_length=66)
    from_address: str = Field(..., min_length=42, max_length=42)
    to_address: Optional[str] = Field(None, min_length=42, max_length=42)
    transaction_type: TransactionType
    value: Optional[float] = Field(None, ge=0)
    status: TransactionStatus = TransactionStatus.PENDING
    metadata: Optional[dict] = {}

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    gas_used: Optional[int] = Field(None, gt=0)
    gas_price: Optional[int] = Field(None, gt=0)
    block_number: Optional[int] = Field(None, gt=0)


class TransactionBase(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    tx_hash: str = Field(..., min_length=66, max_length=66)
    from_address: str = Field(..., min_length=42, max_length=42)
    to_address: Optional[str] = Field(None, min_length=42, max_length=42)
    transaction_type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING
    gas_used: Optional[int] = Field(None, gt=0)
    gas_price: Optional[int] = Field(None, gt=0)
    value: Optional[float] = Field(None, ge=0)  # In ETH
    block_number: Optional[int] = Field(None, gt=0)
    metadata: Optional[dict] = {}

class PaginatedResponse(BaseModel):
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1, le=100)
    has_next: bool
class TransactionPublic(TransactionBase):
    id: str
    created_at: datetime
    updated_at: datetime

class ArtworkListResponse(PaginatedResponse):
    artworks: List[ArtworkPublic]
    has_next: bool

class TransactionListResponse(PaginatedResponse):
    transactions: List[TransactionPublic]
    has_next: bool

class Web3ConnectionStatus(BaseModel):
    connected: bool
    account: Optional[str] = Field(None, min_length=42, max_length=42)
    chain_id: Optional[str] = None
    network_name: Optional[str] = None
    balance: Optional[str] = None

class ContractCallRequest(BaseModel):
    function_name: str
    parameters: List[Any] = []
    from_address: Optional[str] = Field(None, min_length=42, max_length=42)
    value: Optional[str] = Field(None, pattern=r"^[0-9]+$")

class ContractCallResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    tx_hash: Optional[str] = Field(None, min_length=66, max_length=66)

