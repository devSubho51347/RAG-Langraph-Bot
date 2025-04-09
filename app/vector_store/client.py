from typing import List, Optional, Dict, Any
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    UpdateStatus,
    OptimizersConfigDiff,
    CollectionStatus,
)
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.core.config import get_settings

settings = get_settings()


class VectorStore:
    """Vector store client for Qdrant."""
    
    def __init__(self) -> None:
        """Initialize Qdrant client."""
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=10.0
        )
        self.collection_name = "documents"
        self.vector_size = 1536  # OpenAI ada-002 embedding size
    
    async def ensure_collection(self) -> None:
        """Ensure collection exists with proper configuration."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            # Create new collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                ),
                optimizers_config=OptimizersConfigDiff(
                    indexing_threshold=0,  # Index immediately
                ),
            )
            
            # Create payload index for session_id
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="session_id",
                field_schema="keyword"
            )
    
    async def add_texts(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[UUID] = None,
    ) -> List[str]:
        """Add texts and their embeddings to the vector store."""
        if len(texts) != len(embeddings):
            raise ValueError("Number of texts and embeddings must match")
        
        if metadata is None:
            metadata = [{} for _ in texts]
        
        if len(metadata) != len(texts):
            raise ValueError("Number of metadata items must match texts")
        
        # Prepare points for upload
        points = []
        for i, (text, embedding, meta) in enumerate(zip(texts, embeddings, metadata)):
            point = PointStruct(
                id=str(i),
                vector=embedding,
                payload={
                    "text": text,
                    **meta
                }
            )
            if session_id:
                point.payload["session_id"] = str(session_id)
            points.append(point)
        
        # Upload points
        operation_info = self.client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=points
        )
        
        if operation_info.status != UpdateStatus.COMPLETED:
            raise RuntimeError(f"Failed to upload vectors: {operation_info.status}")
        
        return [str(i) for i in range(len(texts))]
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        session_id: Optional[UUID] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar texts using embedding."""
        search_filter = None
        if session_id:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=str(session_id))
                    )
                ]
            )
        
        # Perform search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=limit
        )
        
        return [
            {
                "text": result.payload["text"],
                "score": result.score,
                **{k: v for k, v in result.payload.items() if k != "text"}
            }
            for result in results
        ]
    
    async def delete_by_session(self, session_id: UUID) -> None:
        """Delete all vectors for a given session."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=str(session_id))
                    )
                ]
            ),
            wait=True
        )
