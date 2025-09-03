from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Authentication scheme
http_bearer = HTTPBearer(auto_error=True)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hashed version"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token with expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})

    logger.debug(f"Creating token with data: {to_encode}")

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,        # ✅ Matches .env
        algorithm=settings.JWT_ALGORITHM  # ✅ Matches .env
    )


def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token and return payload if valid"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"Token decode error: {str(e)}")
        return None


async def get_current_user(token: HTTPAuthorizationCredentials = Depends(http_bearer)):
    """Dependency to extract current user from JWT"""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization header missing"
        )

    payload = decode_token(token.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token"
        )

    # Debug info
    logger.debug(f"Token payload: {payload}")
    logger.debug(f"Expected secret: {settings.JWT_SECRET_KEY}")
    logger.debug(f"Expected algorithm: {settings.JWT_ALGORITHM}")

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
        "wallet_address": payload.get("wallet_address", ""),
        "role": payload.get("role", "user")  # ✅ Added role so admin check works
    }


async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    """Dependency that ensures the current user is an admin"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    return current_user
