from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from typing import List, Optional, Dict
from db.models import (
    LicenseCreate, License, LicenseInDB,
    LicenseListResponse, User, LicenseType
)
from db.database import get_database
from api.v1.endpoints.auth import get_current_user
from services.web3_service import web3_service
import logging
from datetime import datetime, timedelta
from bson import ObjectId
from web3 import Web3
import asyncio
import json
import io
import aiohttp

logger = logging.getLogger(__name__)
router = APIRouter()

class LicenseDocumentService:
    """Service to generate and upload license documents to IPFS"""
    
    @staticmethod
    def generate_license_document(
        artwork_title: str,
        artwork_token_id: int,
        licensor_address: str,
        licensee_address: str,
        license_type: str,
        duration_days: int,
        start_date: datetime
    ) -> dict:
        """Generate a comprehensive license document"""
        end_date = start_date + timedelta(days=duration_days)
        
        license_document = {
            "license_agreement": {
                "title": f"Artwork License Agreement - {artwork_title}",
                "artwork": {
                    "title": artwork_title,
                    "token_id": artwork_token_id,
                    "blockchain": "Ethereum Sepolia"
                },
                "parties": {
                    "licensor": {
                        "wallet_address": licensor_address,
                        "role": "Artwork Owner & Rights Grantor"
                    },
                    "licensee": {
                        "wallet_address": licensee_address,
                        "role": "License Holder"
                    }
                },
                "license_terms": {
                    "type": license_type,
                    "duration": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "duration_days": duration_days
                    },
                    "permissions": LicenseDocumentService.get_permissions_by_type(license_type),
                    "restrictions": LicenseDocumentService.get_restrictions_by_type(license_type),
                    "attribution_required": license_type in ["COMMERCIAL", "PERSONAL"]
                },
                "terms_and_conditions": {
                    "usage_rights": LicenseDocumentService.get_usage_rights(license_type),
                    "termination": "This license automatically expires on the end date or can be revoked by the licensor.",
                    "governing_law": "This agreement is governed by blockchain smart contract terms.",
                    "dispute_resolution": "Disputes will be resolved according to the platform's terms of service."
                },
                "technical_details": {
                    "blockchain": "Ethereum",
                    "network": "Sepolia Testnet",
                    "license_fee": "0.1 ETH",
                    "created_at": datetime.utcnow().isoformat(),
                    "document_version": "1.0"
                }
            }
        }
        
        return license_document
    
    @staticmethod
    def get_permissions_by_type(license_type: str) -> list:
        """Get permissions based on license type"""
        permissions = {
            "PERSONAL": [
                "View and display the artwork for personal use",
                "Share the artwork in personal social media with attribution",
                "Use as desktop wallpaper or personal device backgrounds"
            ],
            "COMMERCIAL": [
                "Use in commercial projects and marketing materials",
                "Include in commercial websites and applications",
                "Use for promotional purposes with proper attribution",
                "Modify and create derivative works for commercial use"
            ],
            "EXCLUSIVE": [
                "Exclusive rights to all uses of the artwork",
                "Commercial and non-commercial usage rights",
                "Right to sublicense to third parties",
                "Exclusive access during the license period"
            ]
        }
        return permissions.get(license_type, [])
    
    @staticmethod
    def get_restrictions_by_type(license_type: str) -> list:
        """Get restrictions based on license type"""
        restrictions = {
            "PERSONAL": [
                "No commercial use permitted",
                "Cannot resell or redistribute",
                "Cannot claim ownership of the original work"
            ],
            "COMMERCIAL": [
                "Must provide proper attribution",
                "Cannot claim ownership of the original work",
                "Cannot register trademarks using the artwork"
            ],
            "EXCLUSIVE": [
                "Other parties cannot use the artwork during license period",
                "Licensee is responsible for protecting exclusivity"
            ]
        }
        return restrictions.get(license_type, [])
    
    @staticmethod
    def get_usage_rights(license_type: str) -> str:
        """Get detailed usage rights description"""
        usage_descriptions = {
            "PERSONAL": "This license grants personal, non-commercial usage rights only. The licensee may view, display, and share the artwork for personal purposes with proper attribution.",
            "COMMERCIAL": "This license grants commercial usage rights including marketing, advertising, and business applications. Attribution to the original creator is required in all uses.",
            "EXCLUSIVE": "This license grants exclusive rights to the artwork during the specified period. No other licenses will be granted during this time, and the licensee has full commercial and non-commercial usage rights."
        }
        return usage_descriptions.get(license_type, "Standard usage rights apply.")

