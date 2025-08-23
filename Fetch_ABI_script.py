import requests
import json

def get_contract_abi(contract_address):
    """Fetch contract ABI from Etherscan"""
    
    # Try Etherscan API (Sepolia)
    etherscan_url = f"https://api-sepolia.etherscan.io/api"
    params = {
        'module': 'contract',
        'action': 'getabi',
        'address': contract_address,
        'apikey': 'MCF2GQXJU95G8DBZAB3AYF69FYN9X4DK5H'  # You can use without API key for limited requests
    }
    
    try:
        response = requests.get(etherscan_url, params=params)
        data = response.json()
        
        if data['status'] == '1':
            abi = json.loads(data['result'])
            print("✅ Contract ABI found on Etherscan:")
            print(json.dumps(abi, indent=2))
            
            # Save to file
            with open('contract_abi.json', 'w') as f:
                json.dump(abi, f, indent=2)
            
            return abi
        else:
            print(f"❌ Etherscan error: {data.get('result', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching from Etherscan: {e}")
        return None

def extract_register_function(abi):
    """Extract the registerArtwork function from ABI"""
    for item in abi:
        if item.get('name') == 'registerArtwork' and item.get('type') == 'function':
            print("\n🎯 Found registerArtwork function:")
            print(json.dumps(item, indent=2))
            return item
    
    print("❌ registerArtwork function not found in ABI")
    return None

if __name__ == "__main__":
    contract_address = "0xA07F45FE615E86C6BE90AD207952497c6F23d69d"
    
    print(f"🔍 Fetching ABI for contract: {contract_address}")
    abi = get_contract_abi(contract_address)
    
    if abi:
        register_func = extract_register_function(abi)
        
        if register_func:
            print("\n📝 Use this function definition in your CONTRACT_ABI:")
            print(json.dumps(register_func, indent=2))
    else:
        print("\n💡 Alternative solutions:")
        print("1. Check if contract is verified on Etherscan")
        print("2. Use the ABI from your compilation artifacts")
        print("3. Verify your contract on Etherscan with: npx hardhat verify --network sepolia YOUR_CONTRACT_ADDRESS")