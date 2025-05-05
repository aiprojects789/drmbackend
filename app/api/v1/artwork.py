from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer
from app.db.database import db
from app.db.models import Artwork
from app.core.ipfs_service import upload_to_ipfs
from app.core.blockchain_service import mint_nft
from app.core.security import get_current_user

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

@router.post("/artwork/upload")
async def upload_artwork(
    file: UploadFile,
    title: str,
    description: str,
    license_type: str,
    token: str = Depends(oauth2_scheme),
):
    current_user = await get_current_user(token)
    
    # Upload to IPFS
    ipfs_hash = await upload_to_ipfs(file)
    
    # Create artwork record
    artwork = Artwork(
        title=title,
        description=description,
        ipfs_hash=ipfs_hash,
        creator_email=current_user.email,
        license_type=license_type
    )
    
    # Mint NFT
    token_id = await mint_nft(
        wallet_address=current_user.wallet_address,
        ipfs_hash=ipfs_hash
    )
    
    artwork.token_id = token_id
    await db.artworks.insert_one(artwork.dict())
    
    return {"message": "Artwork uploaded and minted successfully", "token_id": token_id}