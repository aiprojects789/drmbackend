import React, { createContext, useContext, useState, useEffect } from 'react';
import { useWeb3 } from './Web3Context';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [loading, setLoading] = useState(false);
  const { account, connected, disconnectWallet: web3Disconnect } = useWeb3();

  // Auto-login when wallet connects
  useEffect(() => {
    if (connected && account && !user) {
      handleWalletConnect();
    }
  }, [connected, account]);

  const handleWalletConnect = async () => {
    if (!account) return;

    setLoading(true);
    try {
      const response = await authAPI.connectWallet({
        wallet_address: account,
        is_verified: false
      });

      setUser(response.user);
      setToken(response.access_token);
      localStorage.setItem('authToken', response.access_token);
      
      toast.success('Authentication successful!');
    } catch (error) {
      console.error('Authentication failed:', error);
      toast.error('Failed to authenticate with backend');
      // If auth fails, disconnect wallet
      web3Disconnect();
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    // Clear auth state
    setUser(null);
    setToken(null);
    localStorage.removeItem('authToken');
    // Disconnect wallet
    web3Disconnect();
    toast.success('Logged out successfully');
  };

  const getCurrentUser = async () => {
    if (!token) return null;

    try {
      const response = await authAPI.getCurrentUser(token);
      setUser(response);
      return response;
    } catch (error) {
      console.error('Failed to get current user:', error);
      handleLogout();
      return null;
    }
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!user && !!token && connected,
    login: handleWalletConnect,
    logout: handleLogout,
    getCurrentUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};