from fastapi import APIRouter
from app.api.v1 import auth, users

# Create v1 router
router = APIRouter()

# Include route modules
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
