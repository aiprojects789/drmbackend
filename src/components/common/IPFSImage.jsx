import React, { useState, useEffect, useCallback } from 'react';
import { Palette, WifiOff, RefreshCw, ImageIcon } from 'lucide-react';

// IPFS Gateway utilities
const extractIPFSHash = (ipfsUri) => {
  if (!ipfsUri) return null;
  
  // Handle ipfs:// format
  if (ipfsUri.startsWith('ipfs://')) {
    return ipfsUri.replace('ipfs://', '');
  }
  
  // Handle gateway URLs
  if (ipfsUri.includes('/ipfs/')) {
    const parts = ipfsUri.split('/ipfs/');
    return parts[1].split('/')[0];
  }
  
  // Handle direct hash (CIDv0: Qm..., CIDv1: bafy...)
  if (ipfsUri.startsWith('Qm') || ipfsUri.startsWith('bafy') || ipfsUri.startsWith('bafk')) {
    return ipfsUri;
  }
  
  return null;
};

const getIPFSGateways = (hash) => {
  if (!hash) return [];
  
  return [
    `https://ipfs.io/ipfs/${hash}`,
    `https://gateway.pinata.cloud/ipfs/${hash}`,
    `https://nftstorage.link/ipfs/${hash}`,
    `https://${hash}.ipfs.dweb.link/`,
    `https://cloudflare-ipfs.com/ipfs/${hash}`,
    `https://w3s.link/ipfs/${hash}`,
  ];
};

const IPFSImage = ({ 
  ipfsUri, 
  alt = "Artwork", 
  className = "",
  showRetryButton = true,
  onLoad,
  onError,
  ...props 
}) => {
  const [currentGatewayIndex, setCurrentGatewayIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const hash = extractIPFSHash(ipfsUri);
  const gateways = hash ? getIPFSGateways(hash) : [];
  const currentUrl = gateways[currentGatewayIndex];

  // Reset when ipfsUri changes
  useEffect(() => {
    setCurrentGatewayIndex(0);
    setIsLoading(true);
    setHasError(false);
    setRetryCount(0);
  }, [ipfsUri]);

  const tryNextGateway = useCallback(() => {
    if (currentGatewayIndex < gateways.length - 1) {
      setCurrentGatewayIndex(prev => prev + 1);
      setIsLoading(true);
    } else {
      setIsLoading(false);
      setHasError(true);
      if (onError) {
        onError({
          error: 'All gateways failed',
          gateways: gateways.length,
          retries: retryCount
        });
      }
    }
  }, [currentGatewayIndex, gateways.length, onError, retryCount]);

  const handleImageLoad = () => {
    setIsLoading(false);
    setHasError(false);
    if (onLoad) {
      onLoad({ gateway: currentUrl, attempts: currentGatewayIndex + 1 });
    }
  };

  const handleImageError = () => {
    tryNextGateway();
  };

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
    setCurrentGatewayIndex(0);
    setIsLoading(true);
    setHasError(false);
  };

  // Error state - no URI or hash
  if (!ipfsUri || !hash) {
    return (
      <div className={`bg-gray-100 rounded-lg overflow-hidden flex flex-col items-center justify-center p-4 ${className}`}>
        <div className="text-center">
          <ImageIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500 text-sm">No image</p>
        </div>
      </div>
    );
  }

  // Error state - all gateways failed
  if (hasError) {
    return (
      <div className={`bg-gray-100 rounded-lg overflow-hidden flex flex-col items-center justify-center p-4 ${className}`}>
        <div className="text-center">
          <WifiOff className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500 text-sm mb-1">Failed to load</p>
          <p className="text-gray-400 text-xs mb-3">
            {gateways.length} gateways tried
          </p>
          {showRetryButton && (
            <button
              onClick={handleRetry}
              className="flex items-center justify-center text-xs text-purple-500 hover:text-purple-700 mx-auto transition-colors"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Retry
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`relative rounded-lg overflow-hidden bg-gray-100 ${className}`}>
      {/* Loading state */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
          <div className="text-center">
            <Palette className="w-8 h-8 text-purple-400 mx-auto mb-2 animate-pulse" />
            <p className="text-xs text-gray-500">Loading artwork...</p>
            {gateways.length > 1 && (
              <div className="mt-2 w-16 h-1 bg-gray-200 rounded-full mx-auto overflow-hidden">
                <div 
                  className="h-full bg-purple-400 rounded-full transition-all duration-500"
                  style={{ width: `${((currentGatewayIndex + 1) / gateways.length) * 100}%` }}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Image */}
      <img
        src={currentUrl}
        alt={alt}
        className={`w-full h-full object-cover transition-opacity duration-300 ${
          isLoading ? 'opacity-0' : 'opacity-100'
        }`}
        onLoad={handleImageLoad}
        onError={handleImageError}
        {...props}
      />
    </div>
  );
};

export default IPFSImage;