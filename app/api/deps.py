from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.crud import get_user_by_username
from app.db.database import get_db_session
from app.db.models import User

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Type aliases for dependencies
DBSession = Annotated[AsyncSession, Depends(get_db_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(
    db: DBSession,
    token: TokenDep,
) -> User:
    """Dependency to get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        token_data = decode_access_token(token)
        if not token_data:
            raise credentials_exception
        
        # Get user from database
        user = await get_user_by_username(db, token_data.username)
        if not user:
            raise credentials_exception
        
        return user
        
    except ValueError:
        raise credentials_exception


# Type alias for current user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]
