from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from datetime import datetime, timedelta

# Authentication schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
http_bearer = HTTPBearer(auto_error=False)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(token: str = Depends(http_bearer)):
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization header missing"
        )
    
    try:
        payload = decode_token(token.credentials)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token"
            )
        
        # Add these debug prints
        print("Token payload:", payload)
        print("Expected secret:", settings.JWT_SECRET_KEY)
        print("Expected algorithm:", settings.JWT_ALGORITHM)
        
        # Verify required claims
        required_claims = ["sub", "user_id", "exp"]
        for claim in required_claims:
            if claim not in payload:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required claim: {claim}"
                )
        
        return {
            "sub": payload["sub"],
            "user_id": payload["user_id"],
            "wallet_address": payload.get("wallet_address", "")
        }
        
    except JWTError as e:
        print("JWT Validation error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token validation failed"
        )