from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from datetime import datetime
from typing import List
from app.core.security import get_current_user
from app.db.database import get_artwork_collection
from app.db.schemas import ArtworkSchema
from app.core.ipfs_service import upload_to_ipfs
from app.core.blockchain_service import mint_nft
import logging
import os
from pathlib import Path



router = APIRouter(prefix="/artwork", tags=["artwork"])
logger = logging.getLogger(__name__)




UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=ArtworkSchema)
async def upload_artwork(
    title: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    royalty_percentage: float = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed"
            )

        # Read file data once
        file_bytes = await file.read()

        # Save locally
        file_ext = file.filename.split(".")[-1]
        filename = f"{datetime.utcnow().timestamp()}.{file_ext}"
        file_path = UPLOAD_FOLDER / filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)

        # Upload to IPFS using file bytes
        ipfs_hash = await upload_to_ipfs(file_bytes)

        # Mint NFT
        tx_hash = await mint_nft(
            current_user.get("wallet_address", "0x0"),
            title,
            ipfs_hash,
            price,
            royalty_percentage
        )

        # Save to DB (local path for image)
        artwork_data = {
            "title": title,
            "description": description,
            "image": f"/uploads/{filename}",  # so frontend can access directly
            "ipfs_hash": ipfs_hash,
            "blockchain_tx": tx_hash,
            "price": price,
            "royalty_percentage": royalty_percentage,
            "artist_id": current_user["user_id"],
            "artist_email": current_user["sub"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_verified": False,
            "status": "pending"
        }

        artwork_collection = get_artwork_collection()
        result = await artwork_collection.insert_one(artwork_data)
        created_artwork = await artwork_collection.find_one({"_id": result.inserted_id})

        return ArtworkSchema(**created_artwork)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload artwork"
        )

# @router.post("/upload", response_model=ArtworkSchema)
# async def upload_artwork(
#     title: str = Form(...),
#     description: str = Form(None),
#     price: float = Form(...),
#     royalty_percentage: float = Form(...),
#     file: UploadFile = File(...),
#     current_user: dict = Depends(get_current_user)
# ):
#     try:
#         # Verify file is an image
#         if not file.content_type.startswith('image/'):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Only image files are allowed"
#             )
        
#         ipfs_hash = await upload_to_ipfs(file)
#         tx_hash = await mint_nft(
#             current_user.get("wallet_address", "0x0"),
#             title,
#             ipfs_hash,
#             price,
#             royalty_percentage
#         )
        
#         artwork_data = {
#             "title": title,
#             "description": description,
#             "ipfs_hash": ipfs_hash,
#             "blockchain_tx": tx_hash,
#             "price": price,
#             "royalty_percentage": royalty_percentage,
#             "artist_id": current_user["user_id"],
#             "artist_email": current_user["sub"],
#             "created_at": datetime.utcnow(),
#             "updated_at": datetime.utcnow(),
#             "is_verified": False,
#             "status": "pending" # <-- ye line add karo
#         }
        
#         artwork_collection = get_artwork_collection()
#         result = await artwork_collection.insert_one(artwork_data)
#         created_artwork = await artwork_collection.find_one({"_id": result.inserted_id})
        
#         return ArtworkSchema(**created_artwork)
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Upload failed: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to upload artwork"
#         )




@router.get("/my-artwork", response_model=List[ArtworkSchema])
async def get_my_artwork(current_user: dict = Depends(get_current_user)):
    try:
        artworks = []
        async for artwork in get_artwork_collection().find({"artist_id": current_user["user_id"]}):
            artworks.append(ArtworkSchema(**artwork))
        return artworks
    except Exception as e:
        logger.error(f"Failed to fetch artwork: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch artwork"
        )


# from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
# from datetime import datetime
# from typing import List, Optional
# from app.core.security import get_current_user
# from app.db.database import get_artwork_collection, connect_to_mongo
# from app.db.schemas import ArtworkSchema
# from app.core.ipfs_service import upload_to_ipfs
# from app.core.blockchain_service import mint_nft
# import logging
# from bson import ObjectId

# router = APIRouter(prefix="/artwork", tags=["artwork"])
# logger = logging.getLogger(__name__)

# # Constants
# ALLOWED_CONTENT_TYPES = [
#     'image/jpeg',
#     'image/png',
#     'image/gif',
#     'image/webp'
# ]

