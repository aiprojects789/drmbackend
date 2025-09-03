from web3 import Web3
from typing import Optional, Dict, List, Any
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# CORRECTED CONTRACT_ABI - based on actual contract
CONTRACT_ABI = [
   {
        "inputs": [
            {"internalType": "string", "name": "metadataURI", "type": "string"},
            {"internalType": "uint256", "name": "royaltyPercentage", "type": "uint256"}
        ],
        "name": "registerArtwork",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }, 
  {
    "inputs": [],
    "stateMutability": "nonpayable",
    "type": "constructor"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "owner",
        "type": "address"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "approved",
        "type": "address"
      },
      {
        "indexed": True,
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      }
    ],
    "name": "Approval",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "owner",
        "type": "address"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "operator",
        "type": "address"
      },
      {
        "indexed": False,
        "internalType": "bool",
        "name": "approved",
        "type": "bool"
      }
    ],
    "name": "ApprovalForAll",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "creator",
        "type": "address"
      },
      {
        "indexed": False,
        "internalType": "string",
        "name": "metadataURI",
        "type": "string"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "royaltyPercentage",
        "type": "uint256"
      }
    ],
    "name": "ArtworkRegistered",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "_fromTokenId",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "_toTokenId",
        "type": "uint256"
      }
    ],
    "name": "BatchMetadataUpdate",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "uint256",
        "name": "licenseId",
        "type": "uint256"
      },
      {
        "indexed": True,
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "licensee",
        "type": "address"
      },
      {
        "indexed": False,
        "internalType": "enum ArtDRM.LicenseType",
        "name": "licenseType",
        "type": "uint8"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "duration",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "feePaid",
        "type": "uint256"
      }
    ],
    "name": "LicenseGranted",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "uint256",
        "name": "licenseId",
        "type": "uint256"
      },
      {
        "indexed": True,
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "licensee",
        "type": "address"
      }
    ],
    "name": "LicenseRevoked",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "_tokenId",
        "type": "uint256"
      }
    ],
    "name": "MetadataUpdate",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "previousOwner",
        "type": "address"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "newOwner",
        "type": "address"
      }
    ],
    "name": "OwnershipTransferred",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "creator",
        "type": "address"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "amount",
        "type": "uint256"
      }
    ],
    "name": "RoyaltyPaid",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "from",
        "type": "address"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "to",
        "type": "address"
      },
      {
        "indexed": True,
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      }
    ],
    "name": "Transfer",
    "type": "event"
  },
  {
    "inputs": [],
    "name": "LICENSE_FEE",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "MAX_ROYALTY",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "PLATFORM_FEE",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "to",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      }
    ],
    "name": "approve",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "name": "artworks",
    "outputs": [
      {
        "internalType": "address",
        "name": "creator",
        "type": "address"
      },
      {
        "internalType": "string",
        "name": "metadataURI",
        "type": "string"
      },
      {
        "internalType": "uint256",
        "name": "royaltyPercentage",
        "type": "uint256"
      },
      {
        "internalType": "bool",
        "name": "isLicensed",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "owner",
        "type": "address"
      }
    ],
    "name": "balanceOf",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "name": "creatorArtworks",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      }
    ],
    "name": "getActiveLicenses",
    "outputs": [
      {
        "components": [
          {
            "internalType": "uint256",
            "name": "tokenId",
            "type": "uint256"
          },
          {
            "internalType": "address",
            "name": "licensee",
            "type": "address"
          },
          {
            "internalType": "uint256",
            "name": "startDate",
            "type": "uint256"
          },
          {
            "internalType": "uint256",
            "name": "endDate",
            "type": "uint256"
          },
          {
            "internalType": "string",
            "name": "termsHash",
            "type": "string"
          },
          {
            "internalType": "enum ArtDRM.LicenseType",
            "name": "licenseType",
            "type": "uint8"
          },
          {
            "internalType": "bool",
            "name": "isActive",
            "type": "bool"
          },
          {
            "internalType": "uint256",
            "name": "feePaid",
            "type": "uint256"
          }
        ],
        "internalType": "struct ArtDRM.License[]",
        "name": "",
        "type": "tuple[]"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      }
    ],
    "name": "getApproved",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      }
    ],
    "name": "getArtworkInfo",
    "outputs": [
      {
        "internalType": "address",
        "name": "creator",
        "type": "address"
      },
      {
        "internalType": "string",
        "name": "metadataURI",
        "type": "string"
      },
      {
        "internalType": "uint256",
        "name": "royaltyPercentage",
        "type": "uint256"
      },
      {
        "internalType": "bool",
        "name": "isLicensed",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "creator",
        "type": "address"
      }
    ],
    "name": "getCreatorArtworks",
    "outputs": [
      {
        "internalType": "uint256[]",
        "name": "",
        "type": "uint256[]"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "getCurrentTokenId",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "licensee",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "durationDays",
        "type": "uint256"
      },
      {
        "internalType": "string",
        "name": "termsHash",
        "type": "string"
      },
      {
        "internalType": "enum ArtDRM.LicenseType",
        "name": "licenseType",
        "type": "uint8"
      }
    ],
    "name": "grantLicense",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "salePrice",
        "type": "uint256"
      }
    ],
    "name": "handleSale",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "owner",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "operator",
        "type": "address"
      }
    ],
    "name": "isApprovedForAll",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "licensee",
        "type": "address"
      }
    ],
    "name": "isLicenseValid",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "name",
    "outputs": [
      {
        "internalType": "string",
        "name": "",
        "type": "string"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "owner",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      }
    ],
    "name": "ownerOf",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
