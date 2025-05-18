from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Annotated

from app.core.security import (
    create_access_token, 
    get_password_hash, 
    verify_password,
    decode_token,
    oauth2_scheme
)
from app.core.config import settings
from app.db.database import get_user_collection
from app.db.models import UserCreate, Token
from app.db.schemas import UserSchema

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserSchema)
async def signup(user: UserCreate):
    user_collection = get_user_collection()
    
    existing_user = await user_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    
    user_dict = user.dict()
    user_dict.update({
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "wallet_address": None
    })
    del user_dict["password"]
    
    result = await user_collection.insert_one(user_dict)
    created_user = await user_collection.find_one({"_id": result.inserted_id})
    
    return UserSchema(**created_user)

async def authenticate_user(email: str, password: str):
    user_collection = get_user_collection()
    user = await user_collection.find_one({"email": email})
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
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
            "user_id": str(user["_id"]),  # Ensure this matches validation
            "wallet_address": user.get("wallet_address", "")
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

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