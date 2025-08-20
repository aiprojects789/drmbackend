from fastapi import APIRouter, Depends, HTTPException, status
from app.db.database import get_artwork_collection,get_user_collection, connect_to_mongo,get_db
from datetime import datetime,timedelta
from app.db.models import UserCreate, UserOut, UserUpdate, ArtworkCreate
from app.core.security import get_current_admin_user, get_password_hash  # Import the admin user dependency
from bson import ObjectId
from pydantic import BaseModel
from bson.errors import InvalidId

import logging
router = APIRouter(
    tags=["Admin"],
    prefix="/admin"
)

logger = logging.getLogger(__name__)

@router.get("/flagged-artworks")
async def get_flagged_artworks(current_admin: dict = Depends(get_current_admin_user)):
    """Get all flagged artworks (admin only)"""
    return {"artworks": []}  # Placeholder

@router.get("/users/summary-full")
async def users_summary_full(page: int = 1, limit: int = 50, current_admin: dict = Depends(get_current_admin_user)):
    users_collection = get_user_collection()

    total_users = await users_collection.count_documents({})
    active_users = await users_collection.count_documents({"is_active": True})

    # Get admin users and serialize ObjectId
    raw_admin_users = await users_collection.find({"role": "admin"}, {"hashed_password": 0}).to_list(length=None)
    admin_users = [
        {
            "id": str(user["_id"]),
            "username": user.get("username"),
            "email": user.get("email"),
            "is_active": user.get("is_active"),
            "created_at": user.get("created_at").isoformat() if user.get("created_at") else None
        }
        for user in raw_admin_users
    ]

    # New users this week (Pakistan time)
    utc_now = datetime.utcnow()
    pk_offset = timedelta(hours=5)
    pk_now = utc_now + pk_offset
    start_of_week_pk = pk_now - timedelta(days=pk_now.weekday())
    start_of_week_pk = start_of_week_pk.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week_utc = start_of_week_pk - pk_offset
    new_users_this_week = await users_collection.count_documents({"created_at": {"$gte": start_of_week_utc}})

    skip = (page - 1) * limit
    cursor = users_collection.find({}, {"hashed_password": 0}).sort("created_at", -1).skip(skip).limit(limit)

    users_list = []
    async for user in cursor:
        users_list.append({
            "id": str(user["_id"]),
            "username": user.get("username"),
            "email": user.get("email"),
            "is_active": user.get("is_active"),
            "created_at": user.get("created_at").isoformat() if user.get("created_at") else None
        })

    return {
        "total_users": total_users,
        "active_users": active_users,
        "new_users_this_week": new_users_this_week,
        "users": users_list,
        "admin_users": admin_users,  # Already serialized
        "pagination": {
            "current_page": page,
            "per_page": limit
        }
    }

# Create User
@router.post("/users", response_model=UserOut)
async def create_user(user: UserCreate, current_admin: dict = Depends(get_current_admin_user)):
    users = get_user_collection()
    user_dict = user.dict()
    user_dict["created_at"] = datetime.utcnow()
    result = await users.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    return user_dict

# Read User by ID
@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: str, current_admin: dict = Depends(get_current_admin_user)):
    users = get_user_collection()
    user = await users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(404, "User  not found")
    user["_id"] = str(user["_id"])
    return user

# Update User
@router.put("/users/{user_id}")
async def update_user(user_id: str, user: UserUpdate, current_admin: dict = Depends(get_current_admin_user)):
    users = get_user_collection()
    update_data = {k: v for k, v in user.dict().items() if v is not None}
    result = await users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(404, "User  not found")
    return {"message": "User  updated successfully"}

# Delete User
@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_admin: dict = Depends(get_current_admin_user)):
    users_collection = get_user_collection()
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User  not found")
    return {"message": "User  deleted successfully"}

