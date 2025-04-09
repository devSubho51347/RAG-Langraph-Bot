import pytest
from uuid import uuid4
from typing import List

from app.vector_store.client import VectorStore

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def vector_store() -> VectorStore:
    """Create a test vector store instance."""
    store = VectorStore()
    await store.ensure_collection()
    return store


@pytest.fixture
def sample_texts() -> List[str]:
    """Sample texts for testing."""
    return [
        "The quick brown fox jumps over the lazy dog",
        "A journey of a thousand miles begins with a single step",
        "To be or not to be, that is the question"
    ]


@pytest.fixture
def sample_embeddings() -> List[List[float]]:
    """Sample embeddings for testing."""
    # Mock embeddings of size 1536 (OpenAI ada-002)
    return [
        [0.1] * 1536,
        [0.2] * 1536,
        [0.3] * 1536
    ]


async def test_add_texts(
    vector_store: VectorStore,
    sample_texts: List[str],
    sample_embeddings: List[List[float]]
) -> None:
    """Test adding texts to vector store."""
    session_id = uuid4()
    ids = await vector_store.add_texts(
        texts=sample_texts,
        embeddings=sample_embeddings,
        session_id=session_id
    )
    
    assert len(ids) == len(sample_texts)
    assert all(isinstance(id_, str) for id_ in ids)


async def test_similarity_search(
    vector_store: VectorStore,
    sample_texts: List[str],
    sample_embeddings: List[List[float]]
) -> None:
    """Test similarity search."""
    session_id = uuid4()
    await vector_store.add_texts(
        texts=sample_texts,
        embeddings=sample_embeddings,
        session_id=session_id
    )
    
    # Search using first embedding
    results = await vector_store.similarity_search(
        query_embedding=sample_embeddings[0],
        session_id=session_id,
        limit=2
    )
    
    assert len(results) <= 2
    assert isinstance(results[0]["text"], str)
    assert isinstance(results[0]["score"], float)
    assert 0 <= results[0]["score"] <= 1


async def test_delete_by_session(
    vector_store: VectorStore,
    sample_texts: List[str],
    sample_embeddings: List[List[float]]
) -> None:
    """Test deleting vectors by session."""
    session_id = uuid4()
    await vector_store.add_texts(
        texts=sample_texts,
        embeddings=sample_embeddings,
        session_id=session_id
    )
    
    # Delete vectors
    await vector_store.delete_by_session(session_id)
    
    # Search should return empty results
    results = await vector_store.similarity_search(
        query_embedding=sample_embeddings[0],
        session_id=session_id
    )
    
    assert len(results) == 0
