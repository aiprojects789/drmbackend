from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from typing import Optional
from datetime import datetime, timedelta
import json
import asyncio
import logging
from web3 import Web3

from app.db.database import get_license_collection, get_artwork_collection
from app.db.models import (
    LicenseCreate, License, LicenseInDB,
    LicenseListResponse, User
)
from app.core.security import get_current_user
from services.web3_service import web3_service
from .artwork import IPFSService  # Adjust import path as per your project structure

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/license", tags=["license"])


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
        usage_descriptions = {
            "PERSONAL": "This license grants personal, non-commercial usage rights only. The licensee may view, display, and share the artwork for personal purposes with proper attribution.",
            "COMMERCIAL": "This license grants commercial usage rights including marketing, advertising, and business applications. Attribution to the original creator is required in all uses.",
            "EXCLUSIVE": "This license grants exclusive rights to the artwork during the specified period. No other licenses will be granted during this time, and the licensee has full commercial and non-commercial usage rights."
        }
        return usage_descriptions.get(license_type, "Standard usage rights apply.")


@router.post("/grant-with-document")
async def grant_license_with_document(
    token_id: int = Form(...),
    licensee_address: str = Form(...),
    duration_days: int = Form(...),
    license_type: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    try:
        db_licenses = get_license_collection()
        db_artworks = get_artwork_collection()

        if not 1 <= duration_days <= 365:
            raise HTTPException(status_code=400, detail="Duration must be between 1 and 365 days")

        if license_type not in ["PERSONAL", "COMMERCIAL", "EXCLUSIVE"]:
            raise HTTPException(status_code=400, detail="Invalid license type")

        try:
            licensee_address = Web3.to_checksum_address(licensee_address)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Ethereum address")

        artwork_doc = await db_artworks.find_one({"token_id": token_id})
        if not artwork_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artwork not found")

        # FIX: Handle current_user as dict
        user_wallet = None
        if hasattr(current_user, 'wallet_address'):
            user_wallet = current_user.wallet_address
        elif isinstance(current_user, dict) and 'wallet_address' in current_user:
            user_wallet = current_user['wallet_address']
        else:
            logger.error(f"Invalid current_user structure: {current_user}")
            raise HTTPException(status_code=500, detail="User authentication error")

        if artwork_doc["owner_address"].lower() != user_wallet.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only artwork owner can grant licenses")

        start_date = datetime.utcnow()
        license_document = LicenseDocumentService.generate_license_document(
            artwork_title=artwork_doc.get("title", "Untitled"),
            artwork_token_id=token_id,
            licensor_address=user_wallet,
            licensee_address=licensee_address,
            license_type=license_type,
            duration_days=duration_days,
            start_date=start_date
        )

        document_json = json.dumps(license_document, indent=2)
        document_bytes = document_json.encode('utf-8')

        terms_hash = await IPFSService.upload_to_ipfs(
            document_bytes,
            f"license_agreement_{token_id}_{int(start_date.timestamp())}.json"
        )

        license_count = await db_licenses.count_documents({}) + 1

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
                    user_wallet
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
                await asyncio.sleep(1)

        if not tx_data:
            raise HTTPException(status_code=500, detail="Failed to prepare transaction after multiple attempts")

        end_date = start_date + timedelta(days=duration_days)
        fee_eth = 0.1  # Fixed fee

        license_dict = {
            "license_id": license_count,
            "token_id": token_id,
            "licensee_address": licensee_address.lower(),
            "licensor_address": user_wallet.lower(),
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

        license_doc = LicenseInDB.from_mongo(license_dict)
        result = await db_licenses.insert_one(license_doc.model_dump(by_alias=True, exclude={"id"}))

        logger.info(f"Created license document with ID: {result.inserted_id}")

        await db_artworks.update_one(
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
        raise HTTPException(status_code=500, detail=f"Failed to grant license: {str(e)}")


@router.post("/grant", response_model=dict)
async def grant_license(
    license_data: LicenseCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        db_licenses = get_license_collection()
        db_artworks = get_artwork_collection()

        artwork_doc = await db_artworks.find_one({"token_id": license_data.token_id})
        if not artwork_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artwork not found")

        if artwork_doc["owner_address"].lower() != current_user.wallet_address.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only artwork owner can grant licenses")

        license_count = await db_licenses.count_documents({}) + 1

        max_retries = 3
        tx_data = None
        for attempt in range(max_retries):
            try:
                tx_data = await web3_service.prepare_license_transaction(
                    license_data.token_id,
                    license_data.licensee_address,
                    license_data.duration_days,
                    license_data.terms_hash,
                    license_data.license_type.value,
                    current_user.wallet_address
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
                await asyncio.sleep(1)

        if not tx_data:
            raise HTTPException(status_code=500, detail="Failed to prepare transaction after multiple attempts")

        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=license_data.duration_days)
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

        license_doc = LicenseInDB.from_mongo(license_dict)
        result = await db_licenses.insert_one(license_doc.model_dump(by_alias=True, exclude={"id"}))

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
        raise HTTPException(status_code=500, detail=f"Failed to grant license: {str(e)}")


@router.post("/{license_id}/revoke", response_model=dict)
async def revoke_license(
    license_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        db_licenses = get_license_collection()
        db_artworks = get_artwork_collection()

        license_doc = await db_licenses.find_one({"license_id": license_id})
        if not license_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")

        license_obj = LicenseInDB.from_mongo(license_doc)

        # FIX: Handle current_user as dict (same fix as grant endpoint)
        user_wallet = None
        if hasattr(current_user, 'wallet_address'):
            user_wallet = current_user.wallet_address
        elif isinstance(current_user, dict) and 'wallet_address' in current_user:
            user_wallet = current_user['wallet_address']
        else:
            logger.error(f"Invalid current_user structure in revoke: {current_user}")
            raise HTTPException(status_code=500, detail="User authentication error")

        if license_obj.licensor_address.lower() != user_wallet.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only licensor can revoke license")

        if not license_obj.is_active:
            raise HTTPException(status_code=400, detail="License is already revoked")

        update_result = await db_licenses.update_one(
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
            raise HTTPException(status_code=500, detail="Failed to update license status")

        active_licenses = await db_licenses.count_documents({
            "token_id": license_obj.token_id,
            "is_active": True,
            "end_date": {"$gt": datetime.utcnow()}
        })

        await db_artworks.update_one(
            {"token_id": license_obj.token_id},
            {"$set": {"is_licensed": active_licenses > 0, "updated_at": datetime.utcnow()}}
        )

        logger.info(f"Successfully revoked license {license_id} for user {user_wallet}")

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
        raise HTTPException(status_code=500, detail=f"Failed to revoke license: {str(e)}")

@router.get("/", response_model=LicenseListResponse)
async def list_licenses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    token_id: Optional[int] = None,
    licensee_address: Optional[str] = None,
    licensor_address: Optional[str] = None,
    is_active: Optional[bool] = None
):
    try:
        db_licenses = get_license_collection()

        filter_query = {}
        if token_id is not None:
            filter_query["token_id"] = token_id
        if licensee_address:
            filter_query["licensee_address"] = licensee_address.lower()
        if licensor_address:
            filter_query["licensor_address"] = licensor_address.lower()
        if is_active is not None:
            filter_query["is_active"] = is_active

        total = await db_licenses.count_documents(filter_query)
        has_next = (page * size) < total
        skip = (page - 1) * size

        cursor = db_licenses.find(filter_query).skip(skip).limit(size).sort("created_at", -1)
        licenses_data = await cursor.to_list(length=size)

        licenses = []
        for doc in licenses_data:
            try:
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
                if "revoked_at" in doc and doc["revoked_at"] is not None:
                    license_dict["revoked_at"] = doc["revoked_at"].isoformat() if isinstance(doc["revoked_at"], datetime) else doc["revoked_at"]

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
        raise HTTPException(status_code=500, detail=f"Failed to list licenses: {str(e)}")


@router.get("/user/{user_address}", response_model=LicenseListResponse)
async def get_user_licenses(
    user_address: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    as_licensee: bool = Query(True)
):
    try:
        normalized_address = user_address.lower()
        logger.info(f"Getting licenses for user: {user_address} as_licensee={as_licensee}")

        if as_licensee:
            result = await list_licenses(page=page, size=size, licensee_address=normalized_address)
        else:
            result = await list_licenses(page=page, size=size, licensor_address=normalized_address)

        logger.info(f"Returning {len(result.licenses)} licenses for user {user_address}")

        return result

    except Exception as e:
        logger.error(f"Error getting user licenses for {user_address}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get user licenses: {str(e)}")


# Debug endpoint to see raw license documents
@router.get("/debug/raw-licenses/{user_address}")
async def debug_raw_licenses(user_address: str):
    try:
        db_licenses = get_license_collection()
        normalized_address = user_address.lower()

        licensor_docs = await db_licenses.find({
            "licensor_address": normalized_address
        }).to_list(length=10)

        licensee_docs = await db_licenses.find({
            "licensee_address": normalized_address
        }).to_list(length=10)

        def clean_doc(doc):
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
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

# Get license by ID
@router.get("/{license_id}", response_model=License)
async def get_license(license_id: int):
    try:
        db_licenses = get_license_collection()

        license_doc = await db_licenses.find_one({"license_id": license_id})
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

# Get licenses for a specific artwork
@router.get("/artwork/{token_id}", response_model=LicenseListResponse)
async def get_artwork_licenses(
    token_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False)
):
    filter_params = {"token_id": token_id}
    if active_only:
        filter_params["is_active"] = True

    return await list_licenses(
        page=page,
        size=size,
        **filter_params
    )

# Debug endpoint to check what licenses exist for a user
@router.get("/debug/user-licenses/{user_address}")
async def debug_user_licenses(user_address: str):
    try:
        db_licenses = get_license_collection()
        normalized_address = user_address.lower()

        licensor_licenses = await db_licenses.find({
            "licensor_address": normalized_address
        }).to_list(length=100)

        licensee_licenses = await db_licenses.find({
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

# Get the current license fee for a specific license type
@router.get("/fee/{license_type}")
async def get_license_fee(license_type: str):
    try:
        if web3_service.demo_mode:
            fee_eth = 0.1
            return {
                "license_type": license_type,
                "fee_eth": fee_eth,
                "fee_wei": Web3.to_wei(fee_eth, 'ether'),
                "note": "Fixed fee for all license types"
            }

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
        return {
            "license_type": license_type,
            "fee_eth": 0.1,
            "fee_wei": Web3.to_wei(0.1, 'ether'),
            "note": "Using fallback fixed fee",
            "error": str(e)
        }

# Debug endpoint to return raw license data
@router.get("/debug/licenses/{user_address}")
async def debug_licenses(user_address: str):
    try:
        db_licenses = get_license_collection()
        normalized_address = user_address.lower()

        licenses = await db_licenses.find({
            "licensor_address": normalized_address
        }).to_list(length=100)

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
