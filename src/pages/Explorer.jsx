import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useWeb3 } from "../contexts/Web3Context";
import { useAuth } from "../contexts/AuthContext";
import { artworksAPI } from "../services/api";
import { Palette, Search, Filter, ArrowRight, ShoppingCart } from "lucide-react";
import LoadingSpinner from "../components/common/LoadingSpinner";
import IPFSImage from "../components/common/IPFSImage";
import toast from "react-hot-toast";

const Explorer = () => {
  const { account, isCorrectNetwork } = useWeb3();
  const { isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [artworkData, setArtworkData] = useState({
    artworks: [],
    total: 0,
    page: 1,
    size: 20,
    hasNext: false,
  });
  const [filteredArtworks, setFilteredArtworks] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    licensed: "all",
    royalty: "all",
  });

  // Fetch all artworks with pagination
  const fetchArtworks = async (page = 1, size = 20) => {
    setIsLoading(true);
    try {
      const response = await artworksAPI.getAll({ page, size });

      // Handle different response structures
      const artworks = response.data || [];
      const total = response.total || 0;
      const hasNext = response.has_next || false;

      setArtworkData({
        artworks: artworks,
        total: total,
        page: page,
        size: size,
        hasNext: hasNext,
      });

      setFilteredArtworks(artworks);
    } catch (error) {
      console.error("Error fetching artworks:", error);
      toast.error(error.response?.data?.detail || "Failed to load artworks");
      setArtworkData((prev) => ({ ...prev, artworks: [] }));
      setFilteredArtworks([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchArtworks();
  }, []);

  // Apply filters and search
  useEffect(() => {
    let results = [...artworkData.artworks];

    // Apply search
    if (searchTerm) {
      results = results.filter((artwork) => {
        const searchLower = searchTerm.toLowerCase();
        return (
          artwork?.metadata_uri?.toLowerCase().includes(searchLower) ||
          artwork?.creator_address?.toLowerCase().includes(searchLower) ||
          artwork?.token_id?.toString().includes(searchTerm)
        );
      });
    }

    // Apply filters
    if (filters.licensed !== "all") {
      const isLicensed = filters.licensed === "licensed";
      results = results.filter(
        (artwork) => artwork?.is_licensed === isLicensed
      );
    }

    if (filters.royalty !== "all") {
      results = results.filter((artwork) => {
        if (!artwork) return false;
        const royalty = artwork.royalty_percentage / 100;
        switch (filters.royalty) {
          case "low":
            return royalty < 5;
          case "medium":
            return royalty >= 5 && royalty < 15;
          case "high":
            return royalty >= 15;
          default:
            return true;
        }
      });
    }

    setFilteredArtworks(results);
  }, [searchTerm, filters, artworkData.artworks]);

  const loadMore = () => {
    if (artworkData.hasNext) {
      fetchArtworks(artworkData.page + 1, artworkData.size);
    }
  };

  const resetFilters = () => {
    setSearchTerm("");
    setFilters({ licensed: "all", royalty: "all" });
    fetchArtworks(); // Reset to first page
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="flex justify-center mb-4">
          <div className="bg-purple-600 p-3 rounded-full">
            <Palette className="w-8 h-8 text-white" />
          </div>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Artwork Explorer
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Browse all registered artworks in the ArtDRM ecosystem.
        </p>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          {artworkData.total} artworks registered in the ArtDRM ecosystem
        </p>
        
        {/* Register Artwork Button */}
        {isAuthenticated && (
          <div className="mt-6">
            <Link
              to="/register"
              className="inline-flex items-center px-8 py-3 text-lg font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
            >
              Register Artwork
              <ArrowRight className="ml-2 w-5 h-5" />
            </Link>
          </div>
        )}
      </div>

      {/* Search and Filters */}
      <div className="mb-8">
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="relative flex-grow">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search by token ID, creator, or metadata..."
              className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="inline-flex items-center px-4 py-3 border border-gray-300 rounded-lg bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
            <Filter className="w-5 h-5 mr-2" />
            Filters
          </button>
        </div>

        {/* Active filters */}
        <div className="flex flex-wrap gap-2">
          <select
            className="text-sm border border-gray-200 rounded-md px-3 py-1 bg-white"
            value={filters.licensed}
            onChange={(e) =>
              setFilters({ ...filters, licensed: e.target.value })
            }
          >
            <option value="all">All Licenses</option>
            <option value="licensed">Licensed Only</option>
            <option value="unlicensed">Unlicensed Only</option>
          </select>

          <select
            className="text-sm border border-gray-200 rounded-md px-3 py-1 bg-white"
            value={filters.royalty}
            onChange={(e) =>
              setFilters({ ...filters, royalty: e.target.value })
            }
          >
            <option value="all">All Royalties</option>
            <option value="low">Low (&lt;5%)</option>
            <option value="medium">Medium (5-15%)</option>
            <option value="high">High (&gt;15%)</option>
          </select>
        </div>
      </div>

      {/* Artwork Grid */}
      {isLoading && artworkData.page === 1 ? (
        <div className="flex justify-center p-12">
          <LoadingSpinner size="large" />
        </div>
      ) : filteredArtworks.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow border border-gray-200">
          <p className="text-gray-500 mb-4">
            No artworks found matching your criteria
          </p>
          <button
            onClick={resetFilters}
            className="text-purple-600 hover:text-purple-800 font-medium"
          >
            Clear all filters
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {filteredArtworks.map((artwork) => (
              <ArtworkCard 
                key={artwork.token_id} 
                artwork={artwork} 
                currentAccount={account}
              />
            ))}
          </div>

          {artworkData.hasNext && (
            <div className="flex justify-center mt-8">
              <button
                onClick={loadMore}
                disabled={isLoading}
                className={`px-6 py-3 rounded-lg font-medium ${
                  isLoading
                    ? "bg-gray-300 text-gray-500"
                    : "bg-purple-600 text-white hover:bg-purple-700"
                }`}
              >
                {isLoading ? "Loading..." : "Load More"}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

// Artwork Card Component with Link navigation
const ArtworkCard = ({ artwork, currentAccount }) => {
  // Check if current user is the owner
  const isOwner = currentAccount && artwork.owner_address && 
    currentAccount.toLowerCase() === artwork.owner_address.toLowerCase();

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200 hover:shadow-lg transition-shadow">
      <div className="bg-gray-100 h-48 flex items-center justify-center">
        {artwork.metadata_uri?.includes("ipfs://") ? (
          <IPFSImage
            ipfsUri={artwork.metadata_uri}
            alt={`Artwork ${artwork.token_id}`}
            className="h-48"
          />
        ) : (
          <Palette className="w-16 h-16 text-gray-400" />
        )}
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
          {artwork.metadata_uri}
        </p>
        <div className="flex justify-between items-center mb-4">
          <div>
            <p className="text-xs text-gray-500">Creator</p>
            <p className="text-sm font-mono">
              {artwork.creator_address?.substring(0, 6)}...
              {artwork.creator_address?.substring(38)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">Royalty</p>
            <p className="text-sm font-semibold">
              {(artwork.royalty_percentage / 100).toFixed(2)}%
            </p>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex gap-2">
          <Link
            to={`/artwork/${artwork.token_id}`}
            className="flex-1 inline-flex items-center justify-center text-sm font-medium text-purple-600 hover:text-purple-800 border border-purple-200 rounded-lg px-3 py-2 hover:bg-purple-50 transition-colors"
          >
            View details <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
          
          {/* Show Buy button only for non-owners */}
          {!isOwner && (
            <Link
              to={`/sale/${artwork.token_id}`}
              className="inline-flex items-center justify-center px-3 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
              title="Purchase this artwork"
            >
              <ShoppingCart className="w-4 h-4 mr-1" />
              Buy
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};

export default Explorer;