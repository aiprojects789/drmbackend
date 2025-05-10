from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from datetime import datetime
from typing import List
from app.core.security import get_current_user
from app.db.database import get_artwork_collection
from app.db.schemas import ArtworkSchema
from app.core.ipfs_service import upload_to_ipfs
from app.core.blockchain_service import mint_nft
import logging

router = APIRouter(prefix="/artwork", tags=["artwork"])
logger = logging.getLogger(__name__)

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
        # Verify file is an image
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed"
            )
        
        ipfs_hash = await upload_to_ipfs(file)
        tx_hash = await mint_nft(
            current_user.get("wallet_address", "0x0"),
            title,
            ipfs_hash,
            price,
            royalty_percentage
        )
        
        artwork_data = {
            "title": title,
            "description": description,
            "ipfs_hash": ipfs_hash,
            "blockchain_tx": tx_hash,
            "price": price,
            "royalty_percentage": royalty_percentage,
            "artist_id": current_user["user_id"],
            "artist_email": current_user["sub"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_verified": False
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