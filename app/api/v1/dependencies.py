from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user

async def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only"
        )
    return current_user

async def get_current_normal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users only"
        )
    return current_user
