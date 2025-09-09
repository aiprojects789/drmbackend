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
    ArtworkPublic, ArtworkListResponse, User, SaleConfirmation,
    TransactionCreate, TransactionType, TransactionStatus, ContractCallRequest, ContractCallResponse
)
from app.core.config import settings
import json
import aiohttp
import asyncio
import re
from bson import ObjectId


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
    """Service class to handle IPFS uploads with multiple providers"""
    
    @staticmethod
    async def upload_to_pinata(file_data: bytes, filename: str) -> str:
        """Upload to Pinata.cloud with proper error handling"""
        try:
            pinata_api_key = settings.PINATA_API_KEY
            pinata_secret_api_key = settings.PINATA_SECRET_API_KEY
            
            if not pinata_api_key or not pinata_secret_api_key:
                raise Exception("Pinata API credentials not configured")
            
            # For larger files, use the pinFileToIPFS endpoint which handles chunking
            form_data = aiohttp.FormData()
            form_data.add_field('file', file_data, filename=filename)
            
            headers = {
                'pinata_api_key': pinata_api_key,
                'pinata_secret_api_key': pinata_secret_api_key,
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.pinata.cloud/pinning/pinFileToIPFS',
                    headers=headers,
                    data=form_data
                ) as response:
                    # Check if response is JSON
                    content_type = response.headers.get('Content-Type', '')
                    response_text = await response.text()
                    
                    if 'application/json' in content_type:
                        result = await response.json()
                        if response.status == 200:
                            return f"ipfs://{result['IpfsHash']}"
                        else:
                            error_msg = result.get('error', {}).get('message', 'Unknown error')
                            raise Exception(f"Pinata error: {error_msg}")
                    else:
                        # Handle non-JSON responses (usually errors)
                        if response.status == 401:
                            raise Exception("Pinata authentication failed - check API keys")
                        elif response.status == 403:
                            raise Exception("Pinata access denied - check API permissions")
                        elif response.status == 413:
                            raise Exception("Pinata file too large - try smaller image")
                        else:
                            raise Exception(f"Pinata error: HTTP {response.status} - {response_text[:200]}")
                        
        except Exception as e:
            logger.error(f"Pinata upload failed: {str(e)}")
            raise

    @staticmethod
    async def upload_to_nft_storage(file_data: bytes, filename: str) -> str:
        """Upload to NFT.Storage - better for larger files"""
        try:
            nft_storage_key = settings.NFT_STORAGE_API_KEY
            if not nft_storage_key:
                raise Exception("NFT.Storage API key not configured")
            
            headers = {
                'Authorization': f'Bearer {nft_storage_key}',
            }
            
            # Create FormData for better handling
            form_data = aiohttp.FormData()
            form_data.add_field('file', file_data, filename=filename)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.nft.storage/upload',
                    headers=headers,
                    data=form_data
                ) as response:
                    content_type = response.headers.get('Content-Type', '')
                    response_text = await response.text()
                    
                    if 'application/json' in content_type:
                        result = await response.json()
                        if response.status == 200 and result.get('ok'):
                            return f"ipfs://{result['value']['cid']}"
                        else:
                            error_msg = result.get('error', {}).get('message', 'Unknown error')
                            raise Exception(f"NFT.Storage error: {error_msg}")
                    else:
                        if response.status == 401:
                            raise Exception("NFT.Storage authentication failed - check API key")
                        else:
                            raise Exception(f"NFT.Storage error: HTTP {response.status} - {response_text[:200]}")
                        
        except Exception as e:
            logger.error(f"NFT.Storage upload failed: {str(e)}")
            raise

    @staticmethod
    async def upload_to_web3_storage(file_data: bytes, filename: str) -> str:
        """Upload to Web3.Storage"""
        try:
            web3_storage_key = settings.WEB3_STORAGE_API_KEY
            if not web3_storage_key:
                raise Exception("Web3.Storage API key not configured")
            
            headers = {
                'Authorization': f'Bearer {web3_storage_key}',
                'X-Name': filename,
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.web3.storage/upload',
                    headers=headers,
                    data=file_data
                ) as response:
                    content_type = response.headers.get('Content-Type', '')
                    response_text = await response.text()
                    
                    if 'application/json' in content_type:
                        result = await response.json()
                        if response.status == 200:
                            return f"ipfs://{result['cid']}"
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            raise Exception(f"Web3.Storage error: {error_msg}")
                    else:
                        if response.status == 401:
                            raise Exception("Web3.Storage authentication failed - check API key")
                        else:
                            raise Exception(f"Web3.Storage error: HTTP {response.status} - {response_text[:200]}")
                        
        except Exception as e:
            logger.error(f"Web3.Storage upload failed: {str(e)}")
            raise

    @staticmethod
    async def upload_to_ipfs(file_data: bytes, filename: str, max_retries: int = 2) -> str:
        """Main upload method that tries multiple providers with retries"""
        providers = []
        
        # Check which providers are configured
        if settings.PINATA_API_KEY and settings.PINATA_SECRET_API_KEY:
            providers.append(("Pinata", IPFSService.upload_to_pinata))
        
        if settings.NFT_STORAGE_API_KEY:
            providers.append(("NFT.Storage", IPFSService.upload_to_nft_storage))
        
        if settings.WEB3_STORAGE_API_KEY:
            providers.append(("Web3.Storage", IPFSService.upload_to_web3_storage))
        
        if not providers:
            raise Exception("No IPFS providers configured. Please set up at least one IPFS service.")
        
        errors = []
        
        # Try each provider with retries
        for provider_name, provider_func in providers:
            for attempt in range(max_retries):
                try:
                    logger.info(f"Trying {provider_name} (attempt {attempt + 1})...")
                    result = await provider_func(file_data, filename)
                    logger.info(f"Successfully uploaded to IPFS using {provider_name}: {result}")
                    return result
                except Exception as e:
                    error_msg = f"{provider_name} attempt {attempt + 1} failed: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)  # Wait before retry
        
        # If all providers failed, log detailed errors
        detailed_error = "All IPFS providers failed:\n" + "\n".join(errors)
        logger.error(detailed_error)
        raise Exception("All IPFS providers failed. Check API keys and network connectivity.")


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
            creator_address=current_user["wallet_address"],
            owner_address=current_user["wallet_address"],
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
@router.get("/", response_model=ArtworkListResponse)
async def list_artworks(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    creator_address: Optional[str] = None,
    owner_address: Optional[str] = None,
):
    try:
        artworks_collection = get_artwork_collection()

        # Build filter query - only include valid artworks
        filter_query = {
            "token_id": {"$ne": None, "$exists": True},
            "creator_address": {"$ne": None, "$exists": True},
            "owner_address": {"$ne": None, "$exists": True}
        }
        
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
                # Use a more flexible approach for validation
                artwork_public = ArtworkPublic(
                    id=str(doc.get("_id", "")),
                    token_id=doc.get("token_id"),
                    creator_address=doc.get("creator_address"),
                    owner_address=doc.get("owner_address"),
                    metadata_uri=doc.get("metadata_uri", ""),
                    royalty_percentage=doc.get("royalty_percentage", 0),
                    is_licensed=doc.get("is_licensed", False),
                    title=doc.get("title", "Untitled"),
                    description=doc.get("description", ""),
                    attributes=doc.get("attributes", {}),
                    created_at=doc.get("created_at", datetime.utcnow()),
                    updated_at=doc.get("updated_at", datetime.utcnow())
                )
                artworks.append(artwork_public)
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


