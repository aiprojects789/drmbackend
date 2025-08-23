import streamlit as st
import json
from web3 import Web3
from pathlib import Path
import os
from datetime import datetime, timedelta
import logging
import hashlib
import time
from streamlit.components.v1 import html
import requests
from dotenv import load_dotenv

load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Artwork DRM System",
    page_icon="🎨",
    layout="wide"
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state
def init_session_state():
    if 'metamask_account' not in st.session_state:
        st.session_state.metamask_account = None
    if 'metamask_connected' not in st.session_state:
        st.session_state.metamask_connected = False
    if 'chain_id' not in st.session_state:
        st.session_state.chain_id = None
    if 'mock_system' not in st.session_state:
        st.session_state.mock_system = None
    if 'wallet_balance' not in st.session_state:
        st.session_state.wallet_balance = "0"
    if 'contract' not in st.session_state:
        st.session_state.contract = None
    if 'w3' not in st.session_state:
        st.session_state.w3 = None
    if 'network_name' not in st.session_state:
        st.session_state.network_name = None
    if 'pending_transaction' not in st.session_state:
        st.session_state.pending_transaction = False
    if 'connecting' not in st.session_state:
        st.session_state.connecting = False
    if 'last_message' not in st.session_state:
        st.session_state.last_message = None
    if 'last_message_time' not in st.session_state:
        st.session_state.last_message_time = None

init_session_state()

# Configuration
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '0xA07F45FE615E86C6BE90AD207952497c6F23d69d')
WEB3_PROVIDER_URL = os.getenv('WEB3_PROVIDER_URL', 'https://sepolia.infura.io/v3/YOUR_INFURA_KEY')

