import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { Palette, Upload, Percent, FileText, Image as ImageIcon, AlertCircle } from 'lucide-react';
import { useWeb3 } from '../contexts/Web3Context';
import { useAuth } from '../contexts/AuthContext';
import { artworksAPI } from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import toast from 'react-hot-toast';
import imageCompression from 'browser-image-compression';

// Update the validation schema
const schema = yup.object({
  title: yup.string().required('Title is required').max(100, 'Title too long'),
  description: yup.string().max(1000, 'Description too long'),
  royalty_percentage: yup
    .number()
    .required('Royalty percentage is required')
    .min(0, 'Royalty cannot be negative')
    .max(2000, 'Royalty cannot exceed 20% (2000 basis points)')
    .integer('Royalty must be a whole number'),
  image: yup
    .mixed()
    .required('Image is required')
    .test('fileSize', 'File too large (max 5MB)', value => {
      if (!value) return false;
      return value.size <= 5 * 1024 * 1024; // 5MB limit
    })
    .test('fileType', 'Unsupported file type', value => {
      if (!value) return false;
      return ['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(value.type);
    })
    .test('dimensions', 'Image dimensions too large', async (value) => {
      if (!value) return false;
      
      // Check image dimensions
      return new Promise((resolve) => {
        const img = new Image();
        img.onload = function() {
          // Max 4000px on longest side
          resolve(Math.max(this.width, this.height) <= 4000);
        };
        img.onerror = function() {
          resolve(false);
        };
        img.src = URL.createObjectURL(value);
      });
    })
});

const Register = () => {
  const navigate = useNavigate();
  const { account, sendTransaction, isCorrectNetwork } = useWeb3();
  const { isAuthenticated } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [transactionHash, setTransactionHash] = useState(null);
  const [debugInfo, setDebugInfo] = useState(null);
  const [backendStatus, setBackendStatus] = useState(null);
  const [balanceCheck, setBalanceCheck] = useState(null);
  const [preview, setPreview] = useState(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    reset,
    setValue
  } = useForm({
    resolver: yupResolver(schema),
    defaultValues: {
      royalty_percentage: 1000,
      image: null
    }
  });

  const image = watch('image');

  // Generate preview when image changes
  useEffect(() => {
    if (image && image instanceof File) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(image);
    } else {
      setPreview(null);
    }
  }, [image]);

  // Check backend status and wallet balance on component mount
  useEffect(() => {
    const checkBackendStatus = async () => {
      if (!account) return;
      
      try {
        // Use the API service instead of direct fetch
        const statusResponse = await artworksAPI.getBackendStatus();
        setBackendStatus(statusResponse);
        
        const balanceResponse = await artworksAPI.getWalletBalance(account);
        setBalanceCheck(balanceResponse);
      } catch (error) {
        console.error('Failed to check backend status:', error);
        setBackendStatus({ 
          status: 'error', 
          message: 'Cannot connect to backend API' 
        });
      }
    };

    if (account && isAuthenticated) {
      checkBackendStatus();
    }
  }, [account, isAuthenticated]);

  const compressImage = async (file) => {
    const options = {
      maxSizeMB: 2, // Maximum file size in MB
      maxWidthOrHeight: 2000, // Maximum width or height
      useWebWorker: true,
      fileType: 'image/jpeg', // Convert to JPEG for better compression
    };

    try {
      const compressedFile = await imageCompression(file, options);
      return compressedFile;
    } catch (error) {
      console.error('Image compression failed:', error);
      throw new Error('Failed to compress image');
    }
  };

  const validateTransactionData = (txData) => {
    if (!txData) return ['Transaction data is null or undefined'];
    
    const errors = [];
    if (!txData.to || txData.to === '0x0000000000000000000000000000000000000000') {
      errors.push('Invalid contract address');
    }
    if (!txData.data || txData.data === '0x') {
      errors.push('Invalid transaction data');
    }
    return errors;
  };

  const handleRegistrationError = (error) => {
    console.error('Registration error:', error);
    
    if (error.message.includes('timeout')) {
      toast.error('Transaction is taking longer than expected. It may still be processing.');
    }
    else if (error.message.includes('DEMO MODE')) {
      toast.error('Backend Configuration Error', { duration: 10000 });
    } 
    else if (error.message.includes('missing revert data') || error.code === 'CALL_EXCEPTION') {
      toast.error('Smart Contract Error: Contract may not be deployed correctly', { duration: 8000 });
    }
    else if (error.message.includes('Network Error') || error.message.includes('CONNECTION_ERROR')) {
      toast.error('Network connection issue - check if backend can reach Sepolia RPC');
    }
    else if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
      toast.error('Cannot connect to backend server');
    } 
    else if (error.response?.status === 404) {
      toast.error('API endpoint not found');
    } 
    else if (error.response?.status === 500) {
      toast.error('Backend server error - check server logs');
    } 
    else if (error.code === 4001) {
      toast.error('Transaction cancelled by user');
    } 
    else if (error.message.includes('insufficient funds')) {
      toast.error('Insufficient funds for gas fees');
    }
    else if (error.message.includes('nonce')) {
      toast.error('Transaction sequence error. Please try again in a moment.');
    }
    else if (error.response?.data?.detail) {
      toast.error(`API error: ${error.response.data.detail}`);
    } 
    else {
      toast.error(`${error.message || 'Registration failed'}`);
    }
  };
  const onSubmit = async (data) => {
    if (!isCorrectNetwork || !account) {
      toast.error(!isCorrectNetwork 
        ? 'Please switch to Sepolia testnet first' 
        : 'Wallet not connected');
      return;
    }

    setIsSubmitting(true);
    setDebugInfo(null);
    
    try {
      // Compress image before upload
      const compressedImage = await compressImage(data.image);
      
      // Create FormData with compressed image
      const formData = new FormData();
      formData.append('title', data.title);
      formData.append('description', data.description || '');
      formData.append('royalty_percentage', data.royalty_percentage.toString());
      formData.append('image', compressedImage, data.image.name);

      // Phase 1: Prepare registration with image upload
      const prepToast = toast.loading('Uploading image and preparing registration...');
      const preparation = await artworksAPI.registerWithImage(formData);
      toast.dismiss(prepToast);

      setDebugInfo({
        step: 'preparation',
        data: preparation,
        request_data: {
          title: data.title,
          description: data.description,
          royalty_percentage: data.royalty_percentage,
          account: account
        }
      });

      if (!preparation.transaction_data) {
        throw new Error('Backend did not return transaction data');
      }

      // Validate transaction data
      const validationErrors = validateTransactionData(preparation.transaction_data);
      if (validationErrors.length > 0) {
        throw new Error(`Invalid transaction data: ${validationErrors.join(', ')}`);
      }

      // Check for demo mode addresses
      if (preparation.transaction_data.to && preparation.transaction_data.to.startsWith('0x1234567890')) {
        throw new Error('Backend is in demo mode - check contract configuration');
      }

      // Phase 2: Send transaction with longer timeout
      const txToast = toast.loading('Sending transaction... (This may take 1-2 minutes on testnet)');
      const txResponse = await sendTransaction({
        ...preparation.transaction_data,
        from: account,
        gas: 500000 // Higher gas for registration
      });
      toast.dismiss(txToast);

      // Phase 3: Confirm registration (non-blocking)
      const finalizingToast = toast.loading('Finalizing registration...'); // Store toast ID
      try {
        const confirmation = await artworksAPI.confirmRegistration({
          tx_hash: txResponse.hash,
          from_address: account,
          metadata_uri: preparation.metadata_uri,
          royalty_percentage: data.royalty_percentage,
          title: data.title,
          description: data.description
        });

        if (!confirmation.success) {
          console.warn('Registration confirmation had issues:', confirmation);
        }
        
        // Dismiss the finalizing toast
        toast.dismiss(finalizingToast);
        
      } catch (confirmError) {
        console.warn('Registration confirmation failed, but transaction was successful:', confirmError);
        // Dismiss the finalizing toast even if there's an error
        toast.dismiss(finalizingToast);
        // Non-critical error, continue
      }

      // Success
      setTransactionHash(txResponse.hash);
      toast.success('Artwork registration submitted to blockchain!');
      reset();
      
      // Navigate after a delay
      setTimeout(() => navigate('/explorer'), 3000);

    } catch (error) {
      toast.dismiss();
      handleRegistrationError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const StatusIndicator = ({ title, message, type = 'info' }) => {
    const colors = {
      success: 'bg-green-50 border-green-200 text-green-800',
      error: 'bg-red-50 border-red-200 text-red-800',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      info: 'bg-blue-50 border-blue-200 text-blue-800'
    };

    return (
      <div className={`p-4 rounded-lg border ${colors[type]} mb-4`}>
        <div className="flex items-center">
          <AlertCircle className="w-5 h-5 mr-2" />
          <h4 className="font-semibold">{title}</h4>
        </div>
        <p className="text-sm mt-1">{message}</p>
      </div>
    );
  };

  const handleImageChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setValue('image', file, { shouldValidate: true });
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center bg-yellow-50 border border-yellow-200 rounded-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Wallet Connection Required
          </h2>
          <p className="text-gray-600 mb-6">
            Please connect your MetaMask wallet to register artworks.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center mb-12">
        <div className="flex justify-center mb-4">
          <div className="bg-purple-600 p-3 rounded-full">
            <Palette className="w-8 h-8 text-white" />
          </div>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Register New Artwork
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Register your digital artwork on the blockchain with built-in royalty management.
        </p>
      </div>

      {/* <div className="mb-8 space-y-4">
        {backendStatus && (
          <StatusIndicator
            title="Backend Status"
            message={backendStatus.message}
            type={backendStatus.status === 'success' ? 'success' : 'error'}
          />
        )}

        {balanceCheck && (
          <StatusIndicator
            title="Wallet Balance"
            message={balanceCheck.sufficient_balance ? 
              `Sufficient balance: ${balanceCheck.balance_eth} ETH` :
              `Insufficient balance: ${balanceCheck.balance_eth} ETH`}
            type={balanceCheck.sufficient_balance ? 'success' : 'error'}
          />
        )} */}

        {/* {!isCorrectNetwork && (
          <StatusIndicator
            title="Network Error"
            message="Please switch to Sepolia testnet"
            type="error"
          />
        )}
      </div> */}

      {debugInfo && (
        <div className="mb-8 bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Debug Information
          </h3>
          <pre className="text-xs text-gray-600 overflow-auto max-h-64 bg-white p-4 rounded border">
            {JSON.stringify(debugInfo, null, 2)}
          </pre>
        </div>
      )}

      {transactionHash && (
        <div className="mb-8 bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-green-800 mb-2">
              Artwork Registered Successfully!
            </h3>
            <p className="text-sm font-mono text-gray-800 break-all">
              TX: {transactionHash}
            </p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md">
        <form onSubmit={handleSubmit(onSubmit)} className="p-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="space-y-6">
              {/* Title Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Title *</label>
                <input
                  {...register('title')}
                  type="text"
                  placeholder="Enter artwork title"
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 ${
                    errors.title ? 'border-red-300' : 'border-gray-300'
                  }`}
                />
                {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>}
              </div>

              {/* Description Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  {...register('description')}
                  rows={3}
                  placeholder="Describe your artwork..."
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 ${
                    errors.description ? 'border-red-300' : 'border-gray-300'
                  }`}
                />
                {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>}
              </div>

              {/* Royalty Field */}
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <Percent className="w-4 h-4 mr-2" />
                  Royalty Percentage (Basis Points) *
                </label>
                <input
                  {...register('royalty_percentage')}
                  type="number"
                  min="0"
                  max="2000"
                  placeholder="1000"
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 ${
                    errors.royalty_percentage ? 'border-red-300' : 'border-gray-300'
                  }`}
                />
                {errors.royalty_percentage && (
                  <p className="mt-1 text-sm text-red-600">{errors.royalty_percentage.message}</p>
                )}
                <p className="text-gray-500 text-sm mt-1">
                  100 = 1%, max 2000 = 20%
                </p>
              </div>

              {/* Image Upload */}
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <ImageIcon className="w-4 h-4 mr-2" />
                  Artwork Image *
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageChange}
                  className="mt-1 block w-full text-sm text-gray-500
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-md file:border-0
                    file:text-sm file:font-semibold
                    file:bg-purple-50 file:text-purple-700
                    hover:file:bg-purple-100"
                />
                {errors.image && <p className="mt-1 text-sm text-red-600">{errors.image.message}</p>}
                
                {/* Image Preview */}
                {preview && (
                  <div className="mt-4">
                    <img 
                      src={preview} 
                      alt="Preview" 
                      className="max-w-xs max-h-64 rounded-md"
                    />
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={isSubmitting || !isCorrectNetwork}
                className={`w-full flex items-center justify-center px-6 py-3 text-lg font-medium rounded-lg transition-colors ${
                  isSubmitting || !isCorrectNetwork
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-purple-600 text-white hover:bg-purple-700'
                }`}
              >
                {isSubmitting ? (
                  <>
                    <LoadingSpinner size="small" text="" />
                    <span className="ml-2">Registering...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5 mr-2" />
                    Register Artwork
                  </>
                )}
              </button>
            </div>

            <div className="space-y-6">
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-purple-800 mb-3">
                  Requirements
                </h3>
                <ul className="space-y-2 text-sm text-purple-700">
                  <li>• High-quality image (JPG, PNG, GIF, WEBP)</li>
                  <li>• Clear title and description</li>
                  <li>• Royalty between 0-20%</li>
                  <li>• Sepolia testnet connection</li>
                  <li>• Sufficient ETH for gas fees</li>
                </ul>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-blue-800 mb-3">
                  Image Guidelines
                </h3>
                <ul className="space-y-2 text-sm text-blue-700">
                  <li>• Max file size: 5MB</li>
                  <li>• Recommended resolution: 2000px+</li>
                  <li>• Supported formats: JPG, PNG, GIF, WEBP</li>
                  <li>• Square or landscape orientation works best</li>
                </ul>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-green-800 mb-3">
                  What Happens Next
                </h3>
                <ul className="space-y-2 text-sm text-green-700">
                  <li>• Your image will be uploaded to IPFS</li>
                  <li>• Metadata will be created and stored on IPFS</li>
                  <li>• NFT will be minted on the blockchain</li>
                  <li>• Royalty percentage will be locked in</li>
                </ul>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Register;