# ✅ Get artwork blockchain info
@router.get("/{token_id}/blockchain", response_model=dict)
async def get_artwork_blockchain_info(token_id: int):
    try:
        artwork_info = await web3_service.get_artwork_info(token_id)
        owner = await web3_service.get_artwork_owner(token_id)

        if not artwork_info:
            raise HTTPException(status_code=404, detail="Artwork not found on blockchain")

        return {
            "token_id": token_id,
            "creator": artwork_info["creator"],
            "owner": owner,
            "metadata_uri": artwork_info["metadata_uri"],
            "royalty_percentage": artwork_info["royalty_percentage"],
            "is_licensed": artwork_info["is_licensed"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting blockchain info for artwork {token_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get blockchain information")



@router.put("/{token_id}")
async def update_artwork(
    token_id: int,
    artwork_update: ArtworkUpdate,
    current_user: User = Depends(get_current_user)
):
    try:
        artworks_collection = get_artwork_collection()
        artwork_doc = await artworks_collection.find_one({"token_id": token_id})
        if not artwork_doc:
            raise HTTPException(status_code=404, detail="Artwork not found")

        artwork = ArtworkInDB.model_validate(artwork_doc)
        if artwork.owner_address != current_user["wallet_address"]:
            raise HTTPException(status_code=403, detail="Only owner can update")

        update_data = artwork_update.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        await artworks_collection.update_one({"token_id": token_id}, {"$set": update_data})

        updated_doc = await artworks_collection.find_one({"token_id": token_id})
        updated_artwork = ArtworkInDB.model_validate(updated_doc)
        return ArtworkPublic.from_db_model(updated_artwork)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating artwork {token_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update artwork")


# --- Test Contract Endpoint ---
@router.post("/test-contract", response_model=ContractCallResponse)
async def test_contract(request: ContractCallRequest):
    try:
        # ✅ Simulate contract call (replace with real Web3 logic later)
        result = {
            "function": request.function_name,
            "params": request.parameters,
            "from": request.from_address,
            "value": request.value
        }

        return ContractCallResponse(
            success=True,
            result=result,
            tx_hash="0x" + "abc123".ljust(64, "0")  # dummy tx hash
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/debug/contract-abi")
async def debug_contract_abi():
    """Debug contract ABI compatibility"""
    try:
        if web3_service.demo_mode:
            return {
                "status": "demo_mode",
                "message": "Running in demo mode - no real contract testing"
            }
        verification = await web3_service.verify_contract_abi()
        return verification
    except Exception as e:
        logger.error(f"Contract ABI debug failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }

@router.get("/debug/balance/{wallet_address}")
async def debug_wallet_balance(wallet_address: str):
    """Check wallet balance on Sepolia"""
    try:
        if web3_service.demo_mode:
            return {"status": "demo_mode", "balance": "100.0 ETH (mock)"}
        if not web3_service.w3:
            return {"status": "error", "message": "Web3 not connected"}
        wallet_address = web3_service.w3.to_checksum_address(wallet_address)
        balance_wei = web3_service.w3.eth.get_balance(wallet_address)
        balance_eth = web3_service.w3.from_wei(balance_wei, 'ether')
        gas_price = web3_service.w3.eth.gas_price
        estimated_gas = 500000
        gas_cost_wei = gas_price * estimated_gas
        gas_cost_eth = web3_service.w3.from_wei(gas_cost_wei, 'ether')
        sufficient_balance = balance_wei >= gas_cost_wei
        return {
            "status": "success",
            "wallet_address": wallet_address,
            "balance_wei": str(balance_wei),
            "balance_eth": f"{balance_eth:.6f}",
            "gas_price_gwei": web3_service.w3.from_wei(gas_price, 'gwei'),
            "estimated_gas_cost_eth": f"{gas_cost_eth:.6f}",
            "sufficient_balance": sufficient_balance,
            "chain_id": web3_service.w3.eth.chain_id
        }
    except Exception as e:
        logger.error(f"Wallet balance debug failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }


@router.get("/owner/{owner_address}", response_model=ArtworkListResponse)
async def get_artworks_by_owner(
    owner_address: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    try:
        artworks_collection = get_artwork_collection()

        filter_query = {
            "owner_address": {
                "$regex": f"^{re.escape(owner_address)}$",
                "$options": "i"
            }
        }

        total = await artworks_collection.count_documents(filter_query)
        has_next = (page * size) < total
        skip = (page - 1) * size

        cursor = artworks_collection.find(filter_query).skip(skip).limit(size).sort("created_at", -1)
        artworks_data = await cursor.to_list(length=size)

        artworks = []
        for doc in artworks_data:
            try:
                db_model = ArtworkInDB.model_validate(doc)
                artworks.append(ArtworkPublic.from_db_model(db_model))
            except Exception as e:
                logger.warning(f"Skipping invalid artwork document: {e}")
                continue

        return ArtworkListResponse(
            artworks=artworks,
            total=total,
            page=page,
            size=size,
            has_next=has_next
        )
    except Exception as e:
        logger.error(f"Error getting artworks by owner {owner_address}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get artworks")


@router.get("/creator/{creator_address}", response_model=ArtworkListResponse)
async def get_artworks_by_creator(
    creator_address: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    try:
        artworks_collection = get_artwork_collection()

        filter_query = {
            "creator_address": {
                "$regex": f"^{re.escape(creator_address)}$",
                "$options": "i"
            }
        }

        total = await artworks_collection.count_documents(filter_query)
        has_next = (page * size) < total
        skip = (page - 1) * size

        cursor = artworks_collection.find(filter_query).skip(skip).limit(size).sort("created_at", -1)
        artworks_data = await cursor.to_list(length=size)

        artworks = []
        for doc in artworks_data:
            try:
                db_model = ArtworkInDB.model_validate(doc)
                artworks.append(ArtworkPublic.from_db_model(db_model))
            except Exception as e:
                logger.warning(f"Skipping invalid artwork document: {e}")
                continue

        return ArtworkListResponse(
            artworks=artworks,
            total=total,
            page=page,
            size=size,
            has_next=has_next
        )
    except Exception as e:
        logger.error(f"Error getting artworks by creator {creator_address}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get artworks")


@router.post("/debug/test-registration")
async def debug_test_registration(
    test_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Test registration preparation without actually registering"""
    try:
        metadata_uri = test_data.get("metadata_uri", "ipfs://QmTest123")
        royalty_percentage = test_data.get("royalty_percentage", 1000)
        logger.info(f"🧪 Testing registration preparation...")
        logger.info(f"📝 Test inputs: {metadata_uri}, {royalty_percentage}, {current_user.wallet_address}")
        tx_data = await web3_service.prepare_register_transaction(
            metadata_uri,
            royalty_percentage,
            current_user.wallet_address
        )
        return {
            "status": "success",
            "message": "Registration preparation successful",
            "transaction_data": tx_data,
            "test_inputs": {
                "metadata_uri": metadata_uri,
                "royalty_percentage": royalty_percentage,
                "wallet_address": current_user.wallet_address
            }
        }
    except Exception as e:
        logger.error(f"Test registration failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__,
            "details": {
                "demo_mode": getattr(web3_service, 'demo_mode', None),
                "connected": getattr(web3_service, 'connected', None),
                "contract_address": getattr(settings, 'CONTRACT_ADDRESS', None)
            }
        }

@router.get("/debug/ipfs-config")
async def debug_ipfs_config(current_user: User = Depends(get_current_user)):
    """Debug endpoint to check IPFS configuration"""
    config_status = {
        "pinata_configured": bool(settings.PINATA_API_KEY and settings.PINATA_SECRET_API_KEY),
        "nft_storage_configured": bool(settings.NFT_STORAGE_API_KEY),
        "web3_storage_configured": bool(settings.WEB3_STORAGE_API_KEY),
        "file_size_limit": "10MB",
        "image_processing": "Enabled (resize + compression)"
    }
    test_results = {}
    if config_status["pinata_configured"]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.pinata.cloud/data/testAuthentication',
                    headers={
                        'pinata_api_key': settings.PINATA_API_KEY,
                        'pinata_secret_api_key': settings.PINATA_SECRET_API_KEY,
                    }
                ) as response:
                    test_results["pinata"] = {
                        "status": response.status,
                        "authenticated": response.status == 200
                    }
        except Exception as e:
            test_results["pinata"] = {"error": str(e)}
    return {
        "config_status": config_status,
        "connectivity_test": test_results,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/debug/owner-artworks/{owner_address}")
async def debug_owner_artworks(owner_address: str):
    """Debug endpoint to check what artworks exist for an owner"""
    try:
        artworks_collection = get_artwork_collection()
        normalized_address = owner_address.lower()
        artworks = await artworks_collection.find({"owner_address": normalized_address}).to_list(length=100)
        all_artworks = await artworks_collection.find({}).to_list(length=1000)
        possible_matches = []
        for art in all_artworks:
            art_owner = art.get('owner_address', '').lower()
            if art_owner == normalized_address:
                possible_matches.append({
                    "token_id": art.get('token_id'),
                    "owner_address": art.get('owner_address'),
                    "creator_address": art.get('creator_address'),
                    "title": art.get('title')
                })
        return {
            "requested_address": owner_address,
            "normalized_address": normalized_address,
            "exact_matches_count": len(artworks),
            "exact_matches": [
                {
                    "token_id": art.get('token_id'),
                    "owner_address": art.get('owner_address'),
                    "creator_address": art.get('creator_address'),
                    "title": art.get('title')
                }
                for art in artworks
            ],
            "all_artworks_sample": [
                {
                    "token_id": art.get('token_id'),
                    "owner_address": art.get('owner_address'),
                    "creator_address": art.get('creator_address')
                }
                for art in all_artworks[:10]
            ]
        }
    except Exception as e:
        logger.error(f"Debug artworks failed: {e}", exc_info=True)
        return {"error": str(e)}

# # --- Sale transaction preparation ---
@router.post("/prepare-sale-transaction", response_model=dict)
async def prepare_sale_transaction(
    sale_data: dict,
    current_user: User = Depends(get_current_user)
):
    try:
        token_id = sale_data.get("token_id")
        buyer_address = sale_data.get("buyer_address")
        sale_price = sale_data.get("sale_price")
        current_owner = sale_data.get("current_owner")

        if not all([token_id, buyer_address, sale_price, current_owner]):
            raise HTTPException(status_code=400, detail="Missing required sale parameters")

        if not web3_service.w3:
            raise HTTPException(status_code=500, detail="Web3 service not available")

        buyer_address_checksum = web3_service.w3.to_checksum_address(buyer_address)
        current_owner_checksum = web3_service.w3.to_checksum_address(current_owner)
        sale_price_wei = web3_service.w3.to_wei(float(sale_price), 'ether')

        tx_data = await web3_service.prepare_sale_transaction(
            token_id=token_id,
            buyer_address=buyer_address_checksum,
            seller_address=current_owner_checksum,
            sale_price_wei=sale_price_wei
        )

        return {
            "transaction_data": tx_data,
            "sale_details": {
                "token_id": token_id,
                "sale_price_eth": sale_price,
                "sale_price_wei": str(sale_price_wei),
                "current_owner": current_owner_checksum,
                "buyer_address": buyer_address_checksum
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sale preparation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to prepare sale transaction: {str(e)}")


# --- Confirm sale ---
@router.post("/confirm-sale", response_model=dict)
async def confirm_sale(
    sale_confirmation: SaleConfirmation,
    current_user: User = Depends(get_current_user)
):
    try:
        artworks_collection = get_artwork_collection()

        tx_hash = sale_confirmation.tx_hash
        token_id = sale_confirmation.token_id
        buyer_address = sale_confirmation.buyer_address
        seller_address = sale_confirmation.seller_address
        sale_price = sale_confirmation.sale_price

        tx_receipt = await web3_service.get_transaction_receipt(tx_hash)
        if not tx_receipt or tx_receipt.get("status") != 1:
            raise HTTPException(status_code=400, detail="Sale transaction failed or not found")

        await artworks_collection.update_one(
            {"token_id": token_id},
            {"$set": {"owner_address": buyer_address.lower(), "updated_at": datetime.utcnow()}}
        )

        sale_transaction = TransactionCreate(
            tx_hash=tx_hash,
            from_address=seller_address,
            to_address=buyer_address,
            value=str(sale_price),
            transaction_type=TransactionType.SALE,
            status=TransactionStatus.CONFIRMED,
            metadata={"token_id": token_id}
        )

        db = artworks_collection.database  # Get database from collection
        await db.transactions.insert_one(sale_transaction.model_dump(by_alias=True))

        return {
            "success": True,
            "message": "Sale confirmed successfully",
            "new_owner": buyer_address,
            "token_id": token_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sale confirmation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to confirm sale: {str(e)}")



