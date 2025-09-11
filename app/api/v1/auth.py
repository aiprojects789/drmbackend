from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from bson import ObjectId
import logging
import random
import time

from app.db.database import get_user_collection
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user
)
from app.db.models import (
    UserCreate, UserOut, Token, WalletConnectRequest,
    ForgotPasswordRequest, UserEmailRequest
)

router = APIRouter(tags=["Auth"], prefix="/auth")

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# In-memory OTP store
otp_store = {}

# ---------------- Helper Functions ----------------

async def authenticate_user(email: str, password: str):
    """Authenticate user credentials"""
    user_collection = get_user_collection()
    user = await user_collection.find_one({"email": email})
    if not user or not verify_password(password, user.get("hashed_password", "")):
        return None
    return user

async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    """Ensure the current user is admin"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required.",
        )
    return current_user

# ---------------- Auth Endpoints ----------------

@router.post("/signup", response_model=UserOut)
async def signup(user: UserCreate):
    user_collection = get_user_collection()
    if await user_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_data = {
        "_id": str(ObjectId()),
        "email": user.email,
        "username": user.username,
        "full_name": getattr(user, "full_name", ""),
        "role": "user",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "wallet_address": None
    }

    user_data["hashed_password"] = get_password_hash(user.password)
    await user_collection.insert_one(user_data)
    user_data.pop("hashed_password", None)

    return UserOut(**user_data)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for email: {form_data.username}")
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={
            "sub": user["email"],
            "user_id": str(user["_id"]),
            "wallet_address": user.get("wallet_address", ""),
            "role": user["role"]
        },
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# ---------------- Wallet ----------------

@router.post("/connect-wallet", response_model=Token)
async def connect_wallet(payload: WalletConnectRequest, current_user: dict = Depends(get_current_user)):
    if not payload.wallet_address:
        raise HTTPException(status_code=400, detail="Wallet address is required")

    user_collection = get_user_collection()
    user_email = current_user.get("email") or current_user.get("sub")
    if not user_email:
        raise HTTPException(status_code=400, detail="Cannot identify user email")

    result = await user_collection.update_one(
        {"email": user_email},
        {"$set": {"wallet_address": payload.wallet_address, "updated_at": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_access_token(
        data={
            "sub": user_email,
            "user_id": str(current_user.get("_id", "")),
            "wallet_address": payload.wallet_address,
            "role": current_user.get("role", "user")
        },
        expires_delta=timedelta(hours=24)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(current_user.get("_id", "")),
            "wallet_address": payload.wallet_address,
            "email": user_email,
            "username": current_user.get("username", ""),
            "is_verified": current_user.get("is_verified", False),
            "profile_image": current_user.get("profile_image", ""),
            "bio": current_user.get("bio", ""),
            "created_at": current_user.get("created_at"),
            "updated_at": datetime.utcnow()
        }
    }

# ---------------- Password / OTP ----------------

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    user_collection = get_user_collection()
    user = await user_collection.find_one({"email": payload.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = str(random.randint(100000, 999999))
    otp_store[payload.email] = {"otp": otp, "timestamp": time.time()}
    logger.info(f"OTP for {payload.email}: {otp} (send via email)")
    return {"message": "OTP sent to your email"}

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

    user_collection = get_user_collection()
    user = await user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = get_password_hash(new_password)
    await user_collection.update_one(
        {"email": email},
        {"$set": {"hashed_password": hashed_password, "updated_at": datetime.utcnow()}}
    )

    del otp_store[email]
    return {"message": "Password reset successfully"}

@router.post("/update-password")
async def update_password(current_password: str = Body(...), new_password: str = Body(...), current_user: dict = Depends(get_current_user)):
    user_collection = get_user_collection()
    user = await user_collection.find_one({"email": current_user["email"]})

    if not user or not verify_password(current_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    hashed_password = get_password_hash(new_password)
    await user_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {"hashed_password": hashed_password, "updated_at": datetime.utcnow()}}
    )

    return {"message": "Password updated successfully"}

# ---------------- User Management ----------------

@router.get("/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    return {
        "email": current_user["email"],
        "role": current_user.get("role", "user"),
        "user_id": current_user.get("user_id"),
        "wallet_address": current_user.get("wallet_address")
    }

@router.post("/find-user")
async def find_user(payload: UserEmailRequest):
    user_collection = get_user_collection()
    user = await user_collection.find_one({"email": payload.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User found with email {payload.email}"}

# ---------------- Admin Routes ----------------

@router.get("/admin/users")
async def get_all_users(current_admin: dict = Depends(get_current_admin_user)):
    user_collection = get_user_collection()
    users = []
    async for user in user_collection.find({}):
        user["_id"] = str(user["_id"])
        user.pop("hashed_password", None)
        users.append(user)
    return {"users": users, "total": len(users)}

@router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, current_admin: dict = Depends(get_current_admin_user)):
    user_collection = get_user_collection()
    if user_id == current_admin.get("user_id"):
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    result = await user_collection.delete_one({"_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@router.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, new_role: str = Body(..., embed=True), current_admin: dict = Depends(get_current_admin_user)):
    if new_role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
    user_collection = get_user_collection()
    result = await user_collection.update_one(
        {"_id": user_id},
        {"$set": {"role": new_role, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User role updated to {new_role}"}

@router.get("/admin/stats")
async def get_admin_stats(current_admin: dict = Depends(get_current_admin_user)):
    user_collection = get_user_collection()
    total_users = await user_collection.count_documents({})
    total_admins = await user_collection.count_documents({"role": "admin"})
    total_regular_users = await user_collection.count_documents({"role": "user"})
    active_users = await user_collection.count_documents({"is_active": True})
    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "total_regular_users": total_regular_users,
        "active_users": active_users
    }

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    email = current_user.get("email") or current_user.get("sub")
    return {"message": f"User {email} logged out successfully"}




# from fastapi import APIRouter, Depends, HTTPException, status, Body
# from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
# from datetime import datetime, timedelta    
# from app.db.models import ForgotPasswordRequest, UserEmailRequest, UserCreate, UserOut, Token,WalletConnectRequest  
# from app.core.security import (
#     create_access_token, 
#     get_password_hash, 
#     verify_password,
#     decode_token,
#     get_current_user
# )
# from app.core.config import settings
# from app.db.database import get_user_collection, connect_to_mongo
# from .email import send_email

# import logging
# from bson import ObjectId
# import random
# import time

# router = APIRouter(
#     tags=["Auth"],
#     prefix="/auth"
# )

# logger = logging.getLogger(__name__)

# otp_store = {}  # In-memory OTP store

# # OAuth2 scheme for token authentication
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")



# @router.post("/connect-wallet", response_model=Token)
# async def connect_wallet(payload: WalletConnectRequest, current_user: dict = Depends(get_current_user)):
#     wallet_address = payload.wallet_address
#     if not wallet_address:
#         raise HTTPException(status_code=400, detail="Wallet address is required")

    
#     # Safely get user's email
#     user_email = current_user.get("email") or current_user.get("sub")
#     if not user_email:
#         raise HTTPException(status_code=400, detail="Cannot identify user email")

#     await connect_to_mongo()
#     user_collection = get_user_collection()
    
#     # Update wallet address in MongoDB
#     result = await user_collection.update_one(
#         {"email": user_email},
#         {"$set": {"wallet_address": wallet_address, "updated_at": datetime.utcnow()}}
#     )
    
#     if result.matched_count == 0:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Create a new JWT for this user
#     access_token_expires = timedelta(hours=24)
#     access_token = create_access_token(
#         data={
#             "sub": user_email,
#             "user_id": str(current_user.get("_id", "")),
#             "wallet_address": wallet_address,
#             "role": current_user.get("role", "user")
#         },
#         expires_delta=access_token_expires
#     )

#     return {
#         "access_token": access_token,
#         "token_type": "bearer",
#         "user": {
#             "id": str(current_user.get("_id", "")),
#             "wallet_address": wallet_address,
#             "email": user_email,
#             "username": current_user.get("username", ""),
#             "is_verified": current_user.get("is_verified", False),
#             "profile_image": current_user.get("profile_image", ""),
#             "bio": current_user.get("bio", ""),
#             "created_at": current_user.get("created_at"),
#             "updated_at": datetime.utcnow()
#         }
#     }


# @router.post("/signup", response_model=UserOut)
# async def signup(user: UserCreate):
#     """User registration endpoint"""
#     try:
#         await connect_to_mongo()
#         user_collection = get_user_collection()

#         # Check if email already exists
#         if await user_collection.find_one({"email": user.email}):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Email already registered"
#             )

#         # Prepare user data
#         user_data = {
#             "_id": str(ObjectId()),
#             "email": user.email,
#             "username": user.username,
#             "full_name": user.full_name if hasattr(user, "full_name") else "",
#             "role": "user",  # default role
#             "is_active": True,
#             "created_at": datetime.utcnow(),
#             "updated_at": datetime.utcnow(),
#             "wallet_address": None  # Not sent from UI
#         }

#         # Hash password separately
#         hashed_password = get_password_hash(user.password)
#         user_data["hashed_password"] = hashed_password

#         # Insert into MongoDB
#         await user_collection.insert_one(user_data)

#         # Remove hashed_password before returning
#         user_data.pop("hashed_password", None)

#         return UserOut(**user_data)

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Signup error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Registration failed"
#         )

# # Authentication function remains unchanged
# async def authenticate_user(email: str, password: str):
#     """Authenticate user credentials"""
#     try:
#         user_collection = get_user_collection()
#         user = await user_collection.find_one({"email": email})
        
#         if not user or not verify_password(password, user.get("hashed_password", "")):
#             return None
            
#         return user
#     except Exception as e:
#         logger.error(f"Authentication error: {str(e)}")
#         return None


# @router.post("/login", response_model=Token)
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = await authenticate_user(form_data.username, form_data.password)
#     if not user:
#         logger.warning(f"Failed login attempt for email: {form_data.username}")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     # Include role in token data
#     access_token = create_access_token(
#         data={
#             "sub": user["email"],
#             "user_id": str(user["_id"]),
#             "wallet_address": user.get("wallet_address", ""),
#             "role": user["role"]  # Include role in token
#         }
#     )

#     logger.info(f"User logged in: {user['email']} with role: {user['role']}")
#     return {"access_token": access_token, "token_type": "bearer"}

# # Dependency to get current admin user
# async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
#     """Dependency that ensures the current user is an admin"""
#     if current_user.get("role") != "admin":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Access denied. Admin privileges required.",
#         )
#     return current_user

# # Admin-only route to get all users
# @router.get("/admin/users")
# async def get_all_users(current_admin: dict = Depends(get_current_admin_user)):
#     """Get all users - Admin only"""
#     try:
#         await connect_to_mongo()
#         user_collection = get_user_collection()
        
#         users = []
#         async for user in user_collection.find({}):
#             user["_id"] = str(user["_id"])
#             # Don't return password hashes
#             user.pop("hashed_password", None)
#             users.append(user)
        
#         logger.info(f"Admin {current_admin['email']} retrieved all users")
#         return {"users": users, "total": len(users)}
    
#     except Exception as e:
#         logger.error(f"Error getting all users: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve users"
#         )
# @router.post("/logout")
# async def logout(current_user: dict = Depends(get_current_user)):
#     email = current_user.get("email") or current_user.get("sub")
#     if not email:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token"
#         )
#     return {"message": f"User {email} logged out successfully"}

# # Admin-only route to delete a user
# @router.delete("/admin/users/{user_id}")
# async def delete_user(user_id: str, current_admin: dict = Depends(get_current_admin_user)):
#     """Delete a user - Admin only"""
#     try:
#         await connect_to_mongo()
#         user_collection = get_user_collection()
        
#         # Don't allow admin to delete themselves
#         if user_id == current_admin["user_id"]:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Cannot delete your own account"
#             )
        
#         result = await user_collection.delete_one({"_id": user_id})
        
#         if result.deleted_count == 0:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found"
#             )
        
#         logger.info(f"Admin {current_admin['email']} deleted user with ID: {user_id}")
#         return {"message": "User deleted successfully"}
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error deleting user: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to delete user"
#         )

# # Admin-only route to update user role
# @router.put("/admin/users/{user_id}/role")
# async def update_user_role(
#     user_id: str, 
#     new_role: str = Body(..., embed=True),
#     current_admin: dict = Depends(get_current_admin_user)
# ):
#     """Update user role - Admin only"""
#     if new_role not in ["user", "admin"]:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Role must be either 'user' or 'admin'"
#         )
    
#     try:
#         await connect_to_mongo()
#         user_collection = get_user_collection()
        
#         result = await user_collection.update_one(
#             {"_id": user_id},
#             {"$set": {
#                 "role": new_role,
#                 "updated_at": datetime.utcnow()
#             }}
#         )
        
#         if result.matched_count == 0:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found"
#             )
        
#         logger.info(f"Admin {current_admin['email']} updated user {user_id} role to {new_role}")
#         return {"message": f"User role updated to {new_role}"}
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error updating user role: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to update user role"
#         )

# @router.post("/update-password")
# async def update_password(
#     current_password: str,
#     new_password: str,
#     current_user: dict = Depends(get_current_user)
# ):
#     try:
#         user_collection = get_user_collection()
#         user = await user_collection.find_one({"email": current_user["email"]})

#         if not user or not verify_password(current_password, user["hashed_password"]):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Current password is incorrect"
#             )

#         hashed_password = get_password_hash(new_password)
#         await user_collection.update_one(
#             {"email": current_user["email"]},
#             {"$set": {
#                 "hashed_password": hashed_password,
#                 "updated_at": datetime.utcnow()
#             }}
#         )

#         logger.info(f"Password updated for user: {current_user['email']}")
#         return {"message": "Password updated successfully"}

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Password update error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Password update failed"
#         )

# @router.post("/forgot-password")
# async def forgot_password(payload: ForgotPasswordRequest):
#     await connect_to_mongo()
#     user_collection = get_user_collection()
#     user = await user_collection.find_one({"email": payload.email})

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     otp = str(random.randint(100000, 999999))
#     otp_store[payload.email] = {"otp": otp, "timestamp": time.time()}

#     subject = "Your OTP for Password Reset"
#     body = f"Your OTP is {otp}. It is valid for 5 minutes."

#     try:
#         send_email(subject, body, payload.email)
#         return {"message": "OTP sent to your email"}
#     except Exception as e:
#         logger.error(f"Failed to send OTP email: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to send OTP")

# @router.post("/verify-otp")
# async def verify_otp(email: str = Body(...), otp: str = Body(...)):
#     otp_data = otp_store.get(email)
#     if not otp_data:
#         raise HTTPException(status_code=404, detail="No OTP found")

#     if time.time() - otp_data["timestamp"] > 300:
#         del otp_store[email]
#         raise HTTPException(status_code=400, detail="OTP expired")

#     if otp_data["otp"] != otp:
#         raise HTTPException(status_code=400, detail="Invalid OTP")

#     return {"message": "OTP verified"}

# @router.post("/reset-password")
# async def reset_password(email: str = Body(...), otp: str = Body(...), new_password: str = Body(...)):
#     otp_data = otp_store.get(email)
#     if not otp_data or otp_data["otp"] != otp:
#         raise HTTPException(status_code=400, detail="Invalid or expired OTP")

#     await connect_to_mongo()
#     user_collection = get_user_collection()
#     user = await user_collection.find_one({"email": email})

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     hashed_password = get_password_hash(new_password)
#     await user_collection.update_one(
#         {"email": email},
#         {"$set": {
#             "hashed_password": hashed_password,
#             "updated_at": datetime.utcnow()
#         }}
#     )

#     del otp_store[email]
#     return {"message": "Password reset successfully"}

# @router.post("/find-user")
# async def find_user(payload: UserEmailRequest):
#     await connect_to_mongo()
#     user_collection = get_user_collection()
#     user = await user_collection.find_one({"email": payload.email})

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     return {"message": f"User found with email {payload.email}"}

# # Get current user profile
# @router.get("/me")
# async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
#     """Get current user's profile"""
#     return {
#         "email": current_user["email"],
#         "role": current_user.get("role", "user"),
#         "user_id": current_user.get("user_id"),
#         "wallet_address": current_user.get("wallet_address")
#     }

# # Admin dashboard stats
# @router.get("/admin/stats")
# async def get_admin_stats(current_admin: dict = Depends(get_current_admin_user)):
#     """Get admin dashboard statistics"""
#     try:
#         await connect_to_mongo()
#         user_collection = get_user_collection()
        
#         total_users = await user_collection.count_documents({})
#         total_admins = await user_collection.count_documents({"role": "admin"})
#         total_regular_users = await user_collection.count_documents({"role": "user"})
#         active_users = await user_collection.count_documents({"is_active": True})
        
#         return {
#             "total_users": total_users,
#             "total_admins": total_admins,
#             "total_regular_users": total_regular_users,
#             "active_users": active_users
#         }
    
#     except Exception as e:
#         logger.error(f"Error getting admin stats: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve statistics"
#         )

