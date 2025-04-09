from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.db.schemas import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: CurrentUser
) -> UserResponse:
    """Get current user information."""
    return UserResponse.model_validate(current_user)
