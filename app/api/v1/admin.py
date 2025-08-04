from fastapi import APIRouter, Depends, HTTPException, status
from app.db.database import get_user_collection
from datetime import datetime, timedelta
from app.db.database import get_db
from bson import ObjectId
from app.db.database import get_artwork_collection



router = APIRouter(
    tags=["Admin"],
    prefix="/admin"
)


@router.get("/users")
async def list_users():
    """Return total number of users (no login needed temporarily)"""
    users_collection = get_user_collection()
    total_users = await users_collection.count_documents({})
    return {"total_users": total_users}

@router.get("/flagged-artworks")
async def get_flagged_artworks():
    """Get all flagged artworks (admin only)"""
    return {"artworks": []}  # Placeholder

@router.get("/users/weekly")
async def new_users_this_week():
    """Return number of users who signed up this week (starting Monday, Pakistan time)"""
    users_collection = get_user_collection()

    # Current time in UTC
    utc_now = datetime.utcnow()

    # Adjust to Pakistan timezone (UTC+5)
    pk_offset = timedelta(hours=5)
    pk_now = utc_now + pk_offset

    # Calculate Monday 00:00 AM Pakistan time
    start_of_week_pk = pk_now - timedelta(days=pk_now.weekday())
    start_of_week_pk = start_of_week_pk.replace(hour=0, minute=0, second=0, microsecond=0)

    # Convert back to UTC for MongoDB comparison
    start_of_week_utc = start_of_week_pk - pk_offset

    # Count users created after start_of_week_utc
    new_users_count = await users_collection.count_documents({
        "created_at": {"$gte": start_of_week_utc}
    })

    return {
        "new_users_this_week": new_users_count,
        "since": start_of_week_utc.isoformat()
    }

@router.get("/artworks/active")
async def Active_artworks():
    """
    Return total number of approved artworks.
    """
    artworks_collection = get_artwork_collection()

    active_count = await artworks_collection.count_documents({
        "is_verified": True
    })

    return {
        "active": active_count
    }


@router.get("/artworks/pending")
async def Pending_artworks():
    """
    Return All pending artworks.
    """
    artworks_collection = get_artwork_collection()

    pending_count = await artworks_collection.count_documents({
        "is_verified": False
    })

    return {
        "pending": pending_count
    }

def get_artwork_collection():
    db = get_db()
    return db.artworks  # 👈 Make sure your collection is named correctly



@router.delete("/artworks/{artwork_id}/reject")
async def reject_artwork(artwork_id: str):
    """Reject (delete) an artwork by ID"""

    artworks_collection = get_artwork_collection()

    try:
        obj_id = ObjectId(artwork_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid artwork ID")

    result = await artworks_collection.delete_one({"_id": obj_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Artwork not found")

    return {
        "message": "Artwork rejected and deleted successfully",
        "artwork_id": artwork_id
    }


@router.get("/users/summary")
async def users_management():
    """Return list of users with username, joining date, and status"""
    users_collection = get_user_collection()

    users_cursor = users_collection.find({}, {
        "username": 1,
        "created_at": 1,
        "is_active": 1,
        "_id": 0
    }).sort("created_at", -1)  # Latest first

    users = []
    async for user in users_cursor:
        users.append({
            "username": user.get("username", ""),
            "joining_date": user.get("created_at", "").strftime("%Y-%m-%d") if user.get("created_at") else "",
            "status": "Active" if user.get("is_active") else "Inactive"
        })

    return {"users": users}
    
@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    users_collection = get_user_collection()

    result = await users_collection.delete_one({"_id": user_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}

