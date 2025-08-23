import { ArrowUpRight, DollarSign, Clock, TrendingUp } from 'lucide-react';
import LoadingSpinner from '../components/common/LoadingSpinner';
import toast from 'react-hot-toast';
import { useWeb3 } from '../contexts/Web3Context';
import { useAuth } from '../contexts/AuthContext'; 
import { useState, useEffect } from 'react'; 
import { transactionsAPI, artworksAPI } from '../services/api'; 

const Royalties = () => {
  const { account, isCorrectNetwork } = useWeb3();
  const { isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [transactions, setTransactions] = useState([]);
  const [artworks, setArtworks] = useState([]);
  const [royaltyEarnings, setRoyaltyEarnings] = useState('0.0000');
  const [error, setError] = useState(null);

  // Fetch transactions and artworks
  useEffect(() => {
    if (!isAuthenticated || !account) return;

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        console.log(`🔄 Fetching royalty data for account: ${account}`);

        // Fetch all data in parallel
        const [txsRes, artsRes, earningsRes] = await Promise.allSettled([
          transactionsAPI.getByUser(account),
          artworksAPI.getByCreator(account),
          transactionsAPI.getByUser(account, { type: 'ROYALTY' })
        ]);

        // Handle transactions
        if (txsRes.status === 'fulfilled') {
          setTransactions(txsRes.value.data || []);
        } else {
          console.warn('Transactions fetch failed:', txsRes.reason);
          setTransactions([]);
        }

        // Handle artworks
        if (artsRes.status === 'fulfilled') {
          setArtworks(artsRes.value.data || []);
        } else {
          console.warn('Artworks fetch failed:', artsRes.reason);
          setArtworks([]);
        }

        // Handle royalty earnings
        if (earningsRes.status === 'fulfilled') {
          const royaltyTransactions = earningsRes.value.data || [];
          const total = royaltyTransactions.reduce((sum, tx) => {
            const value = parseFloat(tx?.value || 0);
            return sum + (isNaN(value) ? 0 : value);
          }, 0);
          setRoyaltyEarnings(total.toFixed(4));
        } else {
          console.warn('Royalty transactions fetch failed:', earningsRes.reason);
          setRoyaltyEarnings('0.0000');
        }
        
      } catch (error) {
        console.error('❌ Error fetching royalty data:', error);
        setError(`Failed to load royalty data: ${error.message}`);
        toast.error('Failed to load royalty data');
        
        setTransactions([]);
        setArtworks([]);
        setRoyaltyEarnings('0.0000');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [isAuthenticated, account]);

  // Format address helper
  const formatAddress = (address) => {
    if (!address || typeof address !== 'string') return 'Invalid address';
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  // Redirect if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center bg-yellow-50 border border-yellow-200 rounded-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Wallet Connection Required
          </h2>
          <p className="text-gray-600 mb-6">
            Please connect your MetaMask wallet to view royalty information.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="flex justify-center mb-4">
          <div className="bg-purple-600 p-3 rounded-full">
            <DollarSign className="w-8 h-8 text-white" />
          </div>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Royalty Management
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Track your royalty earnings and artwork sales history.
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100 mr-4">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Total Royalties</p>
              <p className="text-2xl font-semibold text-gray-900">
                {isLoading ? '...' : `${royaltyEarnings} ETH`}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100 mr-4">
              <Clock className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Artworks</p>
              <p className="text-2xl font-semibold text-gray-900">
                {isLoading ? '...' : artworks.length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100 mr-4">
              <DollarSign className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Transactions</p>
              <p className="text-2xl font-semibold text-gray-900">
                {isLoading ? '...' : transactions.length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Transaction History */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Transaction History</h2>
          <p className="text-sm text-gray-600 mt-1">
            View all your artwork-related transactions and royalty earnings
          </p>
        </div>
        
        {isLoading ? (
          <div className="flex justify-center p-12">
            <LoadingSpinner size="medium" />
          </div>
        ) : transactions.length === 0 ? (
          <div className="text-center p-12">
            <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No transactions yet</h3>
            <p className="text-gray-500 mb-6">
              Once you register artworks or receive royalties, they'll appear here.
            </p>
            {artworks.length === 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto">
                <p className="text-blue-800 text-sm">
                  <strong>Get started:</strong> Register your first artwork to begin earning royalties from future sales.
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Artwork</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Transaction</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.map(tx => (
                  <tr key={tx.tx_hash || tx.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                        tx.transaction_type === 'ROYALTY' ? 'bg-green-100 text-green-800' :
                        tx.transaction_type === 'REGISTER' ? 'bg-blue-100 text-blue-800' :
                        tx.transaction_type === 'SALE' ? 'bg-purple-100 text-purple-800' :
                        tx.transaction_type === 'LICENSE' ? 'bg-orange-100 text-orange-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {tx.transaction_type?.replace('_', ' ') || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {tx.created_at ? new Date(tx.created_at).toLocaleDateString() : 'N/A'}
                      <div className="text-xs text-gray-400">
                        {tx.created_at ? new Date(tx.created_at).toLocaleTimeString() : ''}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {tx.metadata?.token_id ? (
                        <span className="font-mono">#{tx.metadata.token_id}</span>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-mono font-medium ${
                      tx.transaction_type === 'ROYALTY' ? 'text-green-600' : 
                      tx.value && parseFloat(tx.value) > 0 ? 'text-blue-600' : 'text-gray-500'
                    }`}>
                      {tx.value ? `${parseFloat(tx.value).toFixed(4)} ETH` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                      {tx.tx_hash ? (
                        <a 
                          href={`https://sepolia.etherscan.io/tx/${tx.tx_hash}`} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-purple-600 hover:text-purple-800 flex items-center hover:underline"
                        >
                          {tx.tx_hash.substring(0, 8)}...{tx.tx_hash.substring(tx.tx_hash.length - 6)}
                          <ArrowUpRight className="w-4 h-4 ml-1" />
                        </a>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Royalty Information */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start">
          <TrendingUp className="w-6 h-6 text-blue-600 mt-0.5 mr-3" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">How Royalties Work</h3>
            <div className="text-blue-800 space-y-2">
              <p className="mb-3">
                Earn ongoing revenue from your creative work through our automated royalty system:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <ul className="space-y-2">
                  <li className="flex items-start">
                    <span className="text-blue-600 mr-2">•</span>
                    <span><strong>Automatic Distribution:</strong> Royalties are paid instantly when your artwork is resold</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-600 mr-2">•</span>
                    <span><strong>Blockchain Secured:</strong> All transactions are permanently recorded and verifiable</span>
                  </li>
                </ul>
                <ul className="space-y-2">
                  <li className="flex items-start">
                    <span className="text-blue-600 mr-2">•</span>
                    <span><strong>Set Your Rate:</strong> Choose royalty percentage (up to 20%) when registering</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-600 mr-2">•</span>
                    <span><strong>Lifetime Earnings:</strong> Continue earning from every future resale of your work</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Royalties;