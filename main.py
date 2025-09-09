from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.db.database import connect_to_mongo, close_mongo_connection
import os
import logging
import traceback
from mangum import Mangum  # <-- Add this

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ART_DRM Backend",
    version="1.0.0",
    description="Digital Rights Management for Artworks",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc"     # Optional
)

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Routes ----------------
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "ART_DRM Backend Service"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# ---------------- API Router ----------------
try:
    from app.api.v1 import router as api_router
    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    logger.error(f"API Router import error: {e}")

# ---------------- Static Files ----------------
if os.path.isdir("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ---------------- Database Events ----------------
@app.on_event("startup")
async def startup_db():
    try:
        await connect_to_mongo()
        logger.info("MongoDB connected")
    except Exception as e:
        logger.critical(f"Failed to connect MongoDB: {e}")

@app.on_event("shutdown")
async def shutdown_db():
    try:
        await close_mongo_connection()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# ---------------- Error Handling ----------------
@app.middleware("http")
async def error_handler(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# ---------------- Mangum Handler for Vercel ----------------
handler = Mangum(app)
