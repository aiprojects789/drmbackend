from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from db.database import connect_to_mongo, close_mongo_connection
from api.v1.router import api_router

app = FastAPI(
    title="ArtDRM API",
    description="Artwork Digital Rights Management System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown") 
async def shutdown_event():
    await close_mongo_connection()

# Include routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "ArtDRM API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)