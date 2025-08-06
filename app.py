# import streamlit as st
# import json
# from web3 import Web3
# from pathlib import Path
# import os
# from datetime import datetime, timedelta
# import logging
# import subprocess

# # Set page configuration
# st.set_page_config(
#     page_title="Artwork DRM System",
#     page_icon="🎨",
#     layout="wide"
# )

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Helper functions
# def format_accounts(accounts):
#     formatted = []
#     for i, account in enumerate(accounts):
#         balance = w3.from_wei(w3.eth.get_balance(account), 'ether')
#         formatted.append(f"Account #{i+1}: {account[:6]}...{account[-4:]} (Balance: {balance:.4f} ETH)")
#     return formatted

# def account_selector(label, accounts, default_index=0):
#     """
#     Custom account selector that formats account addresses nicely
#     """
#     account_options = format_accounts(accounts)
#     account_mapping = {option: account for option, account in zip(account_options, accounts)}
#     selected_option = st.selectbox(label, options=account_options, index=default_index)
#     return account_mapping[selected_option]

# def wei_input(label, default_value=0):
#     wei_str = st.text_input(label, value=str(default_value))
#     try:
#         return int(wei_str)
#     except ValueError:
#         st.error("Please enter a valid integer value")
#         return 0

# DEMO_MODE = True  # Set to False for real blockchain connection

# # --- Mock Data Storage ---
# class MockArtworkSystem:
#     def __init__(self):
#         self.artworks = []
#         self.token_count = 0
#         self.licenses = []
#         self.accounts = [
#             "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",  # Owner/creator
#             "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"   # Licensee
#         ]
#         # Initialize balances (100 ETH each)
#         self.balances = {
#             self.accounts[0]: Web3.to_wei(100, 'ether'),
#             self.accounts[1]: Web3.to_wei(100, 'ether')
#         }
#         self.licensing_contract = None
#         self.license_counter = 0
        
#     # Make sure this matches the real contract exactly
#     def getCurrentTokenId(self):
#         return self.token_count
        
#     # Keep this for backward compatibility
#     def get_current_token_id(self):
#         return self.token_count
        
#     def register_artwork(self, *args):
#         # Handle all possible calling patterns
#         if len(args) == 2:  # Simplified call (metadata, royalty)
#             metadata, royalty = args
#             owner = "mock_owner"
#         elif len(args) == 3:  # Direct call (owner, metadata, royalty)
#             owner, metadata, royalty = args
#         elif len(args) == 4:  # Web3 call (tx_dict, owner, metadata, royalty)
#             _, owner, metadata, royalty = args
#         else:
#             raise ValueError(f"Unexpected number of arguments: {len(args)}")

#         if royalty > 20:
#             raise ValueError("Royalty cannot exceed 20%")

#         token_id = self.token_count
#         self.artworks.append({
#             'owner': owner,
#             'creator': owner,
#             'metadata': metadata,
#             'royalty': royalty,
#             'isLicensed': False,
#             'tokenURI': metadata
#         })
#         self.token_count += 1
#         return token_id
        
#     def get_artwork_info(self, token_id):
#         """Handle both direct calls (token_id) and web3 calls (tx_dict, token_id)"""
#         if isinstance(token_id, tuple):  # Handle web3 call pattern
#             _, token_id = token_id  # Extract the actual token_id
        
#         if token_id >= len(self.artworks):
#             raise ValueError("Nonexistent token")
#         art = self.artworks[token_id]
#         return (
#             art['creator'],
#             art['metadata'],
#             art['royalty'],
#             art['isLicensed']
#         )

#     def owner_of(self, token_id):
#         """Handle both direct and web3 call patterns"""
#         if isinstance(token_id, tuple):  # Handle web3 call pattern
#             _, token_id = token_id
#         if token_id >= len(self.artworks):
#             raise ValueError("Nonexistent token")
#         return self.artworks[token_id]['owner']

#     def grant_license(self, *args):
#         # Handle both direct calls (5 args) and web3 calls (6 args)
#         if len(args) == 5:
#             token_id, licensee, duration_days, terms_hash, license_type = args
#         elif len(args) == 6:
#             _, token_id, licensee, duration_days, terms_hash, license_type = args
#         else:
#             raise ValueError(f"Expected 5 or 6 arguments, got {len(args)}")
        
#         # Ensure artwork exists
#         if token_id >= len(self.artworks):
#             raise ValueError("Artwork does not exist")
            
#         license_data = {
#             'licenseId': self.license_counter,
#             'tokenId': token_id,
#             'licensee': licensee,
#             'startDate': datetime.now(),
#             'endDate': datetime.now() + timedelta(days=duration_days),
#             'termsHash': terms_hash,
#             'licenseType': license_type,
#             'isActive': True
#         }
#         self.licenses.append(license_data)
#         self.artworks[token_id]['isLicensed'] = True
#         self.license_counter += 1
#         return self.license_counter - 1  # Return the license ID

#     def get_license_count(self, token_id):
#         return len([l for l in self.licenses if l['tokenId'] == token_id])

#     def get_license_details(self, token_id, index):
#         licenses = [l for l in self.licenses if l['tokenId'] == token_id]
#         if not licenses or index >= len(licenses):
#             raise ValueError("License not found")
#         license = licenses[index]
#         return (
#             license['licensee'],
#             int(license['startDate'].timestamp()),
#             int(license['endDate'].timestamp()),
#             license['termsHash'],
#             license['licenseType'],
#             license['isActive']
#         )
    
#     def revoke_license(self, token_id, licensee):
#         for license_data in self.licenses:
#             if license_data['tokenId'] == token_id and license_data['licensee'] == licensee:
#                 license_data['isActive'] = False
#                 break
        
#         # Check if any active licenses remain for this token
#         has_active_license = any(
#             l['tokenId'] == token_id and l['isActive'] 
#             for l in self.licenses
#         )
#         self.artworks[token_id]['isLicensed'] = has_active_license

# # Replace the mock_system initialization with this:
# if 'mock_system' not in st.session_state:
#     st.session_state.mock_system = MockArtworkSystem()
# mock_system = st.session_state.mock_system

# class MockContractFunction:
#     def __init__(self, callback, estimate_gas=200000):  # Set default estimate_gas
#         self.callback = callback
#         self.estimate_gas_value = estimate_gas
#         self._args = None
#         self._kwargs = None
        
#     def estimate_gas(self, tx_dict):
#         return self.estimate_gas_value  # Always return the preset value
        
#     def __call__(self, *args, **kwargs):
#         self._args = args
#         self._kwargs = kwargs
#         return self
        
#     def call(self, *args, **kwargs):
#         # Use latest args/kwargs if provided, otherwise use stored ones
#         final_args = args if args else (self._args if self._args else ())
#         final_kwargs = kwargs if kwargs else (self._kwargs if self._kwargs else {})
#         return self.callback(*final_args, **final_kwargs)
        
#     def transact(self, tx_dict):
#         # Generate a mock transaction hash
#         import hashlib
#         import time
#         mock_hash = hashlib.sha256(f"tx_{time.time()}".encode()).hexdigest()
        
#         # Use stored args and kwargs
#         result = self.callback(*(self._args or ()), **(self._kwargs or {}))
        
#         # Return a mock transaction hash object
#         class MockTxHash:
#             def __init__(self, hash_str):
#                 self.hash_str = hash_str
#             def hex(self):
#                 return self.hash_str
        
#         return MockTxHash(f"0x{mock_hash}")
    

# class MockContract:
#     def __init__(self, contract_type):
#         # Get the mock system from session state
#         mock_system = st.session_state.mock_system
        
#         if contract_type == "registry":
#             self.functions = type('', (), {
#                 'registerArtwork': self._create_function(
#                     lambda *args: mock_system.register_artwork(*args),
#                     estimate_gas=200000
#                 ),
#                 'getCurrentTokenId': self._create_getter(mock_system.getCurrentTokenId),
#                 'getArtworkInfo': self._create_function(
#                     lambda *args: mock_system.get_artwork_info(args)
#                 ),
#                 'ownerOf': self._create_function(
#                     lambda *args: mock_system.owner_of(args)
#                 )
#             })()

