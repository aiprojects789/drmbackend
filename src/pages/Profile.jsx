// Fixed Profile.jsx with proper data handling
import React, { useState, useEffect } from "react";
import { useWeb3 } from "../contexts/Web3Context";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { artworksAPI, licensesAPI, transactionsAPI } from "../services/api";
import { Palette, Shield, DollarSign, User, ArrowRight } from "lucide-react";
import LoadingSpinner from "../components/common/LoadingSpinner";
import toast from "react-hot-toast";
import IPFSImage from "../components/common/IPFSImage";

const Profile = () => {
  const { account, isCorrectNetwork } = useWeb3();
  const { isAuthenticated, user } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("artworks");
  const [artworks, setArtworks] = useState([]);
  const [licenses, setLicenses] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState({
    artworkCount: 0,
    licenseCount: 0,
    royaltyEarnings: 0,
  });
  const [error, setError] = useState(null);

  // Fetch user data
  useEffect(() => {
    if (!isAuthenticated || !account) return;

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        console.log(`🔄 Fetching profile data for account: ${account}`);

        // Fetch all data in parallel with better error handling
        const [artsRes, licRes, txRes] = await Promise.allSettled([
          artworksAPI.getByOwner(account, { page: 1, size: 100 }),
          licensesAPI.getByUser(account, { as_licensee: false }),
          transactionsAPI.getByUser(account),
        ]);

        // Handle artworks
        let artworksData = [];
        if (artsRes.status === "fulfilled") {
          artworksData = artsRes.value.data || [];
        } else {
          console.warn("Artworks fetch failed:", artsRes.reason);
        }
        setArtworks(artworksData);

        // Handle licenses
        let licensesData = [];
        if (licRes.status === "fulfilled") {
          licensesData = licRes.value.data || [];
        } else {
          console.warn("Licenses fetch failed:", licRes.reason);
        }
        setLicenses(licensesData);

        // Handle transactions
        let transactionsData = [];
        if (txRes.status === "fulfilled") {
          transactionsData = txRes.value.data || [];
        } else {
          console.warn("Transactions fetch failed:", txRes.reason);
        }
        setTransactions(transactionsData);

        // Calculate stats
        const royaltyEarnings = transactionsData
          .filter((tx) => tx?.transaction_type === "ROYALTY")
          .reduce((sum, tx) => {
            const value = parseFloat(tx?.value || 0);
            return sum + (isNaN(value) ? 0 : value);
          }, 0);

        setStats({
          artworkCount: artworksData.length,
          licenseCount: licensesData.length,
          royaltyEarnings: royaltyEarnings.toFixed(4),
        });
      } catch (error) {
        console.error("❌ Error fetching profile data:", error);
        setError(`Failed to load profile data: ${error.message}`);
        toast.error("Failed to load profile data");

        setArtworks([]);
        setLicenses([]);
        setTransactions([]);
        setStats({
          artworkCount: 0,
          licenseCount: 0,
          royaltyEarnings: 0,
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [isAuthenticated, account]);

  // Helper function to format addresses safely
  const formatAddress = (address) => {
    if (!address || typeof address !== "string") return "Invalid address";
    return `${address.substring(0, 6)}...${address.substring(
      address.length - 4
    )}`;
  };

  // Add these date formatting functions at the top of your Profile component
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        const altDate = new Date(dateString.replace(/\.\d+Z$/, 'Z'));
        if (!isNaN(altDate.getTime())) {
          return altDate.toLocaleDateString();
        }
        return 'Invalid Date';
      }
      
      return date.toLocaleDateString();
    } catch (error) {
      console.error('Error formatting date:', error, dateString);
      return 'Invalid Date';
    }
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        const altDate = new Date(dateString.replace(/\.\d+Z$/, 'Z'));
        if (!isNaN(altDate.getTime())) {
          return altDate.toLocaleString();
        }
        return 'Invalid Date';
      }
      
      return date.toLocaleString();
    } catch (error) {
      console.error('Error formatting date:', error, dateString);
      return 'Invalid Date';
    }
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
            Please connect your MetaMask wallet to view your profile.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Profile Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center gap-8 mb-12">
        <div className="bg-purple-100 p-6 rounded-full">
          <User className="w-12 h-12 text-purple-600" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {user?.username || "Anonymous Artist"}
          </h1>
          <p className="text-lg text-gray-600 mb-4">{formatAddress(account)}</p>
          <div className="flex flex-wrap gap-4">
            <div className="px-4 py-2 bg-white border border-gray-200 rounded-lg shadow-sm">
              <p className="text-sm text-gray-500">Artworks</p>
              <p className="text-xl font-semibold">{stats.artworkCount}</p>
            </div>
            <div className="px-4 py-2 bg-white border border-gray-200 rounded-lg shadow-sm">
              <p className="text-sm text-gray-500">Licenses</p>
              <p className="text-xl font-semibold">{stats.licenseCount}</p>
            </div>
            <div className="px-4 py-2 bg-white border border-gray-200 rounded-lg shadow-sm">
              <p className="text-sm text-gray-500">Royalties</p>
              <p className="text-xl font-semibold">
                {stats.royaltyEarnings} ETH
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-8">
        <button
          className={`py-4 px-6 font-medium text-sm border-b-2 transition-colors ${
            activeTab === "artworks"
              ? "border-purple-600 text-purple-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
          onClick={() => setActiveTab("artworks")}
        >
          My Artworks
        </button>
        <button
          className={`py-4 px-6 font-medium text-sm border-b-2 transition-colors ${
            activeTab === "licenses"
              ? "border-purple-600 text-purple-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
          onClick={() => setActiveTab("licenses")}
        >
          My Licenses
        </button>
        <button
          className={`py-4 px-6 font-medium text-sm border-b-2 transition-colors ${
            activeTab === "activity"
              ? "border-purple-600 text-purple-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
          onClick={() => setActiveTab("activity")}
        >
          Activity
        </button>
      </div>

      {/* Artworks Tab */}
      {activeTab === "artworks" && (
        <div>
          {isLoading ? (
            <div className="flex justify-center p-12">
              <LoadingSpinner size="medium" />
            </div>
          ) : artworks.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow border border-gray-200">
              <p className="text-gray-500 mb-4">
                You haven't registered any artworks yet
              </p>
              <a
                href="/register"
                className="text-purple-600 hover:text-purple-800 font-medium"
              >
                Register your first artwork
              </a>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {artworks.map((artwork) => (
                <div
                  key={artwork.token_id}
                  className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200 hover:shadow-lg transition-shadow"
                >
                  <div className="bg-gray-100 h-48 flex items-center justify-center">
                    <IPFSImage
  ipfsUri={artwork.metadata_uri}
  alt={`Artwork ${artwork.token_id}`}
  className="h-48"
/>
                  </div>
                  <div className="p-6">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        #{artwork.token_id}
                      </h3>
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          artwork.is_licensed
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {artwork.is_licensed ? "Licensed" : "Available"}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mb-4 truncate">
                      {artwork.title || artwork.metadata_uri || "Untitled"}
                    </p>
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-xs text-gray-500">Royalty</p>
                        <p className="text-sm font-semibold">
                          {((artwork.royalty_percentage || 0) / 100).toFixed(2)}
                          %
                        </p>
                      </div>
                      <Link
                        to={`/artwork/${artwork.token_id}`}
                        className="inline-flex items-center text-sm font-medium text-purple-600 hover:text-purple-800"
                      >
                        View details <ArrowRight className="w-4 h-4 ml-1" />
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Licenses Tab */}
      {activeTab === "licenses" && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {isLoading ? (
            <div className="flex justify-center p-12">
              <LoadingSpinner size="medium" />
            </div>
          ) : licenses.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">You have no active licenses</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      License ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Artwork
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Expires
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {licenses.map((license) => (
                    <tr key={license.license_id || license.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                        #{license.license_id || license.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        #{license.token_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            license.license_type === "PERSONAL"
                              ? "bg-blue-100 text-blue-800"
                              : license.license_type === "COMMERCIAL"
                              ? "bg-purple-100 text-purple-800"
                              : "bg-green-100 text-green-800"
                          }`}
                        >
                          {license.license_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {license.end_date
                          ? new Date(license.end_date).toLocaleDateString()
                          : "N/A"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {license.is_active ? (
                          <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                            Inactive
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Activity Tab */}
      {activeTab === "activity" && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {isLoading ? (
            <div className="flex justify-center p-12">
              <LoadingSpinner size="medium" />
            </div>
          ) : transactions.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No activity found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Artwork
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Transaction
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.map((tx) => (
                    <tr key={tx.tx_hash}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            tx.transaction_type === "ROYALTY"
                              ? "bg-green-100 text-green-800"
                              : tx.transaction_type === "REGISTER"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-purple-100 text-purple-800"
                          }`}
                        >
                          {tx.transaction_type.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDateTime(tx.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {tx.metadata?.token_id
                          ? `#${tx.metadata.token_id}`
                          : "N/A"}
                      </td>
                      <td
                        className="px-6 py-4 whitespace-nowrap text-sm font-mono ${
                        tx.transaction_type === 'ROYALTY' ? 'text-green-600' : 'text-gray-500'
                      }"
                      >
                        {tx.value
                          ? `${parseFloat(tx.value).toFixed(4)} ETH`
                          : "N/A"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                        <a
                          href={`https://sepolia.etherscan.io/tx/${tx.tx_hash}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-purple-600 hover:text-purple-800"
                        >
                          {tx.tx_hash.substring(0, 8)}...
                          {tx.tx_hash.substring(58)}
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Profile;