# --- Same structure for artworks ---
@router.get("/artworks/summary-full")
async def artworks_summary_full(page: int = 1, limit: int = 50, current_admin: dict = Depends(get_current_admin_user)):
    artworks_collection = get_artwork_collection()

    total_artworks = await artworks_collection.count_documents({})
    approved_artworks = await artworks_collection.count_documents({"is_verified": True})
    pending_artworks = await artworks_collection.count_documents({"is_verified": False})

    skip = (page - 1) * limit
    cursor = artworks_collection.find({}).sort("created_at", -1).skip(skip).limit(limit)

    artworks_list = []
    async for art in cursor:
        artworks_list.append({
            "id": str(art.get("_id")),
            "title": art.get("title"),
            "is_verified": art.get("is_verified"),
            "created_at": art.get("created_at").isoformat() if art.get("created_at") else None
        })

    return {
        "total_artworks": total_artworks,
        "approved_artworks": approved_artworks,
        "pending_artworks": pending_artworks,
        "artworks": artworks_list,
        "pagination": {
            "current_page": page,
            "per_page": limit
        }
    }

# Create Artwork
@router.post("/artworks")
async def create_artwork(artwork: ArtworkCreate, current_admin: dict = Depends(get_current_admin_user)):
    artworks = get_artwork_collection()
    artwork_dict = artwork.dict()
    artwork_dict["created_at"] = datetime.utcnow()
    result = await artworks.insert_one(artwork_dict)
    artwork_dict["_id"] = str(result.inserted_id)
    return artwork_dict

# Read Artwork by ID
@router.get("/artworks/{artwork_id}")
async def get_artwork(artwork_id: str, current_admin: dict = Depends(get_current_admin_user)):
    artworks = get_artwork_collection()
    artwork = await artworks.find_one({"_id": ObjectId(artwork_id)})
    if not artwork:
        raise HTTPException(404, "Artwork not found")
    artwork["_id"] = str(artwork["_id"])
    return artwork

# Update Artwork
@router.put("/artworks/{artwork_id}")
async def update_artwork(artwork_id: str, artwork: ArtworkCreate, current_admin: dict = Depends(get_current_admin_user)):
    artworks = get_artwork_collection()
    update_data = {k: v for k, v in artwork.dict().items() if v is not None}
    result = await artworks.update_one({"_id": ObjectId(artwork_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(404, "Artwork not found")
    return {"message": "Artwork updated successfully"}

# Delete Artwork
@router.delete("/artworks/{artwork_id}")
async def delete_artwork(artwork_id: str, current_admin: dict = Depends(get_current_admin_user)):
    artworks = get_artwork_collection()
    result = await artworks.delete_one({"_id": ObjectId(artwork_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, detail="Artwork not found")
    return {"message": "Artwork deleted successfully"}

@router.patch("/artworks/{artwork_id}/approve")
async def approve_artwork(artwork_id: str, current_admin: dict = Depends(get_current_admin_user)):
    artworks_collection = get_artwork_collection()
    
    result = await artworks_collection.update_one(
        {"_id": ObjectId(artwork_id)},
        {"$set": {"status": "approved"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Artwork not found or already approved")
    
    return {"message": "Artwork approved successfully"}

@router.get("/artworks/status/pending")
async def get_pending_artworks(current_admin: dict = Depends(get_current_admin_user)):
    artworks_collection = get_artwork_collection()
    
    pending_artworks = await artworks_collection.find(
        {"status": "pending"}
    ).to_list(length=None)
    
    return pending_artworks

@router.post("/create-admin", response_model=UserOut)
async def create_admin(user: UserCreate):
    await connect_to_mongo()
    user_collection = get_user_collection()

    # Check if email exists
    if await user_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_data = {
         "_id": str(ObjectId()),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "hashed_password": get_password_hash(user.password),
        "is_active": True,
        "role": "admin",  # fixed
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "wallet_address": None
    }

    await user_collection.insert_one(user_data)
    return UserOut(**user_data)
