from typing import Dict, Any
from uuid import uuid4
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from app.db.models import User, Session
from app.rag.graph import create_chat_graph

pytestmark = pytest.mark.asyncio


async def test_create_session(
    test_client: AsyncClient,
    test_user: User,
    db_session: AsyncMock
) -> None:
    """Test creating a new chat session."""
    # Login first
    login_response = await test_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.username,
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Create session
    response = await test_client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Session"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Session"
    assert "id" in data


async def test_list_sessions(
    test_client: AsyncClient,
    test_user: User,
    db_session: AsyncMock
) -> None:
    """Test listing user's chat sessions."""
    # Create a session first
    session = Session(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Session"
    )
    db_session.add(session)
    await db_session.commit()
    
    # Login
    login_response = await test_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.username,
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]
    
    # List sessions
    response = await test_client.get(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(s["name"] == "Test Session" for s in data)


async def test_send_message(
    test_client: AsyncClient,
    test_user: User,
    db_session: AsyncMock
) -> None:
    """Test sending a message in a chat session."""
    # Create session
    session = Session(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Session"
    )
    db_session.add(session)
    await db_session.commit()
    
    # Login
    login_response = await test_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.username,
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Mock chat graph
    mock_graph = AsyncMock()
    mock_graph.ainvoke.return_value = {
        "response": "Test response"
    }
    
    with patch("app.api.v1.chat.create_chat_graph", return_value=mock_graph):
        # Send message
        response = await test_client.post(
            f"/api/v1/chat/sessions/{session.id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "Test message"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Test response"
