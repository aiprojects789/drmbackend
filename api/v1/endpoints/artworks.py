from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from typing import List, Optional
from db.models import (
    ArtworkCreate, ArtworkUpdate, ArtworkBase as Artwork, ArtworkInDB, SaleConfirmation,
    ArtworkPublic, ArtworkListResponse, User, TransactionCreate, TransactionType
)
from db.database import get_database
from api.v1.endpoints.auth import get_current_user
from services.web3_service import web3_service
import logging
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from core.config import settings
from PIL import Image
import io
import json
import requests
import base64
import aiohttp
import asyncio
import re

logger = logging.getLogger(__name__)
router = APIRouter()

class ImageProcessor:
    """Service class to handle image processing and optimization"""
    
    @staticmethod
    async def process_image(image_data: bytes, max_size: int = 5 * 1024 * 1024) -> bytes:
        """Process and optimize image to reduce file size"""
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary (removes alpha channel)
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            
            # Calculate target dimensions (max 2000px on longest side)
            max_dimension = 2000
            if max(img.size) > max_dimension:
                ratio = max_dimension / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Optimize JPEG/PNG with quality compression
            output = io.BytesIO()
            
            if img.format == 'JPEG' or img.mode == 'RGB':
                img.save(output, format='JPEG', quality=85, optimize=True)
            else:
                img.save(output, format='PNG', optimize=True)
            
            processed_data = output.getvalue()
            
            # If still too large, apply more aggressive compression
            if len(processed_data) > max_size:
                output = io.BytesIO()
                if img.mode == 'RGB':
                    quality = 75  # Lower quality
                    while len(processed_data) > max_size and quality >= 50:
                        img.save(output, format='JPEG', quality=quality, optimize=True)
                        processed_data = output.getvalue()
                        quality -= 5
                else:
                    # For PNG, convert to JPEG if too large
                    rgb_img = img.convert('RGB')
                    rgb_img.save(output, format='JPEG', quality=80, optimize=True)
                    processed_data = output.getvalue()
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Image processing failed: {str(e)}"
            )

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

# Add this endpoint to your router
@router.post("/register-with-image")
async def register_artwork_with_image(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    royalty_percentage: int = Form(...),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Register artwork with image upload to IPFS"""
    try:
        # Validate royalty percentage
        if not 0 <= royalty_percentage <= 2000:
            raise HTTPException(
                status_code=400,
                detail="Royalty must be between 0-2000 basis points"
            )

        # 1. Process and validate the image
        image_data = await image.read()
        
        # Check file size first
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=400,
                detail="Image file too large (max 10MB)"
            )
        
        try:
            # Process image to reduce size
            processed_image_data = await ImageProcessor.process_image(image_data)
            
            # 2. Upload processed image to IPFS
            image_ipfs_uri = await IPFSService.upload_to_ipfs(processed_image_data, image.filename)
            
            # 3. Create metadata JSON
            metadata = {
                "name": title,
                "description": description,
                "image": image_ipfs_uri,
                "attributes": {
                    "royalty_percentage": royalty_percentage,
                    "creator": current_user.wallet_address,
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            
            # 4. Upload metadata to IPFS
            metadata_bytes = json.dumps(metadata).encode('utf-8')
            metadata_uri = await IPFSService.upload_to_ipfs(metadata_bytes, "metadata.json")
            
        except Exception as ipfs_error:
            logger.error(f"IPFS upload failed: {str(ipfs_error)}")
            
            # Provide more specific error messages
            error_msg = str(ipfs_error)
            if "authentication" in error_msg.lower():
                detail = "IPFS service authentication failed. Please check API keys."
            elif "too large" in error_msg.lower():
                detail = "File too large for IPFS service. Please try a smaller image."
            else:
                detail = f"Failed to upload to IPFS: {error_msg}"
            
            raise HTTPException(status_code=500, detail=detail)
        
        # 5. Prepare registration with the metadata URI
        tx_data = await web3_service.prepare_register_transaction(
            metadata_uri,
            royalty_percentage,
            current_user.wallet_address
        )
        
        return {
            "status": "success",
            "transaction_data": tx_data,
            "metadata_uri": metadata_uri,
            "image_uri": image_ipfs_uri,
            "royalty_percentage": royalty_percentage
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration with image failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )
    
@router.post("/confirm-registration", response_model=dict)
async def confirm_registration(
    confirmation_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Finalize registration after successful blockchain transaction"""
    try:
        db = get_database()
        
        # Verify the transaction happened
        tx_receipt = await web3_service.get_transaction_receipt(
            confirmation_data["tx_hash"]
        )
        
        if not tx_receipt or tx_receipt.get("status") != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Blockchain transaction failed"
            )

        # Get the actual token ID from blockchain
        token_id = await web3_service.get_token_id_from_tx(confirmation_data["tx_hash"])
        
        if not token_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not determine token ID from transaction"
            )

        # Handle attributes - convert empty list to empty dict if needed
        attributes = confirmation_data.get("attributes")
        if attributes is not None and isinstance(attributes, list):
            attributes = {}  # Convert empty list to empty dict
        elif attributes is None:
            attributes = {}  # Default to empty dict if None

        # Create the final artwork record
        artwork = ArtworkInDB(
            _id=ObjectId(),
            token_id=token_id,
            creator_address=current_user.wallet_address,
            owner_address=current_user.wallet_address,
            metadata_uri=confirmation_data["metadata_uri"],
            royalty_percentage=confirmation_data["royalty_percentage"],
            title=confirmation_data.get("title"),
            description=confirmation_data.get("description"),
            attributes=attributes,  # Use the processed attributes
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tx_hash=confirmation_data["tx_hash"]
        )

        # Insert into database
        result = await db.artworks.insert_one(artwork.model_dump(by_alias=True))

        return {
            "success": True,
            "artwork_id": str(result.inserted_id),
            "token_id": token_id
        }

    except Exception as e:
        logger.error(f"Artwork confirmation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm artwork registration: {str(e)}"
        )
    
