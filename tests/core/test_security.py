from datetime import datetime, timedelta
import pytest
from uuid import UUID

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password
)


def test_password_hashing() -> None:
    """Test password hashing and verification."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_create_access_token() -> None:
    """Test JWT token creation."""
    user_id = UUID('12345678-1234-5678-1234-567812345678')
    username = "testuser"
    expires_delta = timedelta(minutes=15)
    
    token = create_access_token(
        user_id=user_id,
        username=username,
        expires_delta=expires_delta
    )
    
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token() -> None:
    """Test JWT token decoding."""
    user_id = UUID('12345678-1234-5678-1234-567812345678')
    username = "testuser"
    token = create_access_token(user_id=user_id, username=username)
    
    token_data = decode_access_token(token)
    assert token_data.user_id == user_id
    assert token_data.username == username


def test_decode_invalid_token() -> None:
    """Test decoding invalid JWT token."""
    with pytest.raises(ValueError):
        decode_access_token("invalid.token.here")


def test_token_expiration() -> None:
    """Test JWT token expiration."""
    user_id = UUID('12345678-1234-5678-1234-567812345678')
    username = "testuser"
    # Create token that expires immediately
    token = create_access_token(
        user_id=user_id,
        username=username,
        expires_delta=timedelta(microseconds=1)
    )
    
    # Wait for token to expire
    import time
    time.sleep(0.1)
    
    with pytest.raises(ValueError):
        decode_access_token(token)
