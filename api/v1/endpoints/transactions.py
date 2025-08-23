from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from db.models import (
    TransactionCreate, TransactionUpdate, TransactionBase as Transaction, TransactionInDB,
    TransactionListResponse, TransactionStatus, TransactionType, User
)
from db.database import get_database
from api.v1.endpoints.auth import get_current_user
import logging
from datetime import datetime
from web3 import Web3 

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=dict)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        db = get_database()
        
        # Additional validation
        if not transaction_data.tx_hash or len(transaction_data.tx_hash) != 66:
            raise HTTPException(
                status_code=422,
                detail="Invalid transaction hash format. Must be 66 characters (0x + 64 hex)"
            )
        
        # Normalize addresses to checksum format with better error handling
        try:
            transaction_data.from_address = Web3.to_checksum_address(transaction_data.from_address)
            if transaction_data.to_address:
                transaction_data.to_address = Web3.to_checksum_address(transaction_data.to_address)
        except (ValueError, AttributeError) as addr_error:
            logger.error(f"Address validation failed: {addr_error}")
            raise HTTPException(
                status_code=422,
                detail=f"Invalid Ethereum address format: {str(addr_error)}"
            )
        except NameError as e:
            # Handle case where Web3 is not imported
            logger.error(f"Web3 import error: {e}")
            # Fallback: just use the addresses as-is but validate format
            if not all(c in '0123456789abcdefABCDEFx' for c in transaction_data.from_address):
                raise HTTPException(
                    status_code=422,
                    detail="Invalid Ethereum address characters"
                )
            if transaction_data.to_address and not all(c in '0123456789abcdefABCDEFx' for c in transaction_data.to_address):
                raise HTTPException(
                    status_code=422,
                    detail="Invalid Ethereum address characters for to_address"
                )
            
        # Check for duplicate transaction hash
        existing_tx = await db.transactions.find_one({"tx_hash": transaction_data.tx_hash.lower()})
        if existing_tx:
            logger.info(f"Transaction {transaction_data.tx_hash} already exists, updating status")
            # Update existing transaction instead of creating duplicate
            update_result = await db.transactions.update_one(
                {"tx_hash": transaction_data.tx_hash.lower()},
                {
                    "$set": {
                        "status": transaction_data.status.value,
                        "updated_at": datetime.utcnow(),
                        "metadata": transaction_data.metadata or {}
                    }
                }
            )
            
            if update_result.modified_count > 0:
                return {
                    "success": True,
                    "message": "Transaction updated successfully",
                    "tx_hash": transaction_data.tx_hash,
                    "action": "updated"
                }
            else:
                return {
                    "success": True, 
                    "message": "Transaction already exists with same data",
                    "tx_hash": transaction_data.tx_hash,
                    "action": "no_change"
                }
        
        # Validate user can create this transaction
        user_address = current_user.wallet_address.lower()
        from_address = transaction_data.from_address.lower()
        
        if user_address != from_address:
            logger.warning(f"Address mismatch: user {user_address} vs tx {from_address}")
            # Allow it but log the warning - might be legitimate in some cases
        
        # Create transaction document
        tx_doc = TransactionInDB(
            **transaction_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Convert to dict for MongoDB insertion
        tx_dict = tx_doc.model_dump(by_alias=True, exclude={"id"})
        
        # Ensure metadata is a proper dict
        if tx_dict.get('metadata') is None:
            tx_dict['metadata'] = {}
        
        logger.info(f"Creating transaction record: {tx_dict}")
        
        # Insert into database
        result = await db.transactions.insert_one(tx_dict)
        
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create transaction record"
            )
        
        logger.info(f"✅ Transaction record created with ID: {result.inserted_id}")
        
        return {
            "success": True,
            "message": "Transaction created successfully",
            "transaction_id": str(result.inserted_id),
            "tx_hash": transaction_data.tx_hash,
            "action": "created"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}"
        )

@router.get("/{tx_hash}", response_model=dict)
async def get_transaction(
    tx_hash: str,
    current_user: User = Depends(get_current_user)
):
    """Get transaction by hash"""
    try:
        db = get_database()
        
        # Normalize hash
        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        tx_hash = tx_hash.lower()
        
        transaction = await db.transactions.find_one({"tx_hash": tx_hash})
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Convert ObjectId to string
        if "_id" in transaction:
            transaction["id"] = str(transaction["_id"])
            del transaction["_id"]
        
        return {
            "success": True,
            "transaction": transaction
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transaction: {str(e)}"
        )

@router.get("/", response_model=dict)
async def get_user_transactions(
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    skip: int = 0
):
    """Get user's transactions"""
    try:
        db = get_database()
        
        user_address = current_user.wallet_address.lower()
        
        # Find transactions where user is sender
        cursor = db.transactions.find(
            {"from_address": {"$regex": f"^{user_address}$", "$options": "i"}}
        ).sort("created_at", -1).skip(skip).limit(limit)
        
        transactions = []
        async for tx in cursor:
            if "_id" in tx:
                tx["id"] = str(tx["_id"])
                del tx["_id"]
            transactions.append(tx)
        
        # Get total count
        total = await db.transactions.count_documents(
            {"from_address": {"$regex": f"^{user_address}$", "$options": "i"}}
        )
        
        return {
            "success": True,
            "transactions": transactions,
            "total": total,
            "limit": limit,
            "skip": skip
        }
        
    except Exception as e:
        logger.error(f"Error fetching user transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transactions: {str(e)}"
        )