@router.get("/", response_model=ArtworkListResponse)
async def list_artworks(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    creator_address: Optional[str] = None,
    owner_address: Optional[str] = None
):
    try:
        db = get_database()
        
        # Build filter with normalized addresses
        filter_query = {}
        if creator_address: 
            filter_query["creator_address"] = creator_address.lower()
        if owner_address: 
            filter_query["owner_address"] = owner_address.lower()
        
        total = await db.artworks.count_documents(filter_query)
        has_next = (page * size) < total
        skip = (page - 1) * size
        
        cursor = db.artworks.find(filter_query).skip(skip).limit(size).sort("created_at", -1)
        artworks_data = await cursor.to_list(length=size)
        
        # Convert to ArtworkPublic models
        artworks = []
        for doc in artworks_data:
            try:
                db_model = ArtworkInDB.validate_document(doc)
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
        logger.error(f"Error listing artworks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list artworks"
        )
    
@router.get("/{token_id}", response_model=Artwork)
async def get_artwork(token_id: int):
    try:
        db = get_database()
        artwork_doc = await db.artworks.find_one({"token_id": token_id})
        if not artwork_doc:
            raise HTTPException(status_code=404, detail="Artwork not found")
        
        artwork = ArtworkInDB.validate_document(artwork_doc)
        return Artwork.model_validate(artwork)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting artwork {token_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get artwork"
        )

@router.get("/{token_id}/blockchain", response_model=dict)
async def get_artwork_blockchain_info(token_id: int):
    """Get artwork information from blockchain"""
    try:
        artwork_info = await web3_service.get_artwork_info(token_id)
        owner = await web3_service.get_artwork_owner(token_id)
        
        if not artwork_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found on blockchain"
            )
        
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
        logger.error(f"Error getting blockchain info for artwork {token_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get blockchain information"
        )

@router.put("/{token_id}", response_model=Artwork)
async def update_artwork(
    token_id: int,
    artwork_update: ArtworkUpdate,
    current_user: User = Depends(get_current_user)
):
    try:
        db = get_database()
        artwork_doc = await db.artworks.find_one({"token_id": token_id})
        if not artwork_doc:
            raise HTTPException(status_code=404, detail="Artwork not found")
        
        artwork = ArtworkInDB.validate_document(artwork_doc)
        if artwork.owner_address != current_user.wallet_address:
            raise HTTPException(status_code=403, detail="Only owner can update")
        
        # Apply updates
        update_data = artwork_update.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        await db.artworks.update_one(
            {"token_id": token_id},
            {"$set": update_data}
        )
        
        # Return updated artwork
        updated_doc = await db.artworks.find_one({"token_id": token_id})
        return Artwork.model_validate(ArtworkInDB.validate_document(updated_doc))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating artwork {token_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update artwork"
        )