# Contract ABI (only essential functions)
CONTRACT_ABI = [
    {
        "inputs": [{"internalType": "string", "name": "metadataURI", "type": "string"}, {"internalType": "uint256", "name": "royaltyPercentage", "type": "uint256"}],
        "name": "registerArtwork",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "address", "name": "licensee", "type": "address"}, {"internalType": "uint256", "name": "durationDays", "type": "uint256"}, {"internalType": "string", "name": "termsHash", "type": "string"}, {"internalType": "uint8", "name": "licenseType", "type": "uint8"}],
        "name": "grantLicense",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "getArtworkInfo",
        "outputs": [{"internalType": "address", "name": "creator", "type": "address"}, {"internalType": "string", "name": "metadataURI", "type": "string"}, {"internalType": "uint256", "name": "royaltyPercentage", "type": "uint256"}, {"internalType": "bool", "name": "isLicensed", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getCurrentTokenId",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "address", "name": "licensee", "type": "address"}],
        "name": "revokeLicense",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "getActiveLicenses",
        "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "creator", "type": "address"}],
        "name": "getCreatorArtworks",
        "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# ==============================================
# Mock Blockchain System (for demo mode)
# ==============================================

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
    
    def register_artwork(self, owner, metadata, royalty):
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

    def getArtworkInfo(self, token_id):
        if token_id >= len(self.artworks):
            raise ValueError("Nonexistent token")
        art = self.artworks[token_id]
        return (
            art['creator'],
            art['metadata'],
            art['royalty'],
            art['isLicensed']
        )

    def transfer_eth(self, from_account, to_account, amount):
        from_acc = Web3.to_checksum_address(from_account)
        to_acc = Web3.to_checksum_address(to_account)
        
        if from_acc not in self.balances or to_acc not in self.balances:
            raise ValueError("Account does not exist")
        if self.balances[from_acc] < amount:
            raise ValueError("Insufficient balance")
            
        self.balances[from_acc] -= amount
        self.balances[to_acc] += amount
        return True

    def grant_license(self, token_id, licensee, duration_days, terms_hash, license_type):
        licensee = Web3.to_checksum_address(licensee)
        
        if token_id >= len(self.artworks):
            raise ValueError("Artwork does not exist")
            
        artwork_owner = self.artworks[token_id]['owner']
        license_fee = Web3.to_wei(0.1, 'ether')
        self.transfer_eth(licensee, artwork_owner, license_fee)
        
        license_data = {
            'licenseId': self.license_counter,
            'tokenId': token_id,
            'licensee': licensee,
            'startDate': int(datetime.now().timestamp()),
            'endDate': int((datetime.now() + timedelta(days=duration_days)).timestamp()),
            'termsHash': terms_hash,
            'licenseType': license_type,
            'isActive': True,
            'feePaid': license_fee
        }
        self.licenses.append(license_data)
        self.artworks[token_id]['isLicensed'] = True
        self.license_counter += 1
        return self.license_counter - 1
       
    def getCurrentTokenId(self):
        return self.token_count

    def ownerOf(self, token_id):
        if token_id >= len(self.artworks):
            raise ValueError("Nonexistent token")
        return self.artworks[token_id]['owner']

    def revoke_license(self, token_id, licensee):
        licensee = Web3.to_checksum_address(licensee)
        
        for license_data in self.licenses:
            if license_data['tokenId'] == token_id and license_data['licensee'] == licensee:
                license_data['isActive'] = False
                break
        
        has_active_license = any(
            l['tokenId'] == token_id and l['isActive']
            for l in self.licenses
        )
        self.artworks[token_id]['isLicensed'] = has_active_license
    
    def get_artworks(self):
        return [
            {
                'token_id': i,
                'owner': art['owner'],
                'creator': art['creator'],
                'metadataURI': art['metadata'],
                'royaltyPercentage': art['royalty'],
                'isLicensed': art['isLicensed']
            }
            for i, art in enumerate(self.artworks)
        ]
    
    def transfer_ownership(self, token_id, new_owner):
        new_owner = Web3.to_checksum_address(new_owner)
        if token_id >= len(self.artworks):
            raise ValueError("Artwork does not exist")
        self.artworks[token_id]['owner'] = new_owner
        return True

# Initialize mock system
if DEMO_MODE and st.session_state.mock_system is None:
    st.session_state.mock_system = MockArtworkSystem()
mock_system = st.session_state.mock_system if DEMO_MODE else None

# ==============================================
# Web3 and Contract Integration
# ==============================================

def get_web3_provider():
    """Get Web3 provider with fallback options"""
    providers = [
        os.getenv('WEB3_PROVIDER_URL', 'https://sepolia.infura.io/v3/YOUR_INFURA_KEY'),
        'https://rpc.sepolia.org',
        'https://ethereum-sepolia-rpc.publicnode.com',
    ]
    
    for provider_url in providers:
        try:
            w3 = Web3(Web3.HTTPProvider(provider_url))
            if w3.is_connected():
                return w3
        except:
            continue
    
    return None

def validate_network(w3):
    """Check if connected network matches expected network"""
    expected_chain_id = 11155111  # Sepolia Testnet
    current_chain_id = w3.eth.chain_id
    
    if current_chain_id != expected_chain_id:
        st.warning(f"⚠️ Connected to wrong network (Chain ID: {current_chain_id})")
        st.warning(f"Please switch to Sepolia Testnet (Chain ID: {expected_chain_id})")
        return False
    return True

def init_web3_and_contract():
    """Initialize Web3 connection and contract instance"""
    if DEMO_MODE:
        return None, None
    
    try:
        w3 = get_web3_provider()
        
        if not w3 or not w3.is_connected():
            st.error(f"❌ Could not connect to any Ethereum node")
            return None, None
        
        if not validate_network(w3):
            return None, None
        
        try:
            contract_address = Web3.to_checksum_address(CONTRACT_ADDRESS)
            
            code = w3.eth.get_code(contract_address)
            if code == b'':
                st.error(f"❌ No contract found at address: {CONTRACT_ADDRESS}")
                return None, None
                
            contract = w3.eth.contract(
                address=contract_address,
                abi=CONTRACT_ABI
            )
            
            # Verify contract
            try:
                token_id = contract.functions.getCurrentTokenId().call()
                st.session_state.w3 = w3
                st.session_state.contract = contract
                return w3, contract
            except Exception as e:
                st.error(f"❌ Contract verification failed: {str(e)}")
                return None, None
                
        except ValueError as e:
            st.error(f"❌ Invalid contract address: {CONTRACT_ADDRESS}")
            return None, None
            
    except Exception as e:
        st.error(f"❌ Web3 initialization error: {str(e)}")
        return None, None

# ==============================================
# MetaMask Connection Component
# ==============================================

def create_metamask_connector():
    """Secure MetaMask connector that works with Streamlit's sandbox"""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                padding: 20px;
                margin: 0;
                background: transparent;
            }
            .connect-btn {
                background: linear-gradient(135deg, #f6851b, #e2761b);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
                margin-bottom: 15px;
                transition: all 0.3s ease;
            }
            .connect-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            .connect-btn:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            #status {
                margin-top: 15px;
                font-size: 14px;
            }
            #walletAddress {
                font-family: monospace;
                word-break: break-all;
                font-size: 13px;
            }
        </style>
    </head>
    <body>
        <button id="connectBtn" class="connect-btn">🦊 Connect MetaMask</button>
        <div id="status"></div>

        <script>
            // Safe detection of MetaMask
            function isMetaMaskAvailable() {
                return typeof window.parent.ethereum !== 'undefined' && 
                       window.parent.ethereum.isMetaMask;
            }

            function getNetworkName(chainId) {
                const networks = {
                    '0x1': 'Ethereum Mainnet',
                    '0x5': 'Goerli Testnet',
                    '0xaa36a7': 'Sepolia Testnet',
                    '0x89': 'Polygon Mainnet',
                    '0x13881': 'Polygon Mumbai',
                    '0x539': 'Localhost'
                };
                return networks[chainId] || `Unknown (${chainId})`;
            }

            // Main connection function
            async function connectMetaMask() {
                const statusEl = document.getElementById('status');
                const btn = document.getElementById('connectBtn');
                
                if (!isMetaMaskAvailable()) {
                    statusEl.innerHTML = `
                        <div style="color: #721c24; background: #f8d7da; padding: 10px; border-radius: 4px;">
                            <p><strong>MetaMask not detected</strong></p>
                            <p>Please ensure MetaMask is installed and refresh the page.</p>
                            <p>If using mobile, try opening in MetaMask's built-in browser.</p>
                        </div>
                    `;
                    btn.disabled = true;
                    return;
                }

                btn.disabled = true;
                btn.textContent = 'Connecting...';
                
                try {
                    // Request accounts through parent window
                    const accounts = await window.parent.ethereum.request({ 
                        method: 'eth_requestAccounts' 
                    });

                    if (accounts && accounts.length > 0) {
                        const address = accounts[0];
                        const shortAddress = address.substring(0, 6) + '...' + address.substring(38);
                        
                        // Get chain ID
                        const chainId = await window.parent.ethereum.request({
                            method: 'eth_chainId'
                        });

                        // Get balance
                        const balance = await window.parent.ethereum.request({
                            method: 'eth_getBalance',
                            params: [address, 'latest']
                        });
                        const ethBalance = (parseInt(balance, 16) / 1e18).toFixed(4);
                        
                        statusEl.innerHTML = `
                            <div style="color: #155724; background: #d4edda; padding: 10px; border-radius: 4px;">
                                <p><strong>✅ Connected</strong></p>
                                <p>Address: <span id="walletAddress">${shortAddress}</span></p>
                                <p>Chain ID: ${chainId} (${getNetworkName(chainId)})</p>
                                <p>Balance: ${ethBalance} ETH</p>
                            </div>
                        `;

                        // Notify Streamlit with all connection data
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: {
                                type: 'WALLET_CONNECTED',
                                account: address,
                                chainId: chainId,
                                networkName: getNetworkName(chainId),
                                balance: ethBalance
                            }
                        }, '*');
                        
                        btn.textContent = 'Connected';
                    }
                } catch (error) {
                    statusEl.innerHTML = `
                        <div style="color: #721c24; background: #f8d7da; padding: 10px; border-radius: 4px;">
                            <p><strong>Connection Error</strong></p>
                            <p>${error.message}</p>
                        </div>
                    `;
                    btn.disabled = false;
                    btn.textContent = 'Try Again';
                }
            }

            // Initialize
            document.getElementById('connectBtn').addEventListener('click', connectMetaMask);
            
            // Check if already connected
            if (isMetaMaskAvailable() && window.parent.ethereum.selectedAddress) {
                connectMetaMask();
            }
        </script>
    </body>
    </html>
    """
    
    return html(html_content, height=300)

def handle_wallet_messages():
    """Handle wallet connection messages and update session state"""
    
    handler_js = """
    <script>
        // Handle wallet connection messages
        window.addEventListener('message', function(event) {
            // Only accept messages from our iframe
            if (event.data.type === 'streamlit:setComponentValue' && 
                event.data.value && 
                event.data.value.type === 'WALLET_CONNECTED') {
                
                console.log('Wallet connected message received:', event.data.value);
                
                // Forward the message to Streamlit
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: {
                        'type': 'WALLET_CONNECTED',
                        'account': event.data.value.account,
                        'chainId': event.data.value.chainId,
                        'networkName': event.data.value.networkName,
                        'balance': event.data.value.balance
                    }
                }, '*');
            }
        });
    </script>
    """
    
    return html(handler_js, height=0)

# ==============================================
# Transaction Handling
# ==============================================

def create_transaction_sender(tx_data, action_type):
    """Fixed transaction sender that uses parent window's MetaMask"""
    
    tx_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .status {{ padding: 10px; border-radius: 5px; margin: 10px 0; }}
            .success {{ background: #d4edda; color: #155724; }}
            .error {{ background: #f8d7da; color: #721c24; }}
            .info {{ background: #d1ecf1; color: #0c5460; }}
        </style>
    </head>
    <body>
        <div id="status" class="info">Preparing transaction...</div>
        
        <script>
            async function sendTransaction() {{
                const statusEl = document.getElementById('status');
                
                try {{
                    // Verify MetaMask is available in parent
                    if (typeof window.parent.ethereum === 'undefined') {{
                        throw new Error('MetaMask not detected in parent window');
                    }}
                    
                    statusEl.textContent = 'Sending transaction...';
                    statusEl.className = 'status info';
                    
                    // Send through parent window's MetaMask
                    const txHash = await window.parent.ethereum.request({{
                        method: 'eth_sendTransaction',
                        params: [{json.dumps(tx_data)}]
                    }});
                    
                    statusEl.textContent = `Transaction sent! Hash: ${{txHash.substring(0, 10)}}...`;
                    statusEl.className = 'status success';
                    
                    // Notify Streamlit
                    window.parent.postMessage({{
                        type: 'TRANSACTION_SUCCESS',
                        txHash: txHash,
                        action: '{action_type}'
                    }}, '*');
                    
                }} catch (error) {{
                    console.error('Transaction error:', error);
                    statusEl.textContent = error.message;
                    statusEl.className = 'status error';
                    
                    window.parent.postMessage({{
                        type: 'TRANSACTION_ERROR',
                        error: error.message,
                        code: error.code,
                        action: '{action_type}'
                    }}, '*');
                }}
            }}
            
            // Start immediately
            sendTransaction();
        </script>
    </body>
    </html>
    """
    
    return html(tx_html, height=150)

def handle_transaction_messages():
    """Handle transaction result messages"""
    
    message_handler = """
    <script>
        window.addEventListener('message', function(event) {
            if (event.data && (event.data.type === 'TRANSACTION_SUCCESS' || event.data.type === 'TRANSACTION_ERROR')) {
                console.log('Transaction result received:', event.data);
                
                // Send to Streamlit
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: event.data
                }, '*');
            }
        });
    </script>
    """
    
    return html(message_handler, height=0)

# ==============================================
# Helper Functions
# ==============================================

def validate_and_checksum(address):
    """Validate an Ethereum address and return checksummed version"""
    try:
        if not address or not Web3.is_address(address):
            return None
        return Web3.to_checksum_address(address)
    except:
        return None

def format_accounts(accounts):
    formatted = []
    for i, account in enumerate(accounts):
        if DEMO_MODE and mock_system:
            balance = mock_system.balances.get(Web3.to_checksum_address(account), 0)
            eth_balance = Web3.from_wei(balance, 'ether')
        else:
            eth_balance = 0.0
        formatted.append(f"Account #{i+1}: {account[:6]}...{account[-4:]} (Balance: {eth_balance:.4f} ETH)")
    return formatted

def account_selector(label, accounts, default_index=0, key=None):
    account_options = format_accounts(accounts)
    account_mapping = {
        option: Web3.to_checksum_address(account) 
        for option, account in zip(account_options, accounts)
    }
    selected_option = st.selectbox(
        label, 
        options=account_options, 
        index=default_index,
        key=key
    )
    return account_mapping[selected_option]

def get_network_name(chain_id):
    """Get human-readable network name from chain ID"""
    networks = {
        '0x1': 'Ethereum Mainnet',
        '0x5': 'Goerli Testnet',
        '0xaa36a7': 'Sepolia Testnet',
        '0x89': 'Polygon Mainnet',
        '0x13881': 'Polygon Mumbai',
        '0x539': 'Localhost'
    }
    return networks.get(chain_id, f'Unknown ({chain_id})')

# ==============================================
# Contract Functions
# ==============================================

def get_artwork_count():
    """Get total number of artworks"""
    try:
        if DEMO_MODE and mock_system:
            return mock_system.getCurrentTokenId()
        elif st.session_state.contract:
            return st.session_state.contract.functions.getCurrentTokenId().call()
        return 0
    except Exception as e:
        logger.error(f"Error getting artwork count: {str(e)}")
        st.error("Failed to get artwork count from blockchain")
        return 0

def get_artwork_info(token_id):
    """Get artwork information"""
    try:
        if DEMO_MODE and mock_system:
            return mock_system.getArtworkInfo(token_id)
        elif st.session_state.contract:
            return st.session_state.contract.functions.getArtworkInfo(token_id).call()
        else:
            return None
    except Exception as e:
        st.error(f"Error getting artwork info: {str(e)}")
        return None

def get_artwork_owner(token_id):
    """Get artwork owner"""
    try:
        if DEMO_MODE and mock_system:
            return mock_system.ownerOf(token_id)
        elif st.session_state.contract:
            return st.session_state.contract.functions.ownerOf(token_id).call()
        else:
            return None
    except Exception as e:
        st.error(f"Error getting artwork owner: {str(e)}")
        return None

def prepare_register_transaction(metadata_uri, royalty_basis_points):
    """Prepare transaction data for artwork registration"""
    try:
        if not st.session_state.metamask_connected:
            return None
        
        w3 = st.session_state.w3
        contract = st.session_state.contract
        
        if not w3 or not contract:
            return None
        
        from_address = Web3.to_checksum_address(st.session_state.metamask_account)
        
        # Build transaction
        contract_function = contract.functions.registerArtwork(
            metadata_uri,
            royalty_basis_points
        )
        
        # Estimate gas
        try:
            gas_estimate = contract_function.estimate_gas({'from': from_address})
            gas_limit = int(gas_estimate * 1.2)
        except:
            gas_limit = 500000
        
        # Get gas price
        try:
            gas_price = w3.eth.gas_price
        except:
            gas_price = Web3.to_wei('20', 'gwei')
        
        # Build transaction
        transaction = contract_function.build_transaction({
            'from': from_address,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(from_address),
            'value': 0
        })
        
        return {
            'to': transaction['to'],
            'from': from_address,
            'data': transaction['data'],
            'gas': hex(transaction['gas']),
            'gasPrice': hex(transaction['gasPrice']),
            'value': '0x0'
        }
    
    except Exception as e:
        st.error(f"Transaction preparation failed: {str(e)}")
        return None

def prepare_license_transaction(token_id, licensee, duration_days, terms_hash, license_type):
    """Prepare transaction data for license grant"""
    try:
        if not st.session_state.metamask_connected:
            return None
        
        w3 = st.session_state.w3
        contract = st.session_state.contract
        
        if not w3 or not contract:
            return None
        
        # Convert license type to enum index
        license_type_idx = ["PERSONAL", "COMMERCIAL", "EXCLUSIVE"].index(license_type)
        
        from_address = Web3.to_checksum_address(st.session_state.metamask_account)
        licensee_address = Web3.to_checksum_address(licensee)
        
        # Build transaction
        contract_function = contract.functions.grantLicense(
            token_id,
            licensee_address,
            duration_days,
            terms_hash,
            license_type_idx
        )
        
        # Estimate gas
        try:
            gas_estimate = contract_function.estimate_gas({
                'from': from_address,
                'value': Web3.to_wei(0.1, 'ether')
            })
            gas_limit = int(gas_estimate * 1.2)
        except:
            gas_limit = 500000
        
        # Get gas price
        try:
            gas_price = w3.eth.gas_price
        except:
            gas_price = Web3.to_wei('20', 'gwei')
        
        # Build transaction
        transaction = contract_function.build_transaction({
            'from': from_address,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(from_address),
            'value': Web3.to_wei(0.1, 'ether')
        })
        
        return {
            'to': transaction['to'],
            'from': from_address,
            'data': transaction['data'],
            'gas': hex(transaction['gas']),
            'gasPrice': hex(transaction['gasPrice']),
            'value': hex(Web3.to_wei(0.1, 'ether'))
        }
    
    except Exception as e:
        st.error(f"License transaction preparation failed: {str(e)}")
        return None

# ==============================================
# Main Application
# ==============================================

def main():
    st.title("🎨 Artwork DRM System")
    
    # Initialize session state
    init_session_state()
    
    # Initialize Web3 and contract if not in demo mode
    if not DEMO_MODE:
        if st.session_state.w3 is None or st.session_state.contract is None:
            init_web3_and_contract()
    
    # Display mode info
    if DEMO_MODE:
        st.warning("🚀 **DEMO MODE ACTIVE** - Using simulated blockchain for demonstration")
    else:
        st.success("🔗 **LIVE MODE** - Connected to real blockchain")
        if CONTRACT_ADDRESS:
            st.info(f"📋 **Contract Address:** `{CONTRACT_ADDRESS}`")

    # Debug panel (can be removed in production)
    with st.expander("🛠️ Debug Panel", expanded=False):
        st.write("### Session State")
        st.json({
            "metamask_connected": st.session_state.metamask_connected,
            "metamask_account": st.session_state.metamask_account,
            "chain_id": st.session_state.chain_id,
            "network_name": st.session_state.network_name,
            "wallet_balance": st.session_state.wallet_balance,
            "pending_transaction": st.session_state.pending_transaction,
            "last_message": st.session_state.last_message,
            "last_message_time": st.session_state.last_message_time
        })
        
        if st.button("🔄 Refresh Session State"):
            st.rerun()
    
    # Create components
    wallet_connector = create_metamask_connector()
    message_handler = handle_wallet_messages()
    
    # Check for MetaMask connection messages
    if message_handler and isinstance(message_handler, dict):
        if message_handler.get('type') == 'METAMASK_CONNECTION':
            connection_data = message_handler
            if connection_data.get('connected'):
                st.session_state.metamask_connected = True
                st.session_state.metamask_account = Web3.to_checksum_address(connection_data.get('account'))
                st.session_state.chain_id = connection_data.get('chainId')
                st.session_state.network_name = connection_data.get('networkName')
                st.session_state.wallet_balance = connection_data.get('balance', '0')
                st.rerun()
            else:
                st.session_state.metamask_connected = False
                st.session_state.metamask_account = None
                st.rerun()
        
        elif message_handler.get('type') == 'METAMASK_CHAIN_CHANGED':
            st.session_state.chain_id = message_handler.get('chainId')
            st.session_state.network_name = message_handler.get('networkName')
            st.rerun()
        
        elif message_handler.get('type') == 'METAMASK_DISCONNECTED':
            st.session_state.metamask_connected = False
            st.session_state.metamask_account = None
            st.rerun()

    
    # Handle transaction result messages
    tx_component = handle_transaction_messages()
    if tx_component and isinstance(tx_component, dict):
        if tx_component.get('type') == 'TRANSACTION_SUCCESS':
            st.session_state.pending_transaction = False
            st.success(f"✅ Transaction successful!")
            st.info(f"**Hash:** `{tx_component.get('txHash')}`")
            
            if tx_component.get('action') == 'register':
                st.success("🎨 **Artwork registered successfully!**")
            elif tx_component.get('action') == 'grant_license':
                st.success("📄 **License granted successfully!**")
            elif tx_component.get('action') == 'revoke_license':
                st.success("🗑️ **License revoked successfully!**")
                
            st.balloons()
            
        elif tx_component.get('type') == 'TRANSACTION_ERROR':
            st.session_state.pending_transaction = False
            error_msg = tx_component.get('error', 'Unknown error')
            
            if tx_component.get('code') == 4001:
                st.warning("⚠️ **Transaction cancelled by user**")
            else:
                st.error(f"❌ **Transaction failed:** {error_msg}")

    # Sidebar for wallet connection
    with st.sidebar:
        st.header("🔗 Wallet Connection")
        
        if DEMO_MODE:
            st.info("📱 **Demo Mode** - MetaMask connection simulated")
            if mock_system:
                accounts = mock_system.accounts
                selected_account = account_selector(
                    "Select Demo Account", 
                    accounts,
                    key="demo_account_selector"
                )
                st.session_state.metamask_account = selected_account
                st.session_state.metamask_connected = True
                
                balance = mock_system.balances.get(Web3.to_checksum_address(selected_account), 0)
                eth_balance = Web3.from_wei(balance, 'ether')
                st.success(f"**Connected:** {selected_account[:6]}...{selected_account[-4:]}")
                st.info(f"**Balance:** {eth_balance:.4f} ETH")
                st.info(f"**Network:** Demo Network")
        else:
            # Real MetaMask connection
            st.subheader("🦊 MetaMask Connection")
            st.markdown("**Connect via MetaMask:**")
            create_metamask_connector()
        
        # Display connection status
        st.divider()
        if st.session_state.metamask_connected:
            st.success("✅ **Wallet Connected**")
            if st.session_state.metamask_account:
                st.code(f"Account: {st.session_state.metamask_account}")
                        
            if st.session_state.chain_id:
                network_name = get_network_name(st.session_state.chain_id)
                st.info(f"**Network:** {network_name}")
            if st.session_state.wallet_balance:
                st.info(f"**Balance:** {st.session_state.wallet_balance} ETH")
            
            # Disconnect button
            if st.button("🔓 Disconnect Wallet", type="secondary"):
                st.session_state.metamask_connected = False
                st.session_state.metamask_account = None
                st.session_state.chain_id = None
                st.session_state.network_name = None
                st.session_state.wallet_balance = "0"
                st.session_state.pending_transaction = False
                st.rerun()
        else:
            st.warning("⚠️ **Wallet Not Connected**")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎨 Artwork Registration", 
        "📄 Licensing", 
        "💰 Royalties", 
        "🔍 View Artworks",
        "ℹ️ How to Use"
    ])
    
    # Check if wallet is connected for main functionality
    if not st.session_state.get('metamask_connected', False):
        st.warning("⚠️ **Please connect your MetaMask wallet to use the application features.**")
        return
    
    st.info(f"✅ Connected Wallet: {st.session_state.metamask_account}")
    
    with tab1:
        st.header("🎨 Register New Artwork")
        st.markdown("Register your digital artwork on the blockchain with built-in royalty management.")
        
        # Don't show form if transaction is pending
        if st.session_state.get('pending_transaction', False):
            st.info("⏳ **Transaction in progress...** Please wait for confirmation.")
            return
        
        with st.form("register_artwork"):
            col1, col2 = st.columns(2)
            
            with col1:
                metadata = st.text_input(
                    "IPFS Metadata Hash", 
                    "ipfs://QmExample123abc...",
                    help="Enter the IPFS hash containing your artwork metadata"
                )
                
                royalty = st.slider(
                    "Royalty Percentage", 
                    min_value=0, 
                    max_value=20, 
                    value=10,
                    help="Percentage you'll earn on secondary sales (0-20%)"
                )
                
                royalty_basis_points = royalty * 100
            
            with col2:
                st.markdown("**📋 Metadata Requirements:**")
                st.markdown("""
                - Image URL (hosted on IPFS)
                - Title and description
                - Artist information
                - Attributes/properties
                - Creation date
                """)
                
                st.markdown("**💡 Tip:** Use Pinata or NFT.Storage for IPFS hosting")
            
            submitted = st.form_submit_button("🎨 Register Artwork", type="primary")
            
            if submitted:
                if not metadata.startswith("ipfs://"):
                    st.error("❌ Metadata must be a valid IPFS hash starting with 'ipfs://'")
                    st.stop()
                
                try:
                    if DEMO_MODE and mock_system:
                        with st.spinner("🔄 Registering artwork..."):
                            token_id = mock_system.register_artwork(
                                st.session_state.metamask_account,
                                metadata,
                                royalty_basis_points
                            )
                            
                            tx_hash = hashlib.sha256(f"register_{time.time()}".encode()).hexdigest()
                            
                            st.success("✅ Artwork registered successfully!")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.info(f"**Token ID:** {token_id}")
                                st.info(f"**Creator:** {st.session_state.metamask_account[:10]}...")
                                st.info(f"**Royalty:** {royalty}%")
                            
                            with col2:
                                st.info(f"**Metadata:** {metadata[:30]}...")
                                st.info(f"**Transaction:** 0x{tx_hash[:16]}...")
                                st.info(f"**Status:** ✅ Confirmed")
                            
                            st.balloons()
                    
                    else:  # REAL MODE
                        if not st.session_state.metamask_connected:
                            st.error("❌ Please connect your wallet first")
                            st.stop()
                        
                        # Prepare transaction
                        with st.spinner("🔄 Preparing transaction..."):
                            tx_data = prepare_register_transaction(metadata, royalty_basis_points)
                            
                            if not tx_data:
                                st.error("❌ Failed to prepare transaction")
                                st.stop()
                        
                        # Set pending state
                        st.session_state.pending_transaction = True
                        
                        st.info("🦊 **Opening MetaMask...** Please approve the transaction.")
                        
                        # Send transaction
                        create_transaction_sender(tx_data, 'register')
                
                except Exception as e:
                    st.error(f"❌ Registration failed: {str(e)}")
                    st.session_state.pending_transaction = False

    with tab2:
        st.header("📄 Artwork Licensing")
        st.markdown("Grant or revoke licenses for artwork usage with automatic payment handling.")
        
        artwork_count = get_artwork_count()
        
        if artwork_count == 0:
            st.warning("⚠️ No artworks registered yet. Please register an artwork first.")
            st.stop()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ Grant License")
            
            # Don't show form if transaction is pending
            if st.session_state.get('pending_transaction', False):
                st.info("⏳ **Transaction in progress...** Please wait for confirmation.")
            else:
                with st.form("grant_license"):
                    token_id = st.number_input(
                        "Token ID", 
                        min_value=0, 
                        max_value=artwork_count-1,
                        value=0,
                        help="ID of the artwork to license"
                    )
                    
                    if DEMO_MODE and mock_system:
                        licensee = account_selector(
                            "Licensee Account",
                            mock_system.accounts,
                            default_index=1,
                            key="licensee_selector"
                        )
                    else:
                        licensee = st.text_input("Licensee Address", "0x...", help="Ethereum address of the licensee")
                        if licensee and not Web3.is_address(licensee):
                            st.error("Invalid Ethereum address")
                    
                    duration = st.number_input("Duration (days)", min_value=1, max_value=365, value=30)
                    
                    license_type = st.selectbox(
                        "License Type",
                        ["PERSONAL", "COMMERCIAL", "EXCLUSIVE"],
                        help="Type of license being granted"
                    )
                    
                    terms_hash = st.text_input(
                        "Terms IPFS Hash", 
                        "ipfs://QmTermsExample...",
                        help="IPFS hash of the license terms document"
                    )
                    
                    st.info("💰 **License Fee:** 0.1 ETH (automatically collected)")
                    
                    submitted = st.form_submit_button("✍️ Grant License", type="primary")
                    
                    if submitted:
                        try:
                            # Validate inputs
                            if not DEMO_MODE and not Web3.is_address(licensee):
                                st.error("❌ Invalid licensee address")
                                st.stop()
                            
                            if not terms_hash.startswith("ipfs://"):
                                st.error("❌ Terms hash must start with 'ipfs://'")
                                st.stop()
                            
                            # Check ownership
                            owner = get_artwork_owner(token_id)
                            if owner and Web3.to_checksum_address(owner) != Web3.to_checksum_address(st.session_state.metamask_account):
                                st.error("❌ Only the artwork owner can grant licenses.")
                                st.stop()
                            
                            with st.spinner("🔄 Processing license..."):
                                if DEMO_MODE and mock_system:
                                    license_type_idx = ["PERSONAL", "COMMERCIAL", "EXCLUSIVE"].index(license_type)
                                    license_id = mock_system.grant_license(
                                        token_id,
                                        licensee,
                                        duration,
                                        terms_hash,
                                        license_type_idx
                                    )
                                    
                                    st.success("✅ License granted successfully!")
                                    st.info(f"**License ID:** {license_id}")
                                    st.info(f"**Type:** {license_type}")
                                    st.info(f"**Duration:** {duration} days")
                                    st.info(f"**End Date:** {(datetime.now() + timedelta(days=duration)).strftime('%Y-%m-%d')}")
                                
                                else:
                                    # Prepare transaction
                                    tx_data = prepare_license_transaction(
                                        token_id, licensee, duration, terms_hash, license_type
                                    )
                                    
                                    if tx_data:
                                        st.session_state.pending_transaction = True
                                        st.info("🦊 **Opening MetaMask...** Please approve the transaction.")
                                        create_transaction_sender(tx_data, 'grant_license')
                                    else:
                                        st.error("❌ Failed to prepare license transaction")
                        
                        except Exception as e:
                            st.error(f"❌ License grant failed: {str(e)}")
                            st.session_state.pending_transaction = False
        
        with col2:
            st.subheader("🗑️ Revoke License")
            
            # Don't show form if transaction is pending
            if st.session_state.get('pending_transaction', False):
                st.info("⏳ **Transaction in progress...** Please wait for confirmation.")
            else:
                with st.form("revoke_license"):
                    revoke_token_id = st.number_input(
                        "Token ID", 
                        min_value=0,
                        max_value=artwork_count-1,
                        value=0,
                        key="revoke_token_id"
                    )
                    
                    if DEMO_MODE and mock_system:
                        revoke_licensee = account_selector(
                            "Licensee Account",
                            mock_system.accounts,
                            default_index=1,
                            key="revoke_licensee_selector"
                        )
                    else:
                        revoke_licensee = st.text_input("Licensee Address", "0x...", key="revoke_licensee")
                        if revoke_licensee and not Web3.is_address(revoke_licensee):
                            st.error("Invalid Ethereum address")
                    
                    st.warning("⚠️ **Warning:** This action cannot be undone.")
                    
                    submitted = st.form_submit_button("🗑️ Revoke License", type="secondary")
                    
                    if submitted:
                        try:
                            # Validate inputs
                            if not DEMO_MODE and not Web3.is_address(revoke_licensee):
                                st.error("❌ Invalid licensee address")
                                st.stop()
                            
                            # Check ownership
                            owner = get_artwork_owner(revoke_token_id)
                            if owner and Web3.to_checksum_address(owner) != Web3.to_checksum_address(st.session_state.metamask_account):
                                st.error("❌ Only the artwork owner can revoke licenses.")
                                st.stop()
                            
                            with st.spinner("🔄 Processing revocation..."):
                                if DEMO_MODE and mock_system:
                                    mock_system.revoke_license(revoke_token_id, revoke_licensee)
                                    st.success("✅ License revoked successfully!")
                                
                                else:
                                    # For real mode, prepare revoke transaction
                                    w3 = st.session_state.w3
                                    contract = st.session_state.contract
                                    
                                    if w3 and contract:
                                        from_address = Web3.to_checksum_address(st.session_state.metamask_account)
                                        licensee_address = Web3.to_checksum_address(revoke_licensee)
                                        
                                        contract_function = contract.functions.revokeLicense(
                                            revoke_token_id,
                                            licensee_address
                                        )
                                        
                                        try:
                                            gas_estimate = contract_function.estimate_gas({'from': from_address})
                                            gas_limit = int(gas_estimate * 1.2)
                                        except:
                                            gas_limit = 300000
                                        
                                        try:
                                            gas_price = w3.eth.gas_price
                                        except:
                                            gas_price = Web3.to_wei('20', 'gwei')
                                        
                                        transaction = contract_function.build_transaction({
                                            'from': from_address,
                                            'gas': gas_limit,
                                            'gasPrice': gas_price,
                                            'nonce': w3.eth.get_transaction_count(from_address),
                                            'value': 0
                                        })
                                        
                                        tx_data = {
                                            'to': transaction['to'],
                                            'from': from_address,
                                            'data': transaction['data'],
                                            'gas': hex(transaction['gas']),
                                            'gasPrice': hex(transaction['gasPrice']),
                                            'value': '0x0'
                                        }
                                        
                                        st.session_state.pending_transaction = True
                                        st.info("🦊 **Opening MetaMask...** Please approve the transaction.")
                                        create_transaction_sender(tx_data, 'revoke_license')
                                    else:
                                        st.error("❌ Web3 or contract not initialized")
                        
                        except Exception as e:
                            st.error(f"❌ License revocation failed: {str(e)}")
                            st.session_state.pending_transaction = False
    with tab3:
        st.header("💰 Royalty Management")
        st.markdown("Simulate artwork sales and see how royalties are automatically distributed.")
        
        artwork_count = get_artwork_count()
        
        if artwork_count == 0:
            st.warning("⚠️ No artworks registered yet. Register an artwork first.")
            return
        
        st.subheader("🎯 Simulate Artwork Sale")
        sale_type = st.radio("Sale Type", ["Primary Sale", "Secondary Sale"], horizontal=True)
        
        if sale_type == "Primary Sale":
            st.info("**Primary Sale:** First sale by the original creator")
        else:
            st.info("**Secondary Sale:** Resale by a collector (includes royalty payment)")
        
        with st.form("simulate_sale_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                token_id = st.number_input("Token ID", min_value=0, max_value=artwork_count-1, step=1)
                sale_price = st.number_input("Sale Price (in ETH)", min_value=0.01, value=1.0, step=0.01)
                
            with col2:
                if DEMO_MODE and mock_system:
                    accounts = mock_system.accounts
                    if sale_type == "Primary Sale":
                        buyer = account_selector(
                            "Buyer Address", 
                            accounts, 
                            default_index=1,
                            key="primary_sale_buyer_selector"
                        )
                    else:  # Secondary Sale
                        seller = account_selector(
                            "Seller Address", 
                            accounts, 
                            default_index=1,
                            key="secondary_sale_seller_selector"
                        )
                        buyer = account_selector(
                            "Buyer Address", 
                            accounts, 
                            default_index=2,
                            key="secondary_sale_buyer_selector"
                        )
                else:
                    if sale_type == "Primary Sale":
                        buyer = st.text_input("Buyer Address", "0x...")
                    else:
                        seller = st.text_input("Seller Address", "0x...")
                        buyer = st.text_input("Buyer Address", "0x...")
            
            sale_price_wei = Web3.to_wei(sale_price, 'ether')
            submit_button = st.form_submit_button("💸 Simulate Sale", type="primary")
            
            if submit_button:
                try:
                    artwork_info = get_artwork_info(token_id)
                    if not artwork_info:
                        st.error("❌ Artwork not found")
                        return
                    
                    creator, metadata, royalty_basis_points, is_licensed = artwork_info
                    royalty_percent = royalty_basis_points / 100
                    
                    if sale_type == "Primary Sale":
                        platform_fee = sale_price_wei // 20  # 5%
                        creator_amount = sale_price_wei - platform_fee
                        
                        if DEMO_MODE and mock_system:
                            mock_system.transfer_eth(buyer, creator, creator_amount)
                            if platform_fee > 0:
                                mock_system.transfer_eth(buyer, mock_system.accounts[0], platform_fee)
                            mock_system.transfer_ownership(token_id, buyer)
                        
                        st.success("✅ **Primary sale completed!**")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Creator Receives", f"{Web3.from_wei(creator_amount, 'ether'):.4f} ETH")
                        with col2:
                            st.metric("Platform Fee (5%)", f"{Web3.from_wei(platform_fee, 'ether'):.4f} ETH")
                        with col3:
                            st.metric("New Owner", f"{buyer[:6]}...{buyer[-4:]}")
                        
                    else:  # Secondary Sale
                        royalty_amount = (sale_price_wei * royalty_basis_points) // 10000
                        seller_amount = sale_price_wei - royalty_amount
                        
                        if DEMO_MODE and mock_system:
                            mock_system.transfer_eth(buyer, creator, royalty_amount)
                            mock_system.transfer_eth(buyer, seller, seller_amount)
                            mock_system.transfer_ownership(token_id, buyer)
                        
                        st.success("✅ **Secondary sale completed!**")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Creator Royalty", f"{Web3.from_wei(royalty_amount, 'ether'):.4f} ETH")
                        with col2:
                            st.metric("Seller Receives", f"{Web3.from_wei(seller_amount, 'ether'):.4f} ETH")
                        with col3:
                            st.metric("Royalty Rate", f"{royalty_percent}%")
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Simulation failed: {str(e)}")

    with tab4:
        st.header("🔍 Artwork Explorer")
        st.markdown("Browse all registered artworks and their current status.")
        
        try:
            artwork_count = get_artwork_count()
            
            if artwork_count == 0:
                st.info("📄 No artworks registered yet. Be the first to register!")
                return
            
            # Display artworks in a nice grid
            st.subheader(f"📊 Total Artworks: {artwork_count}")
            
            for token_id in range(artwork_count):
                artwork_info = get_artwork_info(token_id)
                owner = get_artwork_owner(token_id)
                
                if artwork_info and owner:
                    creator, metadata, royalty_basis_points, is_licensed = artwork_info
                    royalty_percent = royalty_basis_points / 100
                    
                    with st.expander(f"🎨 Artwork #{token_id} - {metadata[:30]}...", expanded=(token_id==0)):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**📋 Basic Information**")
                            st.write(f"**Token ID:** `{token_id}`")
                            st.write(f"**Owner:** `{owner[:10]}...{owner[-8:]}`")
                            st.write(f"**Creator:** `{creator[:10]}...{creator[-8:]}`")
                            
                        with col2:
                            st.markdown("**💼 Commercial Details**")
                            st.write(f"**Metadata URI:** `{metadata[:20]}...`")
                            st.write(f"**Royalty Percentage:** `{royalty_percent}%`")
                            
                            if is_licensed:
                                st.success("✅ **Currently Licensed**")
                            else:
                                st.info("🔓 **Available for Licensing**")
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button(f"📄 View Details #{token_id}", key=f"details_{token_id}"):
                                st.info("🔗 In a real implementation, this would show full metadata from IPFS")
                        
                        with col2:
                            checksum_owner = Web3.to_checksum_address(owner)
                            checksum_sender = Web3.to_checksum_address(st.session_state.metamask_account)
                            if checksum_owner != checksum_sender:
                                if st.button(f"⚙️ Manage #{token_id}", key=f"manage_{token_id}"):
                                    st.info("📝 Owner management features would be available here")
                        
                        with col3:
                            if not is_licensed and owner.lower() != st.session_state.metamask_account.lower():
                                if st.button(f"📄 Request License #{token_id}", key=f"license_{token_id}"):
                                    st.info("💬 License request functionality would be available here")
                        
        except Exception as e:
            st.error(f"❌ Error loading artworks: {str(e)}")

    with tab5:
        st.header("ℹ️ How to Use This Application")
        
        # Instructions based on current mode
        if DEMO_MODE:
            st.info("🚀 **You are currently in DEMO MODE** - All transactions are simulated")
        else:
            st.success("🔗 **You are in LIVE MODE** - Real blockchain transactions")

        # Getting started section
        st.subheader("🚀 Getting Started")
        
        with st.expander("1️⃣ Connect Your Wallet", expanded=True):
            if DEMO_MODE:
                st.markdown("""
                **Demo Mode Instructions:**
                - Select a demo account from the sidebar
                - All transactions are simulated
                - Perfect for testing the interface
                - No database operations in demo mode
                """)
            else:
                st.markdown("""
                **Live Mode Instructions:**
                1. Make sure you have MetaMask installed in your browser
                2. Click "Connect MetaMask" in the sidebar
                3. Approve the connection in MetaMask popup
                4. **Wallet data is NOT saved automatically to database**
                5. Switch to Sepolia testnet if prompted
                6. Make sure you have some Sepolia ETH for gas fees
                
                """)

        
        with st.expander("3️⃣ Register Your Artwork"):
            st.markdown("""
            **Before registering:**
            - Upload your artwork to IPFS (try Pinata.cloud or NFT.Storage)
            - Create a metadata JSON file with artwork details
            - Upload metadata to IPFS as well
            
            **Registration Process:**
            1. Go to "Artwork Registration" tab
            2. Enter your IPFS metadata hash
            3. Set your desired royalty percentage (0-20%)
            4. Click "Register Artwork"
            5. Confirm transaction in MetaMask (Live Mode)
            
            **Wallet Integration:**
            - Uses locally connected MetaMask wallet
            - Wallet verification against database (if exists)
            - No automatic wallet saving to database
            """)
        
        with st.expander("4️⃣ Database Browser"):
            st.markdown("""
            **Available in Sidebar:**
            - **All Wallets:** View all registered wallets in database
            - **User Wallets:** Filter by specific user ID
            - **Specific Address:** Search for individual wallet
            
            **Information Displayed:**
            - Wallet address and network
            - Verification status
            - Creation and update timestamps
            - Associated user information
            
            **Current Limitations:**
            - Read-only access from Streamlit
            - Cannot modify or create wallet entries
            """)

if __name__ == "__main__":
    main()