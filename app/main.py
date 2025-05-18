from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
import os
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)

def create_app() -> FastAPI:
    app = FastAPI(title="ART_DRM Backend")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ✅ Add exception logging middleware
    @app.middleware("http")
    async def log_exceptions(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logging.error(f"Unhandled exception: {e}")
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"}
            )

    # Lazy import to avoid circular dependencies
    from app.api.v1 import router as api_router
    from app.db.database import connect_to_mongo, close_mongo_connection

    # Register DB event handlers
    app.add_event_handler("startup", connect_to_mongo)
    app.add_event_handler("shutdown", close_mongo_connection)

    # Register API routes
    app.include_router(api_router, prefix="/api/v1")

    @app.get('/favicon.ico', include_in_schema=False)
    async def favicon():
        return FileResponse(os.path.join('static', 'favicon.ico'))

    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "ART_DRM Backend Service"}

    return app


# Instantiate and expose the app
app = create_app()
