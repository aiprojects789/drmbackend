from .auth import router as auth_router
from .artwork import router as artwork_router
from .blockchain import router as blockchain_router
from .piracy import router as piracy_router
from .admin import router as admin_router

__all__ = [
    "auth_router",
    "artwork_router", 
    "blockchain_router",
    "piracy_router",
    "admin_router"
]