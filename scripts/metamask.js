async function connectMetaMask() {
    if (typeof window.ethereum === 'undefined') {
        return { error: "MetaMask not installed! Please install MetaMask and refresh the page." };
    }
    
    try {
        // Request account access
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        
        // Check if connected to Sepolia (chainId 0xAA36A7)
        const chainId = await window.ethereum.request({ method: 'eth_chainId' });
        if (chainId !== '0xAA36A7') {
            try {
                await window.ethereum.request({
                    method: 'wallet_switchEthereumChain',
                    params: [{ chainId: '0xAA36A7' }] // Sepolia
                });
            } catch (switchError) {
                // This error code indicates that the chain has not been added to MetaMask
                if (switchError.code === 4902) {
                    try {
                        await window.ethereum.request({
                            method: 'wallet_addEthereumChain',
                            params: [{
                                chainId: '0xAA36A7',
                                chainName: 'Sepolia Test Network',
                                nativeCurrency: {
                                    name: 'Sepolia ETH',
                                    symbol: 'ETH',
                                    decimals: 18
                                },
                                rpcUrls: ['https://sepolia.infura.io/v3/e6f455108e5f490a972625f2b4f24e04'],
                                blockExplorerUrls: ['https://sepolia.etherscan.io']
                            }]
                        });
                    } catch (addError) {
                        return { error: "Failed to add Sepolia network: " + addError.message };
                    }
                } else {
                    return { error: "Failed to switch to Sepolia: " + switchError.message };
                }
            }
        }
        
        return { account: accounts[0] };
    } catch (error) {
        return { error: error.message };
    }
}

// Listen for account changes
window.ethereum.on('accountsChanged', (accounts) => {
    if (accounts.length === 0) {
        console.log('MetaMask locked or user disconnected');
    } else {
        console.log('Account changed:', accounts[0]);
    }
});

// Listen for chain changes
window.ethereum.on('chainChanged', (chainId) => {
    window.location.reload();
});

// Make function available globally
window.connectMetaMask = connectMetaMask;