"""
Elasticsearch configuration and index mappings.
"""
from pydantic_settings import BaseSettings


class SearchSettings(BaseSettings):
    """Elasticsearch configuration."""
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX_PREFIX: str = "genio"
    ELASTICSEARCH_TIMEOUT: int = 30
    ELASTICSEARCH_MAX_RETRIES: int = 3
    
    # Search behavior
    SEARCH_RESULTS_PER_PAGE: int = 20
    SEARCH_MAX_RESULTS: int = 1000
    SEARCH_FUZZINESS: str = "AUTO"
    SEARCH_HIGHLIGHT_FRAGMENT_SIZE: int = 150
    SEARCH_HIGHLIGHT_MAX_FRAGMENTS: int = 3
    
    # Boost factors
    BOOST_TITLE: float = 3.0
    BOOST_CONTENT: float = 1.0
    BOOST_AUTHOR: float = 2.0
    BOOST_TAGS: float = 2.5
    BOOST_RECENCY: float = 1.2  # Multiplier for recent content
    
    class Config:
        env_prefix = "GENIO_"


search_settings = SearchSettings()


# Elasticsearch index mappings
ARTICLE_INDEX_MAPPING = {
    "settings": {
        "analysis": {
            "analyzer": {
                "genio_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding",
                        "genio_synonym_filter",
                        "genio_stop_filter"
                    ]
                },
                "genio_search_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding"
                    ]
                }
            },
            "filter": {
                "genio_synonym_filter": {
                    "type": "synonym_graph",
                    "synonyms": [
                        "ai, artificial intelligence",
                        "ml, machine learning",
                        "dl, deep learning",
                        "nlp, natural language processing",
                        "cv, computer vision"
                    ]
                },
                "genio_stop_filter": {
                    "type": "stop",
                    "stopwords": "_english_"
                }
            }
        },
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "5s"
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "user_id": {"type": "keyword"},
            "type": {"type": "keyword"},  # article, document, etc.
            
            # Content fields
            "title": {
                "type": "text",
                "analyzer": "genio_analyzer",
                "search_analyzer": "genio_search_analyzer",
                "boost": 3.0,
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "content": {
                "type": "text",
                "analyzer": "genio_analyzer",
                "search_analyzer": "genio_search_analyzer"
            },
            "excerpt": {
                "type": "text",
                "analyzer": "genio_analyzer"
            },
            "author": {
                "type": "text",
                "boost": 2.0,
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            
            # Tags
            "tags": {
                "type": "nested",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "color": {"type": "keyword"}
                }
            },
            
            # Feed/Document source
            "source_id": {"type": "keyword"},
            "source_name": {"type": "keyword"},
            "source_type": {"type": "keyword"},  # rss, pdf, etc.
            
            # URL
            "url": {"type": "keyword"},
            
            # Dates
            "published_at": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
            },
            "created_at": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
            },
            
            # Scores
            "delta_score": {"type": "float"},
            "reading_time_minutes": {"type": "integer"},
            
            # Status fields (for filtering)
            "is_read": {"type": "boolean"},
            "is_favorited": {"type": "boolean"},
            "is_archived": {"type": "boolean"},
            
            # Vector embedding for semantic search
            "embedding": {
                "type": "dense_vector",
                "dims": 1536,
                "index": True,
                "similarity": "cosine"
            },
            
            # Suggest fields for autocomplete
            "suggest_title": {
                "type": "completion",
                "analyzer": "simple"
            },
            "suggest_tags": {
                "type": "completion",
                "analyzer": "simple"
            }
        }
    }
}


# Index names
INDEX_ARTICLES = f"{search_settings.ELASTICSEARCH_INDEX_PREFIX}_articles"
INDEX_DOCUMENTS = f"{search_settings.ELASTICSEARCH_INDEX_PREFIX}_documents"
INDEX_SEARCH_LOGS = f"{search_settings.ELASTICSEARCH_INDEX_PREFIX}_search_logs"