#         elif contract_type == "licensing":
#             self.functions = type('', (), {
#                 'grantLicense': self._create_function(
#                     lambda *args: mock_system.grant_license(*args),
#                     estimate_gas=150000
#                 ),
#                 'revokeLicense': self._create_function(
#                     lambda token_id, licensee: mock_system.revoke_license(token_id, licensee),
#                     estimate_gas=50000
#                 ),
#                 'getLicenseCount': self._create_function(
#                     lambda token_id: len([l for l in mock_system.licenses 
#                                        if l['tokenId'] == token_id])
#                 ),
#                 'getLicenseDetails': self._create_function(
#                     lambda token_id, index: mock_system.get_license_details(token_id, index)
#                 )
#             })()

#     def _create_function(self, callback, estimate_gas=21000):
#         def wrapper(*args, **kwargs):
#             return MockContractFunction(callback, estimate_gas=estimate_gas)(*args, **kwargs)
#         return wrapper
        
#     def _create_getter(self, callback):
#         def wrapper(*args, **kwargs):
#             return MockContractFunction(lambda: callback())
#         return wrapper

# class MockEth:
#     def __init__(self):
#         self.chain_id = 31337
        
#     def get_balance(self, account):
#         return mock_system.balances.get(account, 0)
        
#     def get_transaction_count(self, account):
#         return 0
        
#     def wait_for_transaction_receipt(self, tx_hash):
#         return {
#             'blockNumber': 1,
#             'gasUsed': 21000,
#             'transactionHash': tx_hash.hex() if hasattr(tx_hash, 'hex') else str(tx_hash)
#         }
        
#     @property
#     def accounts(self):
#         return mock_system.accounts
        
#     def contract(self, address=None, abi=None):
#         if "ArtworkRegistry" in str(abi):
#             return MockContract("registry")
#         else:
#             return MockContract("licensing")

# class MockWeb3:
#     def __init__(self):
#         self.eth = MockEth()
#         self.from_wei = Web3.from_wei
#         self.to_wei = Web3.to_wei
        
#     def is_connected(self):
#         return True

# # --- Web3 Initialization ---
# if DEMO_MODE:
#     st.warning("DEMO MODE: Using simulated blockchain")
#     w3 = MockWeb3()
# else:
#     # Your original Web3 connection code
#     try:
#         local_provider = Web3.HTTPProvider('http://127.0.0.1:8545', request_kwargs={'timeout': 60})
#         w3 = Web3(local_provider)
#         # Check connection
#         if not w3.is_connected():
#             # Fall back to Mumbai testnet if local node not available
#             provider_url = os.getenv(
#                 'WEB3_PROVIDER_URL',
#                 'https://rpc-mumbai.maticvigil.com'  # Free Polygon Mumbai testnet
#             )
#             w3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={'timeout': 60}))
            
#             if not w3.is_connected():
#                 st.error("""
#                     ⚠️ Could not connect to any Ethereum node. Please ensure:
#                     1. For local development: Hardhat node is running (npx hardhat node)
#                     2. For production: You have internet access to Mumbai testnet
#                     3. The chainId matches your environment
#                 """)
#                 if st.button("Try to reconnect"):
#                     st.experimental_rerun()
#                 st.stop()
        
#         # Display connection info
#         chain_id = w3.eth.chain_id
#         if chain_id == 31337:
#             st.success("✅ Connected to local Hardhat node (ChainID: 31337)")
#         elif chain_id == 80001:
#             st.success("✅ Connected to Polygon Mumbai testnet (ChainID: 80001)")
#         else:
#             st.warning(f"⚠️ Connected to unknown network (ChainID: {chain_id})")
            
#     except Exception as e:
#         st.error(f"Connection error: {str(e)}")
#         st.stop()

# # Modify the load_contracts function to handle fallback without modifying DEMO_MODE
# def load_contracts():
#     global DEMO_MODE  # Add this line to allow modification of the global variable
    
#     if DEMO_MODE:
#         # These ABIs can be empty - just need the contract names
#         registry_abi = '{"contractName":"ArtworkRegistry"}'
#         licensing_abi = '{"contractName":"ArtworkLicensing"}'
        
#         return {
#             'registry': w3.eth.contract(abi=registry_abi),
#             'licensing': w3.eth.contract(abi=licensing_abi)
#         }
#     else:
#         try:
#             # First try to load existing contracts
#             if not os.path.exists('contract-addresses.json'):
#                 st.warning("Contracts not deployed - falling back to demo mode behavior")
#                 # Instead of modifying DEMO_MODE, just return demo contracts
#                 registry_abi = '{"contractName":"ArtworkRegistry"}'
#                 licensing_abi = '{"contractName":"ArtworkLicensing"}'
#                 return {
#                     'registry': w3.eth.contract(abi=registry_abi),
#                     'licensing': w3.eth.contract(abi=licensing_abi)
#                 }
            
#             with open('contract-addresses.json') as f:
#                 addresses = json.load(f)
            
#             # Load ABIs with error handling
#             @st.cache_resource
#             def load_abi(name):
#                 try:
#                     path = Path(f'./artifacts/contracts/{name}.sol/{name}.json')
#                     if not path.exists():
#                         raise FileNotFoundError(f"ABI file not found at {path}")
#                     with open(path) as f:
#                         return json.load(f)['abi']
#                 except Exception as e:
#                     st.error(f"Error loading {name} ABI: {str(e)}")
#                     st.stop()

#             # Initialize contracts
#             registry = w3.eth.contract(
#                 address=addresses['registry'],
#                 abi=load_abi('ArtworkRegistry')
#             )
            
#             licensing = w3.eth.contract(
#                 address=addresses['licensing'],
#                 abi=load_abi('ArtworkLicensing')
#             )

#             return {
#                 'registry': registry,
#                 'licensing': licensing
#             }

#         except Exception as e:
#             st.error(f"Contract loading failed: {str(e)} - falling back to demo mode")
#             # Instead of modifying DEMO_MODE, just return demo contracts
#             registry_abi = '{"contractName":"ArtworkRegistry"}'
#             licensing_abi = '{"contractName":"ArtworkLicensing"}'
#             return {
#                 'registry': w3.eth.contract(abi=registry_abi),
#                 'licensing': w3.eth.contract(abi=licensing_abi)
#             }

# def add_demo_toggle():
#     """Add this function to allow runtime demo mode switching"""
#     global DEMO_MODE  # Add this to modify the global variable
    
#     with st.sidebar:
#         st.markdown("---")
#         st.subheader("⚙️ Configuration")
        
#         demo_mode = st.checkbox(
#             "Enable Demo Mode", 
#             value=DEMO_MODE,
#             help="Switch between demo simulation and real blockchain"
#         )
        
#         if demo_mode != DEMO_MODE:
#             DEMO_MODE = demo_mode  # Update the global variable
#             st.warning("⚠️ Mode change requires app restart")
#             if st.button("🔄 Restart App"):
#                 st.rerun()
                
#         return DEMO_MODE

# def main():
#     st.title("🎨 Artwork DRM System")
    
#     # FIX 3: Add clear demo mode indicator
#     if DEMO_MODE:
#         st.warning("🚀 **DEMO MODE ACTIVE** - Using simulated blockchain for demonstration")
#         with st.expander("ℹ️ Demo Mode Information"):
#             st.info("""
#             **Demo Mode Features:**
#             - ✅ Simulated blockchain transactions
#             - ✅ No real gas costs
#             - ✅ Instant confirmations
#             - ✅ All features available for testing
            
#             **Note:** This is for demonstration only. No real blockchain transactions occur.
#             """)
#     else:
#         st.success("🔗 **LIVE MODE** - Connected to real blockchain")

#     # Load contracts
#     contracts = load_contracts()
#     registry = contracts['registry']
#     licensing = contracts['licensing']

#     # Get Ethereum accounts
#     try:
#         accounts = w3.eth.accounts
#         if not accounts:
#             st.error("No accounts found on the Ethereum node.")
#             st.stop()
#     except Exception as e:
#         st.error(f"Error fetching accounts: {str(e)}")
#         st.stop()

#     # Sidebar with account info
#     with st.sidebar:
#         st.header("Account Information")
#         selected_account = account_selector("Select Account", accounts)
#         balance = w3.from_wei(w3.eth.get_balance(selected_account), 'ether')
#         st.info(f"Account: {selected_account}")
#         st.info(f"Balance: {balance:.4f} ETH")


