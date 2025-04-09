from typing import Dict
import pytest
from httpx import AsyncClient
from app.db.models import User

pytestmark = pytest.mark.asyncio


async def test_read_users_me(
    test_client: AsyncClient,
    test_user: User
) -> None:
    """Test getting current user information."""
    # First login to get token
    login_response = await test_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.username,
            "password": "testpass123"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Use token to get user info
    response = await test_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert str(test_user.id) == data["id"]


async def test_read_users_me_no_token(
    test_client: AsyncClient
) -> None:
    """Test accessing protected endpoint without token."""
    response = await test_client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


async def test_read_users_me_invalid_token(
    test_client: AsyncClient
) -> None:
    """Test accessing protected endpoint with invalid token."""
    response = await test_client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]
