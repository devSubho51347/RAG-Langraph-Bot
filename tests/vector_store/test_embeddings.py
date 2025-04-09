import pytest
from unittest.mock import patch, AsyncMock
import openai

from app.vector_store.embeddings import get_embeddings

pytestmark = pytest.mark.asyncio


async def test_get_embeddings_success() -> None:
    """Test successful embedding generation."""
    texts = ["Hello world", "Test text"]
    mock_response = AsyncMock()
    mock_response.data = [
        type("EmbeddingData", (), {"embedding": [0.1] * 1536}),
        type("EmbeddingData", (), {"embedding": [0.2] * 1536})
    ]
    
    with patch("openai.Embedding.acreate", return_value=mock_response):
        embeddings = await get_embeddings(texts)
        
        assert len(embeddings) == len(texts)
        assert all(len(emb) == 1536 for emb in embeddings)
        assert all(isinstance(val, float) for emb in embeddings for val in emb)


async def test_get_embeddings_retry() -> None:
    """Test retry behavior on rate limit."""
    texts = ["Test text"]
    mock_success = AsyncMock()
    mock_success.data = [
        type("EmbeddingData", (), {"embedding": [0.1] * 1536})
    ]
    
    with patch("openai.Embedding.acreate") as mock_create:
        # First call raises rate limit, second succeeds
        mock_create.side_effect = [
            openai.error.RateLimitError("Rate limit"),
            mock_success
        ]
        
        embeddings = await get_embeddings(texts)
        
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536
        assert mock_create.call_count == 2


async def test_get_embeddings_long_text() -> None:
    """Test handling of long texts."""
    long_text = "a" * 10000
    mock_response = AsyncMock()
    mock_response.data = [
        type("EmbeddingData", (), {"embedding": [0.1] * 1536})
    ]
    
    with patch("openai.Embedding.acreate", return_value=mock_response) as mock_create:
        await get_embeddings([long_text])
        
        # Verify text was truncated
        called_text = mock_create.call_args[1]["input"][0]
        assert len(called_text) <= 8191
