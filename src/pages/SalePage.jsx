import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useWeb3 } from '../contexts/Web3Context';
import { useAuth } from '../contexts/AuthContext';
import { artworksAPI } from '../services/api';
import { ShoppingCart, ArrowLeft, User, DollarSign, AlertTriangle, CheckCircle } from 'lucide-react';
import LoadingSpinner from '../components/common/LoadingSpinner';
import IPFSImage from '../components/common/IPFSImage';
import toast from 'react-hot-toast';

const SalePage = () => {
  const { tokenId } = useParams(); // Get tokenId from URL params
  const navigate = useNavigate();
  const { account, isCorrectNetwork, sendTransaction, balance } = useWeb3();
  const { isAuthenticated } = useAuth();
  
  const [artwork, setArtwork] = useState(null);
  const [blockchainInfo, setBlockchainInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(false);
  const [salePrice, setSalePrice] = useState('1.0');
  const [error, setError] = useState(null);
  const [simulationResults, setSimulationResults] = useState(null);

  // Fetch artwork data
  useEffect(() => {
    if (tokenId) {
      fetchArtworkData();
    }
  }, [tokenId]);

  // Calculate simulation whenever price changes
  useEffect(() => {
    if (artwork && blockchainInfo && salePrice) {
      calculateSaleSimulation();
    }
  }, [artwork, blockchainInfo, salePrice]);

  // Check if current user is the owner
  useEffect(() => {
    if (!loading && account && blockchainInfo && 
        account.toLowerCase() === blockchainInfo.owner.toLowerCase()) {
      // Redirect to artwork detail if user is owner
      navigate(`/artwork/${tokenId}`);
    }
  }, [account, blockchainInfo, loading, tokenId, navigate]);

  const fetchArtworkData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [artworkRes, blockchainRes] = await Promise.allSettled([
        artworksAPI.getById(tokenId),
        artworksAPI.getBlockchainInfo(tokenId)
      ]);

      if (artworkRes.status === 'fulfilled') {
        setArtwork(artworkRes.value);
      } else {
        throw new Error('Failed to fetch artwork data');
      }

      if (blockchainRes.status === 'fulfilled') {
        setBlockchainInfo(blockchainRes.value);
      } else {
        throw new Error('Failed to fetch blockchain data');
      }

    } catch (err) {
      setError(err.message);
      toast.error('Failed to load artwork details');
    } finally {
      setLoading(false);
    }
  };

  const calculateSaleSimulation = () => {
    const price = parseFloat(salePrice) || 0;
    const platformFeeRate = 0.05; // 5% platform fee
    const royaltyRate = blockchainInfo.royalty_percentage / 10000; // Convert basis points to percentage
    
    const isPrimarySale = artwork.creator_address.toLowerCase() === blockchainInfo.owner.toLowerCase();
    
    let platformFee = price * platformFeeRate;
    let royaltyAmount = 0;
    let sellerReceives = 0;
    let creatorRoyalty = 0;

    if (isPrimarySale) {
      // Primary sale: Creator gets everything minus platform fee
      sellerReceives = price - platformFee;
      royaltyAmount = 0; // No royalty on primary sales
    } else {
      // Secondary sale: Royalty goes to creator, rest to current owner
      royaltyAmount = price * royaltyRate;
      creatorRoyalty = royaltyAmount;
      sellerReceives = price - platformFee - royaltyAmount;
    }

    setSimulationResults({
      salePrice: price.toFixed(4),
      platformFee: platformFee.toFixed(4),
      royaltyAmount: royaltyAmount.toFixed(4),
      creatorRoyalty: creatorRoyalty.toFixed(4),
      sellerReceives: sellerReceives.toFixed(4),
      isPrimarySale,
      royaltyRate: (royaltyRate * 100).toFixed(2)
    });
  };

  const handlePurchase = async () => {
    if (!isAuthenticated || !account) {
        toast.error('Please connect your wallet');
        return;
    }

    if (!isCorrectNetwork) {
        toast.error('Please switch to Sepolia testnet');
        return;
    }

    const price = parseFloat(salePrice);
    if (price <= 0) {
        toast.error('Please enter a valid price');
        return;
    }

    // Check if user has sufficient balance
    const balanceEth = parseFloat(balance);
    const requiredBalance = price + 0.01; // Price + estimated gas fees
    
    if (balanceEth < requiredBalance) {
        toast.error(`Insufficient balance. Need ${requiredBalance.toFixed(4)} ETH, have ${balanceEth} ETH`);
        return;
    }

    setPurchasing(true);

    try {
        // 1. Prepare the sale transaction on the backend
        const prepareResponse = await artworksAPI.prepareSaleTransaction({
        token_id: parseInt(tokenId),
        buyer_address: account,
        sale_price: salePrice,
        current_owner: blockchainInfo.owner
        });

        const { transaction_data, sale_details } = prepareResponse;

        // 2. Send the transaction using Web3
        const result = await sendTransaction(transaction_data);
        
        if (result.hash) {
        toast.success('Purchase transaction submitted!');
        
        // 3. Confirm the sale on the backend after transaction is sent
        try {
            await artworksAPI.confirmSale({
            tx_hash: result.hash,
            token_id: parseInt(tokenId),
            buyer_address: account,
            seller_address: blockchainInfo.owner,
            sale_price: salePrice
            });
            
            toast.success('Purchase completed successfully!');
            
            // Refresh artwork data
            fetchArtworkData();
            
            // Navigate to artwork detail page after a short delay
            setTimeout(() => {
            navigate(`/artwork/${tokenId}`);
            }, 2000);
        } catch (confirmationError) {
            console.error('Sale confirmation failed:', confirmationError);
            toast.error('Purchase completed but confirmation failed. Please contact support.');
        }
        }

    } catch (error) {
        console.error('Purchase failed:', error);
        toast.error(error.message || 'Purchase failed');
    } finally {
        setPurchasing(false);
    }
    };

  const formatAddress = (address) => {
    if (!address) return 'Unknown';
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex justify-center">
          <LoadingSpinner size="large" />
        </div>
      </div>
    );
  }

  if (error || !artwork || !blockchainInfo) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center bg-red-50 border border-red-200 rounded-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Artwork Not Found</h2>
          <p className="text-gray-600 mb-4">{error || 'The requested artwork could not be loaded.'}</p>
          <Link
            to="/explorer"
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Back to Explorer
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="text-center flex-1">
          <div className="flex justify-center mb-4">
            <div className="bg-purple-600 p-3 rounded-full">
              <ShoppingCart className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Purchase Artwork</h1>
          <p className="text-lg text-gray-600">Artwork #{tokenId}</p>
        </div>
        <Link
          to={`/artwork/${tokenId}`}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          <ArrowLeft className="w-5 h-5 mr-1 inline" />
          Back to Artwork
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Artwork Details */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="bg-gray-100 h-64 sm:h-80 flex items-center justify-center">
            {artwork.metadata_uri?.includes("ipfs://") ? (
              <IPFSImage
                ipfsUri={artwork.metadata_uri}
                alt={`Artwork ${tokenId}`}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="text-center">
                <DollarSign className="w-16 h-16 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500">No preview available</p>
              </div>
            )}
          </div>
          
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {artwork.title || `Artwork #${tokenId}`}
            </h2>
            
            {artwork.description && (
              <p className="text-gray-600 mb-4">{artwork.description}</p>
            )}

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Creator</span>
                <span className="text-sm font-mono text-gray-900">
                  {formatAddress(artwork.creator_address)}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Current Owner</span>
                <span className="text-sm font-mono text-gray-900">
                  {formatAddress(blockchainInfo.owner)}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Royalty</span>
                <span className="text-sm font-semibold text-gray-900">
                  {(blockchainInfo.royalty_percentage / 100).toFixed(2)}%
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Sale Type</span>
                <span className={`text-sm px-2 py-1 rounded-full ${
                  artwork.creator_address.toLowerCase() === blockchainInfo.owner.toLowerCase()
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-green-100 text-green-800'
                }`}>
                  {artwork.creator_address.toLowerCase() === blockchainInfo.owner.toLowerCase() ? 'Primary Sale' : 'Secondary Sale'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Purchase Form */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Purchase Details</h3>
          
          {!isAuthenticated ? (
            <div className="text-center py-8">
              <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
              <h4 className="text-lg font-semibold text-gray-900 mb-2">Wallet Required</h4>
              <p className="text-gray-600">Please connect your wallet to purchase this artwork.</p>
            </div>
          ) : !isCorrectNetwork ? (
            <div className="text-center py-8">
              <AlertTriangle className="w-12 h-12 text-orange-500 mx-auto mb-4" />
              <h4 className="text-lg font-semibold text-gray-900 mb-2">Wrong Network</h4>
              <p className="text-gray-600">Please switch to Sepolia testnet to make purchases.</p>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Purchase Price (ETH)
                </label>
                <input
                  type="number"
                  min="0.001"
                  step="0.01"
                  value={salePrice}
                  onChange={(e) => setSalePrice(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Enter price in ETH"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Your balance: {balance} ETH
                </p>
              </div>

              {/* Simulation Results */}
              {simulationResults && (
                <div className="bg-gray-50 p-4 rounded-lg mb-6">
                  <h4 className="font-semibold text-gray-900 mb-3">Transaction Breakdown</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Sale Price:</span>
                      <span className="font-mono">{simulationResults.salePrice} ETH</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Platform Fee (5%):</span>
                      <span className="font-mono text-red-600">-{simulationResults.platformFee} ETH</span>
                    </div>
                    {!simulationResults.isPrimarySale && simulationResults.royaltyAmount > 0 && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Creator Royalty ({simulationResults.royaltyRate}%):</span>
                        <span className="font-mono text-orange-600">-{simulationResults.creatorRoyalty} ETH</span>
                      </div>
                    )}
                    <div className="border-t pt-2">
                      <div className="flex justify-between font-medium">
                        <span className="text-gray-900">Seller Receives:</span>
                        <span className="font-mono text-green-600">{simulationResults.sellerReceives} ETH</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <button
                onClick={handlePurchase}
                disabled={purchasing || !salePrice || parseFloat(salePrice) <= 0}
                className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                  purchasing || !salePrice || parseFloat(salePrice) <= 0
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-purple-600 text-white hover:bg-purple-700'
                }`}
              >
                {purchasing ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    <span>Processing Purchase...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <ShoppingCart className="w-5 h-5 mr-2" />
                    Purchase Artwork
                  </div>
                )}
              </button>

              <div className="mt-4 text-xs text-gray-500 text-center">
                <p>By purchasing, you agree to the platform's terms and conditions.</p>
                <p className="mt-1">Transaction fees will be deducted automatically.</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Additional Information */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start">
          <CheckCircle className="w-6 h-6 text-blue-600 mt-0.5 mr-3" />
          <div>
            <h4 className="text-lg font-semibold text-blue-900 mb-2">Secure Transaction</h4>
            <p className="text-blue-800 mb-2">
              This transaction is secured by blockchain technology and smart contracts.
            </p>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Ownership transfer is automatic upon payment</li>
              <li>• Creator royalties are distributed automatically</li>
              <li>• Transaction is permanently recorded on blockchain</li>
              <li>• Platform fees support continued development</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SalePage;