#         if DEMO_MODE and st.button("🛠️ Debug Mock System"):
#             st.write("### Mock System State")
#             st.json({
#                 "token_count": mock_system.token_count,
#                 "artworks": mock_system.artworks,
#                 "licenses": mock_system.licenses
#             })

#     # Create tabs
#     tab1, tab2, tab3, tab4 = st.tabs([
#         "🎨 Artwork Registration", 
#         "📄 Licensing", 
#         "💰 Royalties", 
#         "🔍 View Artworks"
#     ])

#     with tab1:
#         st.header("Register New Artwork")
#         with st.form("register_form"):
#             metadata = st.text_input("IPFS Hash", "ipfs://Qm...", help="Enter the IPFS CID of your artwork metadata")
#             royalty = st.slider("Royalty Percentage", 0, 20, 10, help="Percentage creator earns on secondary sales (0-20%)")
            
#             submit_button = st.form_submit_button("Register Artwork")
            
#             if submit_button:
#                 try:
#                     # Input validation
#                     if not metadata.startswith("ipfs://"):
#                         st.error("Metadata URI must start with 'ipfs://'")
#                         st.stop()
                    
#                     if royalty > 20:
#                         st.error("Royalty cannot exceed 20%")
#                         st.stop()

#                     # Get current state
#                     token_count_before = registry.functions.getCurrentTokenId().call()
                    
#                     # Create contract call
#                     register_func = registry.functions.registerArtwork(metadata, royalty)

#                     # Initialize gas estimate with default value
#                     gas_estimate = 300000
                    
#                     # Gas estimation
#                     try:
#                         with st.spinner("Estimating gas requirements..."):
#                             gas_estimate = register_func.estimate_gas({
#                                 'from': selected_account,
#                                 'nonce': w3.eth.get_transaction_count(selected_account)
#                             })
#                             st.success(f"Gas estimate: {gas_estimate} wei")
#                     except Exception as e:
#                         st.warning(f"Gas estimation failed, using default: {str(e)}")

#                     # Prepare transaction with the gas estimate
#                     tx_dict = {
#                         'from': selected_account,
#                         'gas': gas_estimate,
#                         'gasPrice': w3.to_wei('50', 'gwei'),
#                         'nonce': w3.eth.get_transaction_count(selected_account)
#                     }

#                     # Execute transaction
#                     with st.spinner("Processing blockchain transaction..."):
#                         tx_hash = register_func.transact(tx_dict)
#                         receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

#                     # Verification
#                     token_count_after = registry.functions.getCurrentTokenId().call()
                    
#                     if token_count_after > token_count_before:
#                         new_token_id = token_count_after - 1
#                         # In your verification block:
#                         try:
#                             artwork_info = registry.functions.getArtworkInfo(new_token_id).call()
#                             if len(artwork_info) == 4:  # Ensure we got the expected tuple
#                                 creator, stored_metadata, stored_royalty, is_licensed = artwork_info
#                                 st.success("### ✅ Artwork Successfully Registered!")
#                                 st.balloons()
                            
#                                 with st.expander("Registration Details", expanded=True):
#                                     col1, col2 = st.columns(2)
#                                     with col1:
#                                         st.write("**Artwork Information**")
#                                         st.write(f"- Token ID: `{new_token_id}`")
#                                         st.write(f"- Creator: `{creator}`")
#                                         st.write(f"- Royalty: `{stored_royalty}%`")
#                                         st.write(f"- Metadata: `{stored_metadata}`")
                                    
#                                     with col2:
#                                         st.write("**Transaction Details**")
#                                         st.write(f"- TX Hash: `{tx_hash.hex()}`")
#                                         st.write(f"- Block: `{receipt['blockNumber']}`")
#                                         st.write(f"- Gas Used: `{receipt['gasUsed']}`")
#                                         st.write(f"- Status: `Success`")

#                             else:
#                                     st.warning(f"Artwork registered (Token ID: {new_token_id}) but got unexpected response format")

#                         except Exception as e:
#                             st.error(f"Verification failed: {str(e)}")
#                             st.warning(f"Artwork was registered (Token ID: {new_token_id}) but we couldn't verify details")
                    
#                     else:
#                         st.error("❌ Registration failed - no new token was created")

#                 except Exception as e:
#                     st.error("### 🔥 Registration Failed")
                    
#                     # Enhanced error diagnostics
#                     error_type = type(e).__name__
#                     error_msg = str(e)
                    
#                     st.write(f"**Error Type:** {error_type}")
#                     st.write(f"**Message:** {error_msg}")
                    
#                     # Common error scenarios
#                     if "reverted" in error_msg:
#                         st.error("**Possible Reasons:**")
#                         st.error("- Royalty percentage exceeds maximum (20%)")
#                         st.error("- Invalid metadata format")
#                         st.error("- Insufficient account balance for gas")
                    
#                     elif "nonce too low" in error_msg:
#                         st.error("**Solution:** Try the transaction again")
                    
#                     elif "execution reverted" in error_msg:
#                         st.error("**Contract Reverted:** Check smart contract requirements")
                    
#                     # Technical details
#                     with st.expander("Debug Information"):
#                         st.write("### Technical Details")
#                         st.json({
#                             "error_type": error_type,
#                             "error_message": error_msg,
#                             "demo_mode": DEMO_MODE,
#                             "chain_id": w3.eth.chain_id if not DEMO_MODE else "demo",
#                             "account": selected_account,
#                             "metadata": metadata,
#                             "royalty": royalty
#                         })

#     with tab2:
#         st.header("🎫 Artwork Licensing")
        
#         # Enhanced artwork check with demo mode handling
#         try:
#             if DEMO_MODE:
#                 token_count = mock_system.token_count
#                 st.sidebar.info(f"🎯 Demo Mode: {token_count} mock artworks available")
#             else:
#                 token_count = registry.functions.getCurrentTokenId().call()
                
#             if token_count == 0:
#                 st.warning("No artworks registered yet. Please register an artwork first.")
#                 if st.button("⏩ Go to Registration Tab"):
#                     st.session_state.current_tab = "🎨 Artwork Registration"
#                     st.rerun()
#                 st.stop()
                
#             # Debug info in demo mode
#             if DEMO_MODE:
#                 with st.expander("🔍 Mock System State (Debug)"):
#                     st.write(f"Token count: {mock_system.token_count}")
#                     st.write(f"Artworks: {len(mock_system.artworks)}")
#                     st.write(f"Licenses: {len(mock_system.licenses)}")
                    
#         except Exception as e:
#             st.error(f"🔴 Error checking artwork registry: {str(e)}")
#             st.stop()        

#         # Check for registered artworks
#         try:
#             token_count = registry.functions.getCurrentTokenId().call()
#             if token_count == 0:
#                 st.warning("No artworks registered yet. Please register an artwork first.")
#                 if st.button("⏩ Go to Registration Tab"):
#                     st.session_state.current_tab = "🎨 Artwork Registration"
#                     st.rerun()  # Changed from experimental_rerun()
#                 st.stop()
#         except Exception as e:
#             st.error(f"🔴 Error checking artwork registry: {str(e)}")
#             st.stop()

#         col1, col2 = st.columns(2)
        
#         # Grant License Column
#         with col1:
#             st.subheader("🟢 Grant License")
#             with st.form("grant_license_form"):
#                 token_id = st.number_input(
#                     "Artwork Token ID",
#                     min_value=0,
#                     max_value=token_count-1,
#                     value=0,
#                     step=1,
#                     help="ID of the artwork to license"
#                 )
                
#                 st.markdown("**Licensee Address**")
#                 licensee = account_selector("Select Licensee", accounts, default_index=1)
                
#                 duration_days = st.number_input(
#                     "Duration (days)",
#                     min_value=1,
#                     value=30,
#                     step=1,
#                     help="License duration in days"
#                 )
                
#                 license_type = st.selectbox(
#                     "License Type",
#                     ["PERSONAL", "COMMERCIAL", "EXCLUSIVE"],
#                     index=0,
#                     help="Type of usage rights"
#                 )
                
#                 terms_hash = st.text_input(
#                     "Terms IPFS Hash",
#                     "ipfs://Qm...",
#                     help="Hash of license terms document"
#                 )
                
#                 if st.form_submit_button("✍️ Grant License"):
#                     with st.spinner("⏳ Processing license grant..."):
#                         try:
#                             artwork_info = registry.functions.getArtworkInfo(token_id).call()
                            
