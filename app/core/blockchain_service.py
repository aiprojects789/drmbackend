from web3 import Web3
import json
import os
from pathlib import Path
from app.core.config import settings

# Get the absolute path to the ABI file
current_dir = Path(__file__).parent
abi_path = current_dir / "artwork_contract_abi.json"

# Verify file exists
if not abi_path.exists():
    raise FileNotFoundError(f"ABI file not found at {abi_path}")

# Load contract ABI
with open(abi_path) as f:
    contract_abi = json.load(f)

w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
contract = w3.eth.contract(address=settings.CONTRACT_ADDRESS, abi=contract_abi)  # Uppercase

async def mint_nft(wallet_address: str, ipfs_hash: str) -> str:
    tx_hash = contract.functions.mintArtwork(
        wallet_address,
        ipfs_hash
    ).transact({'from': wallet_address})
    
    return tx_hash