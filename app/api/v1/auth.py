from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import (
    Token,
    create_access_token,
    get_password_hash,
    verify_password
)
from app.db.crud import create_user, get_user_by_username
from app.db.schemas import UserCreate, UserResponse
from app.api.deps import DBSession
from app.core.config import get_settings

settings = get_settings()
router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: DBSession
) -> UserResponse:
    """Register a new user."""
    # Check if username already exists
    existing_user = await get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user with hashed password
    hashed_password = get_password_hash(user_data.password)
    user = await create_user(
        db,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    db: DBSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """Authenticate user and return JWT token."""
    # Get user from database
    user = await get_user_by_username(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(access_token=access_token)
