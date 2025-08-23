from fastapi import APIRouter
from api.v1.endpoints import auth, artworks, licenses, transactions, web3

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(artworks.router, prefix="/artworks", tags=["artworks"])
api_router.include_router(licenses.router, prefix="/licenses", tags=["licenses"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(web3.router, prefix="/web3", tags=["web3"])