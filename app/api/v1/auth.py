from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta    
from app.db.models import ForgotPasswordRequest, UserEmailRequest, UserCreate, UserOut, Token  
from app.core.security import (
    create_access_token, 
    get_password_hash, 
    verify_password,
    decode_token,
    get_current_user
)
from app.core.config import settings
from app.db.database import get_user_collection, connect_to_mongo
from .email import send_email

import logging
from bson import ObjectId
import random
import time

router = APIRouter(
    tags=["Auth"],
    prefix="/auth"
)

logger = logging.getLogger(__name__)

otp_store = {}  # In-memory OTP store

@router.post("/signup", response_model=UserOut)
async def signup(user: UserCreate):
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
async def forgot_password(payload: ForgotPasswordRequest):
    await connect_to_mongo()
    user_collection = get_user_collection()
    user = await user_collection.find_one({"email": payload.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = str(random.randint(100000, 999999))
    otp_store[payload.email] = {"otp": otp, "timestamp": time.time()}

    subject = "Your OTP for Password Reset"
    body = f"Your OTP is {otp}. It is valid for 5 minutes."

    try:
        send_email(subject, body, payload.email)
        return {"message": "OTP sent to your email"}
    except Exception as e:
        logger.error(f"Failed to send OTP email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")

@router.post("/verify-otp")
async def verify_otp(email: str = Body(...), otp: str = Body(...)):
    otp_data = otp_store.get(email)
    if not otp_data:
        raise HTTPException(status_code=404, detail="No OTP found")

    if time.time() - otp_data["timestamp"] > 300:
        del otp_store[email]
        raise HTTPException(status_code=400, detail="OTP expired")

    if otp_data["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    return {"message": "OTP verified"}

@router.post("/reset-password")
async def reset_password(email: str = Body(...), otp: str = Body(...), new_password: str = Body(...)):
    otp_data = otp_store.get(email)
    if not otp_data or otp_data["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    await connect_to_mongo()
    user_collection = get_user_collection()
    user = await user_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = get_password_hash(new_password)
    await user_collection.update_one(
        {"email": email},
        {"$set": {
            "hashed_password": hashed_password,
            "updated_at": datetime.utcnow()
        }}
    )

    del otp_store[email]
    return {"message": "Password reset successfully"}

# ✅ NEW: Find User by Email Endpoint
@router.post("/find-user")
async def find_user(payload: UserEmailRequest):
    await connect_to_mongo()
    user_collection = get_user_collection()
    user = await user_collection.find_one({"email": payload.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User found with email {payload.email}"}
