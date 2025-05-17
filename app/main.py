from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(title="ART_DRM Backend")
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Lazy imports to prevent circular dependencies
    from app.api.v1 import router as api_router
    from app.db.database import connect_to_mongo, close_mongo_connection
    
    # Database events
    app.add_event_handler("startup", connect_to_mongo)
    app.add_event_handler("shutdown", close_mongo_connection)
    
    # Include routers
    app.include_router(api_router, prefix="/api/v1")
    
    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "ART_DRM Backend Service"}
    
    return app

# Instantiate the application
app = create_app()