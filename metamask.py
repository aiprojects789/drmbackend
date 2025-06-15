import streamlit as st
import json
from web3 import Web3
from pathlib import Path
import os
from datetime import datetime, timedelta
import logging
import subprocess
from streamlit.components.v1 import html

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
if 'use_metamask' not in st.session_state:
    st.session_state.use_metamask = False
if 'mm_account' not in st.session_state:
    st.session_state.mm_account = None

# Helper functions
def format_accounts(accounts):
    formatted = []
    for i, account in enumerate(accounts):
        balance = w3.from_wei(w3.eth.get_balance(account), 'ether')
        formatted.append(f"Account #{i+1}: {account[:6]}...{account[-4:]} (Balance: {balance:.4f} ETH)")
    return formatted

def account_selector(label, accounts, default_index=0):
    account_options = format_accounts(accounts)
    account_mapping = {option: account for option, account in zip(account_options, accounts)}
    selected_option = st.selectbox(label, options=account_options, index=default_index)
    return account_mapping[selected_option]

def wei_input(label, default_value=0):
    wei_str = st.text_input(label, value=str(default_value))
    try:
        return int(wei_str)
    except ValueError:
        st.error("Please enter a valid integer value")
        return 0

# Initialize Web3
def init_web3():
    if st.session_state.use_metamask:
        return Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/e6f455108e5f490a972625f2b4f24e04'))
    else:
        return Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

w3 = init_web3()

# Load JS helper
def load_js(file_path):
    with open(file_path, 'r') as f:
        return f.read()

# MetaMask connection handler
def handle_metamask_connection():
    js_code = load_js("metamask.js")
    html(js_code)
    
    result = html(
        """
        <script>
        connectMetaMask().then(result => {
            Streamlit.setComponentValue(result);
        });
        </script>
        """,
        height=0,
    )
    
    if result and 'account' in result:
        st.session_state.mm_account = result['account']
        st.success(f"Connected: {result['account']}")
        st.experimental_rerun()
    elif result and 'error' in result:
        st.error(f"Error: {result['error']}")

# Transaction sender
def send_transaction(contract_function, args, value=0, from_account=None):
    if st.session_state.use_metamask:
        # MetaMask transaction
        tx_data = {
            'to': contract_function.address,
            'data': contract_function.encodeABI(args=args),
            'value': hex(value),
            'from': st.session_state.mm_account
        }
        
        js = f"""
        <script>
        async function sendTx() {{
            try {{
                const txHash = await window.ethereum.request({{
                    method: 'eth_sendTransaction',
                    params: [{tx_data}]
                }});
                Streamlit.setComponentValue(txHash);
            }} catch (error) {{
                Streamlit.setComponentValue("error:" + error.message);
            }}
        }}
        sendTx();
        </script>
        """
        html(js, height=0)
        
        result = st.empty()
        if hasattr(result, 'value') and isinstance(result.value, str):
            if result.value.startswith("error:"):
                st.error(result.value[6:])
                return None
            return result.value
        return None
    else:
        # Local transaction
        try:
            tx_hash = contract_function(*args).transact({
                'from': from_account,
                'value': value
            })
            return tx_hash
        except Exception as e:
            st.error(str(e))
            return None

def load_contracts():
    """Load and manage contracts with dual-network (local/Sepolia) support"""
    # Check contract deployment status
    if not os.path.exists('contract-addresses.json'):
        if not attempt_deployment():
            st.stop()

    try:
        with open('contract-addresses.json') as f:
            addresses = json.load(f)
        
        # Network configuration
        network_config = {
            'use_metamask': st.session_state.get('use_metamask', False),
            'name': 'sepolia' if st.session_state.get('use_metamask', False) else 'localhost',
            'chain_id': 11155111 if st.session_state.get('use_metamask', False) else 31337
        }

        # Verify network match
        current_chain_id = w3.eth.chain_id
        if current_chain_id != network_config['chain_id']:
            handle_network_mismatch(network_config, current_chain_id)
            st.stop()

        # Get network-specific addresses
        network_addresses = addresses.get(network_config['name'], {})
        if not network_addresses:
            handle_missing_network_deployment(network_config['name'])
            st.stop()

        # Initialize contracts
        return initialize_contracts(network_addresses)

    except Exception as e:
        st.error(f"Contract loading failed: {str(e)}")
        st.stop()

