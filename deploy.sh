#!/bin/bash

# DRM Backend Vercel Deployment Script

echo "🚀 Starting DRM Backend deployment to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if user is logged in to Vercel
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please log in to Vercel..."
    vercel login
fi

# Deploy to production
echo "📦 Deploying to Vercel..."
vercel --prod

echo "✅ Deployment complete!"
echo "📝 Don't forget to set your environment variables in the Vercel dashboard:"
echo "   - MONGODB_URI"
echo "   - JWT_SECRET_KEY"
echo "   - WEB3_PROVIDER_URL"
echo "   - CONTRACT_ADDRESS"
echo "   - And other required variables (see DEPLOYMENT.md)"