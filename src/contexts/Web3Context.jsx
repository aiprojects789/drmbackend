import React, { createContext, useContext, useState, useEffect } from 'react';
import { ethers } from 'ethers';
import Web3 from 'web3';
import toast from 'react-hot-toast';

const Web3Context = createContext();

export const useWeb3 = () => {
  const context = useContext(Web3Context);
  if (!context) {
    throw new Error('useWeb3 must be used within Web3Provider');
  }
  return context;
};

export const Web3Provider = ({ children }) => {
  const [web3, setWeb3] = useState(null);
  const [ethersProvider, setEthersProvider] = useState(null);
  const [account, setAccount] = useState(null);
  const [chainId, setChainId] = useState(null);
  const [balance, setBalance] = useState('0');
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [pendingTransactions, setPendingTransactions] = useState(new Set());

  const EXPECTED_CHAIN_ID = '0xaa36a7'; // Sepolia
  const EXPECTED_CHAIN_ID_DECIMAL = 11155111;

  // Initialize providers
  const initializeProviders = () => {
    if (typeof window.ethereum !== 'undefined') {
      const web3Instance = new Web3(window.ethereum);
      const provider = new ethers.BrowserProvider(window.ethereum);
      return { web3Instance, provider };
    }
    return { web3Instance: null, provider: null };
  };

  const connectWallet = async () => {
    if (typeof window.ethereum === 'undefined') {
      toast.error('MetaMask not installed');
      return false;
    }

    setConnecting(true);

    try {
      const accounts = await window.ethereum.request({ 
        method: 'eth_requestAccounts' 
      });

      if (accounts.length === 0) {
        toast.error('No accounts found');
        return false;
      }

      const { web3Instance, provider } = initializeProviders();
      const currentChainId = await window.ethereum.request({
        method: 'eth_chainId'
      });

      setWeb3(web3Instance);
      setEthersProvider(provider);
      setAccount(accounts[0]);
      setChainId(currentChainId);
      setConnected(true);

      await updateBalance(accounts[0]);

      if (currentChainId !== EXPECTED_CHAIN_ID) {
        toast.error('Please switch to Sepolia testnet');
      } else {
        toast.success('Wallet connected successfully!');
      }

      return true;
    } catch (error) {
      console.error('Error connecting wallet:', error);
      
      if (error.code === 4001) {
        toast.error('Connection rejected by user');
      } else {
        toast.error(error.message || 'Connection failed');
      }
      
      return false;
    } finally {
      setConnecting(false);
    }
  };

  const updateBalance = async (accountAddress) => {
    if (web3 && accountAddress) {
      try {
        const balanceWei = await web3.eth.getBalance(accountAddress);
        const balanceEth = web3.utils.fromWei(balanceWei, 'ether');
        setBalance(parseFloat(balanceEth).toFixed(4));
      } catch (error) {
        console.error('Error getting balance:', error);
        setBalance('0');
      }
    }
  };

  const switchToSepolia = async () => {
    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: EXPECTED_CHAIN_ID }],
      });
      return true;
    } catch (switchError) {
      if (switchError.code === 4902) {
        try {
          await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [{
              chainId: EXPECTED_CHAIN_ID,
              chainName: 'Sepolia Testnet',
              nativeCurrency: {
                name: 'Sepolia Ether',
                symbol: 'ETH',
                decimals: 18,
              },
              rpcUrls: ['https://rpc.sepolia.org'],
              blockExplorerUrls: ['https://sepolia.etherscan.io'],
            }],
          });
          return true;
        } catch (addError) {
          console.error('Error adding Sepolia network:', addError);
          toast.error('Failed to add Sepolia network');
          return false;
        }
      }
      console.error('Error switching to Sepolia:', switchError);
      toast.error('Failed to switch to Sepolia network');
      return false;
    }
  };

  // // Enhanced gas estimation for different transaction types
  // const estimateGasForTransaction = async (transactionData) => {
  //   try {
  //     // Different gas limits for different transaction types
  //     const transactionType = transactionData.data 
  //       ? (transactionData.data.includes('0x') && transactionData.data.length > 100 ? 'CONTRACT_INTERACTION' : 'LICENSE_TRANSACTION')
  //       : 'ETH_TRANSFER';

  //     const defaultGasLimits = {
  //       'ETH_TRANSFER': 21000, // Simple ETH transfer
  //       'LICENSE_TRANSACTION': 120000, // License transactions (medium complexity)
  //       'CONTRACT_INTERACTION': 250000, // Complex contract interactions
  //       'ARTWORK_REGISTRATION': 300000, // Artwork registration (most complex)
  //     };

  //     let gasEstimate;
      
  //     try {
  //       // Try to estimate gas first - convert all values to proper types
  //       const estimateParams = {
  //         from: transactionData.from,
  //         to: transactionData.to,
  //         value: transactionData.value || '0',
  //         data: transactionData.data || '0x'
  //       };

  //       // Convert value to hex if it's a string number
  //       if (typeof estimateParams.value === 'string' && !estimateParams.value.startsWith('0x')) {
  //         estimateParams.value = web3.utils.toHex(estimateParams.value);
  //       }

  //       gasEstimate = await web3.eth.estimateGas(estimateParams);
  //     } catch (estimationError) {
  //       console.warn('Gas estimation failed, using default:', estimationError);
  //       gasEstimate = defaultGasLimits[transactionType] || 300000;
  //     }

  //     // Add buffer based on transaction type
  //     const bufferMultipliers = {
  //       'ETH_TRANSFER': 1.1, // 10% buffer
  //       'LICENSE_TRANSACTION': 1.3, // 30% buffer
  //       'CONTRACT_INTERACTION': 1.5, // 50% buffer
  //       'ARTWORK_REGISTRATION': 1.5, // 50% buffer
  //     };

  //     // Convert gasEstimate to number for multiplication, then back to BigInt if needed
  //     const gasEstimateNum = typeof gasEstimate === 'bigint' 
  //       ? Number(gasEstimate) 
  //       : parseInt(gasEstimate);
      
  //     const gasWithBuffer = Math.floor(gasEstimateNum * (bufferMultipliers[transactionType] || 1.3));
      
  //     console.log(`Gas estimate for ${transactionType}: ${gasEstimate}, With buffer: ${gasWithBuffer}`);
  //     return gasWithBuffer;

  //   } catch (error) {
  //     console.error('Gas estimation failed:', error);
  //     return 300000; // Safe default
  //   }
  // };

  // Simple gas estimation function (optional - can be used if needed)
  const estimateGasForTransaction = async (transactionData) => {
    try {
      // For license transactions, use a higher gas limit
      if (transactionData.data && transactionData.data.length > 100) {
        return 400000; // Increased gas limit for license transactions
      }
      return 21000; // Standard for ETH transfers
    } catch (error) {
      console.error('Gas estimation failed:', error);
      return 400000; // Safe default for license transactions
    }
  };

  // Get optimized gas prices for testnet - SIMPLIFIED VERSION
  const getOptimizedGasPrices = async () => {
    try {
      // For testnets, use simple and reliable gas pricing
      try {
        // Try to get current gas price from the network
        const gasPrice = await web3.eth.getGasPrice();
        
        // Convert to number if it's BigInt
        let gasPriceValue;
        if (typeof gasPrice === 'bigint') {
          gasPriceValue = Number(gasPrice);
        } else if (typeof gasPrice === 'string') {
          gasPriceValue = parseInt(gasPrice);
        } else {
          gasPriceValue = gasPrice;
        }
        
        // Add 50% buffer for testnet reliability
        const bufferedGasPrice = Math.floor(gasPriceValue * 1.5);
        
        console.log('Gas price:', {
          original: gasPriceValue,
          buffered: bufferedGasPrice,
          originalGwei: web3.utils.fromWei(gasPriceValue.toString(), 'gwei'),
          bufferedGwei: web3.utils.fromWei(bufferedGasPrice.toString(), 'gwei')
        });
        
        return {
          gasPrice: bufferedGasPrice.toString()
        };
        
      } catch (error) {
        console.warn('Error getting gas price, using fallback:', error);
        // Fallback for testnets - use fixed gas price (30 Gwei)
        const fallbackGasPrice = web3.utils.toWei('30', 'gwei');
        return {
          gasPrice: fallbackGasPrice.toString()
        };
      }

    } catch (error) {
      console.error('Error in getOptimizedGasPrices:', error);
      // Final fallback
      const fallbackGasPrice = web3.utils.toWei('30', 'gwei');
      return {
        gasPrice: fallbackGasPrice.toString()
      };
    }
  };

  // Monitor transaction status with proper timeout
  const monitorTransaction = async (transactionHash) => {
    const toastId = toast.loading('Waiting for blockchain confirmation...');
    
    try {
      // Set a reasonable timeout for testnets (3 minutes)
      const timeout = 3 * 60 * 1000;
      const startTime = Date.now();
      
      while (Date.now() - startTime < timeout) {
        try {
          const receipt = await web3.eth.getTransactionReceipt(transactionHash);
          
          if (receipt) {
            if (receipt.status) {
              toast.success('Transaction confirmed on blockchain!', { id: toastId });
              return { success: true, receipt };
            } else {
              toast.error('Transaction failed on blockchain', { id: toastId });
              return { success: false, receipt };
            }
          }
          
          // Wait before checking again
          await new Promise(resolve => setTimeout(resolve, 3000));
          
        } catch (pollError) {
          console.warn('Error checking transaction status:', pollError);
          await new Promise(resolve => setTimeout(resolve, 3000));
        }
      }
      
      // Timeout reached
      toast.error('Confirmation taking longer than expected. Please check blockchain explorer.', { id: toastId });
      return { success: false, error: 'Timeout' };
      
    } catch (error) {
      console.error('Transaction monitoring error:', error);
      toast.error('Confirmation check failed', { id: toastId });
      return { success: false, error };
    }
  };

  const sendTransaction = async (transactionData) => {
    if (!web3 || !account) {
      throw new Error('Web3 not initialized or account not connected');
    }

    const toastId = toast.loading('Preparing transaction...');

    try {
      // Get optimized gas prices
      const gasPrices = await getOptimizedGasPrices();
      
      // Use appropriate gas limit based on transaction type
      let gasLimit = transactionData.gas || 400000; // Use provided gas or default
      
      // For artwork registration, use higher gas limit
      if (transactionData.data && transactionData.data.includes('registerArtwork')) {
        gasLimit = 500000; // Higher gas for registration
      }

      if (transactionData.data && transactionData.data.includes('token')) {
        // Sale transactions might need more gas
        transactionData.gas = transactionData.gas || 100000;
      }

      // Prepare transaction parameters
      const txParams = {
        from: transactionData.from,
        to: transactionData.to,
        value: transactionData.value || '0',
        data: transactionData.data || '0x',
        gas: web3.utils.toHex(gasLimit),
        ...gasPrices
      };

      console.log('Transaction parameters:', {
        ...txParams,
        value: web3.utils.fromWei(txParams.value, 'ether') + ' ETH',
        gasPrice: web3.utils.fromWei(txParams.gasPrice, 'gwei') + ' Gwei',
        gasLimit: gasLimit
      });

      // Check balance - use BigInt for accurate calculations
      const balanceWei = await web3.eth.getBalance(account);
      const balanceBigInt = typeof balanceWei === 'bigint' ? balanceWei : BigInt(balanceWei);
      
      // Calculate total cost using BigInt
      const valueBigInt = BigInt(txParams.value || '0');
      const gasPriceBigInt = BigInt(txParams.gasPrice || '0');
      const gasLimitBigInt = BigInt(gasLimit);
      
      const totalCost = valueBigInt + (gasLimitBigInt * gasPriceBigInt);
      
      console.log('Balance check (Wei):', {
        balance: balanceBigInt.toString(),
        value: valueBigInt.toString(),
        gasCost: (gasLimitBigInt * gasPriceBigInt).toString(),
        totalCost: totalCost.toString()
      });

      if (balanceBigInt < totalCost) {
        const shortfallEth = web3.utils.fromWei((totalCost - balanceBigInt).toString(), 'ether');
        throw new Error(`Insufficient funds. Need ${parseFloat(shortfallEth).toFixed(6)} more ETH.`);
      }

      toast.loading('Sending transaction... (This may take 1-2 minutes)', { id: toastId });

      // Send transaction with longer timeout for testnets
      const sendPromise = web3.eth.sendTransaction(txParams);
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Transaction submission timeout')), 120000) // 2 minutes timeout
      );

      const receipt = await Promise.race([sendPromise, timeoutPromise]);
      const transactionHash = receipt.transactionHash || receipt;

      if (!transactionHash) {
        throw new Error('No transaction hash received');
      }

      // Immediately return success - monitoring happens in background
      toast.success('Transaction submitted successfully!', { id: toastId });

      // Start monitoring in background (non-blocking)
      monitorTransaction(transactionHash)
        .then(result => {
          if (result.success) {
            console.log('✅ Transaction confirmed on chain:', transactionHash);
            toast.success('Transaction confirmed on blockchain!');
          } else {
            console.warn('⚠️ Transaction failed or timeout:', result);
            toast.error('Transaction confirmation failed or timed out');
          }
        })
        .catch(monitorError => {
          console.error('❌ Transaction monitoring failed:', monitorError);
        });

      return { hash: transactionHash, receipt };

    } catch (error) {
      toast.dismiss(toastId);
      console.error('Transaction failed:', error);

      // User-friendly error messages
      const errorMessages = {
        'timeout': 'Transaction timed out. Please try again.',
        'insufficient funds': 'Insufficient funds for transaction. Please add ETH to your wallet.',
        'rejected': 'Transaction rejected by user.',
        'revert': 'Transaction reverted. Check contract requirements.',
        'out of gas': 'Transaction requires more gas. Please try again.',
        'gas': 'Gas estimation failed. Please try again.',
        'network': 'Network error. Please check your connection.',
        'nonce': 'Nonce error. Please try again.'
      };

      const errorMessage = Object.entries(errorMessages).find(([key]) => 
        error.message.toLowerCase().includes(key)
      )?.[1] || error.message || 'Transaction failed';

      throw new Error(errorMessage);
    }
  };

    // const sendTransaction = async (transactionData) => {
    //   if (!web3 || !account) {
    //     throw new Error('Web3 not initialized or account not connected');
    //   }

    //   const toastId = toast.loading('Preparing transaction...');

    //   try {
    //     // Validate transaction data
    //     if (!transactionData.to || !web3.utils.isAddress(transactionData.to)) {
    //       throw new Error('Invalid recipient address in transaction data');
    //     }

    //     // Get optimized gas prices
    //     const gasPrices = await getOptimizedGasPrices();
        
    //     // Use appropriate gas limit
    //     let gasLimit = transactionData.gas || 50000;
        
    //     // Validate and format transaction parameters
    //     const txParams = {
    //       from: account, // Always use the connected account as sender
    //       to: transactionData.to,
    //       value: transactionData.value || '0',
    //       data: transactionData.data || '0x',
    //       gas: web3.utils.toHex(gasLimit),
    //     };

    //     // Add gas pricing
    //     if (gasPrices.maxFeePerGas && gasPrices.maxPriorityFeePerGas) {
    //       txParams.maxFeePerGas = gasPrices.maxFeePerGas;
    //       txParams.maxPriorityFeePerGas = gasPrices.maxPriorityFeePerGas;
    //     } else {
    //       txParams.gasPrice = gasPrices.gasPrice;
    //     }

    //     console.log('Final transaction parameters:', txParams);

    //     // Check balance
    //     const balanceWei = await web3.eth.getBalance(account);
    //     const balanceBigInt = BigInt(balanceWei);
        
    //     const valueBigInt = BigInt(txParams.value || '0');
    //     const gasPriceBigInt = BigInt(txParams.gasPrice || '0');
    //     const gasLimitBigInt = BigInt(gasLimit);
        
    //     const totalCost = valueBigInt + (gasLimitBigInt * gasPriceBigInt);
        
    //     if (balanceBigInt < totalCost) {
    //       const shortfallEth = web3.utils.fromWei((totalCost - balanceBigInt).toString(), 'ether');
    //       throw new Error(`Insufficient funds. Need ${parseFloat(shortfallEth).toFixed(6)} more ETH.`);
    //     }

    //     toast.loading('Sending transaction... (This may take 1-2 minutes)', { id: toastId });

    //     // Send transaction
    //     const sendPromise = web3.eth.sendTransaction(txParams);
    //     const timeoutPromise = new Promise((_, reject) => 
    //       setTimeout(() => reject(new Error('Transaction submission timeout')), 120000)
    //     );

    //     const receipt = await Promise.race([sendPromise, timeoutPromise]);
    //     const transactionHash = receipt.transactionHash || receipt;

    //     if (!transactionHash) {
    //       throw new Error('No transaction hash received');
    //     }

    //     toast.success('Transaction submitted successfully!', { id: toastId });

    //     // Start monitoring in background
    //     monitorTransaction(transactionHash)
    //       .then(result => {
    //         if (result.success) {
    //           console.log('✅ Transaction confirmed on chain:', transactionHash);
    //           toast.success('Transaction confirmed on blockchain!');
    //         } else {
    //           console.warn('⚠️ Transaction failed or timeout:', result);
    //           toast.error('Transaction confirmation failed or timed out');
    //         }
    //       })
    //       .catch(monitorError => {
    //         console.error('❌ Transaction monitoring failed:', monitorError);
    //       });

    //     return { hash: transactionHash, receipt };

    //   } catch (error) {
    //     toast.dismiss(toastId);
    //     console.error('Transaction failed:', error);

    //     // User-friendly error messages
    //     const errorMessages = {
    //       'invalid recipient address': 'Invalid recipient address. Please contact support.',
    //       'invalid parameters': 'Invalid transaction parameters. Please try again.',
    //       'timeout': 'Transaction timed out. Please try again.',
    //       'insufficient funds': 'Insufficient funds for transaction. Please add ETH to your wallet.',
    //       'rejected': 'Transaction rejected by user.',
    //       'revert': 'Transaction reverted. Check contract requirements.',
    //       'out of gas': 'Transaction requires more gas. Please try again.',
    //       'gas': 'Gas estimation failed. Please try again.',
    //       'network': 'Network error. Please check your connection.',
    //       'nonce': 'Nonce error. Please try again.'
    //     };

    //     const errorMessage = Object.entries(errorMessages).find(([key]) => 
    //       error.message.toLowerCase().includes(key)
    //     )?.[1] || error.message || 'Transaction failed';

    //     throw new Error(errorMessage);
    //   }
    // };
  // Check transaction status
  const checkTransactionStatus = async (transactionHash) => {
    try {
      const receipt = await web3.eth.getTransactionReceipt(transactionHash);
      return receipt ? (receipt.status ? 'CONFIRMED' : 'FAILED') : 'PENDING';
    } catch (error) {
      console.error('Error checking transaction status:', error);
      return 'UNKNOWN';
    }
  };

  useEffect(() => {
    if (typeof window.ethereum !== 'undefined') {
      const handleAccountsChanged = (accounts) => {
        if (accounts.length === 0) {
          setAccount(null);
          setConnected(false);
          setBalance('0');
        } else {
          setAccount(accounts[0]);
          updateBalance(accounts[0]);
        }
      };

      const handleChainChanged = (newChainId) => {
        setChainId(newChainId);
        if (newChainId !== EXPECTED_CHAIN_ID) {
          toast.error('Please switch to Sepolia testnet');
        }
      };

      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', handleChainChanged);

      // Auto-connect if previously connected
      const autoConnect = async () => {
        try {
          const accounts = await window.ethereum.request({ method: 'eth_accounts' });
          if (accounts.length > 0) {
            const { web3Instance, provider } = initializeProviders();
            const currentChainId = await window.ethereum.request({ method: 'eth_chainId' });

            setWeb3(web3Instance);
            setEthersProvider(provider);
            setAccount(accounts[0]);
            setChainId(currentChainId);
            setConnected(true);
            await updateBalance(accounts[0]);
          }
        } catch (error) {
          console.error('Auto-connect failed:', error);
        }
      };

      autoConnect();

      return () => {
        window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
        window.ethereum.removeListener('chainChanged', handleChainChanged);
      };
    }
  }, []);

  return (
    <Web3Context.Provider value={{
      web3,
      ethersProvider,
      account,
      chainId,
      balance,
      connected,
      connecting,
      pendingTransactions: Array.from(pendingTransactions),
      connectWallet,
      disconnectWallet: () => {
        setAccount(null);
        setConnected(false);
        setBalance('0');
      },
      switchToSepolia,
      sendTransaction,
      checkTransactionStatus,
      updateBalance,
      isCorrectNetwork: chainId === EXPECTED_CHAIN_ID,
      expectedChainId: EXPECTED_CHAIN_ID,
      expectedChainIdDecimal: EXPECTED_CHAIN_ID_DECIMAL
    }}>
      {children}
    </Web3Context.Provider>
  );
};