def attempt_deployment():
    """Attempt to deploy contracts and return success status"""
    try:
        with st.spinner("Initializing first-time deployment..."):
            if not deploy_contracts():
                st.error("Initial deployment failed")
                return False
            return True
    except Exception as e:
        st.error(f"Deployment attempt failed: {str(e)}")
        return False

def handle_network_mismatch(network_config, current_chain_id):
    """Guide user to correct network mismatch"""
    st.error(f"""
        ⚠️ Network Mismatch!
        Current: Chain ID {current_chain_id}
        Required: Chain ID {network_config['chain_id']} ({network_config['name']})
    """)
    if network_config['use_metamask']:
        st.info("Please switch to Sepolia network in MetaMask")
    else:
        st.info("Please connect to local Hardhat node (npx hardhat node)")

def handle_missing_network_deployment(network_name):
    """Handle case when contracts aren't deployed to required network"""
    st.error(f"No contracts deployed to {network_name} network")
    if st.button(f"🚀 Deploy to {network_name}"):
        deploy_contracts()

def initialize_contracts(network_addresses):
    """Initialize and verify contracts"""
    @st.cache_resource
    def load_abi(name):
        try:
            path = Path(f'./artifacts/contracts/{name}.sol/{name}.json')
            with open(path) as f:
                return json.load(f)['abi']
        except Exception as e:
            st.error(f"Error loading {name} ABI: {str(e)}")
            st.stop()

    try:
        # Initialize contracts
        registry = w3.eth.contract(
            address=network_addresses['registry'],
            abi=load_abi('ArtworkRegistry')
        )
        
        licensing = w3.eth.contract(
            address=network_addresses['licensing'],
            abi=load_abi('ArtworkLicensing')
        )

        # Verify contracts
        registry.functions.getCurrentTokenId().call()
        licensing.functions.getLicenseCount(0).call()  # Will error harmlessly if no licenses
        
        st.sidebar.success(f"Contracts loaded ({network_addresses['registry'][:6]}...)")
        return {'registry': registry, 'licensing': licensing}

    except Exception as e:
        st.error(f"Contract verification failed: {str(e)}")
        st.stop()

def deploy_contracts():
    """Handle contract deployment for current network"""
    try:
        network = "sepolia" if st.session_state.get('use_metamask', False) else "localhost"
        
        with st.spinner(f"Deploying to {network}..."):
            # Prepare deployment command
            npx_cmd = [
                "npx.cmd" if os.name == 'nt' else "npx",
                "hardhat",
                "run",
                "scripts/deploy_all.js",
                "--network",
                network
            ]
            
            # Execute deployment
            result = subprocess.run(
                npx_cmd,
                cwd=os.getcwd(),
                shell=True,
                capture_output=True,
                text=True
            )
            
            # Handle results
            if result.returncode == 0:
                update_address_file(network)
                st.success("✅ Deployment successful!")
                st.experimental_rerun()
                return True
            else:
                st.error(f"Deployment failed:\n{result.stderr}")
                return False
                
    except Exception as e:
        st.error(f"Deployment error: {str(e)}")
        return False

def update_address_file(network):
    """Update contract-addresses.json with proper structure"""
    try:
        with open('contract-addresses.json', 'r+') as f:
            addresses = json.load(f)
            
            # Preserve existing addresses while updating current network
            addresses[network] = {
                'registry': addresses.get('registry', ''),
                'licensing': addresses.get('licensing', '')
            }
            addresses['network'] = network
            
            f.seek(0)
            json.dump(addresses, f, indent=2)
            f.truncate()
    except Exception as e:
        st.error(f"Failed to update address file: {str(e)}")

