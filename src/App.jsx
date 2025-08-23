import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { Web3Provider } from './contexts/Web3Context';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/layout/Navbar';
import Home from './pages/Home';
import Register from './pages/Register';
import Licensing from './pages/Licensing';
import Royalties from './pages/Royalties';
import Explorer from './pages/Explorer';
import Profile from './pages/Profile';
import SalePage from './pages/SalePage';
import ArtworkDetail from './pages/ArtworkDetail';

const queryClient = new QueryClient();

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/" replace />;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Web3Provider>
        <AuthProvider>
          <Router>
            <div className="min-h-screen bg-white">
              <Navbar />
              <main className="pt-16">
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/register" element={
                    <ProtectedRoute>
                      <Register />
                    </ProtectedRoute>
                  } />
                  <Route path="/licensing" element={
                    <ProtectedRoute>
                      <Licensing />
                    </ProtectedRoute>
                  } />
                  <Route path="/royalties" element={
                    <ProtectedRoute>
                      <Royalties />
                    </ProtectedRoute>
                  } />
                  <Route path="/explorer" element={<Explorer />} />
                  <Route path="/sale/:tokenId" element={<SalePage />} />
                  <Route path="/artwork/:tokenId" element={<ArtworkDetail />} />
                  <Route path="/profile" element={
                    <ProtectedRoute>
                      <Profile />
                    </ProtectedRoute>
                  } />
                </Routes>
              </main>
              <Toaster 
                position="top-right"
                toastOptions={{
                  style: {
                    background: '#ffffff',
                    color: '#374151',
                    border: '1px solid #e5e7eb',
                  },
                }}
              />
            </div>
          </Router>
        </AuthProvider>
      </Web3Provider>
    </QueryClientProvider>
  );
}

export default App;