#   {
#     "inputs": [
#       {
#         "internalType": "string",
#         "name": "metadataURI",
#         "type": "string"
#       },
#       {
#         "internalType": "uint256",
#         "name": "royaltyPercentage",
#         "type": "uint256"
#       }
#     ],
#     "name": "registerArtwork",
#     "outputs": [
#       {
#         "internalType": "uint256",
#         "name": "",
#         "type": "uint256"
#       }
#     ],
#     "stateMutability": "nonpayable",
#     "type": "function"
#   },
  {
    "inputs": [],
    "name": "renounceOwnership",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "licensee",
        "type": "address"
      }
    ],
    "name": "revokeLicense",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "salePrice",
        "type": "uint256"
      }
    ],
    "name": "royaltyInfo",
    "outputs": [
      {
        "internalType": "address",
        "name": "receiver",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "royaltyAmount",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "from",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "to",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      }
    ],
    "name": "safeTransferFrom",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "from",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "to",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "internalType": "bytes",
        "name": "data",
        "type": "bytes"
      }
    ],
    "name": "safeTransferFrom",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "operator",
        "type": "address"
      },
      {
        "internalType": "bool",
        "name": "approved",
        "type": "bool"
      }
    ],
    "name": "setApprovalForAll",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "bytes4",
        "name": "interfaceId",
        "type": "bytes4"
      }
    ],
    "name": "supportsInterface",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "symbol",
    "outputs": [
      {
        "internalType": "string",
        "name": "",
        "type": "string"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "name": "tokenLicenses",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "licensee",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "startDate",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "endDate",
        "type": "uint256"
      },
      {
        "internalType": "string",
        "name": "termsHash",
        "type": "string"
      },
      {
        "internalType": "enum ArtDRM.LicenseType",
        "name": "licenseType",
        "type": "uint8"
      },
      {
        "internalType": "bool",
        "name": "isActive",
        "type": "bool"
      },
      {
        "internalType": "uint256",
        "name": "feePaid",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      }
    ],
    "name": "tokenURI",
    "outputs": [
      {
        "internalType": "string",
        "name": "",
        "type": "string"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "from",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "to",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      }
    ],
    "name": "transferFrom",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "newOwner",
        "type": "address"
      }
    ],
    "name": "transferOwnership",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "newFee",
        "type": "uint256"
      }
    ],
    "name": "updatePlatformFee",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "withdrawBalance",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
]


