from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

router = APIRouter(tags=["Authentication"])  # This creates the router

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Example route
@router.post("/auth/login")
async def login():
    return {"message": "Login endpoint"}