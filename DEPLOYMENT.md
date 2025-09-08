# Vercel Deployment Guide

## Prerequisites
1. Vercel account
2. MongoDB Atlas account
3. Environment variables configured

## Deployment Steps

### 1. Environment Variables
Set these environment variables in your Vercel dashboard:

```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=art_drm_production
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
WEB3_PROVIDER_URL=https://eth-sepolia.g.alchemy.com/v2/your-api-key
CONTRACT_ADDRESS=0xA07F45FE615E86C6BE90AD207952497c6F23d69d
DEMO_MODE=false
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://your-app.vercel.app
PINATA_API_KEY=your-pinata-api-key (optional)
PINATA_SECRET_API_KEY=your-pinata-secret-key (optional)
NFT_STORAGE_API_KEY=your-nft-storage-key (optional)
WEB3_STORAGE_API_KEY=your-web3-storage-key (optional)
```

### 2. Deploy to Vercel

#### Option A: Vercel CLI
```bash
npm i -g vercel
vercel login
vercel --prod
```

#### Option B: GitHub Integration
1. Push your code to GitHub
2. Connect your GitHub repo to Vercel
3. Vercel will automatically deploy

### 3. File Structure
The deployment uses:
- `api/index.py` - Main FastAPI application entry point
- `vercel.json` - Vercel configuration
- `requirements.txt` - Python dependencies

### 4. Important Notes
- The app uses MongoDB Atlas for database
- Static files in `uploads/` directory are served
- CORS is configured to allow all origins (adjust for production)
- All API routes are prefixed with `/api/v1`

### 5. Testing Deployment
After deployment, test these endpoints:
- `GET /` - Health check
- `GET /api/v1/` - API documentation
- `GET /api/v1/auth/` - Authentication endpoints
- `GET /api/v1/artwork/` - Artwork endpoints