@router.get("/test-contract")
async def test_contract():
    """Test contract connection and configuration"""
    try:
        from services.web3_service import web3_service
        
        # Check if service is initialized
        if not hasattr(web3_service, 'connected'):
            return {
                "status": "error", 
                "message": "Web3 service not initialized",
                "details": {
                    "service_exists": False
                }
            }
        
        # Check demo mode
        if web3_service.demo_mode:
            return {
                "status": "warning", 
                "message": "Running in demo mode",
                "details": {
                    "demo_mode": True,
                    "connected": web3_service.connected
                }
            }
        
        # Check connection
        if not web3_service.connected:
            return {
                "status": "error", 
                "message": "Web3 not connected",
                "details": {
                    "connected": False,
                    "demo_mode": web3_service.demo_mode
                }
            }
        
        # Test basic contract call
        try:
            current_token_id = await web3_service.get_artwork_count()
            contract_address = web3_service.contract.address if web3_service.contract else "Not available"
            chain_id = web3_service.w3.eth.chain_id if web3_service.w3 else "Not available"
            
            return {
                "status": "success", 
                "message": "Contract connected successfully",
                "details": {
                    "contract_address": contract_address,
                    "current_token_id": current_token_id,
                    "chain_id": chain_id,
                    "connected": True,
                    "demo_mode": False
                }
            }
        except Exception as contract_error:
            return {
                "status": "error",
                "message": f"Contract call failed: {str(contract_error)}",
                "details": {
                    "contract_address": web3_service.contract.address if web3_service.contract else "Not available",
                    "connected": web3_service.connected,
                    "demo_mode": web3_service.demo_mode,
                    "error": str(contract_error)
                }
            }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Test failed: {str(e)}",
            "details": {
                "error": str(e),
                "error_type": type(e).__name__
            }
        }

# Add these debug endpoints to your artwork router

@router.get("/debug/contract-abi")
async def debug_contract_abi():
    """Debug contract ABI compatibility"""
    try:
        from services.web3_service import web3_service
        
        if web3_service.demo_mode:
            return {
                "status": "demo_mode",
                "message": "Running in demo mode - no real contract testing"
            }
        
        # Verify ABI compatibility
        verification = await web3_service.verify_contract_abi()
        return verification
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }

@router.get("/debug/balance/{wallet_address}")
async def debug_wallet_balance(wallet_address: str):
    """Check wallet balance on Sepolia"""
    try:
        from services.web3_service import web3_service
        
        if web3_service.demo_mode:
            return {"status": "demo_mode", "balance": "100.0 ETH (mock)"}
        
        if not web3_service.w3:
            return {"status": "error", "message": "Web3 not connected"}
        
        # Validate address
        wallet_address = web3_service.w3.to_checksum_address(wallet_address)
        
        # Get balance
        balance_wei = web3_service.w3.eth.get_balance(wallet_address)
        balance_eth = web3_service.w3.from_wei(balance_wei, 'ether')
        
        # Get gas price for cost estimation
        gas_price = web3_service.w3.eth.gas_price
        estimated_gas = 500000  # Rough estimate for registration
        gas_cost_wei = gas_price * estimated_gas
        gas_cost_eth = web3_service.w3.from_wei(gas_cost_wei, 'ether')
        
        return {
            "status": "success",
            "wallet_address": wallet_address,
            "balance_wei": str(balance_wei),
            "balance_eth": f"{balance_eth:.6f}",
            "gas_price_gwei": web3_service.w3.from_wei(gas_price, 'gwei'),
            "estimated_gas_cost_eth": f"{gas_cost_eth:.6f}",
            "sufficient_balance": balance >= gas_cost_wei,
            "chain_id": web3_service.w3.eth.chain_id
        }
        
    except Exception as e:
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
    """Get artworks owned by a specific address"""
    try:
        db = get_database()
        
        # Handle both checksum and lowercase addresses
        # Create a case-insensitive filter using regex
        filter_query = {
            "owner_address": {
                "$regex": f"^{re.escape(owner_address)}$", 
                "$options": "i"  # case-insensitive
            }
        }
        
        # Get total count
        total = await db.artworks.count_documents(filter_query)
        has_next = (page * size) < total
        
        # Get artworks with pagination
        skip = (page - 1) * size
        cursor = db.artworks.find(filter_query).skip(skip).limit(size).sort("created_at", -1)
        artworks_data = await cursor.to_list(length=size)
        
        # Convert to response models
        artworks = []
        for artwork_doc in artworks_data:
            try:
                artwork = ArtworkInDB.validate_document(artwork_doc)
                artworks.append(ArtworkPublic.from_db_model(artwork))
            except Exception as e:
                logger.warning(f"Skipping invalid artwork document: {e}")
                continue
        
        logger.info(f"Found {len(artworks)} artworks for owner {owner_address}")
        
        return ArtworkListResponse(
            artworks=artworks,
            total=total,
            page=page,
            size=size,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Error getting artworks by owner {owner_address}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get artworks"
        )

