from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .chat import router as chat_router

# Create v1 router
router = APIRouter(prefix="/api/v1")

# Include route modules
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
