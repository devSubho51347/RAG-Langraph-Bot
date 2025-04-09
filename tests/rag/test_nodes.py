from typing import Dict, Any
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from langchain_core.messages import HumanMessage
from app.rag.nodes import retrieve_context, generate_response, save_message
from app.db.models import Message

pytestmark = pytest.mark.asyncio


@pytest.fixture
def chat_state() -> Dict[str, Any]:
    """Sample chat state for testing."""
    return {
        "messages": [HumanMessage(content="What is the capital of France?")],
        "session_id": str(uuid4())
    }


async def test_retrieve_context(chat_state: Dict[str, Any]) -> None:
    """Test context retrieval."""
    with patch("app.rag.nodes.get_embeddings") as mock_embeddings, \
         patch("app.rag.nodes.VectorStore") as mock_store:
        # Mock embeddings
        mock_embeddings.return_value = [[0.1] * 1536]
        
        # Mock vector store search
        mock_instance = AsyncMock()
        mock_instance.similarity_search.return_value = [
            {"text": "Paris is the capital of France.", "score": 0.9}
        ]
        mock_store.return_value = mock_instance
        
        # Run retrieval
        result = await retrieve_context(chat_state)
        
        assert "context" in result
        assert "Paris is the capital of France" in result["context"]
        mock_instance.similarity_search.assert_called_once()


async def test_generate_response(chat_state: Dict[str, Any]) -> None:
    """Test response generation."""
    chat_state["context"] = "Paris is the capital of France."
    
    with patch("app.rag.nodes.ChatOpenAI") as mock_llm:
        # Mock LLM response
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value.content = "The capital of France is Paris."
        mock_llm.return_value = mock_instance
        
        # Generate response
        result = await generate_response(chat_state)
        
        assert "response" in result
        assert "Paris" in result["response"]
        mock_instance.ainvoke.assert_called_once()


async def test_save_message(
    chat_state: Dict[str, Any],
    db_session: AsyncMock
) -> None:
    """Test message saving."""
    chat_state.update({
        "db_session": db_session,
        "response": "The capital of France is Paris."
    })
    
    # Save message
    result = await save_message(chat_state)
    
    assert db_session.add.called
    assert db_session.commit.called
    assert db_session.refresh.called
