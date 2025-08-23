# Add this at the top of your models.py
from pydantic import BaseModel, Field, ConfigDict, validator, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue
from pydantic import GetCoreSchemaHandler
from web3 import Web3

# Simple ObjectId handling for Pydantic v2
class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.with_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v: Any, info: core_schema.ValidationInfo) -> str:
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return v
            raise ValueError("Invalid ObjectId string")
        raise ValueError("Invalid ObjectId type")

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: JsonSchemaValue, handler) -> JsonSchemaValue:
        schema.update(type="string", format="objectid")
        return schema

# Base model configuration
class MongoModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

# License Type Enum
class LicenseType(str, Enum):
    PERSONAL = "PERSONAL"
    COMMERCIAL = "COMMERCIAL"
    EXCLUSIVE = "EXCLUSIVE"

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

class BaseDocument(BaseModel):
    """Base model for all MongoDB documents"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        from_attributes=True
    )

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

class UserCreate(UserBase):
    wallet_address: str
    email: str | None = None
    
    @validator('email', pre=True, always=True)
    def set_default_email(cls, v, values):
        if v is None:
            return f"{values['wallet_address']}@wallet"
        return v

class UserUpdate(BaseModel):
    email: Optional[str] = Field(
        None, 
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    profile_image: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)

class UserInDB(UserBase, BaseDocument):
    """User model for database storage with MongoDB _id"""
    pass

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
    model_config = ConfigDict(
        json_encoders={ObjectId: str},
        populate_by_name=True
    )

    @classmethod
    def validate_document(cls, document: dict):
        """Helper method to validate MongoDB documents"""
        if '_id' in document:
            document['id'] = str(document['_id'])
        return cls.model_validate(document)

class ArtworkBase(BaseModel):
    """Base model shared by all artwork models"""
    token_id: int = Field(..., gt=0, description="Unique blockchain token ID")
    creator_address: str = Field(
        ..., 
        min_length=42, 
        max_length=42,
        pattern=r"^0x[a-fA-F0-9]{40}$",
        description="Ethereum address of the creator"
    )
    owner_address: str = Field(
        ..., 
        min_length=42, 
        max_length=42,
        pattern=r"^0x[a-fA-F0-9]{40}$",
        description="Current owner's Ethereum address"
    )
    metadata_uri: str = Field(
        ..., 
        pattern=r"^(ipfs://|https?://).+",
        description="URI pointing to artwork metadata"
    )
    royalty_percentage: int = Field(
        ..., 
        ge=0, 
        le=2000,
        description="Royalty percentage in basis points (0-2000 = 0-20%)"
    )
    is_licensed: bool = Field(
        default=False,
        description="Whether the artwork is currently licensed"
    )
    title: Optional[str] = Field(
        None, 
        max_length=100,
        description="Human-readable title of the artwork"
    )
    description: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Detailed description of the artwork"
    )
    attributes: Optional[dict] = Field(
        None,
        description="Additional attributes as key-value pairs"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "token_id": 1,
                "creator_address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                "owner_address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                "metadata_uri": "ipfs://QmXJZx...",
                "royalty_percentage": 500,
                "is_licensed": False,
                "title": "Digital Masterpiece",
                "description": "A beautiful digital artwork",
                "attributes": {"color": "blue", "style": "abstract"}
            }
        }
    )

class ArtworkCreate(ArtworkBase):
    """Model for creating new artworks (excludes auto-generated fields)"""
    token_id: Optional[int] = Field(None, gt=0)  # Will be generated
    creator_address: Optional[str] = Field(None, min_length=42, max_length=42)  # Set from current user
    owner_address: Optional[str] = Field(None, min_length=42, max_length=42)  # Set from current user
    is_licensed: Optional[bool] = Field(False)  # Default value only
    created_at: Optional[datetime] = None  # Will be set on creation
    updated_at: Optional[datetime] = None  # Will be set on creation

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metadata_uri": "ipfs://QmXJZx...",
                "royalty_percentage": 500,
                "title": "Digital Masterpiece",
                "description": "A beautiful digital artwork",
                "attributes": {"color": "blue", "style": "abstract"}
            }
        }
    )

class ArtworkUpdate(BaseModel):
    """Model for updating existing artworks (only updatable fields)"""
    owner_address: Optional[str] = Field(
        None, 
        min_length=42, 
        max_length=42,
        pattern=r"^0x[a-fA-F0-9]{40}$",
        description="New owner's Ethereum address"
    )
    is_licensed: Optional[bool] = Field(
        None,
        description="Update license status"
    )
    title: Optional[str] = Field(
        None, 
        max_length=100,
        description="Updated title"
    )
    description: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Updated description"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Will be set to current time on update"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "owner_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "is_licensed": True,
                "title": "Updated Title",
                "description": "New description"
            }
        }
    )

class ArtworkInDB(ArtworkBase):
    """Complete model as stored in database"""
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def validate_document(cls, data: dict):
        """Helper to handle MongoDB document validation"""
        if '_id' in data and not isinstance(data['_id'], ObjectId):
            try:
                data['_id'] = ObjectId(data['_id'])
            except:
                data['_id'] = ObjectId()
        return cls(**data)

# In your models.py
class ArtworkPublic(ArtworkBase):
    """Public-facing model (excludes sensitive/internal fields)"""
    id: str = Field(..., description="String representation of MongoDB _id")
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db_model(cls, db_model: ArtworkInDB):
        """Convert from database model to public model"""
        data = db_model.model_dump(exclude={"_id", "id"}, exclude_none=True)
        return cls(
            **data,
            id=str(db_model.id)
        )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "token_id": 1,
                "creator_address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                "owner_address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                "metadata_uri": "ipfs://QmXJZx...",
                "royalty_percentage": 500,
                "is_licensed": False,
                "title": "Digital Masterpiece",
                "description": "A beautiful digital artwork",
                "attributes": {"color": "blue", "style": "abstract"},
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }
    )

import logging

logger = logging.getLogger(__name__)

class LicenseBase(BaseModel):
    """Base License model for API responses"""
    license_id: int
    token_id: int
    licensee_address: str
    licensor_address: str
    start_date: datetime
    end_date: datetime
    terms_hash: str
    license_type: str
    is_active: bool
    fee_paid: float
    created_at: datetime
    updated_at: datetime

class LicenseInDB(BaseModel):
    """License model for database storage"""
    id: Optional[str] = Field(alias="_id", default=None)
    license_id: int
    token_id: int
    licensee_address: str
    licensor_address: str
    start_date: datetime
    end_date: datetime
    terms_hash: str
    license_type: str
    is_active: bool = True
    fee_paid: float
    created_at: datetime
    updated_at: datetime
    transaction_data: Optional[Dict[str, Any]] = None
    revoked_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

    @classmethod
    def from_mongo(cls, data: dict):
        """Create LicenseInDB from MongoDB document with robust error handling"""
        try:
            if not data:
                raise ValueError("Empty document")
            
            # Handle ObjectId conversion
            if "_id" in data and isinstance(data["_id"], ObjectId):
                data["_id"] = str(data["_id"])
            
            # Ensure required fields exist
            required_fields = [
                "license_id", "token_id", "licensee_address", "licensor_address",
                "start_date", "end_date", "terms_hash", "license_type", "fee_paid"
            ]
            
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Handle datetime fields
            datetime_fields = ["start_date", "end_date", "created_at", "updated_at", "revoked_at"]
            for field in datetime_fields:
                if field in data and data[field] is not None:
                    if isinstance(data[field], str):
                        try:
                            data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                        except ValueError:
                            # Try parsing with different formats
                            from dateutil.parser import parse
                            data[field] = parse(data[field])
                    elif not isinstance(data[field], datetime):
                        logger.warning(f"Unexpected type for {field}: {type(data[field])}")
            
            # Set defaults for optional fields
            if "is_active" not in data:
                data["is_active"] = True
            if "created_at" not in data:
                data["created_at"] = datetime.utcnow()
            if "updated_at" not in data:
                data["updated_at"] = datetime.utcnow()
            
            return cls(**data)
            
        except Exception as e:
            logger.error(f"Failed to convert license document: {e}")
            logger.error(f"Document data: {data}")
            raise ValueError(f"Invalid license document: {str(e)}")

    def model_dump(self, **kwargs):
        """Override model_dump to handle MongoDB serialization"""
        data = super().model_dump(**kwargs)
        
        # Convert ObjectId to string if present
        if "_id" in data and isinstance(data["_id"], ObjectId):
            data["_id"] = str(data["_id"])
        
        return data


class License(BaseModel):
    """License model for API responses (simplified from LicenseInDB)"""
    license_id: int
    token_id: int
    licensee_address: str
    licensor_address: str
    start_date: datetime
    end_date: datetime
    terms_hash: str
    license_type: str
    is_active: bool
    fee_paid: float
    created_at: datetime
    updated_at: datetime
    revoked_at: Optional[datetime] = None

    @classmethod
    def from_mongo(cls, data: dict):
        """Create License from MongoDB document - SIMPLIFIED VERSION"""
        try:
            # Create a copy to avoid modifying the original
            license_data = dict(data)
            
            # Convert ObjectId to string if present
            if '_id' in license_data:
                license_data['id'] = str(license_data['_id'])
                del license_data['_id']
            
            # Remove any fields that aren't in the License model
            expected_fields = {
                'license_id', 'token_id', 'licensee_address', 'licensor_address',
                'start_date', 'end_date', 'terms_hash', 'license_type', 'is_active',
                'fee_paid', 'created_at', 'updated_at', 'revoked_at'
            }
            
            # Only keep fields that are in the License model
            filtered_data = {k: v for k, v in license_data.items() if k in expected_fields}
            
            return cls(**filtered_data)
            
        except Exception as e:
            logger.error(f"Failed to create License from mongo: {e}")
            logger.error(f"Document data: {data}")
            raise

class LicenseListResponse(BaseModel):
    """Response model for license listings"""
    licenses: List[License]
    total: int
    page: int
    size: int
    has_next: bool

# License Create Model
class LicenseCreate(MongoModel):
    token_id: int
    licensee_address: str
    duration_days: int
    terms_hash: str
    license_type: LicenseType



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

class TransactionInDB(TransactionCreate):
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_mongo(cls, data: dict):
        """Convert MongoDB document to Pydantic model"""
        if "_id" in data:
            data["id"] = str(data["_id"])
        return cls(**data)

class TransactionPublic(TransactionBase):
    id: str
    created_at: datetime
    updated_at: datetime

class PaginatedResponse(BaseModel):
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1, le=100)
    has_next: bool

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

class TokenMetadata(BaseModel):
    name: str
    description: str
    image: str
    attributes: List[dict]
    external_url: Optional[str] = None
    animation_url: Optional[str] = None

class SaleConfirmation(BaseModel):
    tx_hash: str
    token_id: int
    buyer_address: str
    seller_address: str
    sale_price: str

    class Config:
        # This allows the model to be created from JSON/dict
        from_attributes = True