from fastapi import APIRouter, HTTPException, status
from db.models import ContractCallRequest, ContractCallResponse, Web3ConnectionStatus
from services.web3_service import web3_service
import logging
from web3.exceptions import ContractLogicError


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status", response_model=Web3ConnectionStatus)
async def get_web3_status():
    """Get Web3 connection status"""
    try:
        return Web3ConnectionStatus(
            connected=web3_service.connected,
            network_name="Sepolia Testnet" if web3_service.connected else None
        )
    except Exception as e:
        logger.error(f"Error getting Web3 status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Web3 status"
        )

@router.get("/artwork-count", response_model=dict)
async def get_artwork_count():
    """Get total artwork count from blockchain"""
    try:
        count = await web3_service.get_artwork_count()
        return {"count": count}
    except Exception as e:
        logger.error(f"Error getting artwork count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get artwork count"
        )

@router.get("/artwork/{token_id}/info", response_model=dict)
async def get_blockchain_artwork_info(token_id: int):
    """Get artwork info from blockchain"""
    try:
        artwork_info = await web3_service.get_artwork_info(token_id)
        if not artwork_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found on blockchain"
            )
        return artwork_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting blockchain artwork info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get artwork info from blockchain"
        )

@router.get("/artwork/{token_id}/owner", response_model=dict)
async def get_artwork_owner(token_id: int):
    """Get artwork owner from blockchain"""
    try:
        owner = await web3_service.get_artwork_owner(token_id)
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found on blockchain"
            )
        return {"owner": owner}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting artwork owner: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get artwork owner from blockchain"
        )

@router.post("/prepare-transaction/register", response_model=dict)
async def prepare_register_transaction(request: dict):
    """Prepare artwork registration transaction"""
    try:
        metadata_uri = request.get("metadata_uri")
        royalty_percentage = request.get("royalty_percentage")
        from_address = request.get("from_address")
        
        if not all([metadata_uri, royalty_percentage is not None, from_address]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameters"
            )
        
        tx_data = await web3_service.prepare_register_transaction(
            metadata_uri, royalty_percentage, from_address
        )
        
        if not tx_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to prepare transaction"
            )
        
        return {"transaction_data": tx_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error preparing register transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prepare transaction"
        )

@router.post("/prepare-transaction/license", response_model=dict)
async def prepare_license_transaction(request: dict):
    """Prepare license grant transaction"""
    try:
        token_id = request.get("token_id")
        licensee = request.get("licensee")
        duration_days = request.get("duration_days")
        terms_hash = request.get("terms_hash")
        license_type = request.get("license_type")
        from_address = request.get("from_address")
        
        if not all([
            token_id is not None, licensee, duration_days is not None,
            terms_hash, license_type, from_address
        ]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameters"
            )
        
        tx_data = await web3_service.prepare_license_transaction(
            token_id, licensee, duration_days, terms_hash, license_type, from_address
        )
        
        if not tx_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to prepare transaction"
            )
        
        return {"transaction_data": tx_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error preparing license transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prepare transaction"
        )