from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File, Query
from datetime import datetime
from typing import List, Optional
from app.core.security import get_current_user
from app.db.database import get_artwork_collection
from app.db.schemas import ArtworkSchema
from services.web3_service import web3_service
import logging
from PIL import Image
import io
from app.db.models import (
    ArtworkCreate, ArtworkUpdate, ArtworkBase as Artwork, ArtworkInDB,
    ArtworkPublic, ArtworkListResponse, User
)
from app.core.config import settings
import json
import aiohttp
import asyncio

router = APIRouter(prefix="/artwork", tags=["artwork"])
logger = logging.getLogger(__name__)


# ✅ Image Processing Class
class ImageProcessor:
    @staticmethod
    async def process_image(image_data: bytes, max_size: int = 5 * 1024 * 1024) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_data))

            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background

            max_dimension = 2000
            if max(img.size) > max_dimension:
                ratio = max_dimension / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            processed_data = output.getvalue()

            return processed_data
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Image processing failed: {str(e)}")


# ✅ IPFS Upload Service
class IPFSService:
    @staticmethod
    async def upload_to_ipfs(file_data: bytes, filename: str) -> str:
        """Stub for IPFS upload (Pinata/NFT.Storage/Web3.Storage)"""
        # Just demo: always return dummy URI
        return f"ipfs://demo/{filename}"


# ✅ Register artwork with image
@router.post("/register-with-image")
async def register_artwork_with_image(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    royalty_percentage: int = Form(...),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        if not 0 <= royalty_percentage <= 2000:
            raise HTTPException(status_code=400, detail="Royalty must be between 0-2000 basis points")

        image_data = await image.read()
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image file too large (max 10MB)")

        processed_image_data = await ImageProcessor.process_image(image_data)
        image_ipfs_uri = await IPFSService.upload_to_ipfs(processed_image_data, image.filename)

        metadata = {
            "name": title,
            "description": description,
            "image": image_ipfs_uri,
            "attributes": {
                "royalty_percentage": royalty_percentage,
                "creator": current_user["wallet_address"],
                "created_at": datetime.utcnow().isoformat()
            }
        }

        metadata_bytes = json.dumps(metadata).encode('utf-8')
        metadata_uri = await IPFSService.upload_to_ipfs(metadata_bytes, "metadata.json")

        tx_data = await web3_service.prepare_register_transaction(
            metadata_uri,
            royalty_percentage,
            from_address=current_user["wallet_address"]
        )

        return {
            "status": "success",
            "transaction_data": tx_data,
            "metadata_uri": metadata_uri,
            "image_uri": image_ipfs_uri,
            "royalty_percentage": royalty_percentage
        }
    except Exception as e:
        logger.error(f"Registration with image failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


# ✅ Confirm registration
@router.post("/confirm-registration")
async def confirm_registration(confirmation_data: dict, current_user: User = Depends(get_current_user)):
    try:
        artworks_collection = get_artwork_collection()

        tx_receipt = await web3_service.get_transaction_receipt(confirmation_data["tx_hash"])
        if not tx_receipt or tx_receipt.get("status") != 1:
            raise HTTPException(status_code=400, detail="Blockchain transaction failed")

        token_id = await web3_service.get_token_id_from_tx(confirmation_data["tx_hash"])
        if not token_id:
            raise HTTPException(status_code=400, detail="Could not determine token ID from transaction")

        attributes = confirmation_data.get("attributes") or {}

        artwork = ArtworkInDB(
            token_id=token_id,
            creator_address=current_user.wallet_address,
            owner_address=current_user.wallet_address,
            metadata_uri=confirmation_data["metadata_uri"],
            royalty_percentage=confirmation_data["royalty_percentage"],
            title=confirmation_data.get("title"),
            description=confirmation_data.get("description"),
            attributes=attributes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tx_hash=confirmation_data["tx_hash"]
        )

        result = await artworks_collection.insert_one(artwork.model_dump(by_alias=True))

        return {"success": True, "artwork_id": str(result.inserted_id), "token_id": token_id}
    except Exception as e:
        logger.error(f"Artwork confirmation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to confirm artwork registration: {str(e)}")


# ✅ List artworks

# ✅ List artworks


@router.get("/", response_model=ArtworkListResponse)
async def list_artworks(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    creator_address: Optional[str] = None,
    owner_address: Optional[str] = None,
):
    try:
        artworks_collection = get_artwork_collection()

        # Build filter query
        filter_query = {}
        if creator_address:
            filter_query["creator_address"] = creator_address.lower()
        if owner_address:
            filter_query["owner_address"] = owner_address.lower()

        logger.debug(f"Filter query: {filter_query}")

        # Count and pagination
        total = await artworks_collection.count_documents(filter_query)
        has_next = (page * size) < total
        skip = (page - 1) * size

        # Fetch documents
        cursor = artworks_collection.find(filter_query).skip(skip).limit(size).sort("created_at", -1)
        artworks_data = await cursor.to_list(length=size)
        logger.debug(f"Fetched {len(artworks_data)} artworks from DB")

        artworks = []
        for doc in artworks_data:
            try:
                # Validate MongoDB document
                db_model = ArtworkInDB.model_validate(doc)

                # Dump with alias (id instead of _id)
                data = db_model.model_dump(by_alias=True)
                logger.debug(f"Model dump data: {data}")

                # Convert into public response model
                artworks.append(ArtworkPublic(**data))
            except Exception as e:
                logger.warning(f"Skipping invalid artwork: {e} | Raw doc: {doc}")
                continue

        return ArtworkListResponse(
            artworks=artworks,
            total=total,
            page=page,
            size=size,
            has_next=has_next
        )
    except Exception as e:
        logger.error(f"Error listing artworks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list artworks"
        )


# ✅ Get single artwork
@router.get("/{token_id}", response_model=ArtworkPublic)
async def get_artwork(token_id: int):
    try:
        artworks_collection = get_artwork_collection()
        artwork_doc = await artworks_collection.find_one({"token_id": token_id})
        if not artwork_doc:
            raise HTTPException(status_code=404, detail="Artwork not found")

        artwork = ArtworkInDB.validate_document(artwork_doc)
        return ArtworkPublic.from_db_model(artwork)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting artwork {token_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get artwork")
