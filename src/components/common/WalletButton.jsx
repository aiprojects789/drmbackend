import React from 'react';
import { Wallet, AlertCircle, CheckCircle } from 'lucide-react';
import { useWeb3 } from '../../contexts/Web3Context';
import { useAuth } from '../../contexts/AuthContext'; // Add this import

const WalletButton = () => {
  const { 
    connected, 
    connecting, 
    account, 
    balance, 
    networkName, 
    connectWallet, 
    disconnectWallet: web3Disconnect,
    isCorrectNetwork,
    switchToSepolia 
  } = useWeb3();
  const { logout } = useAuth(); // Now this will work

  const handleDisconnect = () => {
    logout(); // This will handle both auth and wallet disconnection
    web3Disconnect(); // Ensure wallet is disconnected
  };

  if (connected && account) {
    return (
      <div className="flex items-center space-x-2">
        {/* Network Status */}
        <div className="hidden sm:flex items-center space-x-2">
          {isCorrectNetwork ? (
            <div className="flex items-center space-x-1 text-green-600">
              <CheckCircle className="w-4 h-4" />
              <span className="text-xs">{networkName}</span>
            </div>
          ) : (
            <button
              onClick={switchToSepolia}
              className="flex items-center space-x-1 text-orange-600 hover:text-orange-700"
            >
              <AlertCircle className="w-4 h-4" />
              <span className="text-xs">Wrong Network</span>
            </button>
          )}
        </div>

        {/* Wallet Info */}
        <div className="flex items-center space-x-2 bg-gray-50 px-3 py-2 rounded-lg">
          <Wallet className="w-4 h-4 text-purple-600" />
          <div className="flex flex-col">
            <span className="text-xs text-gray-600">
              {account.substring(0, 6)}...{account.substring(38)}
            </span>
            <span className="text-xs text-gray-500">{balance} ETH</span>
          </div>
        </div>

        {/* Disconnect Button */}
        <button
          onClick={handleDisconnect}
          className="px-3 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
        >
          Disconnect
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={connectWallet}
      disabled={connecting}
      className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        connecting
          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
          : 'bg-purple-600 text-white hover:bg-purple-700'
      }`}
    >
      <Wallet className="w-4 h-4" />
      <span>{connecting ? 'Connecting...' : 'Connect Wallet'}</span>
    </button>
  );
};

export default WalletButton;