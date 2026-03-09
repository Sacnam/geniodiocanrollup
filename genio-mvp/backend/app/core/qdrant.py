from functools import lru_cache
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    CollectionStatus,
    Distance,
    HnswConfig,
    PointIdsList,
    PointStruct,
    ScoredPoint,
    SearchParams,
    VectorParams,
)

from app.core.config import settings


class QdrantService:
    """Service for Qdrant vector database operations."""
    
    def __init__(self) -> None:
        self.client: Optional[QdrantClient] = None
        self.collection_name = getattr(settings, 'QDRANT_COLLECTION', 'genio')
    
    def connect(self) -> QdrantClient:
        if self.client is None:
            self.client = QdrantClient(url=settings.QDRANT_URL)
        return self.client
    
    def init_collection(self) -> bool:
        """Initialize articles collection if not exists."""
        client = self.connect()
        
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name in collection_names:
            return False  # Already exists
        
        # Create collection with HNSW index (B01: 1536-dim)
        client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=getattr(settings, 'EMBEDDING_DIMENSION', 1536),  # 1536
                distance=Distance.COSINE,
            ),
            hnsw_config=HnswConfig(
                m=16,
                ef_construct=100,
                full_scan_threshold=10000,
            ),
            optimizers_config={
                "default_segment_number": 2,
                "memmap_threshold_kb": 20000,
            },
        )
        
        return True
    
    def upsert_vectors(
        self,
        points: List[PointStruct],
        batch_size: int = 100,
    ) -> bool:
        """Upsert vectors in batches."""
        client = self.connect()
        
        # Process in batches
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            client.upsert(
                collection_name=self.collection_name,
                points=batch,
            )
        
        return True
    
    def search_similar(
        self,
        vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[dict] = None,
    ) -> List[ScoredPoint]:
        """Search for similar vectors."""
        client = self.connect()
        
        search_params = SearchParams(hnsw_ef=128)
        
        results = client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=filter_conditions,
            search_params=search_params,
        )
        
        return results
    
    def search_by_article_id(
        self,
        article_id: str,
        limit: int = 10,
        score_threshold: float = 0.85,
        time_filter_days: int = 7,
    ) -> List[ScoredPoint]:
        """Find similar articles to given article."""
        client = self.connect()
        
        # First, get the vector for the article
        result = client.retrieve(
            collection_name=self.collection_name,
            ids=[article_id],
            with_vectors=True,
        )
        
        if not result:
            return []
        
        vector = result[0].vector
        
        # Search for similar vectors
        from datetime import datetime, timedelta
        from qdrant_client.http.models import FieldCondition, Filter, Range
        
        cutoff_date = datetime.utcnow() - timedelta(days=time_filter_days)
        
        filter_conditions = Filter(
            must=[
                FieldCondition(
                    key="published_at",
                    range=Range(
                        gte=cutoff_date.isoformat(),
                    ),
                ),
            ],
        )
        
        results = client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=filter_conditions,
        )
        
        # Exclude self
        return [r for r in results if r.id != article_id]
    
    def delete_vectors(self, ids: List[str]) -> bool:
        """Delete vectors by IDs."""
        client = self.connect()
        
        client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=ids),
        )
        
        return True
    
    def get_collection_info(self) -> dict:
        """Get collection statistics."""
        client = self.connect()
        
        info = client.get_collection(self.collection_name)
        return {
            "name": info.config.params.vectors.size,
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "points_count": info.points_count,
            "status": info.status,
        }


@lru_cache()
def get_qdrant() -> QdrantService:
    return QdrantService()


qdrant_service = get_qdrant()
