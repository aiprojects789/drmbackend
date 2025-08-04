from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import logging
from bson import ObjectId

from app.core.security import (
    create_access_token, 
    get_password_hash, 
    verify_password,
    decode_token,
    get_current_user
)
from app.core.config import settings
from app.db.models import UserCreate, UserOut, Token
from app.db.database import get_user_collection, connect_to_mongo

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

@router.post("/signup", response_model=UserOut)
async def signup(user: UserCreate):
    """User registration endpoint"""
    try:
        await connect_to_mongo()
        user_collection = get_user_collection()

        if await user_collection.find_one({"email": user.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        user_data = {
            "_id": str(ObjectId()),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "hashed_password": get_password_hash(user.password),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "wallet_address": None
        }

        await user_collection.insert_one(user_data)
        return UserOut(**user_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

async def authenticate_user(email: str, password: str):
    """Authenticate user credentials"""
    try:
        user_collection = get_user_collection()
        user = await user_collection.find_one({"email": email})
        
        if not user or not verify_password(password, user["hashed_password"]):
            return None
            
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return None

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """User login endpoint"""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={
            "sub": user["email"],
            "user_id": str(user["_id"]),
            "wallet_address": user.get("wallet_address", "")
        }
    )
    
    logger.info(f"User logged in: {user['email']}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/update-password")
async def update_password(
    current_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user)
):
    """Update user password"""
    try:
        user_collection = get_user_collection()
        user = await user_collection.find_one({"email": current_user["email"]})
        
        if not user or not verify_password(current_password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        hashed_password = get_password_hash(new_password)
        await user_collection.update_one(
            {"email": current_user["email"]},
            {"$set": {
                "hashed_password": hashed_password,
                "updated_at": datetime.utcnow()
            }}
        )
        
        logger.info(f"Password updated for user: {current_user['email']}")
        return {"message": "Password updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password update failed"
        )

@router.post("/forgot-password")
async def forgot_password(email: str):
    """Initiate password reset"""
    return {"message": "If your email is registered, you'll receive a password reset link"}

@router.post("/reset-password")
async def reset_password(token: str, new_password: str):
    """Complete password reset with token"""
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_collection = get_user_collection()
    user = await user_collection.find_one({"email": payload["sub"]})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    hashed_password = get_password_hash(new_password)
    await user_collection.update_one(
        {"email": payload["sub"]},
        {"$set": {
            "hashed_password": hashed_password,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {"message": "Password updated successfully"}