def normalize_transaction_document(tx_doc: dict) -> dict:
    """Normalize transaction document to ensure all required fields are present"""
    # Ensure required fields exist with defaults
    defaults = {
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "status": TransactionStatus.PENDING.value,
        "transaction_type": TransactionType.REGISTER.value,
        "value": "0",
        "metadata": {},
        "from_address": "",
        "to_address": ""
    }
    
    normalized = tx_doc.copy()
    
    for field, default_value in defaults.items():
        if field not in normalized or normalized[field] is None:
            normalized[field] = default_value
    
    # Convert ObjectId to string if present
    if "_id" in normalized:
        normalized["id"] = str(normalized["_id"])
        del normalized["_id"]
    
    return normalized

async def list_transactions(
    page: int = 1,
    size: int = 20,
    from_address: Optional[str] = None,
    to_address: Optional[str] = None,
    transaction_type: Optional[TransactionType] = None  # Keep this as TransactionType
):
    """Reusable function to list transactions with filtering"""
    db = get_database()
    skip = (page - 1) * size
    
    # Build query
    query = {}
    if from_address:
        query["from_address"] = {"$regex": f"^{from_address}$", "$options": "i"}
    if to_address:
        query["to_address"] = {"$regex": f"^{to_address}$", "$options": "i"}
    if transaction_type:
        query["transaction_type"] = transaction_type.value  # Use .value here
    
    cursor = db.transactions.find(query).sort("created_at", -1).skip(skip).limit(size)
    
    transactions = []
    async for tx in cursor:
        # Normalize the transaction document to ensure all required fields
        normalized_tx = normalize_transaction_document(tx)
        transactions.append(normalized_tx)
    
    total = await db.transactions.count_documents(query)
    total_pages = (total + size - 1) // size if size > 0 else 1
    has_next = page < total_pages
    
    return TransactionListResponse(
        success=True,
        transactions=transactions,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages,
        has_next=has_next
    )

@router.get("/user/{user_address}", response_model=TransactionListResponse)
async def get_user_transactions_endpoint(
    user_address: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None)  # Change from TransactionType to str
):
    """Get transactions for a specific user"""
    try:
        # Normalize and validate address
        try:
            user_address = Web3.to_checksum_address(user_address)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Invalid Ethereum address format"
            )
        
        # Convert string type to TransactionType enum if provided
        transaction_type = None
        if type:
            try:
                transaction_type = TransactionType(type.upper())
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid transaction type: {type}. Must be one of: {[t.value for t in TransactionType]}"
                )
        
        return await list_transactions(
            page=page,
            size=size,
            from_address=user_address,
            transaction_type=transaction_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transactions for user {user_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user transactions: {str(e)}"
        )

@router.get("/user/{user_address}/royalties", response_model=TransactionListResponse)
async def get_user_royalty_transactions(
    user_address: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """Get royalty transactions for a specific user"""
    try:
        # Normalize and validate address
        try:
            user_address = Web3.to_checksum_address(user_address)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Invalid Ethereum address format"
            )
        
        return await list_transactions(
            page=page,
            size=size,
            to_address=user_address,
            transaction_type=TransactionType.ROYALTY  # Fixed: use the enum directly
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching royalty transactions for user {user_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch royalty transactions: {str(e)}"
        )

@router.put("/{tx_hash}", response_model=dict)
async def update_transaction(
    tx_hash: str,
    update_data: TransactionUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update transaction status"""
    try:
        db = get_database()
        
        # Normalize hash
        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        tx_hash = tx_hash.lower()
        
        # Check if transaction exists
        existing_tx = await db.transactions.find_one({"tx_hash": tx_hash})
        if not existing_tx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Update transaction
        update_result = await db.transactions.update_one(
            {"tx_hash": tx_hash},
            {
                "$set": {
                    "status": update_data.status.value,
                    "updated_at": datetime.utcnow(),
                    **update_data.model_dump(exclude={"status"}, exclude_unset=True)
                }
            }
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No changes made to transaction"
            )
        
        return {
            "success": True,
            "message": "Transaction updated successfully",
            "tx_hash": tx_hash
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating transaction {tx_hash}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update transaction: {str(e)}"
        )

@router.delete("/{tx_hash}", response_model=dict)
async def delete_transaction(
    tx_hash: str,
    current_user: User = Depends(get_current_user)
):
    """Delete transaction (admin only)"""
    try:
        db = get_database()
        
        # Normalize hash
        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        tx_hash = tx_hash.lower()
        
        # Check if transaction exists
        existing_tx = await db.transactions.find_one({"tx_hash": tx_hash})
        if not existing_tx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Delete transaction
        delete_result = await db.transactions.delete_one({"tx_hash": tx_hash})
        
        if delete_result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete transaction"
            )
        
        return {
            "success": True,
            "message": "Transaction deleted successfully",
            "tx_hash": tx_hash
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transaction {tx_hash}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete transaction: {str(e)}"
        )