@router.get("/creator/{creator_address}", response_model=ArtworkListResponse)
async def get_artworks_by_creator(
    creator_address: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """Get artworks created by a specific address"""
    try:
        db = get_database()
        
        # Use case-insensitive search with regex
        filter_query = {
            "creator_address": {
                "$regex": f"^{re.escape(creator_address)}$", 
                "$options": "i"  # case-insensitive
            }
        }
        
        # Get total count
        total = await db.artworks.count_documents(filter_query)
        has_next = (page * size) < total
        
        # Get artworks with pagination
        skip = (page - 1) * size
        cursor = db.artworks.find(filter_query).skip(skip).limit(size).sort("created_at", -1)
        artworks_data = await cursor.to_list(length=size)
        
        # Convert to response models
        artworks = []
        for artwork_doc in artworks_data:
            try:
                artwork = ArtworkInDB.validate_document(artwork_doc)
                artworks.append(ArtworkPublic.from_db_model(artwork))
            except Exception as e:
                logger.warning(f"Skipping invalid artwork document: {e}")
                continue
        
        logger.info(f"Found {len(artworks)} artworks for creator {creator_address}")
        
        return ArtworkListResponse(
            artworks=artworks,
            total=total,
            page=page,
            size=size,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Error getting artworks by creator {creator_address}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get artworks"
        )

@router.post("/debug/test-registration")
async def debug_test_registration(
    test_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Test registration preparation without actually registering"""
    try:
        from services.web3_service import web3_service
        
        metadata_uri = test_data.get("metadata_uri", "ipfs://QmTest123")
        royalty_percentage = test_data.get("royalty_percentage", 1000)
        
        logger.info(f"🧪 Testing registration preparation...")
        logger.info(f"📝 Test inputs: {metadata_uri}, {royalty_percentage}, {current_user.wallet_address}")
        
        # This will test everything except actually sending the transaction
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
        logger.error(f"💥 Test registration failed: {e}")
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
    
    # Test connectivity to each service
    test_results = {}
    
    # Test Pinata connectivity
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
        db = get_database()
        normalized_address = owner_address.lower()
        
        # Check what's actually in the database
        artworks = await db.artworks.find({"owner_address": normalized_address}).to_list(length=100)
        
        # Also check with case-insensitive search to see if there are variations
        all_artworks = await db.artworks.find({}).to_list(length=1000)
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
                for art in all_artworks[:10]  # First 10 for sampling
            ]
        }
        
    except Exception as e:
        logger.error(f"Debug artworks failed: {e}", exc_info=True)
        return {"error": str(e)}
    
@router.post("/prepare-sale-transaction", response_model=dict)
async def prepare_sale_transaction(
    sale_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Prepare a sale transaction for an artwork"""
    try:
        from services.web3_service import web3_service
        
        token_id = sale_data.get("token_id")
        buyer_address = sale_data.get("buyer_address")
        sale_price = sale_data.get("sale_price")
        current_owner = sale_data.get("current_owner")
        
        if not all([token_id, buyer_address, sale_price, current_owner]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required sale parameters"
            )
        
        # Validate addresses
        if not web3_service.w3:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Web3 service not available"
            )
        
        buyer_address_checksum = web3_service.w3.to_checksum_address(buyer_address)
        current_owner_checksum = web3_service.w3.to_checksum_address(current_owner)
        
        # Convert price to wei
        sale_price_wei = web3_service.w3.to_wei(float(sale_price), 'ether')
        
        # Prepare transaction - use the improved method with proper gas estimation
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to prepare sale transaction: {str(e)}"
        )

@router.post("/confirm-sale", response_model=dict)
async def confirm_sale(
    sale_confirmation: SaleConfirmation,  # This is now a Pydantic model, not a dict
    current_user: User = Depends(get_current_user)
):
    """Confirm a completed sale transaction"""
    try:
        db = get_database()
        
        # Access attributes directly from the Pydantic model
        tx_hash = sale_confirmation.tx_hash
        token_id = sale_confirmation.token_id
        buyer_address = sale_confirmation.buyer_address
        seller_address = sale_confirmation.seller_address
        sale_price = sale_confirmation.sale_price
        
        # Verify the transaction
        from services.web3_service import web3_service
        tx_receipt = await web3_service.get_transaction_receipt(tx_hash)
        
        if not tx_receipt or tx_receipt.get("status") != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sale transaction failed or not found"
            )
        
        # Update artwork ownership in database
        await db.artworks.update_one(
            {"token_id": token_id},
            {
                "$set": {
                    "owner_address": buyer_address.lower(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Create sale transaction record with status field
        from db.models import TransactionCreate, TransactionType, TransactionStatus
        sale_transaction = TransactionCreate(
            tx_hash=tx_hash,
            from_address=seller_address,
            to_address=buyer_address,
            value=str(sale_price),
            transaction_type=TransactionType.SALE,
            status=TransactionStatus.CONFIRMED,
            metadata={
                "token_id": token_id
            }
        )
        
        # Insert transaction record
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm sale: {str(e)}"
        )