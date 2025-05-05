from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_admin_user  # You'll need to implement this

router = APIRouter(
    tags=["Admin"],
    prefix="/admin",
    dependencies=[Depends(get_current_admin_user)]  # Protects all admin routes
)

@router.get("/users")
async def list_users():
    """List all users (admin only)"""
    return {"users": []}  # Implement actual user listing

@router.get("/flagged-artworks")
async def get_flagged_artworks():
    """Get all flagged artworks (admin only)"""
    return {"artworks": []}  # Implement actual artwork listing