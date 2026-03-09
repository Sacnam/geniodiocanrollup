"""
Vector Store - Qdrant integration for embeddings storage and search.
"""
from typing import List, Optional, Dict, Any
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.core.config import settings


class VectorStore:
    """Qdrant vector store wrapper."""
    
    def __init__(self):
        """Initialize Qdrant client."""
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=getattr(settings, 'QDRANT_API_KEY', None),
        )
        self.collection_name = getattr(settings, 'QDRANT_COLLECTION', 'genio')
        self.embedding_dim = getattr(settings, 'EMBEDDING_DIMENSION', 1536)
        
        # Ensure collection exists
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE,
                ),
            )
    
    def upsert_document(
        self,
        doc_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        content: Optional[str] = None,
    ) -> str:
        """
        Store or update a document embedding.
        
        Args:
            doc_id: Document ID
            embedding: Embedding vector
            metadata: Document metadata
            content: Optional content text
            
        Returns:
            Vector ID
        """
        vector_id = str(uuid.uuid4())
        
        point = PointStruct(
            id=vector_id,
            vector=embedding,
            payload={
                "doc_id": doc_id,
                "content": content,
                **metadata,
            },
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )
        
        return vector_id
    
    def search(
        self,
        vector: List[float],
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        score_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            vector: Query vector
            filter_dict: Filter conditions
            limit: Max results
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results
        """
        # Build filter
        search_filter = None
        if filter_dict:
            conditions = []
            for key, value in filter_dict.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                )
            if conditions:
                search_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            query_filter=search_filter,
            limit=limit,
            score_threshold=score_threshold,
        )
        
        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload,
            }
            for r in results
        ]
    
    def delete_document(self, vector_id: str) -> bool:
        """
        Delete a document by vector ID.
        
        Args:
            vector_id: Vector ID to delete
            
        Returns:
            True if deleted
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[vector_id],
            )
            return True
        except:
            return False
    
    def get_document(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by vector ID.
        
        Args:
            vector_id: Vector ID
            
        Returns:
            Document payload or None
        """
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[vector_id],
            )
            if result:
                return {
                    "id": result[0].id,
                    "payload": result[0].payload,
                }
            return None
        except:
            return None


# Singleton instance
vector_store = VectorStore()


# Helper functions for embeddings module
def store_document_embedding(
    doc_id: str,
    embedding: List[float],
    user_id: str,
    title: str,
    excerpt: str,
) -> str:
    """Store document embedding."""
    return vector_store.upsert_document(
        doc_id=doc_id,
        embedding=embedding,
        metadata={
            "type": "document",
            "user_id": user_id,
            "title": title,
            "excerpt": excerpt,
        },
        content=excerpt,
    )


def store_chunk_embeddings(
    chunk_id: str,
    embedding: List[float],
    document_id: str,
    user_id: str,
) -> str:
    """Store chunk embedding."""
    return vector_store.upsert_document(
        doc_id=chunk_id,
        embedding=embedding,
        metadata={
            "type": "chunk",
            "user_id": user_id,
            "document_id": document_id,
        },
    )