def main():
    st.title("🎨 Artwork DRM System")

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
        metadata = st.text_input("IPFS Hash", "ipfs://Qm...")
        royalty = st.slider("Royalty %", 0, 20, 10)
        
        if st.form_submit_button("Register"):
            try:
                # Get current token count
                token_count_before = registry.functions.getCurrentTokenId().call()
                
                # Create transaction dictionary
                tx_dict = {
                    'from': selected_account,
                    'gas': 300000,
                    'gasPrice': w3.to_wei('50', 'gwei'),
                    'nonce': w3.eth.get_transaction_count(selected_account)
                }
                
                # Build function call
                register_func = registry.functions.registerArtwork(
                    selected_account,  # owner
                    metadata,
                    royalty
                )
                
                # Estimate gas (optional but recommended)
                try:
                    gas_estimate = register_func.estimate_gas(tx_dict)
                    tx_dict['gas'] = gas_estimate
                    st.info(f"Gas estimate: {gas_estimate}")
                except Exception as e:
                    st.warning(f"Gas estimation failed, using default: {str(e)}")
                
                # Send transaction
                tx_hash = register_func.transact(tx_dict)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                # Verify registration
                token_count_after = registry.functions.getCurrentTokenId().call()
                if token_count_after > token_count_before:
                    new_token_id = token_count_after - 1
                    st.success(f"✅ Artwork registered! Token ID: {new_token_id}")
                    st.json({
                        "Transaction hash": tx_hash.hex(),
                        "Block number": receipt['blockNumber'],
                        "Gas used": receipt['gasUsed']
                    })
                else:
                    st.error("Registration failed - token count didn't increase")
                    
            except Exception as e:
                st.error(f"Registration failed: {type(e).__name__}: {str(e)}")
                if "reverted" in str(e):
                    st.error("Transaction reverted - check contract requirements")
                if "nonce too low" in str(e):
                    st.error("Nonce error - try again")

    with tab2:
        st.header("Artwork Licensing")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Grant License")
            with st.form("grant_license_form"):
                token_id = st.number_input("Token ID", min_value=0, step=1, key="license_token_id")
                licensee = account_selector("Licensee Address", accounts, default_index=1)
                duration_days = st.number_input("License Duration (days)", min_value=1, value=30)
                license_type = st.selectbox("License Type", ["PERSONAL", "COMMERCIAL", "EXCLUSIVE"])
                terms_hash = st.text_input("License Terms (IPFS Hash)", "ipfs://Qm...")

                submitted = st.form_submit_button("Grant License")
                
                if submitted:
                    with st.spinner("Granting license..."):
                        try:
                            tx_hash = licensing.functions.grantLicense(
                                token_id,
                                licensee,
                                duration_days,
                                terms_hash,
                                ["PERSONAL", "COMMERCIAL", "EXCLUSIVE"].index(license_type)
                            ).transact({'from': selected_account})
                            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                            st.success("✅ License granted successfully!")
                            st.info(f"Transaction hash: {tx_hash.hex()}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        with col2:
            st.subheader("Revoke License")
            with st.form("revoke_license_form"):
                revoke_token_id = st.number_input("Token ID", min_value=0, step=1, key="revoke_token_id")
                revoke_licensee = account_selector("Licensee to Revoke", accounts, default_index=1)

                submitted = st.form_submit_button("Revoke License")
                
                if submitted:
                    with st.spinner("Revoking license..."):
                        try:
                            tx_hash = licensing.functions.revokeLicense(
                                revoke_token_id,
                                revoke_licensee
                            ).transact({'from': selected_account})
                            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                            st.success("✅ License revoked successfully!")
                            st.info(f"Transaction hash: {tx_hash.hex()}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

    with tab3:
     st.header("Royalty Management")
    
    # First check if we have any artworks
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
                    
                    st.info(f"**Creator:** {creator}")
                    st.info(f"**Royalty Percentage:** {royalty_percent}%")
                    st.success(f"**Creator Receives:** {w3.from_wei(creator_amount, 'ether'):.4f} ETH")
                    st.success(f"**Platform Fee:** {w3.from_wei(platform_fee, 'ether'):.4f} ETH")
                    
                except Exception as e:
                    st.error(f"Simulation failed: {str(e)}")
        
        else:  # Secondary Sale
            seller = account_selector("Seller Address", accounts, default_index=1)
            sale_price = st.number_input("Sale Price (in ETH)", min_value=0.1, value=1.0, step=0.1)
            sale_price_wei = w3.to_wei(sale_price, 'ether')
            
            if st.form_submit_button("Simulate Secondary Sale"):
                try:
                    # Get artwork info
                    creator, metadata, royalty_percent, is_licensed = registry.functions.getArtworkInfo(token_id).call()
                    
                    royalty_amount = (sale_price_wei * royalty_percent) // 100
                    seller_amount = sale_price_wei - royalty_amount
                    
                    st.info(f"**Creator:** {creator}")
                    st.info(f"**Royalty Percentage:** {royalty_percent}%")
                    st.success(f"**Royalty Amount:** {w3.from_wei(royalty_amount, 'ether'):.4f} ETH")
                    st.success(f"**Seller Receives:** {w3.from_wei(seller_amount, 'ether'):.4f} ETH")
                    
                except Exception as e:
                    st.error(f"Simulation failed: {str(e)}")

    with tab4:
        st.header("Artwork Explorer")
        
        # Display all artworks by checking ownerOf until failure
        st.info("Scanning blockchain for registered artworks...")
        artworks = []
        token_id = 0
        
        with st.spinner("Searching for artworks..."):
            while True:
                try:
                    owner = registry.functions.ownerOf(token_id).call()
                    artwork_info = registry.functions.getArtworkInfo(token_id).call()
                    
                    # Get license status
                    is_licensed = artwork_info[3]
                    license_info = None
                    
                    if is_licensed:
                        try:
                            # Get current licensee
                            licensee = licensing.functions.currentLicensee(token_id).call()
                            if licensee != "0x0000000000000000000000000000000000000000":
                                # Get license count
                                license_count = licensing.functions.getLicenseCount(token_id).call()
                                licenses = []
                                
                                for i in range(license_count):
                                    # Get each license's details
                                    license_details = licensing.functions.getLicenseDetails(token_id, i).call()
                                    licenses.append({
                                        'licensee': license_details[0],
                                        'startDate': datetime.fromtimestamp(license_details[1]),
                                        'endDate': datetime.fromtimestamp(license_details[2]),
                                        'termsHash': license_details[3],
                                        'licenseType': ["PERSONAL", "COMMERCIAL", "EXCLUSIVE"][license_details[4]],
                                        'isActive': license_details[5]
                                    })
                                
                                license_info = {
                                    'currentLicensee': licensee,
                                    'licenses': licenses
                                }
                        except Exception as e:
                            st.warning(f"Couldn't fetch license info for token {token_id}: {str(e)}")
                    
                    artworks.append({
                        'token_id': token_id,
                        'owner': owner,
                        'creator': artwork_info[0],
                        'metadataURI': artwork_info[1],
                        'royaltyPercentage': artwork_info[2],
                        'isLicensed': is_licensed,
                        'licenseInfo': license_info
                    })
                    token_id += 1
                except Exception as e:
                    if "reverted" in str(e) or "invalid opcode" in str(e):
                        break  # Reached end of artworks
                    st.warning(f"Error checking token {token_id}: {str(e)}")
                    break
        
        if not artworks:
            st.info("No artworks registered yet")
            st.stop()
        
        # Display all found artworks
        for artwork in artworks:
            with st.expander(f"Artwork #{artwork['token_id']}"):
                # Display basic info
                st.write(f"**Owner:** `{artwork['owner']}`")
                st.write(f"**Creator:** `{artwork['creator']}`")
                st.write(f"**Metadata URI:** `{artwork['metadataURI']}`")
                st.write(f"**Royalty Percentage:** `{artwork['royaltyPercentage']}%`")
                st.write(f"**Licensed:** `{'Yes' if artwork['isLicensed'] else 'No'}`")
                
                # Show license info if licensed
                if artwork['isLicensed'] and artwork['licenseInfo']:
                    st.write("---")
                    st.subheader("License Details")
                    
                    # Find active license
                    active_license = None
                    for license in artwork['licenseInfo']['licenses']:
                        if license['isActive'] and license['licensee'] == artwork['licenseInfo']['currentLicensee']:
                            active_license = license
                            break
                    
                    if active_license:
                        st.write(f"**Current Licensee:** `{active_license['licensee']}`")
                        st.write(f"**Type:** `{active_license['licenseType']}`")
                        st.write(f"**Start Date:** `{active_license['startDate']}`")
                        st.write(f"**End Date:** `{active_license['endDate']}`")
                        st.write(f"**Terms:** `{active_license['termsHash']}`")
                    else:
                        st.warning("No active license found")
                    
                    # Show all licenses if requested
                    if st.checkbox(f"Show all licenses for Artwork #{artwork['token_id']}", key=f"licenses_{artwork['token_id']}"):
                        for i, license in enumerate(artwork['licenseInfo']['licenses']):
                            st.write(f"#### License #{i+1}")
                            st.write(f"- Licensee: `{license['licensee']}`")
                            st.write(f"- Type: `{license['licenseType']}`")
                            st.write(f"- Status: `{'Active' if license['isActive'] else 'Inactive'}`")
                            st.write(f"- Dates: `{license['startDate']}` to `{license['endDate']}`")
                            st.write(f"- Terms: `{license['termsHash']}`")

if __name__ == "__main__":
    main()