class Web3Service:
    # License type enum mapping (matches your smart contract)
    LICENSE_TYPES = {
        'PERSONAL': 0,
        'COMMERCIAL': 1,
        'EXCLUSIVE': 2,
        'UNLIMITED': 3
    }
    
    def __init__(self):
        self.w3 = None
        self.web3 = None  # Add this alias for backward compatibility
        self.contract = None
        self.connected = False
        self.demo_mode = getattr(settings, 'DEMO_MODE', False)
        
        # Initialize mock system for demo mode
        if self.demo_mode:
            self.mock_system = MockArtworkSystem()
        
        if not self.demo_mode:
            self._initialize_web3()

    def _initialize_web3(self):
      """Initialize Web3 connection with enhanced error handling"""
      try:
          self.w3 = Web3(Web3.HTTPProvider(
              settings.WEB3_PROVIDER_URL,
              request_kwargs={'timeout': 60}
          ))
          
          # Set the alias for backward compatibility
          self.web3 = self.w3
          
          if not self.w3.is_connected():
              raise ConnectionError("Failed to connect to Web3 provider")
              
          # Get chain ID
          self.chain_id = self.w3.eth.chain_id  # Add this line
          
          # Verify contract
          contract_address = Web3.to_checksum_address(settings.CONTRACT_ADDRESS)
          code = self.w3.eth.get_code(contract_address)
          if code == '0x':
              raise ValueError(f"No contract at {contract_address}")
              
          self.contract = self.w3.eth.contract(
              address=contract_address,
              abi=CONTRACT_ABI
          )
          
                      
            # Test connection (optional)
          try:
                if hasattr(self.contract.functions, "getCurrentTokenId"):
                    current_id = self.contract.functions.getCurrentTokenId().call()
                    logger.info(f"✅ Contract connected. Current token ID: {current_id}")
                    self.connected = True
                else:
                    logger.warning("⚠️ ABI does not include getCurrentTokenId()")
                    self.connected = True  # Contract connected, but function not available
          except Exception as e:
                logger.warning(f"⚠️ Contract connected but test call failed: {e}")
                self.connected = True  # Still mark as connected, just skip test


      except Exception as e:
          logger.error(f"Web3 initialization failed: {e}")
          raise
    
    def get_contract(self):
        """Get the contract instance"""
        if self.demo_mode:
            return None  # Mock system doesn't need real contract
        
        if not self.contract:
            raise Exception("Contract not initialized")
        
        return self.contract

    async def get_current_gas_price(self):
        """Get current gas prices with better fallbacks for testnets"""
        try:
            if self.demo_mode:
                return {
                    'gasPrice': Web3.to_wei(30, 'gwei')
                }
            
            # Get current base fee from latest block
            latest_block = self.w3.eth.get_block('latest')
            
            # Check if EIP-1559 is supported
            if latest_block.get('baseFeePerGas'):
                try:
                    base_fee = latest_block['baseFeePerGas']
                    
                    # Try to get priority fee, with fallback
                    try:
                        max_priority_fee_per_gas = self.w3.eth.max_priority_fee
                    except Exception:
                        # Fallback: use a reasonable priority fee (1.5 gwei for testnets)
                        max_priority_fee_per_gas = Web3.to_wei(1.5, 'gwei')
                    
                    # Calculate max fee per gas: base fee * 2 + priority fee (aggressive for testnet)
                    max_fee_per_gas = (base_fee * 2) + max_priority_fee_per_gas
                    
                    # Ensure priority fee is reasonable compared to max fee
                    if max_priority_fee_per_gas >= max_fee_per_gas:
                        max_priority_fee_per_gas = max_fee_per_gas // 3
                    
                    return {
                        'maxFeePerGas': max_fee_per_gas,
                        'maxPriorityFeePerGas': max_priority_fee_per_gas
                    }
                except Exception as eip1559_error:
                    logger.warning(f"EIP-1559 gas pricing failed: {eip1559_error}")
                    # Fall through to legacy pricing
            
            # Legacy gas pricing
            try:
                gas_price = self.w3.eth.gas_price
                # Add 50% buffer for testnet reliability
                buffered_gas_price = int(gas_price * 1.5)
                
                return {
                    'gasPrice': buffered_gas_price
                }
            except Exception as legacy_error:
                logger.error(f"Legacy gas pricing failed: {legacy_error}")
                # Final fallback
                return {
                    'gasPrice': Web3.to_wei(40, 'gwei')  # 40 Gwei fallback
                }
                
        except Exception as e:
            logger.error(f"Error getting gas prices: {e}")
            # Final fallback for any error
            return {
                'gasPrice': Web3.to_wei(40, 'gwei')  # Safe fallback
            }

    async def prepare_license_transaction(self, token_id, licensee_address, duration_days, 
                                    terms_hash, license_type, from_address):
        """Prepare license transaction with better gas handling"""
        try:
            # Get current gas prices with proper fallbacks
            gas_prices = await self.get_current_gas_price()
            
            contract = self.get_contract()
            
            # Convert license type to integer if needed
            if isinstance(license_type, str):
                license_type_int = self.LICENSE_TYPES.get(license_type.upper(), 1)  # Default to COMMERCIAL
            else:
                license_type_int = int(license_type)
            
            # Convert all addresses to checksum format
            from_address_checksum = Web3.to_checksum_address(from_address)
            licensee_address_checksum = Web3.to_checksum_address(licensee_address)
            
            # Get nonce
            nonce = await self.get_nonce(from_address_checksum)
            
            # Prepare base transaction parameters
            base_params = {
                'from': from_address_checksum,
                'value': Web3.to_wei(0.1, 'ether'),  # Fixed 0.1 ETH fee
                'chainId': self.chain_id,
                'nonce': nonce
            }
            
            # Add gas pricing (EIP-1559 or legacy)
            if 'maxFeePerGas' in gas_prices:
                # EIP-1559 transaction
                base_params.update({
                    'maxFeePerGas': gas_prices['maxFeePerGas'],
                    'maxPriorityFeePerGas': gas_prices['maxPriorityFeePerGas']
                })
            else:
                # Legacy transaction
                base_params['gasPrice'] = gas_prices['gasPrice']
            
            # Build the transaction
            transaction = contract.functions.grantLicense(
                token_id,
                licensee_address_checksum,
                duration_days,
                terms_hash,
                license_type_int
            ).build_transaction(base_params)
            
            # Estimate gas with fallback
            try:
                gas_estimate = contract.functions.grantLicense(
                    token_id,
                    licensee_address_checksum,
                    duration_days,
                    terms_hash,
                    license_type_int
                ).estimate_gas({
                    'from': from_address_checksum,
                    'value': Web3.to_wei(0.1, 'ether')
                })
                transaction['gas'] = int(gas_estimate * 1.3)  # Add 30% buffer
            except Exception as gas_error:
                logger.warning(f"Gas estimation failed, using default: {gas_error}")
                transaction['gas'] = 250000  # Safe default for license transactions
            
            # Return the transaction data in the expected format
            result = {
                'to': transaction['to'],
                'data': transaction['data'],
                'value': hex(transaction['value']),
                'gas': hex(transaction['gas']),
                'chainId': hex(transaction['chainId']),
                'nonce': hex(transaction['nonce'])
            }
            
            # Add gas pricing fields
            if 'maxFeePerGas' in transaction:
                result.update({
                    'maxFeePerGas': hex(transaction['maxFeePerGas']),
                    'maxPriorityFeePerGas': hex(transaction['maxPriorityFeePerGas'])
                })
            else:
                result['gasPrice'] = hex(transaction['gasPrice'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error preparing license transaction: {e}", exc_info=True)
            
            # Fallback for demo mode or connection issues
            if self.demo_mode:
                return {
                    'to': settings.CONTRACT_ADDRESS,
                    'data': '0x' + '0' * 128,
                    'value': hex(Web3.to_wei(0.1, 'ether')),
                    'gas': '0x3d090',  # 250,000 gas
                    'gasPrice': hex(Web3.to_wei(30, 'gwei')),
                    'chainId': hex(self.chain_id if hasattr(self, 'chain_id') else 11155111),
                    'nonce': '0x0'
                }
            raise
      
    async def get_nonce(self, address):
        """Get the transaction nonce for an address"""
        try:
            if self.demo_mode:
                return 0
            
            address_checksum = Web3.to_checksum_address(address)
            return self.w3.eth.get_transaction_count(address_checksum)
        except Exception as e:
            logger.error(f"Error getting nonce for {address}: {e}")
            return 0

    async def estimate_gas(self, transaction: dict) -> int:
        """Estimate gas for a transaction"""
        if self.demo_mode:
            return 200000  # Mock gas estimate
        
        try:
            return self.w3.eth.estimate_gas(transaction)
        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}")
            # Return a safe default
            return 300000

    async def prepare_register_transaction(self, metadata_uri: str, royalty_basis_points: int, from_address: str):
        """Prepare artwork registration transaction with improved gas handling"""
        try:
            # Handle demo mode
            if self.demo_mode:
                return {
                    'to': settings.CONTRACT_ADDRESS,
                    'data': '0x' + '0' * 128,  # Mock transaction data
                    'value': '0x0',
                    'gas': '0x493e0',  # 300000 in hex
                    'gasPrice': hex(Web3.to_wei(30, 'gwei'))
                }
            
            from_address = Web3.to_checksum_address(from_address)
            
            # Get optimized gas prices
            gas_prices = await self.get_current_gas_price()
            
            # Check balance first
            balance = self.w3.eth.get_balance(from_address)
            estimated_gas = 300000  # Conservative estimate for registration
            
            # Calculate required balance based on gas pricing method
            if 'maxFeePerGas' in gas_prices:
                required_balance = gas_prices['maxFeePerGas'] * estimated_gas
            else:
                required_balance = gas_prices['gasPrice'] * estimated_gas
            
            if balance < required_balance:
                raise ValueError(
                    f"Insufficient funds. Need {Web3.from_wei(required_balance, 'ether')} ETH, "
                    f"but only have {Web3.from_wei(balance, 'ether')} ETH"
                )

            # Prepare base transaction parameters
            base_params = {
                'from': from_address,
                'nonce': self.w3.eth.get_transaction_count(from_address),
                'gas': estimated_gas,
            }
            
            # Add gas pricing
            base_params.update(gas_prices)

            # Build transaction
            tx = self.contract.functions.registerArtwork(
                metadata_uri,
                royalty_basis_points
            ).build_transaction(base_params)

            # Return in expected format
            result = {
                'to': tx['to'],
                'data': tx['data'],
                'gas': hex(estimated_gas),
                'value': '0x0'
            }
            
            # Add gas pricing fields
            if 'maxFeePerGas' in gas_prices:
                result.update({
                    'maxFeePerGas': hex(gas_prices['maxFeePerGas']),
                    'maxPriorityFeePerGas': hex(gas_prices['maxPriorityFeePerGas'])
                })
            else:
                result['gasPrice'] = hex(gas_prices['gasPrice'])
            
            return result
            
        except Exception as e:
            logger.error(f"Transaction preparation failed: {e}")
            raise

    # Add this method to verify ABI compatibility
    async def verify_contract_abi(self) -> Dict[str, Any]:
        """Verify that the contract ABI matches the deployed contract"""
        try:
            if self.demo_mode:
                return {"status": "demo_mode", "message": "Running in demo mode"}
            
            if not self.contract or not self.w3:
                return {"status": "error", "message": "Contract not initialized"}
            
            # Test various function calls to verify ABI
            test_results = {}
            
            # Test view functions
            try:
                current_id = self.contract.functions.getCurrentTokenId().call()
                test_results["getCurrentTokenId"] = {"status": "success", "value": current_id}
            except Exception as e:
                test_results["getCurrentTokenId"] = {"status": "error", "error": str(e)}
            
            try:
                name = self.contract.functions.name().call()
                test_results["name"] = {"status": "success", "value": name}
            except Exception as e:
                test_results["name"] = {"status": "error", "error": str(e)}
            
            try:
                symbol = self.contract.functions.symbol().call()
                test_results["symbol"] = {"status": "success", "value": symbol}
            except Exception as e:
                test_results["symbol"] = {"status": "error", "error": str(e)}
            
            return {
                "status": "success",
                "contract_address": self.contract.address,
                "chain_id": self.w3.eth.chain_id,
                "test_results": test_results
            }
            
        except Exception as e:
            logger.error(f"ABI verification failed: {e}")
            return {"status": "error", "message": str(e)}

    async def get_artwork_count(self) -> int:
        """Get current artwork count for testing"""
        try:
            if self.demo_mode:
                return self.mock_system.get_current_token_id()
            
            if not self.contract:
                raise Exception("Contract not initialized")
                
            count = self.contract.functions.getCurrentTokenId().call()
            return count
            
        except Exception as e:
            logger.error(f"Failed to get artwork count: {e}")
            raise

    async def get_artwork_info(self, token_id: int) -> Optional[Dict[str, Any]]:
        """Get artwork info from blockchain"""
        try:
            if self.demo_mode:
                return self.mock_system.get_artwork_info(token_id)
            
            if not self.contract:
                return None
                
            result = self.contract.functions.getArtworkInfo(token_id).call()
            return {
                "creator": result[0],
                "metadata_uri": result[1], 
                "royalty_percentage": result[2],
                "is_licensed": result[3]
            }
            
        except Exception as e:
            logger.error(f"Failed to get artwork info for token {token_id}: {e}")
            return None

    async def get_artwork_owner(self, token_id: int) -> Optional[str]:
        """Get artwork owner from blockchain"""
        try:
            if self.demo_mode:
                return self.mock_system.owner_of(token_id)
            
            if not self.contract:
                return None
                
            owner = self.contract.functions.ownerOf(token_id).call()
            return owner
            
        except Exception as e:
            logger.error(f"Failed to get owner for token {token_id}: {e}")
            return None

    async def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction receipt"""
        try:
            if self.demo_mode:
                # Return mock receipt for demo
                return {
                    'status': 1,
                    'blockNumber': 12345,
                    'gasUsed': 300000,
                    'logs': []
                }
            
            if not self.w3:
                return None
                
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return {
                'status': receipt['status'],
                'blockNumber': receipt['blockNumber'],
                'gasUsed': receipt['gasUsed'],
                'logs': receipt['logs']
            }
        except Exception as e:
            logger.error(f"Failed to get transaction receipt for {tx_hash}: {e}")
            return None

    async def get_token_id_from_tx(self, tx_hash: str) -> Optional[int]:
        """Extract token ID from transaction logs"""
        try:
            if self.demo_mode:
                # Return mock token ID for demo
                if hasattr(self, 'mock_system'):
                    return self.mock_system.get_current_token_id()
                return 1
            
            if not self.w3 or not self.contract:
                return None
                
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            # Process logs to find ArtworkRegistered event
            for log in receipt['logs']:
                try:
                    # Decode the log using contract ABI
                    decoded_log = self.contract.events.ArtworkRegistered().process_log(log)
                    token_id = decoded_log['args']['tokenId']
                    logger.info(f"✅ Found token ID {token_id} in transaction {tx_hash}")
                    return token_id
                except Exception:
                    # This log is not the event we're looking for
                    continue
                    
            logger.warning(f"No ArtworkRegistered event found in transaction {tx_hash}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract token ID from transaction {tx_hash}: {e}")
            return None

    @classmethod
    def get_license_types(cls) -> Dict[str, int]:
        """Get available license types mapping"""
        return cls.LICENSE_TYPES.copy()

    @classmethod
    def validate_license_type(cls, license_type) -> int:
        """Validate and convert license type to integer"""
        if isinstance(license_type, str):
            license_type_upper = license_type.upper()
            if license_type_upper not in cls.LICENSE_TYPES:
                raise ValueError(f"Invalid license type: {license_type}. Must be one of: {list(cls.LICENSE_TYPES.keys())}")
            return cls.LICENSE_TYPES[license_type_upper]
        else:
            license_type_int = int(license_type)
            if license_type_int not in cls.LICENSE_TYPES.values():
                raise ValueError(f"Invalid license type integer: {license_type_int}. Must be one of: {list(cls.LICENSE_TYPES.values())}")
            return license_type_int

    async def prepare_marketplace_sale_transaction(self, token_id: int, buyer_address: str,
                                            seller_address: str, sale_price_wei: int) -> Dict[str, Any]:
      """Prepare a marketplace sale transaction using a smart contract"""
      try:
          if self.demo_mode:
              return {
                  'to': settings.CONTRACT_ADDRESS,
                  'data': '0x' + '0' * 128,  # Mock transaction data
                  'value': hex(sale_price_wei),
                  'gas': '0x7a120',  # 500000 in hex for marketplace interaction
                  'gasPrice': hex(Web3.to_wei(30, 'gwei'))
              }
          
          buyer_address_checksum = Web3.to_checksum_address(buyer_address)
          seller_address_checksum = Web3.to_checksum_address(seller_address)
          
          # Get optimized gas prices
          gas_prices = await self.get_current_gas_price()
          
          # Prepare marketplace transaction
          base_params = {
              'from': buyer_address_checksum,
              'value': sale_price_wei,
              'gas': 200000,  # Higher gas for contract interaction
              'nonce': self.w3.eth.get_transaction_count(buyer_address_checksum),
          }
          
          # Add gas pricing
          base_params.update(gas_prices)
          
          # Build the transaction to call a marketplace purchase function
          # This would be your marketplace contract function
          tx = self.contract.functions.purchaseArtwork(
              token_id,
              seller_address_checksum
          ).build_transaction(base_params)
          
          # Return in expected format
          result = {
              'to': tx['to'],
              'value': hex(tx['value']),
              'gas': hex(tx['gas']),
              'data': tx['data'],
              'nonce': hex(tx['nonce'])
          }
          
          # Add gas pricing fields
          if 'maxFeePerGas' in gas_prices:
              result.update({
                  'maxFeePerGas': hex(gas_prices['maxFeePerGas']),
                  'maxPriorityFeePerGas': hex(gas_prices['maxPriorityFeePerGas'])
              })
          else:
              result['gasPrice'] = hex(gas_prices['gasPrice'])
          
          return result
          
      except Exception as e:
          logger.error(f"Marketplace sale transaction preparation failed: {e}")
          raise

    # In your Web3Service class, add these methods:

    async def prepare_sale_transaction(self, token_id: int, buyer_address: str, 
                                 seller_address: str, sale_price_wei: int) -> Dict[str, Any]:
      """Prepare a sale transaction with proper address validation"""
      try:
          if self.demo_mode:
              return {
                  'to': seller_address,
                  'data': f'0x{token_id:064x}',
                  'value': hex(sale_price_wei),
                  'gas': '0x5265c00',
                  'gasPrice': hex(Web3.to_wei(30, 'gwei'))
              }
          
          # Validate and convert addresses to checksum format
          try:
              buyer_address_checksum = Web3.to_checksum_address(buyer_address)
              seller_address_checksum = Web3.to_checksum_address(seller_address)
          except ValueError as e:
              logger.error(f"Invalid Ethereum address: {e}")
              raise ValueError(f"Invalid Ethereum address: {e}")
          
          # Get optimized gas prices
          gas_prices = await self.get_current_gas_price()
          
          # Check buyer balance
          balance = self.w3.eth.get_balance(buyer_address_checksum)
          
          # Estimate gas properly for the transaction
          try:
              gas_estimate = self.w3.eth.estimate_gas({
                  'from': buyer_address_checksum,
                  'to': seller_address_checksum,
                  'value': sale_price_wei,
                  'data': f'0x{token_id:064x}'
              })
              estimated_gas = int(gas_estimate * 1.2)  # Add 20% buffer
          except Exception as gas_error:
              logger.warning(f"Gas estimation failed, using safe default: {gas_error}")
              estimated_gas = 50000
          
          # Calculate required balance
          if 'maxFeePerGas' in gas_prices:
              required_balance = sale_price_wei + (gas_prices['maxFeePerGas'] * estimated_gas)
          else:
              required_balance = sale_price_wei + (gas_prices['gasPrice'] * estimated_gas)
          
          if balance < required_balance:
              raise ValueError(
                  f"Insufficient funds. Need {Web3.from_wei(required_balance, 'ether')} ETH, "
                  f"but only have {Web3.from_wei(balance, 'ether')} ETH"
              )
          
          # Prepare base transaction parameters
          base_params = {
              'from': buyer_address_checksum,
              'to': seller_address_checksum,
              'value': sale_price_wei,
              'gas': estimated_gas,
              'nonce': self.w3.eth.get_transaction_count(buyer_address_checksum),
              'data': f'0x{token_id:064x}'
          }
          
          # Add gas pricing
          base_params.update(gas_prices)
          
          # Return transaction data with properly formatted addresses
          result = {
              'to': base_params['to'],
              'value': hex(base_params['value']),
              'gas': hex(base_params['gas']),
              'data': base_params['data'],
              'nonce': hex(base_params['nonce'])
          }
          
          # Add gas pricing fields
          if 'maxFeePerGas' in gas_prices:
              result.update({
                  'maxFeePerGas': hex(gas_prices['maxFeePerGas']),
                  'maxPriorityFeePerGas': hex(gas_prices['maxPriorityFeePerGas'])
              })
          else:
              result['gasPrice'] = hex(gas_prices['gasPrice'])
          
          logger.info(f"Prepared transaction: {result}")
          return result
          
      except Exception as e:
          logger.error(f"Sale transaction preparation failed: {e}")
          raise

    async def transfer_artwork_ownership(self, token_id: int, from_address: str, 
                                      to_address: str) -> Dict[str, Any]:
        """Prepare transaction to transfer artwork ownership"""
        try:
            if self.demo_mode:
                # Mock ownership transfer
                return {
                    'to': settings.CONTRACT_ADDRESS,
                    'data': '0x' + f'{token_id:064x}' + from_address[2:].lower().ljust(64, '0') + to_address[2:].lower().ljust(64, '0'),
                    'value': '0x0',
                    'gas': '0x493e0',  # 300000 in hex
                    'gasPrice': hex(Web3.to_wei(30, 'gwei'))
                }
            
            from_address_checksum = Web3.to_checksum_address(from_address)
            to_address_checksum = Web3.to_checksum_address(to_address)
            
            # Get optimized gas prices
            gas_prices = await self.get_current_gas_price()
            
            # Prepare base transaction parameters
            base_params = {
                'from': from_address_checksum,
                'gas': 200000,  # Estimated gas for transfer
                'nonce': self.w3.eth.get_transaction_count(from_address_checksum),
            }
            
            # Add gas pricing
            base_params.update(gas_prices)
            
            # Build the transfer transaction
            tx = self.contract.functions.transferFrom(
                from_address_checksum,
                to_address_checksum,
                token_id
            ).build_transaction(base_params)
            
            # Return in expected format
            result = {
                'to': tx['to'],
                'data': tx['data'],
                'gas': hex(tx['gas']),
                'value': '0x0',
                'nonce': hex(tx['nonce'])
            }
            
            # Add gas pricing fields
            if 'maxFeePerGas' in gas_prices:
                result.update({
                    'maxFeePerGas': hex(gas_prices['maxFeePerGas']),
                    'maxPriorityFeePerGas': hex(gas_prices['maxPriorityFeePerGas'])
                })
            else:
                result['gasPrice'] = hex(gas_prices['gasPrice'])
            
            return result
            
        except Exception as e:
            logger.error(f"Ownership transfer preparation failed: {e}")
            raise

    async def simulate_sale_economics(self, token_id: int, sale_price_eth: float,
                                    creator_address: str, current_owner: str) -> Dict[str, Any]:
        """Simulate the economics of a sale transaction"""
        try:
            # Get artwork info
            artwork_info = await self.get_artwork_info(token_id)
            if not artwork_info:
                raise ValueError(f"Artwork {token_id} not found")
            
            # Determine if primary or secondary sale
            is_primary_sale = creator_address.lower() == current_owner.lower()
            
            # Calculate amounts
            sale_price_wei = Web3.to_wei(sale_price_eth, 'ether')
            platform_fee_rate = 0.05  # 5%
            platform_fee_wei = int(sale_price_wei * platform_fee_rate)
            
            royalty_wei = 0
            if not is_primary_sale:
                royalty_rate = artwork_info['royalty_percentage'] / 10000
                royalty_wei = int(sale_price_wei * royalty_rate)
            
            seller_receives_wei = sale_price_wei - platform_fee_wei - royalty_wei
            
            return {
                'sale_price_eth': sale_price_eth,
                'sale_price_wei': str(sale_price_wei),
                'platform_fee_wei': str(platform_fee_wei),
                'platform_fee_eth': str(Web3.from_wei(platform_fee_wei, 'ether')),
                'royalty_wei': str(royalty_wei),
                'royalty_eth': str(Web3.from_wei(royalty_wei, 'ether')),
                'seller_receives_wei': str(seller_receives_wei),
                'seller_receives_eth': str(Web3.from_wei(seller_receives_wei, 'ether')),
                'is_primary_sale': is_primary_sale,
                'royalty_rate': artwork_info['royalty_percentage'] / 100,  # As percentage
                'creator_address': creator_address,
                'current_owner': current_owner
            }
            
        except Exception as e:
            logger.error(f"Sale simulation failed: {e}")
            raise


# Mock system for demo mode
class MockArtworkSystem:
    def __init__(self):
        self.artworks = []
        self.token_count = 0
        self.licenses = []
        self.license_counter = 0
        self.accounts = [
            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", 
            "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
            "0x90F79bf6EB2c4f870365E785982E1f101E93b906"
        ]
        self.balances = {
            Web3.to_checksum_address(acc): Web3.to_wei(100, 'ether') for acc in self.accounts
        }
    
    def register_artwork(self, owner: str, metadata: str, royalty: int) -> int:
        owner = Web3.to_checksum_address(owner)
        metadata = str(metadata)
        royalty = int(royalty)

        if royalty > 2000:
            raise ValueError("Royalty cannot exceed 20%")

        token_id = self.token_count
        self.artworks.append({
            'owner': owner,
            'creator': owner,
            'metadata': metadata,
            'royalty': royalty,
            'isLicensed': False,
            'tokenURI': metadata
        })
        self.token_count += 1
        return token_id

    def get_artwork_info(self, token_id: int) -> Dict[str, Any]:
        if token_id >= len(self.artworks):
            raise ValueError("Nonexistent token")
        art = self.artworks[token_id]
        return {
            "creator": art['creator'],
            "metadata_uri": art['metadata'],
            "royalty_percentage": art['royalty'],
            "is_licensed": art['isLicensed']
        }

    def get_current_token_id(self) -> int:
        return self.token_count

    def owner_of(self, token_id: int) -> str:
        if token_id >= len(self.artworks):
            raise ValueError("Nonexistent token")
        return self.artworks[token_id]['owner']

# Global service instance
web3_service = Web3Service()