# @router.post("/upload", response_model=ArtworkSchema)
# async def upload_artwork(
#     title: str = Form(...),
#     description: Optional[str] = Form(None),
#     price: float = Form(...),
#     royalty_percentage: float = Form(...),
#     file: UploadFile = File(...),
#     current_user: dict = Depends(get_current_user)
# ):
#     """
#     Upload artwork to IPFS, mint NFT, and store metadata
#     """
#     try:
#         # Verify file type
#         if file.content_type not in ALLOWED_CONTENT_TYPES:
#             logger.warning(f"Invalid file type attempted: {file.content_type}")
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Only image files are allowed (JPEG, PNG, GIF, WEBP)"
#             )

#         # Verify wallet address exists
#         wallet_address = current_user.get("wallet_address")
#         if not wallet_address:
#             logger.error(f"User {current_user['email']} has no wallet address")
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="No wallet address associated with account"
#             )

#         # Ensure database connection
#         await connect_to_mongo()

#         # Upload to IPFS
#         logger.info(f"Uploading artwork to IPFS for user {current_user['email']}")
#         ipfs_hash = await upload_to_ipfs(file)
#         logger.debug(f"IPFS hash received: {ipfs_hash}")

#         # Mint NFT
#         logger.info("Minting NFT on blockchain...")
#         tx_hash = await mint_nft(
#             wallet_address,
#             title,
#             ipfs_hash,
#             price,
#             royalty_percentage
#         )
#         logger.debug(f"Transaction hash: {tx_hash}")

#         # Store artwork metadata
#         artwork_data = ArtworkCreate(
#             title=title,
#             description=description,
#             ipfs_hash=ipfs_hash,
#             blockchain_tx=tx_hash,
#             price=price,
#             royalty_percentage=royalty_percentage,
#             artist_id=current_user["user_id"],
#             artist_email=current_user["email"],
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow(),
#             is_verified=False
#         )

#         artwork_collection = get_artwork_collection()
#         result = await artwork_collection.insert_one(artwork_data.dict())
#         created_artwork = await artwork_collection.find_one({"_id": result.inserted_id})

#         logger.info(f"Artwork created with ID: {result.inserted_id}")
#         return ArtworkSchema(**created_artwork)

#     except HTTPException as he:
#         logger.warning(f"HTTPException in upload_artwork: {he.detail}")
#         raise
#     except Exception as e:
#         logger.error(f"Unexpected error in upload_artwork: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to process artwork upload"
#         )

# @router.get("/my-artwork", response_model=List[ArtworkSchema])
# async def get_my_artwork(current_user: dict = Depends(get_current_user)):
#     """
#     Get all artwork for the current user
#     """
#     try:
#         await connect_to_mongo()
#         artwork_collection = get_artwork_collection()
        
#         logger.info(f"Fetching artwork for user {current_user['email']}")
#         artworks = []
#         async for artwork in artwork_collection.find({"artist_id": current_user["user_id"]}):
#             artworks.append(ArtworkSchema(**artwork))
        
#         logger.debug(f"Found {len(artworks)} artworks")
#         return artworks

#     except Exception as e:
#         logger.error(f"Error fetching artwork: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve artwork"
#         )

# @router.get("/{artwork_id}", response_model=ArtworkSchema)
# async def get_artwork_details(artwork_id: str):
#     """
#     Get details for a specific artwork
#     """
#     try:
#         await connect_to_mongo()
#         artwork_collection = get_artwork_collection()
        
#         artwork = await artwork_collection.find_one({"_id": ObjectId(artwork_id)})
#         if not artwork:
#             logger.warning(f"Artwork not found: {artwork_id}")
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Artwork not found"
#             )
            
#         return ArtworkSchema(**artwork)
        
#     except Exception as e:
#         logger.error(f"Error fetching artwork details: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve artwork details"
#         )

# @router.delete("/{artwork_id}")
# async def delete_artwork(
#     artwork_id: str,
#     current_user: dict = Depends(get_current_user)
# ):
#     """
#     Delete artwork (only by owner)
#     """
#     try:
#         await connect_to_mongo()
#         artwork_collection = get_artwork_collection()
        
#         # Verify artwork exists and belongs to user
#         artwork = await artwork_collection.find_one({
#             "_id": ObjectId(artwork_id),
#             "artist_id": current_user["user_id"]
#         })
        
#         if not artwork:
#             logger.warning(
#                 f"Delete attempt failed for artwork {artwork_id} by user {current_user['email']}"
#             )
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Artwork not found or not owned by user"
#             )
            
#         await artwork_collection.delete_one({"_id": ObjectId(artwork_id)})
#         logger.info(f"Artwork deleted: {artwork_id}")
#         return {"message": "Artwork deleted successfully"}
        
#     except Exception as e:
#         logger.error(f"Error deleting artwork: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to delete artwork"
#         )