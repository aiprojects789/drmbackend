import React from 'react';
import { Link } from 'react-router-dom';
import { Palette, Shield, DollarSign, Users, ArrowRight, CheckCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const Home = () => {
  const { isAuthenticated } = useAuth();

  const features = [
    {
      icon: <Palette className="w-8 h-8 text-purple-600" />,
      title: 'Artwork Registration',
      description: 'Register your digital artwork on the blockchain with built-in royalty management and ownership verification.'
    },
    {
      icon: <Shield className="w-8 h-8 text-purple-600" />,
      title: 'Licensing System',
      description: 'Grant and manage licenses for your artwork with automatic payment handling and terms enforcement.'
    },
    {
      icon: <DollarSign className="w-8 h-8 text-purple-600" />,
      title: 'Royalty Management',
      description: 'Earn automatic royalties on secondary sales with customizable percentages and transparent distribution.'
    },
    {
      icon: <Users className="w-8 h-8 text-purple-600" />,
      title: 'Artist Community',
      description: 'Connect with other artists and collectors in a secure, decentralized marketplace environment.'
    }
  ];

  const benefits = [
    'Blockchain-based ownership verification',
    'Automatic royalty payments',
    'Flexible licensing terms',
    'Transparent transaction history',
    'Secure smart contract infrastructure',
    'IPFS metadata storage'
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-purple-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6">
              Protect Your Digital
              <span className="text-purple-600 block">Artwork Rights</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              A comprehensive Digital Rights Management system for artists. Register, license, 
              and earn royalties from your digital creations on the blockchain.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              {isAuthenticated ? (
                <>
                  <Link
                    to="/register"
                    className="inline-flex items-center px-8 py-3 text-lg font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
                  >
                    Register Artwork
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Link>
                  <Link
                    to="/explorer"
                    className="inline-flex items-center px-8 py-3 text-lg font-medium text-purple-600 border-2 border-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                  >
                    Explore Artworks
                  </Link>
                </>
              ) : (
                <>
                  <div className="inline-flex items-center px-8 py-3 text-lg font-medium text-white bg-purple-600 rounded-lg">
                    Connect Wallet to Get Started
                  </div>
                  <Link
                    to="/explorer"
                    className="inline-flex items-center px-8 py-3 text-lg font-medium text-purple-600 border-2 border-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                  >
                    Explore Artworks
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Everything You Need to Protect Your Art
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Our platform provides comprehensive tools for digital rights management, 
              from registration to royalty collection.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="text-center p-6 rounded-lg border border-gray-200 hover:border-purple-200 hover:shadow-md transition-all">
                <div className="flex justify-center mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Benefits Section */}
      <div className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-6">
                Why Choose ArtDRM?
              </h2>
              <p className="text-lg text-gray-600 mb-8">
                Built on blockchain technology, our platform ensures your digital rights 
                are protected, transparent, and enforceable across the digital ecosystem.
              </p>
              
              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-gray-700">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white p-8 rounded-xl shadow-lg">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Getting Started is Easy
              </h3>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="bg-purple-600 text-white w-6 h-6 rounded-full flex items-center justify-center text-sm font-medium">
                    1
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Connect Your Wallet</h4>
                    <p className="text-sm text-gray-600">Connect your MetaMask wallet to get started</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="bg-purple-600 text-white w-6 h-6 rounded-full flex items-center justify-center text-sm font-medium">
                    2
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Register Your Artwork</h4>
                    <p className="text-sm text-gray-600">Upload metadata and set royalty percentages</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="bg-purple-600 text-white w-6 h-6 rounded-full flex items-center justify-center text-sm font-medium">
                    3
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Start Earning</h4>
                    <p className="text-sm text-gray-600">Grant licenses and earn automatic royalties</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-20 bg-purple-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Protect Your Digital Art?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
            Join thousands of artists who trust ArtDRM to protect their digital creations 
            and earn fair compensation for their work.
          </p>
          
          {isAuthenticated ? (
            <Link
              to="/register"
              className="inline-flex items-center px-8 py-3 text-lg font-medium text-purple-600 bg-white hover:bg-gray-100 rounded-lg transition-colors"
            >
              Register Your First Artwork
              <ArrowRight className="ml-2 w-5 h-5" />
            </Link>
          ) : (
            <div className="inline-flex items-center px-8 py-3 text-lg font-medium text-purple-600 bg-white rounded-lg">
              Connect Wallet to Get Started
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Home;