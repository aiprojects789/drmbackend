// Enhanced IPFS Utilities with improved error handling and gateway management

export const getIPFSGatewayUrl = (ipfsUri, gatewayIndex = 0) => {
  if (!ipfsUri) return null;
  
  const hash = extractIPFShash(ipfsUri);
  if (!hash) return null;
  
  const gateways = getIPFSGateways();
  const gateway = gateways[gatewayIndex % gateways.length];
  return gateway.replace('{hash}', hash);
};

export const extractIPFShash = (ipfsUri) => {
  if (!ipfsUri) return null;
  
  // Handle ipfs:// format
  if (ipfsUri.startsWith('ipfs://')) {
    return ipfsUri.replace('ipfs://', '');
  }
  
  // Handle gateway URLs
  if (ipfsUri.includes('/ipfs/')) {
    const parts = ipfsUri.split('/ipfs/');
    return parts[1].split('/')[0]; // Get just the hash part
  }
  
  // Assume it's already a hash if it starts with Qm and is 46 chars (CIDv0)
  if (ipfsUri.startsWith('Qm') && ipfsUri.length === 46) {
    return ipfsUri;
  }
  
  // Handle CIDv1 (starts with bafy, bafk, bafz, etc.)
  if (/^baf[a-z0-9]{4,}/.test(ipfsUri)) {
    return ipfsUri;
  }
  
  // Handle other CID formats (starting with z, f, etc.)
  if (/^[a-z0-9]{46,}$/.test(ipfsUri)) {
    return ipfsUri;
  }
  
  return null;
};

export const getIPFSGateways = () => {
  return [
    // Most reliable gateways (updated list as of 2024)
    'https://ipfs.io/ipfs/{hash}',
    'https://gateway.pinata.cloud/ipfs/{hash}',
    'https://nftstorage.link/ipfs/{hash}',
    'https://w3s.link/ipfs/{hash}',
    'https://4everland.io/ipfs/{hash}',
    
    // Subdomain gateways (better for security)
    'https://{hash}.ipfs.dweb.link/',
    'https://{hash}.ipfs.nftstorage.link/',
    'https://{hash}.ipfs.w3s.link/',
    
    // Alternative gateways
    'https://ipfs-gateway.cloud/ipfs/{hash}',
    'https://cloudflare-ipfs.com/ipfs/{hash}',
    
    // Local gateway (if running IPFS locally)
    'http://localhost:8080/ipfs/{hash}',
    'http://127.0.0.1:8080/ipfs/{hash}',
    
    // Fallback gateways
    'https://gateway.ipfs.io/ipfs/{hash}',
    'https://{hash}.ipfs.cf-ipfs.com/',
  ];
};

// Get only the most reliable gateways
export const getReliableIPFSGateways = () => {
  return [
    'https://ipfs.io/ipfs/{hash}',
    'https://gateway.pinata.cloud/ipfs/{hash}',
    'https://nftstorage.link/ipfs/{hash}',
    'https://w3s.link/ipfs/{hash}',
    'https://{hash}.ipfs.dweb.link/',
    'https://{hash}.ipfs.nftstorage.link/',
    'https://4everland.io/ipfs/{hash}',
  ];
};

export const getIPFSUrlWithFallback = (ipfsUri) => {
  const hash = extractIPFShash(ipfsUri);
  if (!hash) return [];
  
  return getReliableIPFSGateways().map(gateway => gateway.replace('{hash}', hash));
};

// Enhanced availability check with better error handling
export const checkIPFSAvailability = async (ipfsUri, timeout = 5000) => {
  const urls = getIPFSUrlWithFallback(ipfsUri);
  const results = [];
  
  // Check gateways in parallel for faster results
  const promises = urls.map(async (url) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      const start = Date.now();
      
      // Try a lightweight GET request first for images
      const response = await fetch(url, { 
        method: 'HEAD',
        signal: controller.signal,
        // Don't use no-cors for better error information
        headers: {
          'Cache-Control': 'no-cache'
        }
      });
      
      clearTimeout(timeoutId);
      
      return {
        url,
        available: response.ok,
        status: response.status,
        responseTime: Date.now() - start,
        contentType: response.headers.get('content-type'),
        contentLength: response.headers.get('content-length')
      };
      
    } catch (error) {
      return {
        url,
        available: false,
        error: error.name,
        message: error.message,
        isTimeout: error.name === 'AbortError'
      };
    }
  });
  
  try {
    const results = await Promise.all(promises);
    return results.sort((a, b) => {
      // Sort by availability first, then by response time
      if (a.available && !b.available) return -1;
      if (!a.available && b.available) return 1;
      if (a.available && b.available) {
        return (a.responseTime || Infinity) - (b.responseTime || Infinity);
      }
      return 0;
    });
  } catch (error) {
    console.warn('Error checking IPFS availability:', error);
    return [];
  }
};

// Enhanced image preload with better promise handling
export const preloadImage = (url, timeout = 8000) => {
  return new Promise((resolve) => {
    const img = new Image();
    let resolved = false;
    
    const cleanup = () => {
      if (!resolved) {
        resolved = true;
        img.onload = null;
        img.onerror = null;
        img.src = '';
      }
    };
    
    img.onload = () => {
      cleanup();
      resolve({
        success: true,
        width: img.naturalWidth,
        height: img.naturalHeight
      });
    };
    
    img.onerror = () => {
      cleanup();
      resolve({
        success: false,
        error: 'Image failed to load'
      });
    };
    
    // Set timeout
    const timeoutId = setTimeout(() => {
      cleanup();
      resolve({
        success: false,
        error: 'Timeout'
      });
    }, timeout);
    
    img.src = url;
    
    // Clear timeout if image loads/errors before timeout
    const originalOnLoad = img.onload;
    const originalOnError = img.onerror;
    
    img.onload = (e) => {
      clearTimeout(timeoutId);
      if (originalOnLoad) originalOnLoad(e);
    };
    
    img.onerror = (e) => {
      clearTimeout(timeoutId);
      if (originalOnError) originalOnError(e);
    };
  });
};

// Utility to get the fastest working gateway
export const getFastestWorkingGateway = async (ipfsUri, timeout = 3000) => {
  const results = await checkIPFSAvailability(ipfsUri, timeout);
  const workingGateway = results.find(result => result.available);
  return workingGateway?.url || null;
};

// Cache for gateway performance to avoid repeated checks
const gatewayPerformanceCache = new Map();

export const getCachedGatewayPerformance = (ipfsUri) => {
  return gatewayPerformanceCache.get(ipfsUri);
};

export const setCachedGatewayPerformance = (ipfsUri, results, ttl = 300000) => { // 5 min TTL
  const cacheEntry = {
    results,
    timestamp: Date.now(),
    ttl
  };
  gatewayPerformanceCache.set(ipfsUri, cacheEntry);
  
  // Clean up expired entries
  setTimeout(() => {
    const entry = gatewayPerformanceCache.get(ipfsUri);
    if (entry && Date.now() - entry.timestamp > entry.ttl) {
      gatewayPerformanceCache.delete(ipfsUri);
    }
  }, ttl);
};

// Get optimal gateway order based on cached performance
export const getOptimalGatewayOrder = (ipfsUri) => {
  const cached = getCachedGatewayPerformance(ipfsUri);
  if (cached && Date.now() - cached.timestamp < cached.ttl) {
    return cached.results
      .filter(r => r.available)
      .sort((a, b) => (a.responseTime || Infinity) - (b.responseTime || Infinity))
      .map(r => r.url);
  }
  return getIPFSUrlWithFallback(ipfsUri);
};