# Import the IPFSService from the artworks router
from api.v1.endpoints.artworks import IPFSService

@router.post("/grant-with-document")
async def grant_license_with_document(
    token_id: int = Form(...),
    licensee_address: str = Form(...),
    duration_days: int = Form(...),
    license_type: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Grant a license with automatic document generation and IPFS upload"""
    try:
        db = get_database()
        
        # Validate inputs
        if not 1 <= duration_days <= 365:
            raise HTTPException(
                status_code=400,
                detail="Duration must be between 1 and 365 days"
            )
        
        if license_type not in ["PERSONAL", "COMMERCIAL", "EXCLUSIVE"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid license type"
            )
        
        # Validate Ethereum address
        try:
            from web3 import Web3
            licensee_address = Web3.to_checksum_address(licensee_address)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid Ethereum address"
            )
        
        # Check if artwork exists and user is owner
        artwork_doc = await db.artworks.find_one({"token_id": token_id})
        if not artwork_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found"
            )
        
        # Normalize addresses for comparison
        artwork_owner = artwork_doc["owner_address"].lower()
        current_user_addr = current_user.wallet_address.lower()
        
        if artwork_owner != current_user_addr:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only artwork owner can grant licenses"
            )
        
        # Generate license document
        start_date = datetime.utcnow()
        
        license_document = LicenseDocumentService.generate_license_document(
            artwork_title=artwork_doc.get("title", "Untitled"),
            artwork_token_id=token_id,
            licensor_address=current_user.wallet_address,
            licensee_address=licensee_address,
            license_type=license_type,
            duration_days=duration_days,
            start_date=start_date
        )
        
        # Upload license document to IPFS
        try:
            document_json = json.dumps(license_document, indent=2)
            document_bytes = document_json.encode('utf-8')
            
            # Upload to IPFS using the same service as artworks
            terms_hash = await IPFSService.upload_to_ipfs(
                document_bytes, 
                f"license_agreement_{token_id}_{int(start_date.timestamp())}.json"
            )
            
        except Exception as ipfs_error:
            logger.error(f"IPFS upload failed: {str(ipfs_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload license document to IPFS: {str(ipfs_error)}"
            )
        
        # Get next license ID
        license_count = await db.licenses.count_documents({}) + 1
        
        # Prepare transaction data with retry logic
        max_retries = 3
        tx_data = None
        
        for attempt in range(max_retries):
            try:
                tx_data = await web3_service.prepare_license_transaction(
                    token_id,
                    licensee_address,
                    duration_days,
                    terms_hash,
                    license_type,
                    current_user.wallet_address
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
                await asyncio.sleep(1)
        
        if not tx_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to prepare transaction after multiple attempts"
            )
        
        # Create license document using LicenseInDB model
        end_date = start_date + timedelta(days=duration_days)
        fee_eth = 0.1  # Fixed fee
        
        license_dict = {
            "license_id": license_count,
            "token_id": token_id,
            "licensee_address": licensee_address.lower(),
            "licensor_address": current_user.wallet_address.lower(),
            "start_date": start_date,
            "end_date": end_date,
            "terms_hash": terms_hash,
            "license_type": license_type,
            "is_active": True,
            "fee_paid": fee_eth,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "transaction_data": tx_data
        }
        
        # Use LicenseInDB model to validate before insertion
        license_doc = LicenseInDB.from_mongo(license_dict)
        result = await db.licenses.insert_one(license_doc.model_dump(by_alias=True, exclude={"id"}))
        
        logger.info(f"Created license document with ID: {result.inserted_id}")

        # Update artwork licensing status
        await db.artworks.update_one(
            {"token_id": token_id},
            {"$set": {"is_licensed": True, "updated_at": datetime.utcnow()}}
        )
        
        return {
            "success": True,
            "license_id": license_count,
            "transaction_data": tx_data,
            "terms_hash": terms_hash,
            "license_document_preview": license_document["license_agreement"],
            "fee": fee_eth
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error granting license with document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant license: {str(e)}"
        )

@router.post("/grant", response_model=dict)
async def grant_license(
    license_data: LicenseCreate,
    current_user: User = Depends(get_current_user)
):
    """Grant a license for an artwork (legacy endpoint)"""
    try:
        db = get_database()
        
        # Check if artwork exists and user is owner
        artwork_doc = await db.artworks.find_one({"token_id": license_data.token_id})
        if not artwork_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found"
            )
        
        # Normalize addresses for comparison
        artwork_owner = artwork_doc["owner_address"].lower()
        current_user_addr = current_user.wallet_address.lower()
        
        if artwork_owner != current_user_addr:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only artwork owner can grant licenses"
            )
        
        # Get next license ID
        license_count = await db.licenses.count_documents({}) + 1
        
        # Prepare transaction data with retry logic
        max_retries = 3
        tx_data = None
        
        for attempt in range(max_retries):
            try:
                tx_data = await web3_service.prepare_license_transaction(
                    license_data.token_id,
                    license_data.licensee_address,  # This will be converted to checksum in the service
                    license_data.duration_days,
                    license_data.terms_hash,
                    license_data.license_type.value,
                    current_user.wallet_address  # This will be converted to checksum in the service
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
                await asyncio.sleep(1)  # Wait before retry
        
        if not tx_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to prepare transaction after multiple attempts"
            )
        
        # Create license document using LicenseInDB model
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=license_data.duration_days)
        
        # Fixed fee of 0.1 ETH as per contract
        fee_eth = 0.1
        
        license_dict = {
            "license_id": license_count,
            "token_id": license_data.token_id,
            "licensee_address": license_data.licensee_address.lower(),
            "licensor_address": current_user.wallet_address.lower(),
            "start_date": start_date,
            "end_date": end_date,
            "terms_hash": license_data.terms_hash,
            "license_type": license_data.license_type,
            "is_active": True,
            "fee_paid": fee_eth,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "transaction_data": tx_data
        }
        
        # Use LicenseInDB model to validate before insertion
        license_doc = LicenseInDB.from_mongo(license_dict)
        result = await db.licenses.insert_one(license_doc.model_dump(by_alias=True, exclude={"id"}))
        
        logger.info(f"Created license document with ID: {result.inserted_id}")
        
        return {
            "success": True,
            "license_id": license_count,
            "transaction_data": tx_data,
            "fee": fee_eth
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error granting license: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant license: {str(e)}"
        )

@router.post("/{license_id}/revoke", response_model=dict)
async def revoke_license(
    license_id: int,
    current_user: User = Depends(get_current_user)
):
    """Revoke a license"""
    try:
        db = get_database()
        
        # Find license
        license_doc = await db.licenses.find_one({"license_id": license_id})
        if not license_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="License not found"
            )
        
        # Use from_mongo method which should handle ObjectId conversion
        license_obj = LicenseInDB.from_mongo(license_doc)
        
        # Check if user is the licensor (normalize addresses)
        licensor_addr = license_obj.licensor_address.lower()
        current_user_addr = current_user.wallet_address.lower()
        
        if licensor_addr != current_user_addr:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only licensor can revoke license. Licensor: {licensor_addr}, Current: {current_user_addr}"
            )
        
        # Check if license is already revoked
        if not license_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License is already revoked"
            )
        
        # Update license status
        update_result = await db.licenses.update_one(
            {"license_id": license_id},
            {
                "$set": {
                    "is_active": False, 
                    "updated_at": datetime.utcnow(),
                    "revoked_at": datetime.utcnow()
                }
            }
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update license status"
            )
        
        # Check if artwork still has active licenses
        active_licenses = await db.licenses.count_documents({
            "token_id": license_obj.token_id,
            "is_active": True,
            "end_date": {"$gt": datetime.utcnow()}
        })
        
        # Update artwork licensing status
        await db.artworks.update_one(
            {"token_id": license_obj.token_id},
            {"$set": {"is_licensed": active_licenses > 0, "updated_at": datetime.utcnow()}}
        )
        
        logger.info(f"Successfully revoked license {license_id} for user {current_user.wallet_address}")
        
        return {
            "success": True,
            "message": "License revoked successfully",
            "license_id": license_id,
            "remaining_active_licenses": active_licenses
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking license {license_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke license: {str(e)}"
        )

# Replace the list_licenses function in your licenses.py with this improved version
@router.get("/", response_model=LicenseListResponse)
async def list_licenses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    token_id: Optional[int] = None,
    licensee_address: Optional[str] = None,
    licensor_address: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """List licenses with pagination and filtering - DIRECT APPROACH"""
    try:
        db = get_database()
        
        # Build filter
        filter_query = {}
        if token_id is not None:
            filter_query["token_id"] = token_id
        if licensee_address:
            filter_query["licensee_address"] = licensee_address.lower()
        if licensor_address:
            filter_query["licensor_address"] = licensor_address.lower()
        if is_active is not None:
            filter_query["is_active"] = is_active
        
        # Get total count
        total = await db.licenses.count_documents(filter_query)
        has_next = (page * size) < total
        
        # Get licenses with pagination
        skip = (page - 1) * size
        cursor = db.licenses.find(filter_query).skip(skip).limit(size).sort("created_at", -1)
        licenses_data = await cursor.to_list(length=size)
        
        # Convert to response models - DIRECT APPROACH (no from_mongo)
        licenses = []
        
        for doc in licenses_data:
            try:
                # Convert datetime objects to ISO strings for JSON serialization
                license_dict = {
                    "license_id": doc["license_id"],
                    "token_id": doc["token_id"],
                    "licensee_address": doc["licensee_address"],
                    "licensor_address": doc["licensor_address"],
                    "start_date": doc["start_date"].isoformat() if isinstance(doc["start_date"], datetime) else doc["start_date"],
                    "end_date": doc["end_date"].isoformat() if isinstance(doc["end_date"], datetime) else doc["end_date"],
                    "terms_hash": doc["terms_hash"],
                    "license_type": doc["license_type"],
                    "is_active": doc.get("is_active", True),
                    "fee_paid": doc["fee_paid"],
                    "created_at": doc.get("created_at", datetime.utcnow()).isoformat() if isinstance(doc.get("created_at"), datetime) else doc.get("created_at"),
                    "updated_at": doc.get("updated_at", datetime.utcnow()).isoformat() if isinstance(doc.get("updated_at"), datetime) else doc.get("updated_at"),
                }
                
                # Add revoked_at if it exists
                if "revoked_at" in doc and doc["revoked_at"] is not None:
                    license_dict["revoked_at"] = doc["revoked_at"].isoformat() if isinstance(doc["revoked_at"], datetime) else doc["revoked_at"]
                
                # Create License object directly
                license_obj = License(**license_dict)
                licenses.append(license_obj)
                
            except Exception as e:
                logger.error(f"Skipping license document {doc.get('license_id', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"Successfully processed {len(licenses)} out of {len(licenses_data)} licenses")
        
        return LicenseListResponse(
            licenses=licenses,
            total=total,
            page=page,
            size=size,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Error listing licenses: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list licenses: {str(e)}"
        )
    
@router.get("/user/{user_address}", response_model=LicenseListResponse)
async def get_user_licenses(
    user_address: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    as_licensee: bool = Query(True)
):
    """Get licenses for a user (as licensee or licensor) - improved version"""
    try:
        # Normalize address
        normalized_address = user_address.lower()
        
        logger.info(f"Getting licenses for user: {user_address} (normalized: {normalized_address}), as_licensee: {as_licensee}")
        
        if as_licensee:
            result = await list_licenses(
                page=page, 
                size=size, 
                licensee_address=normalized_address
            )
        else:
            result = await list_licenses(
                page=page, 
                size=size, 
                licensor_address=normalized_address
            )
        
        logger.info(f"Returning {len(result.licenses)} licenses for user {user_address}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting user licenses for {user_address}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user licenses: {str(e)}"
        )

# Add this debug endpoint to help diagnose license data issues
@router.get("/debug/raw-licenses/{user_address}")
async def debug_raw_licenses(user_address: str):
    """Debug endpoint to see raw license documents"""
    try:
        db = get_database()
        normalized_address = user_address.lower()
        
        # Get raw documents without processing
        licensor_docs = await db.licenses.find({
            "licensor_address": normalized_address
        }).to_list(length=10)
        
        licensee_docs = await db.licenses.find({
            "licensee_address": normalized_address
        }).to_list(length=10)
        
        # Convert ObjectIds to strings for JSON serialization
        def clean_doc(doc):
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            # Convert datetime objects to strings
            for key, value in doc.items():
                if isinstance(value, datetime):
                    doc[key] = value.isoformat()
            return doc
        
        cleaned_licensor = [clean_doc(doc.copy()) for doc in licensor_docs]
        cleaned_licensee = [clean_doc(doc.copy()) for doc in licensee_docs]
        
        return {
            "user_address": user_address,
            "normalized_address": normalized_address,
            "as_licensor": {
                "count": len(cleaned_licensor),
                "documents": cleaned_licensor
            },
            "as_licensee": {
                "count": len(cleaned_licensee),
                "documents": cleaned_licensee
            }
        }
        
    except Exception as e:
        logger.error(f"Debug raw licenses failed: {e}", exc_info=True)
        return {
            "error": str(e),
            "user_address": user_address
        }

@router.get("/{license_id}", response_model=License)
async def get_license(license_id: int):
    """Get license by ID"""
    try:
        db = get_database()
        
        license_doc = await db.licenses.find_one({"license_id": license_id})
        if not license_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="License not found"
            )
        
        license_obj = LicenseInDB.from_mongo(license_doc)
        return License.from_mongo(license_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting license {license_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get license: {str(e)}"
        )

@router.get("/artwork/{token_id}", response_model=LicenseListResponse)
async def get_artwork_licenses(
    token_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False)
):
    """Get licenses for a specific artwork"""
    filter_params = {"token_id": token_id}
    if active_only:
        filter_params["is_active"] = True
    
    return await list_licenses(
        page=page,
        size=size,
        **filter_params
    )


    
@router.get("/debug/user-licenses/{user_address}")
async def debug_user_licenses(user_address: str):
    """Debug endpoint to check what licenses exist for a user"""
    try:
        db = get_database()
        normalized_address = user_address.lower()
        
        # Get licenses where user is licensor
        licensor_licenses = await db.licenses.find({
            "licensor_address": normalized_address
        }).to_list(length=100)
        
        # Get licenses where user is licensee
        licensee_licenses = await db.licenses.find({
            "licensee_address": normalized_address
        }).to_list(length=100)
        
        return {
            "user_address": user_address,
            "normalized_address": normalized_address,
            "as_licensor": {
                "count": len(licensor_licenses),
                "licenses": [
                    {
                        "license_id": lic.get("license_id"),
                        "token_id": lic.get("token_id"),
                        "licensee_address": lic.get("licensee_address"),
                        "is_active": lic.get("is_active"),
                        "license_type": lic.get("license_type")
                    }
                    for lic in licensor_licenses
                ]
            },
            "as_licensee": {
                "count": len(licensee_licenses),
                "licenses": [
                    {
                        "license_id": lic.get("license_id"),
                        "token_id": lic.get("token_id"),
                        "licensor_address": lic.get("licensor_address"),
                        "is_active": lic.get("is_active"),
                        "license_type": lic.get("license_type")
                    }
                    for lic in licensee_licenses
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Debug licenses failed: {e}", exc_info=True)
        return {
            "error": str(e),
            "user_address": user_address
        }
    
@router.get("/fee/{license_type}")
async def get_license_fee(license_type: str):
    """Get the current license fee for a specific license type"""
    try:
        # Your contract has a fixed fee of 0.1 ETH for all license types
        if web3_service.demo_mode:
            fee_eth = 0.1  # Fixed fee for demo mode too
            return {
                "license_type": license_type, 
                "fee_eth": fee_eth, 
                "fee_wei": Web3.to_wei(fee_eth, 'ether'),
                "note": "Fixed fee for all license types"
            }
        
        # Get actual fee from contract - it's fixed at 0.1 ETH
        contract = web3_service.get_contract()
        fee_wei = contract.functions.LICENSE_FEE().call()
        fee_eth = Web3.from_wei(fee_wei, 'ether')
        
        return {
            "license_type": license_type,
            "fee_eth": float(fee_eth),
            "fee_wei": fee_wei,
            "note": "Fixed fee for all license types"
        }
        
    except Exception as e:
        logger.error(f"Error getting license fee: {e}")
        # Fallback to the known fixed fee
        return {
            "license_type": license_type,
            "fee_eth": 0.1,
            "fee_wei": Web3.to_wei(0.1, 'ether'),
            "note": "Using fallback fixed fee",
            "error": str(e)
        }
    
@router.get("/debug/licenses/{user_address}")
async def debug_licenses(user_address: str):
    """Debug endpoint to return raw license data"""
    try:
        db = get_database()
        normalized_address = user_address.lower()
        
        # Get licenses where user is licensor
        licenses = await db.licenses.find({
            "licensor_address": normalized_address
        }).to_list(length=100)
        
        # Convert for JSON serialization
        for license in licenses:
            if '_id' in license:
                license['_id'] = str(license['_id'])
            for key in ['start_date', 'end_date', 'created_at', 'updated_at']:
                if key in license and isinstance(license[key], datetime):
                    license[key] = license[key].isoformat()
        
        return {
            "user_address": user_address,
            "normalized_address": normalized_address,
            "count": len(licenses),
            "licenses": licenses
        }
        
    except Exception as e:
        logger.error(f"Debug licenses failed: {e}")
        return {"error": str(e)}