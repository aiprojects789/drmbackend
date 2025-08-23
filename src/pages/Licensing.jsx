import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import {
  Shield,
  Clock,
  XCircle,
  CheckCircle,
  Image,
  User,
  FileText,
} from "lucide-react";
import { useWeb3 } from "../contexts/Web3Context";
import { useAuth } from "../contexts/AuthContext";
import { artworksAPI, licensesAPI, transactionsAPI } from "../services/api";
import LoadingSpinner from "../components/common/LoadingSpinner";
import toast from "react-hot-toast";

const schema = yup.object({
  token_id: yup
    .number()
    .required("Token ID is required")
    .min(0, "Token ID must be positive"),
  licensee_address: yup
    .string()
    .required("Licensee address is required")
    .matches(/^0x[a-fA-F0-9]{40}$/, "Must be a valid Ethereum address"),
  duration_days: yup
    .number()
    .required("Duration is required")
    .min(1, "Minimum 1 day")
    .max(365, "Maximum 1 year"),
  license_type: yup
    .string()
    .required("License type is required")
    .oneOf(["PERSONAL", "COMMERCIAL", "EXCLUSIVE"], "Invalid license type"),
});

const Licensing = () => {
  const navigate = useNavigate();
  const { account, sendTransaction, isCorrectNetwork, web3 } = useWeb3();
  const { isAuthenticated } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [transactionHash, setTransactionHash] = useState(null);
  const [activeTab, setActiveTab] = useState("grant");
  const [artworks, setArtworks] = useState([]);
  const [licenses, setLicenses] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedArtwork, setSelectedArtwork] = useState(null);
  const [licensePreview, setLicensePreview] = useState(null);

  // Initialize react-hook-form
  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm({
    resolver: yupResolver(schema),
    defaultValues: {
      token_id: "",
      licensee_address: "",
      duration_days: 30,
      license_type: "PERSONAL",
    },
  });

  // Watch license_type for any conditional rendering - DECLARE IT HERE ONLY ONCE
  const licenseType = watch("license_type");

  const testLicenseResponse = async () => {
    try {
      const response = await fetch(`/api/v1/licenses/debug/licenses/${account}`);
      const data = await response.json();
      console.log('DEBUG License response:', data);
    } catch (error) {
      console.error('Debug fetch error:', error);
    }
  };

  // Fetch artworks and licenses
  useEffect(() => {
    if (!isAuthenticated || !account) {
      console.log("🚫 Not authenticated or no account, skipping data fetch");
      return;
    }

    const fetchData = async () => {
      setIsLoading(true);
      console.log("🚀 Starting data fetch for account:", account);
      
      try {
        // Fetch user's artworks
        console.log("🎨 Fetching artworks...");
        const artworksResponse = await artworksAPI.getByOwner(
          account.toLowerCase(),
          { page: 1, size: 100 }
        );

        console.log("🎨 Artworks API response:", artworksResponse);
        const userArtworks = artworksResponse.data || [];
        setArtworks(userArtworks);
        console.log(`✅ Set ${userArtworks.length} artworks`);

        // Fetch user's licenses (as licensor)
        console.log("🔐 Fetching licenses as licensor...");
        testLicenseResponse();
        const licensesResponse = await licensesAPI.getByUser(account, { 
          as_licensee: false,
          page: 1,
          size: 100
        });
        
        console.log("🔐 Licenses API response:", licensesResponse);
        
        let userLicenses = [];
        
        // Debug the response structure
        console.log('Response type:', typeof licensesResponse);
        console.log('Is array:', Array.isArray(licensesResponse));
        console.log('Has data property:', licensesResponse && 'data' in licensesResponse);
        console.log('Has licenses property:', licensesResponse && 'licenses' in licensesResponse);
        
        // Handle response based on actual structure
        if (licensesResponse && licensesResponse.licenses && Array.isArray(licensesResponse.licenses)) {
          // Structure: { licenses: [], total: X, page: X, ... }
          userLicenses = licensesResponse.licenses;
          console.log("📦 Found licenses in response.licenses");
        } else if (licensesResponse && Array.isArray(licensesResponse)) {
          // Structure: [license1, license2, ...] (direct array)
          userLicenses = licensesResponse;
          console.log("📦 Found licenses as direct array");
        } else if (licensesResponse && licensesResponse.data && licensesResponse.data.licenses) {
          // Structure: { data: { licenses: [], total: X, ... } }
          userLicenses = licensesResponse.data.licenses;
          console.log("📦 Found licenses in response.data.licenses");
        } else if (licensesResponse && licensesResponse.data && Array.isArray(licensesResponse.data)) {
          // Structure: { data: [license1, license2, ...] }
          userLicenses = licensesResponse.data;
          console.log("📦 Found licenses in response.data array");
        } else {
          console.warn("⚠️ Unexpected licenses response structure:", licensesResponse);
          userLicenses = [];
        }
        
        console.log(`✅ Processing ${userLicenses.length} licenses`);
        
        // Filter out any invalid license objects
        const validLicenses = userLicenses.filter(license => {
          const isValid = license && 
                        (license.license_id !== undefined || license.id !== undefined) &&
                        license.token_id !== undefined;
          if (!isValid) {
            console.warn("⚠️ Filtering out invalid license:", license);
          }
          return isValid;
        });
        
        console.log(`🎯 Setting ${validLicenses.length} valid licenses`);
        setLicenses(validLicenses);
        
      } catch (error) {
        console.error("❌ Error in fetchData:", error);
        console.error("Error details:", error.response?.data || error.message);
        toast.error("Failed to load your data");
        setArtworks([]);
        setLicenses([]);
      } finally {
        setIsLoading(false);
        console.log("🏁 Data fetch complete");
      }
    };

    fetchData();
  }, [isAuthenticated, account]);

  // Handle artwork selection change
  const handleArtworkChange = (tokenId) => {
    if (!tokenId) {
      setSelectedArtwork(null);
      return;
    }

    const artwork = artworks.find((art) => art.token_id === parseInt(tokenId));
    if (artwork) {
      setSelectedArtwork(artwork);
    }
  };

  const onSubmitGrant = async (data) => {
    if (!isCorrectNetwork) {
      toast.error("Please switch to Sepolia testnet first");
      return;
    }

    setIsSubmitting(true);
    setLicensePreview(null);
    setTransactionHash(null);

    try {
      // Fixed license fee of 0.1 ETH as per the smart contract
      const licenseFeeWei = web3.utils.toWei("0.1", "ether");

      // Step 1: Prepare license with automatic document generation
      const prepToast = toast.loading(
        "Generating license document and preparing transaction..."
      );

      const licenseResponse = await licensesAPI.grantWithDocument({
        token_id: parseInt(data.token_id),
        licensee_address: data.licensee_address,
        duration_days: parseInt(data.duration_days),
        license_type: data.license_type,
      });

      toast.dismiss(prepToast);

      if (!licenseResponse.success) {
        throw new Error(licenseResponse.detail || "Failed to prepare license");
      }

      // Show license preview if available
      if (licenseResponse.license_document_preview) {
        setLicensePreview(licenseResponse.license_document_preview);
      }

      // Step 2: Send blockchain transaction
      let txResponse;
      try {
        const txToast = toast.loading("Sending transaction to blockchain...");

        console.log("Sending transaction with data:", {
          to: licenseResponse.transaction_data.to,
          data: licenseResponse.transaction_data.data,
          from: account,
          value: licenseFeeWei.toString(),
        });

        txResponse = await sendTransaction({
          to: licenseResponse.transaction_data.to,
          data: licenseResponse.transaction_data.data,
          from: account,
          value: licenseFeeWei,
        });

        toast.dismiss(txToast);

        console.log("Transaction response:", txResponse);
        console.log("Transaction hash:", txResponse?.hash);

        if (!txResponse || !txResponse.hash) {
          throw new Error("No transaction hash received");
        }
      } catch (txError) {
        console.error("Transaction sending failed:", txError);
        throw new Error(`Transaction failed: ${txError.message}`);
      }

      setTransactionHash(txResponse.hash);

      // Step 3: Create transaction record (non-blocking)
      try {
        const txHash = txResponse.hash.startsWith("0x")
          ? txResponse.hash
          : `0x${txResponse.hash}`;

        if (!/^0x[a-fA-F0-9]{64}$/.test(txHash)) {
          console.warn("Invalid transaction hash format, skipping record");
          return;
        }

        let fromAddress, toAddress;
        try {
          fromAddress = web3.utils.toChecksumAddress(account);
          toAddress = web3.utils.toChecksumAddress(
            licenseResponse.transaction_data.to
          );
        } catch (addrError) {
          console.warn("Address checksum failed, using raw addresses");
          fromAddress = account;
          toAddress = licenseResponse.transaction_data.to;
        }

        const transactionData = {
          tx_hash: txHash,
          from_address: fromAddress,
          to_address: toAddress,
          value: 0.1,
          transaction_type: "GRANT_LICENSE",
          status: "PENDING",
          metadata: {
            token_id: parseInt(data.token_id),
            license_id: licenseResponse.license_id,
            licensee_address: data.licensee_address.toLowerCase(),
            duration_days: parseInt(data.duration_days),
            license_type: data.license_type,
            terms_hash: licenseResponse.terms_hash,
          },
        };

        console.log("Creating transaction record:", transactionData);

        // Create transaction record with retry logic
        for (let attempt = 0; attempt < 3; attempt++) {
          try {
            await transactionsAPI.create(transactionData);
            console.log("✅ Transaction record created successfully");
            break;
          } catch (createError) {
            if (attempt === 2) {
              console.warn(
                "Failed to create transaction record after 3 attempts"
              );
            }
            await new Promise((resolve) => setTimeout(resolve, 1000));
          }
        }
      } catch (transactionError) {
        console.error("Transaction record creation failed:", transactionError);
        // Non-critical error, continue
      }

      toast.success(
        "License granted successfully! Transaction submitted to blockchain."
      );
      reset();

      // Refresh licenses after a delay
      setTimeout(async () => {
        try {
          const licensesRes = await licensesAPI.getByUser(account, {
            as_licensee: false,
          });
          let userLicenses = [];
          if (licensesRes?.licenses) {
            userLicenses = licensesRes.licenses;
          } else if (Array.isArray(licensesRes)) {
            userLicenses = licensesRes;
          }
          setLicenses(userLicenses);
        } catch (error) {
          console.error("Error refreshing licenses:", error);
        }
      }, 2000);
    } catch (error) {
      console.error("License grant failed:", error);
      toast.dismiss();

      // Specific error handling
      if (error.code === 4001) {
        toast.error("Transaction cancelled by user");
      } else if (error.message?.includes("insufficient funds")) {
        toast.error("Insufficient funds. Please add ETH to your wallet.");
      } else if (error.message?.includes("out of gas")) {
        toast.error("Transaction requires more gas. Please try again.");
      } else if (error.message?.includes("rejected")) {
        toast.error("Transaction rejected by user.");
      } else if (error.message) {
        const errorMsg =
          error.message.length > 100
            ? error.message.substring(0, 100) + "..."
            : error.message;
        toast.error(`License grant failed: ${errorMsg}`);
      } else {
        toast.error("License grant failed. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const onSubmitRevoke = async (licenseId) => {
    if (!isCorrectNetwork) {
      toast.error("Please switch to Sepolia testnet first");
      return;
    }

    setIsSubmitting(true);

    try {
      // Step 1: Prepare revocation in backend
      const revokeResponse = await licensesAPI.revoke(licenseId);

      if (!revokeResponse.success) {
        throw new Error(
          revokeResponse.detail || "Failed to prepare revocation"
        );
      }

      // If there's transaction data, send blockchain transaction
      if (revokeResponse.transaction_data) {
        const txResponse = await sendTransaction({
          ...revokeResponse.transaction_data,
          from: account,
        });

        setTransactionHash(txResponse.hash);

        // Create transaction record with better error handling
        try {
          const transactionData = {
            tx_hash: txResponse.hash,
            from_address: web3.utils.toChecksumAddress(account),
            to_address: web3.utils.toChecksumAddress(
              revokeResponse.transaction_data.to || account
            ),
            value: 0,
            transaction_type: "REVOKE_LICENSE",
            status: "PENDING",
            metadata: {
              license_id: licenseId,
            },
          };

          // Add retry logic
          for (let attempt = 0; attempt < 3; attempt++) {
            try {
              await transactionsAPI.create(transactionData);
              break;
            } catch (createError) {
              if (attempt === 2) {
                console.error(
                  "Failed to create revoke transaction record:",
                  createError
                );
              } else {
                await new Promise((resolve) => setTimeout(resolve, 1000));
              }
            }
          }
        } catch (transactionError) {
          console.warn(
            "License revoked but transaction record creation failed:",
            transactionError
          );
        }
      }

      toast.success("License revoked successfully!");

      // Refresh licenses after a delay
      setTimeout(async () => {
        try {
          const licensesRes = await licensesAPI.getByUser(account, {
            as_licensee: false,
          });
          let userLicenses = [];
          if (licensesRes.licenses) {
            userLicenses = licensesRes.licenses;
          } else if (Array.isArray(licensesRes)) {
            userLicenses = licensesRes;
          }
          setLicenses(userLicenses);
        } catch (error) {
          console.error("Error refreshing licenses:", error);
        }
      }, 2000);
    } catch (error) {
      console.error("License revocation failed:", error);

      if (error.code === 4001) {
        toast.error("Transaction cancelled by user");
      } else if (error.message.includes("License revocation failed:")) {
        toast.error(error.message);
      } else if (error.message) {
        toast.error(`License revocation failed: ${error.message}`);
      } else {
        toast.error("License revocation failed. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
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
            Please connect your MetaMask wallet to manage licenses.
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
            <Shield className="w-8 h-8 text-white" />
          </div>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Artwork Licensing
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Grant or revoke licenses for artwork usage with automatic license
          document generation and payment handling.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-8">
        <button
          className={`py-4 px-6 font-medium text-sm border-b-2 ${
            activeTab === "grant"
              ? "border-purple-600 text-purple-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
          onClick={() => setActiveTab("grant")}
        >
          Grant License
        </button>
        <button
          className={`py-4 px-6 font-medium text-sm border-b-2 ${
            activeTab === "revoke"
              ? "border-purple-600 text-purple-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
          onClick={() => setActiveTab("revoke")}
        >
          Manage Licenses
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <LoadingSpinner
            size="medium"
            text="Loading your artworks and licenses..."
          />
        </div>
      )}

      {/* Success Message */}
      {transactionHash && (
        <div className="mb-8 bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-green-800 mb-2">
              ✅ Transaction Submitted!
            </h3>
            <p className="text-green-600 mb-4">
              Your transaction has been submitted to the blockchain.
            </p>
            {transactionHash && (
              <div className="bg-white p-3 rounded border">
                <p className="text-sm text-gray-600 mb-1">Transaction Hash:</p>
                <p className="text-sm font-mono text-gray-800 break-all">
                  {typeof transactionHash === "string"
                    ? transactionHash
                    : transactionHash.hash}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* License Preview */}
      {licensePreview && (
        <div className="mb-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-800 mb-4">
            📄 Generated License Document Preview
          </h3>
          <div className="bg-white p-4 rounded-lg border text-sm">
            <h4 className="font-semibold mb-2">{licensePreview.title}</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <strong>Artwork:</strong> {licensePreview.artwork?.title} (#
                {licensePreview.artwork?.token_id})
              </div>
              <div>
                <strong>License Type:</strong>{" "}
                {licensePreview.license_terms?.type}
              </div>
              <div>
                <strong>Duration:</strong>{" "}
                {licensePreview.license_terms?.duration?.duration_days} days
              </div>
              <div>
                <strong>Fee:</strong>{" "}
                {licensePreview.technical_details?.license_fee}
              </div>
            </div>
            <div className="mb-3">
              <strong>Usage Rights:</strong>
              <p className="text-gray-600 text-xs mt-1">
                {licensePreview.terms_and_conditions?.usage_rights}
              </p>
            </div>
            <div className="mb-3">
              <strong>Permissions:</strong>
              <ul className="text-xs text-gray-600 mt-1 list-disc list-inside">
                {licensePreview.license_terms?.permissions?.map(
                  (permission, index) => (
                    <li key={index}>{permission}</li>
                  )
                )}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Grant License Form */}
      {activeTab === "grant" && !isLoading && (
        <div className="bg-white rounded-lg shadow-md">
          <form onSubmit={handleSubmit(onSubmitGrant)} className="p-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Form Fields */}
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Grant New License
                </h3>

                {/* Token ID */}
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                    <Image className="w-4 h-4 mr-2" />
                    Select Artwork
                  </label>
                  <select
                    {...register("token_id")}
                    onChange={(e) => {
                      handleArtworkChange(e.target.value);
                    }}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors ${
                      errors.token_id ? "border-red-300" : "border-gray-300"
                    }`}
                    disabled={artworks.length === 0}
                  >
                    <option value="">Select an artwork you own</option>
                    {artworks.map((artwork) => (
                      <option key={artwork.token_id} value={artwork.token_id}>
                        #{artwork.token_id} - {artwork.title || "Untitled"}
                      </option>
                    ))}
                  </select>
                  {errors.token_id && (
                    <p className="text-red-500 text-sm mt-1">
                      {errors.token_id.message}
                    </p>
                  )}
                  {artworks.length === 0 && (
                    <p className="text-orange-600 text-sm mt-1">
                      You don't own any artworks yet. Register artworks first.
                    </p>
                  )}
                </div>

                {/* Selected Artwork Info */}
                {selectedArtwork && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-medium text-blue-800 mb-2">
                      Selected Artwork:
                    </h4>
                    <p className="text-sm text-blue-700">
                      <strong>Title:</strong>{" "}
                      {selectedArtwork.title || "Untitled"}
                    </p>
                    <p className="text-sm text-blue-700">
                      <strong>Token ID:</strong> #{selectedArtwork.token_id}
                    </p>
                    {selectedArtwork.description && (
                      <p className="text-sm text-blue-700">
                        <strong>Description:</strong>{" "}
                        {selectedArtwork.description.length > 100
                          ? selectedArtwork.description.substring(0, 100) +
                            "..."
                          : selectedArtwork.description}
                      </p>
                    )}
                  </div>
                )}

                {/* Licensee Address */}
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                    <User className="w-4 h-4 mr-2" />
                    Licensee Wallet Address
                  </label>
                  <input
                    {...register("licensee_address")}
                    type="text"
                    placeholder="0x..."
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors ${
                      errors.licensee_address
                        ? "border-red-300"
                        : "border-gray-300"
                    }`}
                  />
                  {errors.licensee_address && (
                    <p className="text-red-500 text-sm mt-1">
                      {errors.licensee_address.message}
                    </p>
                  )}
                </div>

                {/* License Type */}
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                    <Shield className="w-4 h-4 mr-2" />
                    License Type
                  </label>
                  <select
                    {...register("license_type")}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors ${
                      errors.license_type ? "border-red-300" : "border-gray-300"
                    }`}
                  >
                    <option value="PERSONAL">Personal Use (0.1 ETH)</option>
                    <option value="COMMERCIAL">Commercial Use (0.1 ETH)</option>
                    <option value="EXCLUSIVE">
                      Exclusive Rights (0.1 ETH)
                    </option>
                  </select>
                  {errors.license_type && (
                    <p className="text-red-500 text-sm mt-1">
                      {errors.license_type.message}
                    </p>
                  )}
                </div>

                {/* Duration */}
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                    <Clock className="w-4 h-4 mr-2" />
                    Duration (Days)
                  </label>
                  <input
                    {...register("duration_days")}
                    type="number"
                    min="1"
                    max="365"
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors ${
                      errors.duration_days
                        ? "border-red-300"
                        : "border-gray-300"
                    }`}
                  />
                  {errors.duration_days && (
                    <p className="text-red-500 text-sm mt-1">
                      {errors.duration_days.message}
                    </p>
                  )}
                </div>

                {/* Submit Button */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-medium text-gray-700">
                      License Fee:
                    </span>
                    <span className="text-lg font-bold text-purple-600">
                      0.1 ETH
                    </span>
                  </div>

                  <button
                    type="submit"
                    disabled={
                      isSubmitting || !isCorrectNetwork || artworks.length === 0
                    }
                    className={`w-full flex items-center justify-center px-6 py-3 text-lg font-medium rounded-lg transition-colors ${
                      isSubmitting || !isCorrectNetwork || artworks.length === 0
                        ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                        : "bg-purple-600 text-white hover:bg-purple-700"
                    }`}
                  >
                    {isSubmitting ? (
                      <>
                        <LoadingSpinner size="small" text="" />
                        <span className="ml-2">Processing...</span>
                      </>
                    ) : (
                      <>
                        <Shield className="w-5 h-5 mr-2" />
                        Grant License (0.1 ETH)
                      </>
                    )}
                  </button>

                  {!isCorrectNetwork && (
                    <p className="text-orange-600 text-sm text-center mt-2">
                      Please switch to Sepolia testnet to manage licenses
                    </p>
                  )}
                </div>
              </div>

              {/* Info Panel */}
              <div className="space-y-6">
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-purple-800 mb-3">
                    📄 License Types
                  </h3>
                  <ul className="space-y-3 text-sm text-purple-700">
                    <li className="flex items-start">
                      <span className="font-semibold mr-2">PERSONAL:</span>
                      <span>Non-commercial use only</span>
                    </li>
                    <li className="flex items-start">
                      <span className="font-semibold mr-2">COMMERCIAL:</span>
                      <span>Commercial use with attribution</span>
                    </li>
                    <li className="flex items-start">
                      <span className="font-semibold mr-2">EXCLUSIVE:</span>
                      <span>Exclusive rights for licensee</span>
                    </li>
                  </ul>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-blue-800 mb-3">
                    💰 License Fees
                  </h3>
                  <ul className="space-y-2 text-sm text-blue-700">
                    <li>• All license types: 0.1 ETH</li>
                    <li>• Fees are automatically collected</li>
                    <li>• 90% to creator, 10% platform fee</li>
                  </ul>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-green-800 mb-3">
                    📋 Automatic License Documents
                  </h3>
                  <p className="text-sm text-green-700 mb-2">
                    License documents are automatically generated and stored on
                    IPFS with:
                  </p>
                  <ul className="space-y-1 text-sm text-green-600">
                    <li>• Detailed terms and conditions</li>
                    <li>• Usage rights and restrictions</li>
                    <li>• Attribution requirements</li>
                    <li>• Duration and termination terms</li>
                    <li>• Blockchain verification</li>
                  </ul>
                </div>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Manage Licenses */}
      {activeTab === "revoke" && !isLoading && (
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            Your Active Licenses ({licenses.length})
          </h2>

          {licenses.length === 0 ? (
            <div className="text-center py-12">
              <div className="bg-gray-50 rounded-lg p-8">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 mb-2">
                  You haven't granted any licenses yet
                </p>
                <p className="text-gray-400 text-sm">
                  Use the "Grant License" tab to create your first license
                </p>
              </div>
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
                      Licensee
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Expires
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {licenses.map((license) => {
                    // Handle different license object structures
                    const licenseId =
                      license.license_id || license.id || license._id;
                    const tokenId = license.token_id;
                    const licenseeAddress = license.licensee_address;
                    const licensorAddress = license.licensor_address;
                    const endDate = license.end_date;
                    const licenseType = license.license_type;
                    const isActive = license.is_active !== false; // default to true if undefined

                    return (
                      <tr key={licenseId}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                          #{licenseId}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          Token #{tokenId}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                          {licenseeAddress?.substring(0, 6)}...
                          {licenseeAddress?.substring(38)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(endDate).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${
                              licenseType === "PERSONAL"
                                ? "bg-blue-100 text-blue-800"
                                : licenseType === "COMMERCIAL"
                                ? "bg-purple-100 text-purple-800"
                                : "bg-green-100 text-green-800"
                            }`}
                          >
                            {licenseType}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${
                              isActive
                                ? "bg-green-100 text-green-800"
                                : "bg-red-100 text-red-800"
                            }`}
                          >
                            {isActive ? "Active" : "Revoked"}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          {isActive ? (
                            <button
                              onClick={() => onSubmitRevoke(licenseId)}
                              disabled={isSubmitting || !isCorrectNetwork}
                              className={`inline-flex items-center px-3 py-1 border rounded-md text-sm ${
                                isSubmitting || !isCorrectNetwork
                                  ? "bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed"
                                  : "bg-red-50 text-red-700 border-red-200 hover:bg-red-100"
                              }`}
                            >
                              <XCircle className="w-4 h-4 mr-1" />
                              Revoke
                            </button>
                          ) : (
                            <span className="text-gray-400 text-sm">
                              Revoked
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Licensing;