#                             tx_dict = {
#                                 'from': selected_account,
#                                 'gas': 250000,
#                                 'gasPrice': w3.to_wei('50', 'gwei'),
#                                 'nonce': w3.eth.get_transaction_count(selected_account)
#                             }
                            
#                             license_type_index = ["PERSONAL", "COMMERCIAL", "EXCLUSIVE"].index(license_type)
                            
#                             tx_hash = licensing.functions.grantLicense(
#                                 token_id,
#                                 licensee,
#                                 duration_days,
#                                 terms_hash,
#                                 license_type_index
#                             ).transact(tx_dict)
                            
#                             receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                            
#                             st.success("✅ License Granted Successfully!")
#                             with st.expander("📄 License Details", expanded=True):
#                                 cols = st.columns(2)
#                                 cols[0].write(f"**Artwork ID:** {token_id}")
#                                 cols[1].write(f"**Licensee:** `{licensee}`")
#                                 cols[0].write(f"**Duration:** {duration_days} days")
#                                 cols[1].write(f"**Type:** {license_type}")
#                                 st.write(f"**Terms Hash:** `{terms_hash}`")
#                                 st.write(f"**TX Hash:** `{tx_hash.hex()}`")
                                
#                         except Exception as e:
#                             st.error(f"❌ Failed to grant license: {str(e)}")
#                             if "Not owner" in str(e):
#                                 st.error("⚠️ You must be the artwork owner")
#                             elif "Nonexistent token" in str(e):
#                                 st.error("⚠️ Artwork doesn't exist")

#         # Revoke License Column
#         with col2:
#             st.subheader("🔴 Revoke License")
#             with st.form("revoke_license_form"):
#                 revoke_token_id = st.number_input(
#                     "Artwork Token ID",
#                     min_value=0,
#                     max_value=token_count-1,
#                     value=0,
#                     step=1,
#                     help="ID of licensed artwork"
#                 )
                
#                 st.markdown("**Licensee Address**")
#                 revoke_licensee = account_selector("Select Licensee", accounts, default_index=1)
                
#                 if st.form_submit_button("🗑️ Revoke License"):
#                     with st.spinner("⏳ Processing revocation..."):
#                         try:
#                             tx_dict = {
#                                 'from': selected_account,
#                                 'gas': 150000,
#                                 'gasPrice': w3.to_wei('50', 'gwei'),
#                                 'nonce': w3.eth.get_transaction_count(selected_account)
#                             }
                            
#                             tx_hash = licensing.functions.revokeLicense(
#                                 revoke_token_id,
#                                 revoke_licensee
#                             ).transact(tx_dict)
                            
#                             receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                            
#                             st.success("✅ License Revoked Successfully!")
#                             with st.expander("📄 Revocation Details"):
#                                 cols = st.columns(2)
#                                 cols[0].write(f"**Artwork ID:** {revoke_token_id}")
#                                 cols[1].write(f"**Licensee:** `{revoke_licensee}`")
#                                 st.write(f"**TX Hash:** `{tx_hash.hex()}`")
#                                 st.write(f"**Gas Used:** {receipt['gasUsed']}")
                                
#                         except Exception as e:
#                             st.error(f"❌ Failed to revoke license: {str(e)}")
#                             if "Not owner" in str(e):
#                                 st.error("⚠️ You must be the artwork owner")
#                             elif "License not active" in str(e):
#                                 st.error("⚠️ License already inactive")

#     with tab3:
#         st.header("Royalty Management")
        
#         # First check if we have any artworks
#         try:
#             token_count = registry.functions.getCurrentTokenId().call()
#             if token_count == 0:
#                 st.warning("No artworks registered yet. Register an artwork first.")
#                 st.stop()
#         except Exception as e:
#             st.error(f"Couldn't check artwork count: {str(e)}")
#             st.stop()

#         st.subheader("Simulate Artwork Sale")
#         sale_type = st.radio("Sale Type", ["Primary Sale", "Secondary Sale"])
        
#         with st.form("simulate_sale_form"):
#             token_id = st.number_input("Token ID", min_value=0, max_value=token_count-1, step=1)
            
#             if sale_type == "Primary Sale":
#                 buyer = account_selector("Buyer Address", accounts, default_index=1)
#                 sale_price = st.number_input("Sale Price (in ETH)", min_value=0.1, value=1.0, step=0.1)
#                 sale_price_wei = w3.to_wei(sale_price, 'ether')
                
#                 if st.form_submit_button("Simulate Primary Sale"):
#                     try:
#                         # Get artwork info
#                         creator, metadata, royalty_percent, is_licensed = registry.functions.getArtworkInfo(token_id).call()
                        
#                         platform_fee = sale_price_wei // 20  # 5%
#                         creator_amount = sale_price_wei - platform_fee
                        
#                         st.info(f"**Creator:** {creator}")
#                         st.info(f"**Royalty Percentage:** {royalty_percent}%")
#                         st.success(f"**Creator Receives:** {w3.from_wei(creator_amount, 'ether'):.4f} ETH")
#                         st.success(f"**Platform Fee:** {w3.from_wei(platform_fee, 'ether'):.4f} ETH")
                        
#                     except Exception as e:
#                         st.error(f"Simulation failed: {str(e)}")
            
#             else:  # Secondary Sale
#                 seller = account_selector("Seller Address", accounts, default_index=1)
#                 sale_price = st.number_input("Sale Price (in ETH)", min_value=0.1, value=1.0, step=0.1)
#                 sale_price_wei = w3.to_wei(sale_price, 'ether')
                
#                 if st.form_submit_button("Simulate Secondary Sale"):
#                     try:
#                         # Get artwork info
#                         creator, metadata, royalty_percent, is_licensed = registry.functions.getArtworkInfo(token_id).call()
                        
#                         royalty_amount = (sale_price_wei * royalty_percent) // 100
#                         seller_amount = sale_price_wei - royalty_amount
                        
#                         st.info(f"**Creator:** {creator}")
#                         st.info(f"**Royalty Percentage:** {royalty_percent}%")
#                         st.success(f"**Royalty Amount:** {w3.from_wei(royalty_amount, 'ether'):.4f} ETH")
#                         st.success(f"**Seller Receives:** {w3.from_wei(seller_amount, 'ether'):.4f} ETH")
                        
#                     except Exception as e:
#                         st.error(f"Simulation failed: {str(e)}")

#     with tab4:
#         st.header("Artwork Explorer")
        
#         try:
#             token_count = registry.functions.getCurrentTokenId().call()
#             artworks = []
            
#             for token_id in range(token_count):
#                 try:
#                     owner = registry.functions.ownerOf(token_id).call()
#                     artwork_info = registry.functions.getArtworkInfo(token_id).call()
                    
#                     artworks.append({
#                         'token_id': token_id,
#                         'owner': owner,
#                         'creator': artwork_info[0],
#                         'metadataURI': artwork_info[1],
#                         'royaltyPercentage': artwork_info[2],
#                         'isLicensed': artwork_info[3]
#                     })
#                 except Exception as e:
#                     continue
                    
#             if not artworks:
#                 st.info("No artworks registered yet")
#             else:
#                 for artwork in artworks:
#                     with st.expander(f"Artwork #{artwork['token_id']}"):
#                         st.write(f"**Owner:** `{artwork['owner']}`")
#                         st.write(f"**Creator:** `{artwork['creator']}`")
#                         st.write(f"**Metadata URI:** `{artwork['metadataURI']}`")
#                         st.write(f"**Royalty Percentage:** `{artwork['royaltyPercentage']}%`")
#                         st.write(f"**Licensed:** `{'Yes' if artwork['isLicensed'] else 'No'}`")
                        
#         except Exception as e:
#             st.error(f"Error scanning artworks: {str(e)}")

# if __name__ == "__main__":
#     main()


import streamlit as st
import json
from web3 import Web3
from pathlib import Path
import os
from datetime import datetime, timedelta
import logging
import hashlib
import time
import subprocess

