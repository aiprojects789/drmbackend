from fastapi import APIRouter, Depends
from app.core.blockchain_service import mint_nft
from app.core.security import get_current_user

router = APIRouter(tags=["Blockchain"])  # This creates the router

@router.post("/blockchain/mint")
async def mint_nft_endpoint(
    ipfs_hash: str,
    current_user: dict = Depends(get_current_user)
):
    tx_hash = await mint_nft(
        wallet_address=current_user["wallet_address"],
        ipfs_hash=ipfs_hash
    )
    return {"transaction_hash": tx_hash}