from fastapi import APIRouter
from .auth import router as auth_router
from .artwork import router as artwork_router
from .blockchain import router as blockchain_router
from .admin import router as admin_router  
from .contact import router as contact_router
from .email import router as email_router
from .licenses import router as license_router   # 👈 direct router import
from .transactions import router as transactions_router  # 👈 agar file hai

router = APIRouter()

# Include all versioned routers
router.include_router(auth_router)
router.include_router(email_router)
router.include_router(contact_router)
router.include_router(artwork_router)
router.include_router(license_router)
router.include_router(transactions_router)
router.include_router(blockchain_router)
router.include_router(admin_router)