# Set page configuration
st.set_page_config(
    page_title="Artwork DRM System",
    page_icon="🎨",
    layout="wide"
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper functions
def format_accounts(accounts):
    formatted = []
    for i, account in enumerate(accounts):
        if DEMO_MODE:
            balance = mock_system.balances.get(account, 0)
        else:
            balance = w3.eth.get_balance(account)
        eth_balance = w3.from_wei(balance, 'ether')
        formatted.append(f"Account #{i+1}: {account[:6]}...{account[-4:]} (Balance: {eth_balance:.4f} ETH)")
    return formatted

def account_selector(label, accounts, default_index=0):
    account_options = format_accounts(accounts)
    account_mapping = {
        option: Web3.to_checksum_address(account) 
        for option, account in zip(account_options, accounts)
    }
    selected_option = st.selectbox(label, options=account_options, index=default_index)
    return account_mapping[selected_option]

def wei_input(label, default_value=0):
    wei_str = st.text_input(label, value=str(default_value))
    try:
        return int(wei_str)
    except ValueError:
        st.error("Please enter a valid integer value")
        return 0

DEMO_MODE = True  # Set to False for real blockchain connection

# --- Mock Data Storage ---
class MockArtworkSystem:
    def __init__(self):
        self.artworks = []
        self.token_count = 0
        self.licenses = []
        self.license_counter = 0
        # Store accounts as strings
        self.accounts = [
            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", 
            "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
            "0x90F79bf6EB2c4f870365E785982E1f101E93b906"
        ]
        # Store balances as integers
        self.balances = {
            acc: 100000000000000000000 for acc in self.accounts  # 100 ETH in wei
        }
    
    def register_artwork(self, *args):
        """Handle all calling patterns (2 or 3 args)"""
        # Web3 contract calls pass the transaction dict as first arg
        if len(args) == 4:  # tx_dict, owner, metadata, royalty
            _, owner, metadata, royalty = args
        elif len(args) == 3:  # owner, metadata, royalty
            owner, metadata, royalty = args
        elif len(args) == 2:  # metadata, royalty
            metadata, royalty = args
            owner = self.accounts[0]  # Default to first account
        else:
            raise ValueError("Invalid number of arguments")

        # Convert to basic types
        owner = str(Web3.to_checksum_address(owner))
        metadata = str(metadata)
        royalty = int(royalty)

        if royalty > 20:
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

    def getArtworkInfo(self, *args):
        """Handle both direct calls (token_id) and web3 calls (tx_dict, token_id)"""
        # Extract token_id from args (handles both patterns)
        token_id = args[-1] if args else 0
        
        if token_id >= len(self.artworks):
            raise ValueError("Nonexistent token")
        art = self.artworks[token_id]
        return (
            str(art['creator']),
            str(art['metadata']),
            int(art['royalty']),
            bool(art['isLicensed'])
        )

    def transfer_eth(self, from_account, to_account, amount):
        """Transfer ETH between demo accounts"""
        from_acc = Web3.to_checksum_address(from_account)
        to_acc = Web3.to_checksum_address(to_account)
        
        if from_acc not in self.balances or to_acc not in self.balances:
            raise ValueError("Account does not exist")
        if self.balances[from_acc] < amount:
            raise ValueError("Insufficient balance")
            
        self.balances[from_acc] -= amount
        self.balances[to_acc] += amount
        return True

    def grant_license(self, *args):
        if len(args) == 5:
            token_id, licensee, duration_days, terms_hash, license_type = args
        elif len(args) == 6:
            _, token_id, licensee, duration_days, terms_hash, license_type = args
        
        licensee = Web3.to_checksum_address(licensee)
        
        if token_id >= len(self.artworks):
            raise ValueError("Artwork does not exist")
            
        artwork_owner = self.artworks[token_id]['owner']
        license_fee = Web3.to_wei(0.1, 'ether')
        self.transfer_eth(licensee, artwork_owner, license_fee)
        
        license_data = {
            'licenseId': int(self.license_counter),
            'tokenId': int(token_id),
            'licensee': licensee,
            'startDate': int(datetime.now().timestamp()),
            'endDate': int((datetime.now() + timedelta(days=duration_days)).timestamp()),
            'termsHash': terms_hash,
            'licenseType': int(license_type),
            'isActive': True,
            'feePaid': int(license_fee)
        }
        self.licenses.append(license_data)
        self.artworks[token_id]['isLicensed'] = True
        self.license_counter += 1
        return self.license_counter - 1
       
    # Make sure this matches the real contract exactly
    def getCurrentTokenId(self):
        return self.token_count
        
    # Keep this for backward compatibility
    def get_current_token_id(self):
        return self.token_count

    def ownerOf(self, token_id):
        """Handle both direct and web3 call patterns"""
        if isinstance(token_id, tuple):  # Handle web3 call pattern
            _, token_id = token_id
        if token_id >= len(self.artworks):
            raise ValueError("Nonexistent token")
        return str(self.artworks[token_id]['owner'])  # Ensure string

    def get_license_count(self, token_id):
        return len([l for l in self.licenses if l['tokenId'] == token_id])

    def get_license_details(self, token_id, index):
        licenses = [l for l in self.licenses if l['tokenId'] == token_id]
        if not licenses or index >= len(licenses):
            raise ValueError("License not found")
        license = licenses[index]
        return (
            license['licensee'],
            int(license['startDate'].timestamp()),
            int(license['endDate'].timestamp()),
            license['termsHash'],
            license['licenseType'],
            license['isActive']
        )
    
    def revoke_license(self, *args):
        """Handle all calling patterns (tx_dict, token_id, licensee)"""
        # Web3 contract calls pass the transaction dict as first arg
        if len(args) == 3:  # tx_dict, token_id, licensee
            _, token_id, licensee = args
        elif len(args) == 2:  # token_id, licensee
            token_id, licensee = args
        else:
            raise ValueError(f"Invalid number of arguments: {len(args)}")

        licensee = Web3.to_checksum_address(licensee)
        
        for license_data in self.licenses:
            if license_data['tokenId'] == token_id and license_data['licensee'] == licensee:
                license_data['isActive'] = False
                break
        
        # Check if any active licenses remain
        has_active_license = any(
            l['tokenId'] == token_id and l['isActive']
            for l in self.licenses
        )
        self.artworks[token_id]['isLicensed'] = has_active_license
    
    def get_artworks(self):
        """Return all registered artworks in a standardized format"""
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
        """Transfer artwork ownership in demo mode"""
        new_owner = Web3.to_checksum_address(new_owner)
        if token_id >= len(self.artworks):
            raise ValueError("Artwork does not exist")
        self.artworks[token_id]['owner'] = new_owner
        return True

# Replace the mock_system initialization with this:
if 'mock_system' not in st.session_state:
    st.session_state.mock_system = MockArtworkSystem()
mock_system = st.session_state.mock_system


class MockContractFunction:
    def __init__(self, callback, estimate_gas=200000):
        self.callback = callback
        self.estimate_gas_value = estimate_gas
        self._args = None
        self._kwargs = None
        
    def estimate_gas(self, tx_dict):
        return int(self.estimate_gas_value)
        
    def __call__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        return self
        
    def call(self, *args, **kwargs):
        result = self.callback(*(self._args or ()), **(self._kwargs or {}))
        # Convert all results to basic types
        if isinstance(result, tuple):
            return tuple(self._convert_to_basic_type(v) for v in result)
        return self._convert_to_basic_type(result)
        
    def _convert_to_basic_type(self, value):
        """Convert any value to a JSON-serializable type"""
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, bytes):
            return value.hex()
        elif hasattr(value, 'hex'):  # For hash objects
            return value.hex()
        return str(value)  # Fallback to string representation
        
    def transact(self, tx_dict):
        mock_hash = hashlib.sha256(f"tx_{time.time()}".encode()).hexdigest()
        self.callback(*(self._args or ()), **(self._kwargs or {}))

        # Return a mock transaction hash object
        class MockTxHash:
            def __init__(self, hash_str):
                self.hash_str = hash_str
            def hex(self):
                return self.hash_str

        return MockTxHash(f"0x{mock_hash}")
