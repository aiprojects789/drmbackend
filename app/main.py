from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, artwork, blockchain, piracy, admin
from app.db.database import init_db
from app.api.v1 import (
    auth_router,
    artwork_router,
    blockchain_router,
    piracy_router,
    admin_router
)
from app.api.v1 import auth_router, artwork_router
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
app = FastAPI(title="Digital Art DRM Platform",
              description="Blockchain-based digital rights management for artists")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from app.api.v1 import (
    auth_router,
    artwork_router,
    blockchain_router,
    piracy_router,
    admin_router
)




@app.on_event("startup")
async def startup_db():
    await init_db()

app.include_router(auth_router, prefix="/api/v1")
app.include_router(artwork_router, prefix="/api/v1")
app.include_router(blockchain_router, prefix="/api/v1") 
app.include_router(piracy_router, prefix="/api/v1")
app.include_router(admin_router)  # Note: No prefix since it's defined in the router

@app.get("/config-test")
async def config_test():
    return {
        "db_url": settings.MONGODB_URL,
        "db_name": settings.DB_NAME
    }
@app.get("/")
async def root():
    return {
        "message": "Digital Art DRM Platform",
        "docs": "/docs",
        "redoc": "/redoc"
    }

app.include_router(auth_router, prefix="/api/v1")
app.include_router(artwork_router, prefix="/api/v1")
