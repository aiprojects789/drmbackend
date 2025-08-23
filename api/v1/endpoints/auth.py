from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.models import UserCreate, UserInDB, User
from db.database import get_database
from core.security import create_access_token, verify_token
from datetime import timedelta
from core.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.post("/connect-wallet", response_model=dict)
async def connect_wallet(user_data: UserCreate):
    try:
        db = get_database()
        existing_user = await db.users.find_one({"wallet_address": user_data.wallet_address})
        
        current_time = datetime.utcnow()
        
        if existing_user:
            # Ensure required fields exist
            existing_user['_id'] = str(existing_user['_id'])
            if 'created_at' not in existing_user:
                existing_user['created_at'] = current_time
            if 'updated_at' not in existing_user:
                existing_user['updated_at'] = current_time
            
            # Update last login time
            await db.users.update_one(
                {"_id": existing_user["_id"]},
                {"$set": {"updated_at": current_time}}
            )
            
            return {
                "access_token": create_access_token(
                    data={"sub": user_data.wallet_address},
                    expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                ),
                "token_type": "bearer",
                "user": User(**existing_user).model_dump()
            }
        else:
            # Create new user with current timestamps
            user_dict = user_data.model_dump()
            user_dict.update({
                "created_at": current_time,
                "updated_at": current_time
            })
            
            result = await db.users.insert_one(user_dict)
            created_user = await db.users.find_one({"_id": result.inserted_id})
            created_user['_id'] = str(created_user['_id'])
            
            return {
                "access_token": create_access_token(
                    data={"sub": user_data.wallet_address},
                    expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                ),
                "token_type": "bearer",
                "user": User(**created_user).model_dump()
            }
            
    except Exception as e:
        logger.error(f"Error connecting wallet: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect wallet"
        )

@router.get("/me", response_model=User)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = verify_token(token)
        wallet_address = payload.get("sub")
        
        if not wallet_address:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        db = get_database()
        user_doc = await db.users.find_one({"wallet_address": wallet_address})
        
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Ensure required fields exist
        user_doc['_id'] = str(user_doc['_id'])
        current_time = datetime.utcnow()
        
        if 'created_at' not in user_doc:
            user_doc['created_at'] = current_time
            await db.users.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"created_at": current_time}}
            )
        
        if 'updated_at' not in user_doc:
            user_doc['updated_at'] = current_time
            await db.users.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"updated_at": current_time}}
            )
        
        return User(**user_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")