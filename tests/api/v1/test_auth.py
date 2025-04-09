from typing import Dict, Any
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.core.security import verify_password

pytestmark = pytest.mark.asyncio


async def test_register_user(
    test_client: AsyncClient,
    db_session: AsyncSession
) -> None:
    """Test user registration endpoint."""
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert "created_at" in data


async def test_register_duplicate_username(
    test_client: AsyncClient,
    test_user: User
) -> None:
    """Test registration with existing username."""
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": test_user.username,
            "email": "another@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


async def test_login_success(
    test_client: AsyncClient,
    test_user: User
) -> None:
    """Test successful login."""
    response = await test_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.username,
            "password": "testpass123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_invalid_password(
    test_client: AsyncClient,
    test_user: User
) -> None:
    """Test login with invalid password."""
    response = await test_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.username,
            "password": "wrongpass"
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


async def test_login_invalid_username(
    test_client: AsyncClient
) -> None:
    """Test login with non-existent username."""
    response = await test_client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent",
            "password": "testpass123"
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


async def test_password_hashing(test_user: User) -> None:
    """Test password hashing functionality."""
    assert test_user.hashed_password != "testpass123"
    assert verify_password("testpass123", test_user.hashed_password)
