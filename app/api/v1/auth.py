from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Annotated
import logging

from app.core.security import (
    create_access_token, 
    get_password_hash, 
    verify_password,
    decode_token,
    oauth2_scheme
)
from app.core.config import settings
from bson import ObjectId
from app.db.models import UserCreate, UserOut, UserRole, Token
from app.db.database import get_user_collection
from app.core.security import get_password_hash

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

from app.db.database import connect_to_mongo  # Ensure it's imported

@router.post("/signup", response_model=UserOut)
async def signup(user: UserCreate):
    """User registration endpoint"""
    try:
        # Ensure MongoDB connection is alive (important for Vercel / serverless)
        await connect_to_mongo()

        user_collection = get_user_collection()

        if user_collection is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database not initialized"
            )

        # Check if user already exists
        if await user_collection.find_one({"email": user.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Prepare user data
        user_data = {
            "_id": str(ObjectId()),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "hashed_password": get_password_hash(user.password),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "wallet_address": None
        }

        # Insert user
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
    """Authenticate user with email and password"""
    try:
        user_collection = get_user_collection()
        user = await user_collection.find_one({"email": email})
        
        if not user or not verify_password(password, user["hashed_password"]):
            return False
            
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return False

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """User login endpoint"""
    try:
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user["email"],
                "user_id": str(user["_id"]),
                "wallet_address": user.get("wallet_address", "")
            },
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/forgot-password")
async def forgot_password(email: str):
    return {"message": "If your email is registered, you'll receive a password reset link"}

@router.post("/reset-password")
async def reset_password(token: str, new_password: str):
    payload = decode_token(token)
    if not payload or "email" not in payload:
     raise HTTPException(status_code=401, detail="Invalid or expired token.")

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    
    user_collection = get_user_collection()
    user = await user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    hashed_password = get_password_hash(new_password)
    await user_collection.update_one(
        {"email": email},
        {"$set": {"hashed_password": hashed_password, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Password updated successfully"}

@router.post("/update-password")
async def update_password(
    current_password: str,
    new_password: str,
    token: str = Depends(oauth2_scheme)  # Now using the locally defined scheme
):
    payload = decode_token(token)
    if not payload or "email" not in payload:
     raise HTTPException(status_code=401, detail="Invalid or expired token.")

    
    email = payload.get("sub")
    user_collection = get_user_collection()
    user = await user_collection.find_one({"email": email})
    
    if not user or not verify_password(current_password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    hashed_password = get_password_hash(new_password)
    await user_collection.update_one(
        {"email": email},
        {"$set": {"hashed_password": hashed_password, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Password updated successfully"}