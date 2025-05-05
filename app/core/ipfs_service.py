import os
from pathlib import Path
from fastapi import UploadFile

async def upload_to_ipfs(file: UploadFile) -> str:
    # Save to local "uploads" folder
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    return str(file_path)  # Return local path as mock "IPFS hash"