class MockContract:
    def __init__(self, contract_type):
        mock_system = st.session_state.mock_system
        
        if contract_type == "registry":
            self.functions = type('', (), {
                'registerArtwork': self._create_function(
                    lambda *args: mock_system.register_artwork(*args),
                    estimate_gas=200000
                ),
                'getCurrentTokenId': self._create_getter(mock_system.getCurrentTokenId),
                'getArtworkInfo': self._create_function(
                    lambda *args: mock_system.getArtworkInfo(*args)  # Pass all args
                ),
                'ownerOf': self._create_function(
                    lambda *args: mock_system.ownerOf(*args)  # Pass all args
                )
            })()

        elif contract_type == "licensing":
            self.functions = type('', (), {
                'grantLicense': self._create_function(
                    lambda *args: mock_system.grant_license(*args),
                    estimate_gas=150000
                ),
                'revokeLicense': self._create_function(
                    lambda *args: mock_system.revoke_license(*args),  # Pass all args
                    estimate_gas=50000
                ),
                'getLicenseCount': self._create_function(
                    lambda token_id: len([l for l in mock_system.licenses 
                                       if l['tokenId'] == token_id])
                ),
                'getLicenseDetails': self._create_function(
                    lambda token_id, index: mock_system.get_license_details(token_id, index)
                )
            })()

    def _create_function(self, callback, estimate_gas=21000):
        def wrapper(*args, **kwargs):
            return MockContractFunction(callback, estimate_gas=estimate_gas)(*args, **kwargs)
        return wrapper
        
    def _create_getter(self, callback):
        def wrapper(*args, **kwargs):
            return MockContractFunction(lambda: callback())
        return wrapper

class MockEth:
    def __init__(self):
        self.chain_id = 31337
        
    def get_balance(self, account):
        return mock_system.balances.get(account, 0)
        
    def get_transaction_count(self, account):
        return 0
        
    def wait_for_transaction_receipt(self, tx_hash):
        return {
            'blockNumber': 1,
            'gasUsed': 21000,
            'transactionHash': tx_hash.hex() if hasattr(tx_hash, 'hex') else str(tx_hash)
        }
        
    @property
    def accounts(self):
        return mock_system.accounts
        
    def contract(self, address=None, abi=None):
        if "ArtworkRegistry" in str(abi):
            return MockContract("registry")
        else:
            return MockContract("licensing")

class MockWeb3:
    def __init__(self):
        self.eth = MockEth()
        self.from_wei = Web3.from_wei
        self.to_wei = Web3.to_wei
        
    def is_connected(self):
        return True

# --- Web3 Initialization ---
if DEMO_MODE:
    st.warning("DEMO MODE: Using simulated blockchain")
    w3 = MockWeb3()
else:
    # Your original Web3 connection code
    try:
        local_provider = Web3.HTTPProvider('http://127.0.0.1:8545', request_kwargs={'timeout': 60})
        w3 = Web3(local_provider)
        # Check connection
        if not w3.is_connected():
            # Fall back to Mumbai testnet if local node not available
            provider_url = os.getenv(
                'WEB3_PROVIDER_URL',
                'https://rpc-mumbai.maticvigil.com'  # Free Polygon Mumbai testnet
            )
            w3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={'timeout': 60}))
            
            if not w3.is_connected():
                st.error("""
                    ⚠️ Could not connect to any Ethereum node. Please ensure:
                    1. For local development: Hardhat node is running (npx hardhat node)
                    2. For production: You have internet access to Mumbai testnet
                    3. The chainId matches your environment
                """)
                if st.button("Try to reconnect"):
                    st.experimental_rerun()
                st.stop()
        
        # Display connection info
        chain_id = w3.eth.chain_id
        if chain_id == 31337:
            st.success("✅ Connected to local Hardhat node (ChainID: 31337)")
        elif chain_id == 80001:
            st.success("✅ Connected to Polygon Mumbai testnet (ChainID: 80001)")
        else:
            st.warning(f"⚠️ Connected to unknown network (ChainID: {chain_id})")
            
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        st.stop()

# Modify the load_contracts function to handle fallback without modifying DEMO_MODE
def load_contracts():
    global DEMO_MODE  # Add this line to allow modification of the global variable
    
    if DEMO_MODE:
        # These ABIs can be empty - just need the contract names
        registry_abi = '{"contractName":"ArtworkRegistry"}'
        licensing_abi = '{"contractName":"ArtworkLicensing"}'
        
        return {
            'registry': w3.eth.contract(abi=registry_abi),
            'licensing': w3.eth.contract(abi=licensing_abi)
        }
    else:
        try:
            # First try to load existing contracts
            if not os.path.exists('contract-addresses.json'):
                st.warning("Contracts not deployed - falling back to demo mode behavior")
                # Instead of modifying DEMO_MODE, just return demo contracts
                registry_abi = '{"contractName":"ArtworkRegistry"}'
                licensing_abi = '{"contractName":"ArtworkLicensing"}'
                return {
                    'registry': w3.eth.contract(abi=registry_abi),
                    'licensing': w3.eth.contract(abi=licensing_abi)
                }
            
            with open('contract-addresses.json') as f:
                addresses = json.load(f)
            
            # Load ABIs with error handling
            @st.cache_resource
            def load_abi(name):
                try:
                    path = Path(f'./artifacts/contracts/{name}.sol/{name}.json')
                    if not path.exists():
                        raise FileNotFoundError(f"ABI file not found at {path}")
                    with open(path) as f:
                        return json.load(f)['abi']
                except Exception as e:
                    st.error(f"Error loading {name} ABI: {str(e)}")
                    st.stop()

            # Initialize contracts
            registry = w3.eth.contract(
                address=addresses['registry'],
                abi=load_abi('ArtworkRegistry')
            )
            
            licensing = w3.eth.contract(
                address=addresses['licensing'],
                abi=load_abi('ArtworkLicensing')
            )

            return {
                'registry': registry,
                'licensing': licensing
            }

        except Exception as e:
            st.error(f"Contract loading failed: {str(e)} - falling back to demo mode")
            # Instead of modifying DEMO_MODE, just return demo contracts
            registry_abi = '{"contractName":"ArtworkRegistry"}'
            licensing_abi = '{"contractName":"ArtworkLicensing"}'
            return {
                'registry': w3.eth.contract(abi=registry_abi),
                'licensing': w3.eth.contract(abi=licensing_abi)
            }

def add_demo_toggle():
    """Add this function to allow runtime demo mode switching"""
    global DEMO_MODE  # Add this to modify the global variable
    
    with st.sidebar:
        st.markdown("---")
        st.subheader("⚙️ Configuration")
        
        demo_mode = st.checkbox(
            "Enable Demo Mode", 
            value=DEMO_MODE,
            help="Switch between demo simulation and real blockchain"
        )
        
        if demo_mode != DEMO_MODE:
            DEMO_MODE = demo_mode  # Update the global variable
            st.warning("⚠️ Mode change requires app restart")
            if st.button("🔄 Restart App"):
                st.rerun()
                
        return DEMO_MODE

