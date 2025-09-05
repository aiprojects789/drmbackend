from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from app.core.security import get_current_user
from app.db.database import get_transaction_collection
from app.db.models import (
    TransactionCreate, TransactionUpdate, TransactionBase as Transaction, TransactionInDB,
    TransactionListResponse, TransactionStatus, TransactionType, User
)
from web3 import Web3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transaction", tags=["transaction"])

@router.post("/", response_model=dict)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        transactions_collection = get_transaction_collection()

        if not transaction_data.tx_hash or len(transaction_data.tx_hash) != 66:
            raise HTTPException(
                status_code=422,
                detail="Invalid transaction hash format. Must be 66 characters (0x + 64 hex)"
            )

        try:
            transaction_data.from_address = Web3.to_checksum_address(transaction_data.from_address)
            if transaction_data.to_address:
                transaction_data.to_address = Web3.to_checksum_address(transaction_data.to_address)
        except Exception as addr_error:
            logger.error(f"Address validation failed: {addr_error}")
            raise HTTPException(
                status_code=422,
                detail=f"Invalid Ethereum address format: {str(addr_error)}"
            )

        existing_tx = await transactions_collection.find_one({"tx_hash": transaction_data.tx_hash.lower()})
        if existing_tx:
            logger.info(f"Transaction {transaction_data.tx_hash} already exists, updating status")
            update_result = await transactions_collection.update_one(
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

        user_address = current_user.wallet_address.lower()
        from_address = transaction_data.from_address.lower()

        if user_address != from_address:
            logger.warning(f"Address mismatch: user {user_address} vs tx {from_address}")
            # Allow but log warning

        tx_doc = TransactionInDB(
            **transaction_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        tx_dict = tx_doc.model_dump(by_alias=True, exclude={"id"})
        if tx_dict.get('metadata') is None:
            tx_dict['metadata'] = {}

        logger.info(f"Creating transaction record: {tx_dict}")

        result = await transactions_collection.insert_one(tx_dict)
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
    try:
        transactions_collection = get_transaction_collection()

        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        tx_hash = tx_hash.lower()

        transaction = await transactions_collection.find_one({"tx_hash": tx_hash})
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

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
    try:
        transactions_collection = get_transaction_collection()
        user_address = current_user.wallet_address.lower()

        cursor = transactions_collection.find(
            {"from_address": {"$regex": f"^{user_address}$", "$options": "i"}}
        ).sort("created_at", -1).skip(skip).limit(limit)

        transactions = []
        async for tx in cursor:
            if "_id" in tx:
                tx["id"] = str(tx["_id"])
                del tx["_id"]
            transactions.append(tx)

        total = await transactions_collection.count_documents(
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
    if "_id" in normalized:
        normalized["id"] = str(normalized["_id"])
        del normalized["_id"]
    return normalized


async def list_transactions(
    page: int = 1,
    size: int = 20,
    from_address: Optional[str] = None,
    to_address: Optional[str] = None,
    transaction_type: Optional[TransactionType] = None
):
    transactions_collection = get_transaction_collection()
    skip = (page - 1) * size
    query = {}
    if from_address:
        query["from_address"] = {"$regex": f"^{from_address}$", "$options": "i"}
    if to_address:
        query["to_address"] = {"$regex": f"^{to_address}$", "$options": "i"}
    if transaction_type:
        query["transaction_type"] = transaction_type.value

    cursor = transactions_collection.find(query).sort("created_at", -1).skip(skip).limit(size)
    transactions = []
    async for tx in cursor:
        normalized_tx = normalize_transaction_document(tx)
        transactions.append(normalized_tx)

    total = await transactions_collection.count_documents(query)
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
    type: Optional[str] = Query(None)
):
    try:
        try:
            user_address = Web3.to_checksum_address(user_address)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid Ethereum address format")

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
        raise HTTPException(status_code=500, detail=f"Failed to fetch user transactions: {str(e)}")


@router.get("/user/{user_address}/royalties", response_model=TransactionListResponse)
async def get_user_royalty_transactions(
    user_address: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    try:
        try:
            user_address = Web3.to_checksum_address(user_address)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid Ethereum address format")

        return await list_transactions(
            page=page,
            size=size,
            to_address=user_address,
            transaction_type=TransactionType.ROYALTY
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching royalty transactions for user {user_address}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch royalty transactions: {str(e)}")


@router.put("/{tx_hash}", response_model=dict)
async def update_transaction(
    tx_hash: str,
    update_data: TransactionUpdate,
    current_user: User = Depends(get_current_user)
):
    try:
        transactions_collection = get_transaction_collection()

        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        tx_hash = tx_hash.lower()

        existing_tx = await transactions_collection.find_one({"tx_hash": tx_hash})
        if not existing_tx:
            raise HTTPException(status_code=404, detail="Transaction not found")

        update_result = await transactions_collection.update_one(
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
            raise HTTPException(status_code=400, detail="No changes made to transaction")

        return {
            "success": True,
            "message": "Transaction updated successfully",
            "tx_hash": tx_hash
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating transaction {tx_hash}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update transaction: {str(e)}")


@router.delete("/{tx_hash}", response_model=dict)
async def delete_transaction(
    tx_hash: str,
    current_user: User = Depends(get_current_user)
):
    try:
        transactions_collection = get_transaction_collection()

        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        tx_hash = tx_hash.lower()

        existing_tx = await transactions_collection.find_one({"tx_hash": tx_hash})
        if not existing_tx:
            raise HTTPException(status_code=404, detail="Transaction not found")

        delete_result = await transactions_collection.delete_one({"tx_hash": tx_hash})
        if delete_result.deleted_count == 0:
            raise HTTPException(status_code=500, detail="Failed to delete transaction")

        return {
            "success": True,
            "message": "Transaction deleted successfully",
            "tx_hash": tx_hash
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transaction {tx_hash}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete transaction: {str(e)}")
