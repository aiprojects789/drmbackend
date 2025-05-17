from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import inside function to prevent circular imports
@app.on_event("startup")
async def startup():
    from app.db.database import connect_to_mongo
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown():
    from app.db.database import close_mongo_connection
    await close_mongo_connection()

# Import router after app creation
from app.api.v1 import router as api_router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "ART_DRM Backend Service"}