def main():
    st.title("🎨 Artwork DRM System")
    
    # FIX 3: Add clear demo mode indicator
    if DEMO_MODE:
        st.warning("🚀 **DEMO MODE ACTIVE** - Using simulated blockchain for demonstration")
        with st.expander("ℹ️ Demo Mode Information"):
            st.info("""
            **Demo Mode Features:**
            - ✅ Simulated blockchain transactions
            - ✅ No real gas costs
            - ✅ Instant confirmations
            - ✅ All features available for testing
            
            **Note:** This is for demonstration only. No real blockchain transactions occur.
            """)
            if mock_system.artworks:
                st.write("Artwork Owner:", mock_system.artworks[0]['owner'])
                st.write("Account Balances:", mock_system.balances)
            else:
                st.write("No artworks registered yet")
            for i, account in enumerate(mock_system.accounts):
                balance = w3.from_wei(mock_system.balances[account], 'ether')
                st.write(f"Account #{i+1}: {account} - Balance: {balance:.4f} ETH")
    else:
        st.success("🔗 **LIVE MODE** - Connected to real blockchain")

    # Load contracts
    contracts = load_contracts()
    registry = contracts['registry']
    licensing = contracts['licensing']

    # Get Ethereum accounts
    try:
        accounts = w3.eth.accounts
        if not accounts:
            st.error("No accounts found on the Ethereum node.")
            st.stop()
    except Exception as e:
        st.error(f"Error fetching accounts: {str(e)}")
        st.stop()

    # Sidebar with account info
    with st.sidebar:
        st.header("Account Information")
        selected_account = account_selector("Select Account", accounts)
        balance = w3.from_wei(w3.eth.get_balance(selected_account), 'ether')
        st.info(f"Account: {selected_account}")
        st.info(f"Balance: {balance:.4f} ETH")


        if DEMO_MODE and st.button("🛠️ Debug Mock System"):
            st.write("### Mock System State")
            
            # Create a serializable version of the state
            debug_state = {
                "token_count": int(mock_system.token_count),
                "artworks": [{
                    'owner': str(art['owner']),
                    'creator': str(art['creator']),
                    'metadata': str(art['metadata']),
                    'royalty': int(art['royalty']),
                    'isLicensed': bool(art['isLicensed']),
                    'tokenURI': str(art['tokenURI'])
                } for art in mock_system.artworks],
                "licenses": mock_system.licenses,
                "balances": {str(k): str(v) for k, v in mock_system.balances.items()}
            }
            
            st.json(debug_state)

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎨 Artwork Registration", 
        "📄 Licensing", 
        "💰 Royalties", 
        "🔍 View Artworks"
    ])

    with tab1:
        st.header("Register New Artwork")
        with st.form("register_form"):
            metadata = st.text_input("IPFS Hash", "ipfs://Qm...", 
                                help="Enter the IPFS CID of your artwork metadata",
                                max_chars=100)
            royalty = st.slider("Royalty Percentage", 0, 20, 10,
                            help="Percentage creator earns on secondary sales (0-20%)")
            
            if st.form_submit_button("Register Artwork"):
                try:
                    # Convert inputs to proper types
                    metadata = str(metadata).strip()
                    royalty = int(royalty)
                    account = Web3.to_checksum_address(selected_account)
                    
                    # Input validation
                    if not metadata.startswith("ipfs://"):
                        st.error("Metadata URI must start with 'ipfs://'")
                        st.stop()
                    
                    if royalty > 20:
                        st.error("Royalty cannot exceed 20%")
                        st.stop()

                    # Get current state
                    token_count_before = registry.functions.getCurrentTokenId().call()
                    
                    # Create contract call - works for both demo and live modes
                    register_func = registry.functions.registerArtwork(
                        account,    # owner address
                        metadata,   # metadata URI
                        royalty     # royalty percentage
                    )

                    # Gas estimation
                    gas_estimate = 300000  # Default value
                    try:
                        with st.spinner("Estimating gas requirements..."):
                            gas_estimate = register_func.estimate_gas({
                                'from': account,
                                'nonce': w3.eth.get_transaction_count(account)
                            })
                            st.success(f"Gas estimate: {gas_estimate} wei")
                    except Exception as e:
                        st.warning(f"Gas estimation failed, using default: {str(e)}")

                    # Prepare transaction
                    tx_dict = {
                        'from': account,
                        'gas': gas_estimate,
                        'gasPrice': w3.to_wei('50', 'gwei'),
                        'nonce': w3.eth.get_transaction_count(account)
                    }

                    # Execute transaction
                    with st.spinner("Processing blockchain transaction..."):
                        tx_hash = register_func.transact(tx_dict)
                        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                    # Verification
                    token_count_after = registry.functions.getCurrentTokenId().call()

                    if token_count_after > token_count_before:
                        new_token_id = token_count_after - 1
                        try:
                            artwork_info = registry.functions.getArtworkInfo(new_token_id).call()
                            if len(artwork_info) == 4:
                                creator, stored_metadata, stored_royalty, is_licensed = artwork_info
                                
                                display_info = {
                                    'token_id': new_token_id,
                                    'creator': creator,
                                    'metadata': stored_metadata,
                                    'royalty': stored_royalty,
                                    'is_licensed': is_licensed,
                                    'tx_hash': tx_hash.hex(),
                                    'block': receipt['blockNumber'],
                                    'gas_used': receipt['gasUsed']
                                }
                                
                                st.success("### ✅ Artwork Successfully Registered!")
                                st.balloons()
                                
                                with st.expander("Registration Details", expanded=True):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write("**Artwork Information**")
                                        st.write(f"- Token ID: `{display_info['token_id']}`")
                                        st.write(f"- Creator: `{display_info['creator']}`")
                                        st.write(f"- Royalty: `{display_info['royalty']}%`")
                                        st.write(f"- Metadata: `{display_info['metadata']}`")
                                    
                                    with col2:
                                        st.write("**Transaction Details**")
                                        st.write(f"- TX Hash: `{display_info['tx_hash']}`")
                                        st.write(f"- Block: `{display_info['block']}`")
                                        st.write(f"- Gas Used: `{display_info['gas_used']}`")
                                        st.write(f"- Status: `Success`")
                            
                            else:
                                st.warning(f"Artwork registered (Token ID: {new_token_id}) but got unexpected response format")
                        
                        except Exception as e:
                            st.error(f"Verification failed: {str(e)}")
                            st.warning(f"Artwork registered (Token ID: {new_token_id}) but details couldn't be verified")

                except Exception as e:
                    st.error("### 🔥 Registration Failed")
                    error_type = type(e).__name__
                    error_msg = str(e)
                    
                    st.write(f"**Error Type:** {error_type}")
                    st.write(f"**Message:** {error_msg}")
                    
                    # Enhanced error diagnostics
                    debug_info = {
                        'error': {
                            'type': error_type,
                            'message': error_msg
                        },
                        'input': {
                            'metadata': metadata,
                            'royalty': royalty,
                            'account': account
                        },
                        'system': {
                            'demo_mode': DEMO_MODE,
                            'timestamp': int(datetime.now().timestamp()),
                            'token_count': mock_system.token_count if DEMO_MODE else token_count_before,
                            'balances': {str(k): str(v) for k, v in mock_system.balances.items()} if DEMO_MODE else None
                        }
                    }
                    
                    with st.expander("Debug Information"):
                        st.json(debug_info)
                    
                    if "revert" in error_msg.lower():
                        st.error("**Possible Solutions:**")
                        st.error("- Check royalty percentage (max 20%)")
                        st.error("- Verify metadata format starts with 'ipfs://'")
                        st.error("- Ensure account has sufficient ETH balance")
    with tab2:
        st.header("🎫 Artwork Licensing")
        
        # Enhanced artwork check with demo mode handling
        try:
            if DEMO_MODE:
                token_count = mock_system.token_count
                st.sidebar.info(f"🎯 Demo Mode: {token_count} mock artworks available")
            else:
                token_count = registry.functions.getCurrentTokenId().call()
                
            if token_count == 0:
                st.warning("No artworks registered yet. Please register an artwork first.")
                if st.button("⏩ Go to Registration Tab"):
                    st.session_state.current_tab = "🎨 Artwork Registration"
                    st.rerun()
                st.stop()
                
            # Debug info in demo mode
            if DEMO_MODE:
                with st.expander("🔍 Mock System State (Debug)"):
                    st.write(f"Token count: {mock_system.token_count}")
                    st.write(f"Artworks: {len(mock_system.artworks)}")
                    st.write(f"Licenses: {len(mock_system.licenses)}")
                    
        except Exception as e:
            st.error(f"🔴 Error checking artwork registry: {str(e)}")
            st.stop()        

        # Check for registered artworks
        try:
            token_count = registry.functions.getCurrentTokenId().call()
            if token_count == 0:
                st.warning("No artworks registered yet. Please register an artwork first.")
                if st.button("⏩ Go to Registration Tab"):
                    st.session_state.current_tab = "🎨 Artwork Registration"
                    st.rerun()  # Changed from experimental_rerun()
                st.stop()
        except Exception as e:
            st.error(f"🔴 Error checking artwork registry: {str(e)}")
            st.stop()

        col1, col2 = st.columns(2)
        
        # Grant License Column
        with col1:
            st.subheader("🟢 Grant License")
            with st.form("grant_license_form"):
                token_id = st.number_input(
                    "Artwork Token ID",
                    min_value=0,
                    max_value=token_count-1,
                    value=0,
                    step=1,
                    help="ID of the artwork to license"
                )
                
                st.markdown("**Licensee Address**")
                licensee = account_selector("Select Licensee", accounts, default_index=1)
                
                duration_days = st.number_input(
                    "Duration (days)",
                    min_value=1,
                    value=30,
                    step=1,
                    help="License duration in days"
                )
                
                license_type = st.selectbox(
                    "License Type",
                    ["PERSONAL", "COMMERCIAL", "EXCLUSIVE"],
                    index=0,
                    help="Type of usage rights"
                )
                
                terms_hash = st.text_input(
                    "Terms IPFS Hash",
                    "ipfs://Qm...",
                    help="Hash of license terms document"
                )
                
                if st.form_submit_button("✍️ Grant License"):
                    with st.spinner("⏳ Processing license grant..."):
                        try:
                            if licensee not in mock_system.accounts:
                                st.error("Invalid licensee address - use one of the demo accounts")
                                st.stop()
                            artwork_info = registry.functions.getArtworkInfo(token_id).call()
                            
                            tx_dict = {
                                'from': selected_account,
                                'gas': 250000,
                                'gasPrice': w3.to_wei('50', 'gwei'),
                                'nonce': w3.eth.get_transaction_count(selected_account)
                            }
                            
                            license_type_index = ["PERSONAL", "COMMERCIAL", "EXCLUSIVE"].index(license_type)
                            
                            tx_hash = licensing.functions.grantLicense(
                                token_id,
                                licensee,
                                duration_days,
                                terms_hash,
                                license_type_index
                            ).transact(tx_dict)
                            
                            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                            
                            st.success("✅ License Granted Successfully!")
                            with st.expander("📄 License Details", expanded=True):
                                cols = st.columns(2)
                                cols[0].write(f"**Artwork ID:** {token_id}")
                                cols[1].write(f"**Licensee:** `{licensee}`")
                                cols[0].write(f"**Duration:** {duration_days} days")
                                cols[1].write(f"**Type:** {license_type}")
                                st.write(f"**Terms Hash:** `{terms_hash}`")
                                st.write(f"**TX Hash:** `{tx_hash.hex()}`")
                                
                        except Exception as e:
                            st.error(f"❌ Failed to grant license: {str(e)}")
                            if "Not owner" in str(e):
                                st.error("⚠️ You must be the artwork owner")
                            elif "Nonexistent token" in str(e):
                                st.error("⚠️ Artwork doesn't exist")

        # Revoke License Column
        with col2:
            st.subheader("🔴 Revoke License")
            with st.form("revoke_license_form"):
                revoke_token_id = st.number_input(
                    "Artwork Token ID",
                    min_value=0,
                    max_value=token_count-1,
                    value=0,
                    step=1,
                    help="ID of licensed artwork"
                )
                
                st.markdown("**Licensee Address**")
                revoke_licensee = account_selector("Select Licensee", accounts, default_index=1)
                
                if st.form_submit_button("🗑️ Revoke License"):
                    with st.spinner("⏳ Processing revocation..."):
                        try:
                            tx_dict = {
                                'from': selected_account,
                                'gas': 150000,
                                'gasPrice': w3.to_wei('50', 'gwei'),
                                'nonce': w3.eth.get_transaction_count(selected_account)
                            }
                            
                            tx_hash = licensing.functions.revokeLicense(
                                revoke_token_id,
                                revoke_licensee
                            ).transact(tx_dict)
                            
                            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                            
                            st.success("✅ License Revoked Successfully!")
                            with st.expander("📄 Revocation Details"):
                                cols = st.columns(2)
                                cols[0].write(f"**Artwork ID:** {revoke_token_id}")
                                cols[1].write(f"**Licensee:** `{revoke_licensee}`")
                                st.write(f"**TX Hash:** `{tx_hash.hex()}`")
                                st.write(f"**Gas Used:** {receipt['gasUsed']}")
                                
                        except Exception as e:
                            st.error(f"❌ Failed to revoke license: {str(e)}")
                            if "Not owner" in str(e):
                                st.error("⚠️ You must be the artwork owner")
                            elif "License not active" in str(e):
                                st.error("⚠️ License already inactive")

    with tab3:
        st.header("Royalty Management")
        
        try:
            token_count = registry.functions.getCurrentTokenId().call()
            if token_count == 0:
                st.warning("No artworks registered yet. Register an artwork first.")
                st.stop()
        except Exception as e:
            st.error(f"Couldn't check artwork count: {str(e)}")
            st.stop()

        st.subheader("Simulate Artwork Sale")
        sale_type = st.radio("Sale Type", ["Primary Sale", "Secondary Sale"])
        
        with st.form("simulate_sale_form"):
            token_id = st.number_input("Token ID", min_value=0, max_value=token_count-1, step=1)
            
            if sale_type == "Primary Sale":
                buyer = account_selector("Buyer Address", accounts, default_index=1)
                sale_price = st.number_input("Sale Price (in ETH)", min_value=0.1, value=1.0, step=0.1)
                sale_price_wei = w3.to_wei(sale_price, 'ether')
                
                if st.form_submit_button("Simulate Primary Sale"):
                    try:
                        # Get artwork info
                        creator, metadata, royalty_percent, is_licensed = registry.functions.getArtworkInfo(token_id).call()
                        
                        platform_fee = sale_price_wei // 20  # 5%
                        creator_amount = sale_price_wei - platform_fee
                        
                        if DEMO_MODE:
                            # Actually transfer funds in demo mode
                            mock_system.transfer_eth(buyer, creator, creator_amount)
                            if platform_fee > 0:
                                mock_system.transfer_eth(buyer, mock_system.accounts[0], platform_fee)  # Platform gets fee
                            mock_system.transfer_ownership(token_id, buyer)
                        
                        st.info(f"**Creator:** {creator}")
                        st.info(f"**Royalty Percentage:** {royalty_percent}%")
                        st.success(f"**Creator Receives:** {w3.from_wei(creator_amount, 'ether'):.4f} ETH")
                        st.success(f"**Platform Fee:** {w3.from_wei(platform_fee, 'ether'):.4f} ETH")
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Simulation failed: {str(e)}")
            
            else:  # Secondary Sale
                seller = account_selector("Seller Address", accounts, default_index=1)
                buyer = account_selector("Buyer Address", accounts, default_index=2)
                sale_price = st.number_input("Sale Price (in ETH)", min_value=0.1, value=1.0, step=0.1)
                sale_price_wei = w3.to_wei(sale_price, 'ether')
                
                if st.form_submit_button("Simulate Secondary Sale"):
                    try:
                        # Get artwork info
                        creator, metadata, royalty_percent, is_licensed = registry.functions.getArtworkInfo(token_id).call()
                        
                        royalty_amount = (sale_price_wei * royalty_percent) // 100
                        seller_amount = sale_price_wei - royalty_amount
                        
                        if DEMO_MODE:
                            # Transfer funds between accounts
                            mock_system.transfer_eth(buyer, creator, royalty_amount)
                            mock_system.transfer_eth(buyer, seller, seller_amount)
                            mock_system.transfer_ownership(token_id, buyer)
                        
                        st.info(f"**Creator:** {creator}")
                        st.info(f"**Royalty Percentage:** {royalty_percent}%")
                        st.success(f"**Royalty Amount:** {w3.from_wei(royalty_amount, 'ether'):.4f} ETH")
                        st.success(f"**Seller Receives:** {w3.from_wei(seller_amount, 'ether'):.4f} ETH")
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Simulation failed: {str(e)}")

    # Finally, update tab4 to use the new get_artworks method:

    with tab4:
        st.header("Artwork Explorer")
        
        try:
            if DEMO_MODE:
                artworks = mock_system.get_artworks()
                token_count = len(artworks)
            else:
                token_count = registry.functions.getCurrentTokenId().call()
                artworks = []
                
                for token_id in range(token_count):
                    try:
                        owner = registry.functions.ownerOf(token_id).call()
                        artwork_info = registry.functions.getArtworkInfo(token_id).call()
                        
                        artworks.append({
                            'token_id': token_id,
                            'owner': owner,
                            'creator': artwork_info[0],
                            'metadataURI': artwork_info[1],
                            'royaltyPercentage': artwork_info[2],
                            'isLicensed': artwork_info[3]
                        })
                    except Exception as e:
                        continue
                        
            if not artworks:
                st.info("No artworks registered yet")
            else:
                for artwork in artworks:
                    with st.expander(f"Artwork #{artwork['token_id']}"):
                        st.write(f"**Owner:** `{artwork['owner']}`")
                        st.write(f"**Creator:** `{artwork['creator']}`")
                        st.write(f"**Metadata URI:** `{artwork['metadataURI']}`")
                        st.write(f"**Royalty Percentage:** `{artwork['royaltyPercentage']}%`")
                        st.write(f"**Licensed:** `{'Yes' if artwork['isLicensed'] else 'No'}`")
                        
        except Exception as e:
            st.error(f"Error scanning artworks: {str(e)}")

if __name__ == "__main__":
    main()