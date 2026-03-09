"""
Elasticsearch service for full-text search.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from app.core.search_config import (
    search_settings, ARTICLE_INDEX_MAPPING,
    INDEX_ARTICLES, INDEX_DOCUMENTS
)
from app.core.ai_gateway import embed_texts

logger = logging.getLogger(__name__)


class SearchService:
    """Elasticsearch search service."""
    
    def __init__(self):
        self.client: Optional[AsyncElasticsearch] = None
        
    async def connect(self):
        """Initialize Elasticsearch connection."""
        if self.client is None:
            self.client = AsyncElasticsearch(
                [search_settings.ELASTICSEARCH_URL],
                timeout=search_settings.ELASTICSEARCH_TIMEOUT,
                max_retries=search_settings.ELASTICSEARCH_MAX_RETRIES,
                retry_on_timeout=True
            )
            logger.info("Elasticsearch client initialized")
    
    async def disconnect(self):
        """Close Elasticsearch connection."""
        if self.client:
            await self.client.close()
            self.client = None
    
    async def ensure_index(self, index_name: str, mapping: Dict = None):
        """Create index if it doesn't exist."""
        await self.connect()
        
        exists = await self.client.indices.exists(index=index_name)
        if not exists:
            mapping = mapping or ARTICLE_INDEX_MAPPING
            await self.client.indices.create(
                index=index_name,
                body=mapping
            )
            logger.info(f"Created index: {index_name}")
    
    async def index_article(
        self,
        article_id: str,
        user_id: str,
        title: str,
        content: str,
        excerpt: Optional[str] = None,
        author: Optional[str] = None,
        url: Optional[str] = None,
        published_at: Optional[datetime] = None,
        tags: List[Dict] = None,
        source_feed_id: Optional[str] = None,
        source_feed_title: Optional[str] = None,
        delta_score: float = 0.0,
        is_read: bool = False,
        is_favorited: bool = False,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """Index an article in Elasticsearch."""
        await self.connect()
        await self.ensure_index(INDEX_ARTICLES)
        
        doc = {
            "id": article_id,
            "user_id": user_id,
            "type": "article",
            "title": title,
            "content": content,
            "excerpt": excerpt or content[:500] if content else None,
            "author": author,
            "url": url,
            "published_at": published_at.isoformat() if published_at else None,
            "created_at": datetime.utcnow().isoformat(),
            "tags": tags or [],
            "source_id": source_feed_id,
            "source_name": source_feed_title,
            "source_type": "rss",
            "delta_score": delta_score,
            "is_read": is_read,
            "is_favorited": is_favorited,
            "is_archived": False,
            "suggest_title": {"input": title.split() if title else []},
            "suggest_tags": {"input": [t["name"] for t in tags] if tags else []}
        }
        
        if embedding:
            doc["embedding"] = embedding
        
        try:
            await self.client.index(
                index=INDEX_ARTICLES,
                id=article_id,
                document=doc,
                refresh=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to index article {article_id}: {e}")
            return False
    
    async def bulk_index_articles(self, articles: List[Dict]) -> Tuple[int, int]:
        """Bulk index multiple articles."""
        await self.connect()
        await self.ensure_index(INDEX_ARTICLES)
        
        actions = []
        for article in articles:
            actions.append({
                "_index": INDEX_ARTICLES,
                "_id": article["id"],
                "_source": article
            })
        
        try:
            success, errors = await async_bulk(
                self.client,
                actions,
                refresh=True
            )
            return success, len(errors)
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return 0, len(actions)
    
    async def search(
        self,
        user_id: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        content_types: List[str] = None,
        sort_by: str = "relevance",
        page: int = 1,
        per_page: int = None,
        highlight: bool = True,
        fuzzy: bool = False
    ) -> Dict[str, Any]:
        """Execute full-text search."""
        await self.connect()
        per_page = per_page or search_settings.SEARCH_RESULTS_PER_PAGE
        
        # Build query
        must_clauses = [{"term": {"user_id": user_id}}]
        
        if content_types:
            must_clauses.append({"terms": {"type": content_types}})
        
        # Main search query
        if query:
            # Check for phrase search (quoted)
            if query.startswith('"') and query.endswith('"'):
                # Exact phrase match
                search_clause = {
                    "match_phrase": {
                        "content": {
                            "query": query[1:-1],
                            "boost": 2.0
                        }
                    }
                }
            else:
                # Standard multi-match with field boosting
                search_clause = {
                    "multi_match": {
                        "query": query,
                        "fields": [
                            f"title^{search_settings.BOOST_TITLE}",
                            f"content^{search_settings.BOOST_CONTENT}",
                            f"author^{search_settings.BOOST_AUTHOR}",
                            "tags.name^2.5",
                            "excerpt^1.5"
                        ],
                        "type": "best_fields",
                        "fuzziness": search_settings.SEARCH_FUZZINESS if fuzzy else "0",
                        "prefix_length": 1
                    }
                }
            must_clauses.append(search_clause)
        
        # Apply filters
        filter_clauses = []
        if filters:
            if filters.get("is_read") is not None:
                filter_clauses.append({"term": {"is_read": filters["is_read"]}})
            if filters.get("is_favorited") is not None:
                filter_clauses.append({"term": {"is_favorited": filters["is_favorited"]}})
            if filters.get("is_archived") is not None:
                filter_clauses.append({"term": {"is_archived": filters["is_archived"]}})
            
            if filters.get("tags"):
                filter_clauses.append({
                    "nested": {
                        "path": "tags",
                        "query": {
                            "terms": {"tags.id": filters["tags"]}
                        }
                    }
                })
            
            if filters.get("feeds"):
                filter_clauses.append({"terms": {"source_id": filters["feeds"]}})
            
            if filters.get("date_from") or filters.get("date_to"):
                date_range = {"range": {"published_at": {}}}
                if filters.get("date_from"):
                    date_range["range"]["published_at"]["gte"] = filters["date_from"]
                if filters.get("date_to"):
                    date_range["range"]["published_at"]["lte"] = filters["date_to"]
                filter_clauses.append(date_range)
            
            if filters.get("delta_score_min") is not None:
                filter_clauses.append({
                    "range": {
                        "delta_score": {"gte": filters["delta_score_min"]}
                    }
                })
            
            if filters.get("author"):
                filter_clauses.append({
                    "match": {"author.keyword": filters["author"]}
                })
        
        # Build complete query
        es_query = {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
            }
        }
        
        # Sorting
        sort_clause = []
        if sort_by == "relevance" and query:
            sort_clause.append("_score")
        elif sort_by == "published_at":
            sort_clause.append({"published_at": "desc"})
        elif sort_by == "delta_score":
            sort_clause.append({"delta_score": "desc"})
        elif sort_by == "created_at":
            sort_clause.append({"created_at": "desc"})
        
        # Always add _score as secondary sort
        if sort_by != "relevance":
            sort_clause.append("_score")
        
        # Highlighting
        highlight_config = None
        if highlight and query:
            highlight_config = {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
                "fields": {
                    "title": {"fragment_size": 150, "number_of_fragments": 1},
                    "content": {"fragment_size": 150, "number_of_fragments": 3},
                    "excerpt": {"fragment_size": 150, "number_of_fragments": 1}
                }
            }
        
        # Facets (aggregations)
        aggs = {
            "tags": {
                "nested": {"path": "tags"},
                "aggs": {
                    "tag_names": {
                        "terms": {"field": "tags.name", "size": 20}
                    }
                }
            },
            "feeds": {
                "terms": {"field": "source_name", "size": 20}
            },
            "date_histogram": {
                "date_histogram": {
                    "field": "published_at",
                    "calendar_interval": "month"
                }
            }
        }
        
        try:
            response = await self.client.search(
                index=INDEX_ARTICLES,
                query=es_query,
                sort=sort_clause,
                highlight=highlight_config,
                aggs=aggs,
                from_=(page - 1) * per_page,
                size=per_page,
                track_total_hits=True
            )
            
            # Format results
            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]
            
            items = []
            for hit in hits:
                item = {
                    "id": hit["_source"]["id"],
                    "type": hit["_source"]["type"],
                    "title": hit["_source"].get("title"),
                    "content": hit["_source"].get("content", "")[:1000],  # Truncate
                    "author": hit["_source"].get("author"),
                    "published_at": hit["_source"].get("published_at"),
                    "tags": hit["_source"].get("tags", []),
                    "source_name": hit["_source"].get("source_name"),
                    "delta_score": hit["_source"].get("delta_score", 0),
                    "is_read": hit["_source"].get("is_read", False),
                    "is_favorited": hit["_source"].get("is_favorited", False),
                    "_score": hit["_score"]
                }
                
                if highlight and "highlight" in hit:
                    item["highlight"] = hit["highlight"]
                
                items.append(item)
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page,
                "took_ms": response.get("took", 0),
                "facets": {
                    "tags": [
                        {"name": b["key"], "count": b["doc_count"]}
                        for b in response["aggregations"]["tags"]["tag_names"]["buckets"]
                    ],
                    "feeds": [
                        {"name": b["key"], "count": b["doc_count"]}
                        for b in response["aggregations"]["feeds"]["buckets"]
                    ],
                    "date_histogram": [
                        {"date": b["key_as_string"], "count": b["doc_count"]}
                        for b in response["aggregations"]["date_histogram"]["buckets"]
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
                "took_ms": 0,
                "facets": {"tags": [], "feeds": [], "date_histogram": []},
                "error": str(e)
            }
    
    async def semantic_search(
        self,
        user_id: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        per_page: int = None
    ) -> Dict[str, Any]:
        """Semantic search using vector similarity."""
        await self.connect()
        per_page = per_page or search_settings.SEARCH_RESULTS_PER_PAGE
        
        # Generate embedding for query
        try:
            embeddings = await embed_texts([query])
            query_vector = embeddings[0]
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return {"items": [], "total": 0, "error": "Embedding failed"}
        
        # Build kNN query
        knn_query = {
            "field": "embedding",
            "query_vector": query_vector,
            "k": per_page,
            "num_candidates": per_page * 2,
            "filter": {"term": {"user_id": user_id}}
        }
        
        # Add additional filters
        if filters:
            filter_clauses = []
            if filters.get("is_read") is not None:
                filter_clauses.append({"term": {"is_read": filters["is_read"]}})
            if filters.get("tags"):
                filter_clauses.append({
                    "nested": {
                        "path": "tags",
                        "query": {"terms": {"tags.id": filters["tags"]}}
                    }
                })
            
            if filter_clauses:
                knn_query["filter"] = {"bool": {"filter": filter_clauses}}
        
        try:
            response = await self.client.search(
                index=INDEX_ARTICLES,
                knn=knn_query,
                from_=(page - 1) * per_page,
                size=per_page
            )
            
            hits = response["hits"]["hits"]
            
            items = []
            for hit in hits:
                items.append({
                    "id": hit["_source"]["id"],
                    "type": hit["_source"]["type"],
                    "title": hit["_source"].get("title"),
                    "excerpt": hit["_source"].get("excerpt"),
                    "semantic_score": hit["_score"],
                    "published_at": hit["_source"].get("published_at")
                })
            
            return {
                "items": items,
                "total": len(items),
                "page": page,
                "per_page": per_page,
                "took_ms": response.get("took", 0)
            }
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {"items": [], "total": 0, "error": str(e)}
    
    async def get_suggestions(
        self,
        user_id: str,
        query: str,
        size: int = 10
    ) -> List[str]:
        """Get autocomplete suggestions."""
        await self.connect()
        
        suggest_query = {
            "suggest": {
                "title_suggest": {
                    "prefix": query,
                    "completion": {
                        "field": "suggest_title",
                        "size": size,
                        "fuzzy": {"fuzziness": "AUTO"}
                    }
                },
                "tag_suggest": {
                    "prefix": query,
                    "completion": {
                        "field": "suggest_tags",
                        "size": size
                    }
                }
            },
            "query": {"term": {"user_id": user_id}}
        }
        
        try:
            response = await self.client.search(
                index=INDEX_ARTICLES,
                body=suggest_query,
                size=0
            )
            
            suggestions = set()
            
            # Extract title suggestions
            title_options = response["suggest"]["title_suggest"][0]["options"]
            for opt in title_options:
                suggestions.add(opt["text"])
            
            # Extract tag suggestions
            tag_options = response["suggest"]["tag_suggest"][0]["options"]
            for opt in tag_options:
                suggestions.add(opt["text"])
            
            return list(suggestions)[:size]
            
        except Exception as e:
            logger.error(f"Suggestions failed: {e}")
            return []
    
    async def delete_document(self, index: str, doc_id: str):
        """Delete a document from the index."""
        await self.connect()
        try:
            await self.client.delete(index=index, id=doc_id, refresh=True)
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False
    
    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get search index statistics."""
        await self.connect()
        
        try:
            # Count documents for user
            count_response = await self.client.count(
                index=INDEX_ARTICLES,
                query={"term": {"user_id": user_id}}
            )
            
            # Get index stats
            stats_response = await self.client.indices.stats(index=INDEX_ARTICLES)
            
            return {
                "total_indexed": count_response["count"],
                "total_index_size_mb": stats_response["indices"][INDEX_ARTICLES]["total"]["store"]["size_in_bytes"] / (1024 * 1024),
                "last_index_update": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"total_indexed": 0, "error": str(e)}


# Global instance
search_service = SearchService()
