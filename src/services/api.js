// services/api.js - Fixed version with proper error handling and data structures

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Handle responses and errors
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`❌ API Error: ${error.config?.url}`, error.response?.data || error.message);
    
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      localStorage.removeItem('userData');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Enhanced error handler
const handleApiError = (error, context) => {
  console.error(`❌ ${context} Error:`, error);
  
  if (error.response) {
    const { status, data } = error.response;
    
    if (status === 422 && data.detail) {
      const errorMessages = Array.isArray(data.detail) 
        ? data.detail.map(err => `${err.loc?.join('.')}: ${err.msg}`).join(', ')
        : JSON.stringify(data.detail);
      
      throw new Error(`Validation failed: ${errorMessages}`);
    }
    
    throw new Error(`${context} failed (${status}): ${data.detail || data.message || 'Unknown error'}`);
  } else if (error.request) {
    throw new Error(`No response received: ${error.message}`);
  } else {
    throw new Error(`${context} failed: ${error.message}`);
  }
};

// Auth API
export const authAPI = {
  connectWallet: (data) => 
    api.post('/auth/connect-wallet', data)
      .then(res => res.data)
      .catch(error => handleApiError(error, 'Wallet connection')),

  getCurrentUser: (token) => 
    api.get('/auth/me', {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.data)
      .catch(error => handleApiError(error, 'User fetch')),

  logout: () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    return Promise.resolve();
  }
};

// FIXED: Artworks API with proper data extraction
export const artworksAPI = {
  registerWithImage: (formData) => 
    api.post('/artworks/register-with-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000
    })
      .then(res => res.data)
      .catch(error => handleApiError(error, 'Artwork registration')),

  confirmRegistration: (data) => 
    api.post('/artworks/confirm-registration', data)
      .then(res => res.data)
      .catch(error => handleApiError(error, 'Registration confirmation')),

  getAll: (params = {}) => 
    api.get('/artworks', { params })
      .then(res => {
        console.log('📦 All artworks response:', res.data);
        return {
          data: res.data.artworks || [],
          total: res.data.total || 0,
          page: res.data.page || 1,
          size: res.data.size || 20,
          has_next: res.data.has_next || false
        };
      })
      .catch(error => handleApiError(error, 'Fetch artworks')),

  getById: (tokenId) => 
    api.get(`/artworks/${tokenId}`)
      .then(res => res.data)
      .catch(error => handleApiError(error, `Fetch artwork ${tokenId}`)),

  getBlockchainInfo: (tokenId) => 
    api.get(`/artworks/${tokenId}/blockchain`)
      .then(res => res.data)
      .catch(error => handleApiError(error, `Fetch blockchain info ${tokenId}`)),

  getByTokenId: (tokenId) => {
    return api.get(`/artworks/${tokenId}`);
  },

  prepareSaleTransaction: (data) => 
    api.post('/artworks/prepare-sale-transaction', data)
      .then(res => res.data)
      .catch(error => handleApiError(error, 'Prepare sale transaction')),

  confirmSale: (data) => 
    api.post('/artworks/confirm-sale', data)
      .then(res => res.data)
      .catch(error => handleApiError(error, 'Confirm sale')),

  // FIXED: Owner artworks with proper data structure
  getByOwner: async (ownerAddress, params = {}) => {
    try {
      const response = await api.get(`/artworks/owner/${ownerAddress}`, { params });
      
      // Handle different response structures
      let artworks = [];
      let total = 0;
      
      if (response.data && Array.isArray(response.data.artworks)) {
        artworks = response.data.artworks;
        total = response.data.total || artworks.length;
      } else if (Array.isArray(response.data)) {
        artworks = response.data;
        total = response.data.length;
      } else if (response.data && response.data.data && Array.isArray(response.data.data)) {
        artworks = response.data.data;
        total = response.data.total || artworks.length;
      }
      
      console.log(`📦 Owner artworks for ${ownerAddress}:`, { count: artworks.length, total });
      
      return {
        data: artworks,
        total: total,
        page: response.data?.page || 1,
        size: response.data?.size || 20,
        has_next: response.data?.has_next || false
      };
    } catch (error) {
      console.warn(`Owner artworks failed for ${ownerAddress}:`, error.message);
      return {
        data: [],
        total: 0,
        page: 1,
        size: 20,
        has_next: false
      };
    }
  },

  getByCreator: async (creatorAddress, params = {}) => {
    try {
      const response = await api.get(`/artworks/creator/${creatorAddress}`, { params });
      
      // Handle different response structures
      let artworks = [];
      let total = 0;
      
      if (response.data && Array.isArray(response.data.artworks)) {
        artworks = response.data.artworks;
        total = response.data.total || artworks.length;
      } else if (Array.isArray(response.data)) {
        artworks = response.data;
        total = response.data.length;
      }
      
      console.log(`📦 Creator artworks for ${creatorAddress}:`, { count: artworks.length, total });
      
      return {
        data: artworks,
        total: total,
        page: response.data?.page || 1,
        size: response.data?.size || 20,
        has_next: response.data?.has_next || false
      };
    } catch (error) {
      console.warn(`Creator artworks failed for ${creatorAddress}:`, error.message);
      return {
        data: [],
        total: 0,
        page: 1,
        size: 20,
        has_next: false
      };
    }
  }
};

