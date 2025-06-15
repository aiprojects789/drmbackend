import streamlit as st
import json
from web3 import Web3
from pathlib import Path
import os
import time
from web3.exceptions import CannotHandleRequest

# Helper functions
def format_accounts(accounts):
    """Format accounts as 'Account #1: 0x123...456 (Balance: X ETH)'"""
    formatted = []
    for i, account in enumerate(accounts):
        balance = w3.from_wei(w3.eth.get_balance(account), 'ether')
        formatted.append(f"Account #{i+1}: {account[:6]}...{account[-4:]} (Balance: {balance:.4f} ETH)")
    return formatted

def connect_to_web3():
    try:
        w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
        if w3.is_connected():
            return w3
        else:
            st.error("Could not connect to Ethereum node. Please make sure it's running.")
            st.stop()
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        st.error("Please make sure your local Ethereum node (Ganache/Hardhat) is running on port 8545")
        st.stop()

w3 = connect_to_web3()

def load_contract_abi(contract_name):
    try:
        path = Path(f'./artifacts/contracts/{contract_name}.sol/{contract_name}.json')
        with open(path) as f:
            return json.load(f)['abi']
    except FileNotFoundError:
        st.error(f"Contract ABI not found for {contract_name}. Please compile your contracts first.")
        st.stop()

def account_selector(label, accounts, default_index=0):
    account_options = format_accounts(accounts)
    account_mapping = {option: account for option, account in zip(account_options, accounts)}
    selected_option = st.selectbox(label, options=account_options, index=default_index)
    return account_mapping[selected_option]

def main():
    st.title("Smart Contract Deployment Dashboard")
    
    # Check connection status
    if not w3.is_connected():
        st.error("Not connected to Ethereum node")
        st.stop()
    
    st.success(f"Connected to Ethereum node (Chain ID: {w3.eth.chain_id})")
    
    # Get accounts
    try:
        accounts = w3.eth.accounts
        if not accounts:
            st.error("No accounts available in the connected node")
            st.stop()
    except Exception as e:
        st.error(f"Error getting accounts: {str(e)}")
        st.stop()
    
    deployer = account_selector("Select Deployer Account", accounts)
    
    st.header("1. Deploy MyToken (ERC20)")
    with st.form("deploy_token"):
        initial_supply = st.number_input("Initial Supply", min_value=1, value=1000000)
        
        if st.form_submit_button("Deploy Token"):
            with st.spinner("Deploying MyToken..."):
                try:
                    abi = load_contract_abi("MyToken")
                    MyToken = w3.eth.contract(abi=abi, bytecode=json.loads(open(Path('./artifacts/contracts/MyToken.sol/MyToken.json')).read())['bytecode'])
                    
                    tx_hash = MyToken.constructor(
                        w3.to_wei(initial_supply, 'ether')
                    ).transact({'from': deployer})
                    
                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                    st.success(f"MyToken deployed at: {receipt.contractAddress}")
                    
                    # Save address
                    addresses = {}
                    if os.path.exists('contract-addresses.json'):
                        with open('contract-addresses.json', 'r') as f:
                            addresses = json.load(f)
                    
                    addresses['token'] = receipt.contractAddress
                    with open('contract-addresses.json', 'w') as f:
                        json.dump(addresses, f, indent=2)
                    
                except Exception as e:
                    st.error(f"Error deploying MyToken: {str(e)}")

    st.header("2. Deploy PaymentSplitter")
    with st.form("deploy_splitter"):
        payee1 = account_selector("Payee 1", accounts)
        share1 = st.number_input("Share 1 (%)", min_value=1, max_value=99, value=60)
        payee2 = account_selector("Payee 2", accounts, default_index=1)
        share2 = st.number_input("Share 2 (%)", min_value=1, max_value=99, value=40)
        
        if st.form_submit_button("Deploy PaymentSplitter"):
            with st.spinner("Deploying PaymentSplitter..."):
                try:
                    abi = load_contract_abi("PaymentSplitter")
                    PaymentSplitter = w3.eth.contract(abi=abi, bytecode=json.loads(open(Path('./artifacts/contracts/PaymentSplitter.sol/PaymentSplitter.json')).read())['bytecode'])
                    
                    tx_hash = PaymentSplitter.constructor(
                        [payee1, payee2],
                        [share1, share2]
                    ).transact({'from': deployer})
                    
                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                    st.success(f"PaymentSplitter deployed at: {receipt.contractAddress}")
                    
                    # Save address
                    addresses = {}
                    if os.path.exists('contract-addresses.json'):
                        with open('contract-addresses.json', 'r') as f:
                            addresses = json.load(f)
                    
                    addresses['splitter'] = receipt.contractAddress
                    with open('contract-addresses.json', 'w') as f:
                        json.dump(addresses, f, indent=2)
                    
                except Exception as e:
                    st.error(f"Error deploying PaymentSplitter: {str(e)}")

    st.header("3. Deploy TimeLock")
    with st.form("deploy_timelock"):
        beneficiary = account_selector("Beneficiary", accounts)
        release_delay = st.number_input("Release Delay (hours)", min_value=1, value=24)
        
        if st.form_submit_button("Deploy TimeLock"):
            with st.spinner("Deploying TimeLock..."):
                try:
                    abi = load_contract_abi("TimeLock")
                    TimeLock = w3.eth.contract(abi=abi, bytecode=json.loads(open(Path('./artifacts/contracts/TimeLock.sol/TimeLock.json')).read())['bytecode'])
                    
                    release_time = int(time.time()) + (release_delay * 3600)
                    
                    tx_hash = TimeLock.constructor(
                        beneficiary,
                        release_time
                    ).transact({'from': deployer})
                    
                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                    st.success(f"TimeLock deployed at: {receipt.contractAddress}")
                    
                    # Save address
                    addresses = {}
                    if os.path.exists('contract-addresses.json'):
                        with open('contract-addresses.json', 'r') as f:
                            addresses = json.load(f)
                    
                    addresses['timelock'] = receipt.contractAddress
                    with open('contract-addresses.json', 'w') as f:
                        json.dump(addresses, f, indent=2)
                    
                except Exception as e:
                    st.error(f"Error deploying TimeLock: {str(e)}")

if __name__ == "__main__":
    main()