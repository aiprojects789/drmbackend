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
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()  # Add issued at timestamp
    })

    # Debug logging
    logger.debug(f"Creating token with data: {to_encode}")
    logger.debug(f"Using JWT_SECRET_KEY: {settings.JWT_SECRET_KEY[:10]}...")
    logger.debug(f"Using JWT_ALGORITHM: {settings.JWT_ALGORITHM}")

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        # Validate the token was created properly
        token_parts = encoded_jwt.split('.')
        logger.debug(f"Generated JWT has {len(token_parts)} parts")
        logger.debug(f"JWT preview: {encoded_jwt[:50]}...")
        
        if len(token_parts) != 3:
            logger.error(f"Invalid JWT format generated! Parts: {len(token_parts)}")
            raise Exception("Failed to generate valid JWT")
            
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Error creating JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create authentication token"
        )


def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token and return payload if valid"""
    try:
        # Check token format first
        token_parts = token.split('.')
        logger.debug(f"Received token has {len(token_parts)} parts")
        
        if len(token_parts) != 3:
            logger.error(f"Invalid token format: expected 3 parts, got {len(token_parts)}")
            return None
            
        # Debug the settings being used
        logger.debug(f"Decoding with JWT_SECRET_KEY: {settings.JWT_SECRET_KEY[:10]}...")
        logger.debug(f"Decoding with JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
        
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        logger.debug(f"Successfully decoded token payload: {payload}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token error: {e}")
        return None
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {e}")
        return None


async def get_current_user(token: HTTPAuthorizationCredentials = Depends(http_bearer)):
    """Dependency to extract current user from JWT"""
    if token is None:
        logger.error("Authorization header missing")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization header missing"
        )

    logger.debug(f"Processing token: {token.credentials[:20]}...")
    
    payload = decode_token(token.credentials)
    if payload is None:
        logger.error("Token decode failed")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token"
        )

    # Debug info
    logger.debug(f"Token payload: {payload}")

    # Verify required claims
    required_claims = ["sub", "user_id", "exp"]
    for claim in required_claims:
        if claim not in payload:
            logger.error(f"Missing required claim: {claim}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required claim: {claim}"
            )

    logger.debug(f"Authentication successful for user: {payload['sub']}")
    
    return {
        "email": payload["sub"],  # Add email field for compatibility
        "sub": payload["sub"],
        "user_id": payload["user_id"],
        "wallet_address": payload.get("wallet_address", ""),
        "role": payload.get("role", "user")
    }


async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    """Dependency that ensures the current user is an admin"""
    if current_user.get("role") != "admin":
        logger.warning(f"Non-admin user {current_user.get('email')} attempted admin access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    return current_user