// FIXED: Licenses API with proper data structure
export const licensesAPI = {
  grant: (data) => 
    api.post('/licenses/grant', data)
      .then(res => res.data)
      .catch(error => handleApiError(error, 'Grant license')),

  revoke: (licenseId) => 
    api.post(`/licenses/${licenseId}/revoke`)
      .then(res => res.data)
      .catch(error => handleApiError(error, `Revoke license ${licenseId}`)),

  // FIXED: User licenses with proper data structure
  getByUser: async (userAddress, params = {}) => {
    try {
      console.log(`🚀 Fetching licenses for user: ${userAddress}`, params);
      
      // Build query parameters properly
      const queryParams = new URLSearchParams();
      
      if (params.as_licensee !== undefined) {
        queryParams.append('as_licensee', params.as_licensee.toString());
      }
      if (params.page) {
        queryParams.append('page', params.page.toString());
      }
      if (params.size) {
        queryParams.append('size', params.size.toString());
      }
      
      const url = `/licenses/user/${userAddress}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      console.log(`🌐 API URL: ${url}`);
      
      const response = await api.get(url);
      console.log(`📡 Raw API response:`, response);
      console.log(`📦 Response data:`, response.data);
      
      // Handle different response structures more robustly
      let licenses = [];
      let total = 0;
      let page = 1;
      let size = 20;
      let hasNext = false;
      
      if (response.data) {
        // Check for standard paginated response
        if (response.data.licenses && Array.isArray(response.data.licenses)) {
          licenses = response.data.licenses;
          total = response.data.total || licenses.length;
          page = response.data.page || 1;
          size = response.data.size || 20;
          hasNext = response.data.has_next || false;
          console.log(`✅ Standard paginated response: ${licenses.length} licenses`);
        }
        // Check for direct array response
        else if (Array.isArray(response.data)) {
          licenses = response.data;
          total = response.data.length;
          console.log(`✅ Direct array response: ${licenses.length} licenses`);
        }
        // Check for nested data structure
        else if (response.data.data && Array.isArray(response.data.data)) {
          licenses = response.data.data;
          total = response.data.total || licenses.length;
          page = response.data.page || 1;
          size = response.data.size || 20;
          hasNext = response.data.has_next || false;
          console.log(`✅ Nested data response: ${licenses.length} licenses`);
        }
        // Log unexpected structure
        else {
          console.warn(`⚠️ Unexpected response structure:`, response.data);
          console.warn(`Response keys:`, Object.keys(response.data));
        }
      }
      
      // Validate license objects
      const validLicenses = licenses.filter(license => {
        const isValid = license && 
                      (license.license_id !== undefined || license.id !== undefined) &&
                      license.token_id !== undefined;
        if (!isValid) {
          console.warn(`⚠️ Invalid license object:`, license);
        }
        return isValid;
      });
      
      console.log(`🎯 Final result: ${validLicenses.length} valid licenses out of ${licenses.length} total`);
      
      const result = {
        data: validLicenses,
        total: total,
        page: page,
        size: size,
        has_next: hasNext
      };
      
      console.log(`📊 Returning result:`, result);
      return result;
      
    } catch (error) {
      console.error(`❌ User licenses API failed for ${userAddress}:`, error);
      console.error(`Error details:`, error.response?.data || error.message);
      
      // Return empty result instead of throwing
      return {
        data: [],
        total: 0,
        page: 1,
        size: 20,
        has_next: false,
        error: error.message
      };
    }
  },

  getAll: (params = {}) => 
    api.get('/licenses', { params })
      .then(res => res.data)
      .catch(error => handleApiError(error, 'Fetch licenses')),

  getById: (licenseId) => 
    api.get(`/licenses/${licenseId}`)
      .then(res => res.data)
      .catch(error => handleApiError(error, `Fetch license ${licenseId}`)),

  getByArtwork: (tokenId, params = {}) => 
    api.get(`/licenses/artwork/${tokenId}`, { params })
      .then(res => res.data)
      .catch(error => handleApiError(error, `Fetch artwork licenses ${tokenId}`)),

  getByArtwork: (tokenId, page = 1, size = 20) => {
    return api.get(`/licenses/artwork/${tokenId}`, {
      params: { page, size }
    });
  },

  grantWithDocument: async (licenseData) => {
    try {
      const formData = new FormData();
      formData.append('token_id', licenseData.token_id.toString());
      formData.append('licensee_address', licenseData.licensee_address);
      formData.append('duration_days', licenseData.duration_days.toString());
      formData.append('license_type', licenseData.license_type);

      const response = await api.post('/licenses/grant-with-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      return response.data;
    } catch (error) {
      handleApiError(error, 'Grant license with document');
    }
  }
};

// FIXED: Transactions API with proper data structure
export const transactionsAPI = {
  create: async (data) => {
    console.log('Creating transaction with data:', JSON.stringify(data, null, 2));
    try {
      const response = await api.post('/transactions', data);
      return response.data;
    } catch (error) {
      console.error('Transaction creation error:', error.response?.data);
      throw error;
    }
  },

  update: (txHash, data) => 
    api.put(`/transactions/${txHash}`, data)
      .then(res => res.data)
      .catch(error => handleApiError(error, `Update transaction ${txHash}`)),

  getAll: (params = {}) => 
    api.get('/transactions', { params })
      .then(res => res.data)
      .catch(error => handleApiError(error, 'Fetch transactions')),

  getById: (txHash) => 
    api.get(`/transactions/${txHash}`)
      .then(res => res.data)
      .catch(error => handleApiError(error, `Fetch transaction ${txHash}`)),

  // FIXED: User transactions with proper data structure and type filtering
  getByUser: async (userAddress, params = {}) => {
    try {
      const response = await api.get(`/transactions/user/${userAddress}`, { params });
      
      // Handle different response structures
      let transactions = [];
      let total = 0;
      
      if (response.data && Array.isArray(response.data.transactions)) {
        transactions = response.data.transactions;
        total = response.data.total || transactions.length;
      } else if (Array.isArray(response.data)) {
        transactions = response.data;
        total = response.data.length;
      } else if (response.data && response.data.data && Array.isArray(response.data.data)) {
        transactions = response.data.data;
        total = response.data.total || transactions.length;
      }
      
      // Apply type filtering if requested
      if (params.type && transactions.length > 0) {
        transactions = transactions.filter(tx => 
          tx.transaction_type === params.type
        );
      }
      
      console.log(`📦 User transactions for ${userAddress}:`, { count: transactions.length, total });
      
      return {
        data: transactions,
        total: total
      };
    } catch (error) {
      console.warn(`User transactions failed for ${userAddress}:`, error.message);
      return {
        data: [],
        total: 0
      };
    }
  }
};

// Web3 API
export const web3API = {
  getStatus: () => 
    api.get('/web3/status')
      .then(res => res.data)
      .catch(error => handleApiError(error, 'Web3 status')),

  getArtworkCount: () => 
    api.get('/web3/artwork-count')
      .then(res => res.data)
      .catch(error => handleApiError(error, 'Artwork count')),

  prepareRegisterTransaction: (data) => 
    api.post('/web3/prepare-transaction/register', data)
      .then(res => res.data)
      .catch(error => handleApiError(error, 'Prepare registration transaction')),

  prepareLicenseTransaction: (data) => 
    api.post('/web3/prepare-transaction/license', data)
      .then(res => res.data)
      .catch(error => handleApiError(error, 'Prepare license transaction')),

  waitForTransaction: (txHash) => 
    api.get(`/web3/transactions/${txHash}/wait`)
      .then(res => res.data)
      .catch(error => handleApiError(error, `Wait for transaction ${txHash}`)),

  getTransactionReceipt: (txHash) => 
    api.get(`/web3/transactions/${txHash}/receipt`)
      .then(res => res.data)
      .catch(error => handleApiError(error, `Transaction receipt ${txHash}`)),

  getTokenIdFromTx: (txHash) => 
    api.get(`/web3/transactions/${txHash}/token-id`)
      .then(res => res.data)
      .catch(error => handleApiError(error, `Token ID from transaction ${txHash}`))
};

// Health check utility
export const checkAPIHealth = async () => {
  try {
    const response = await api.get('/health');
    return { healthy: true, data: response.data };
  } catch (error) {
    return { healthy: false, error: error.message };
  }
};

// Token management utilities
export const getAuthToken = () => localStorage.getItem('authToken');
export const setAuthToken = (token) => localStorage.setItem('authToken', token);
export const clearAuth = () => {
  localStorage.removeItem('authToken');
  localStorage.removeItem('userData');
};

export default api;