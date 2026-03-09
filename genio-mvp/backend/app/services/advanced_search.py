"""
Advanced search with query operators support.

Supported operators:
- "exact phrase" - Phrase matching
- AND, OR, NOT - Boolean operators
- author:name - Filter by author
- tag:name - Filter by tag
- feed:name - Filter by feed
- date:2026-01-01 - Specific date
- date:2026-01-01..2026-12-31 - Date range
- delta:>0.7 - Delta score filter
- is:read, is:unread, is:favorite - Status filters
- sort:date, sort:delta - Sorting
"""
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedQuery:
    """Parsed search query with operators."""
    text_query: str = ""
    phrases: List[str] = None
    author: Optional[str] = None
    tags: List[str] = None
    feeds: List[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    delta_min: Optional[float] = None
    delta_max: Optional[float] = None
    is_read: Optional[bool] = None
    is_favorited: Optional[bool] = None
    is_archived: Optional[bool] = None
    sort_by: str = "relevance"
    sort_order: str = "desc"
    
    def __post_init__(self):
        if self.phrases is None:
            self.phrases = []
        if self.tags is None:
            self.tags = []
        if self.feeds is None:
            self.feeds = []


class AdvancedSearchParser:
    """Parser for advanced search queries."""
    
    # Regex patterns for operators
    PATTERNS = {
        'phrase': r'"([^"]+)"',
        'author': r'author:(\S+)',
        'tag': r'tag:(\S+)',
        'feed': r'feed:(\S+)',
        'date_exact': r'date:(\d{4}-\d{2}-\d{2})$',
        'date_range': r'date:(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})',
        'delta_gt': r'delta:>(\d+\.?\d*)',
        'delta_lt': r'delta:<(\d+\.?\d*)',
        'delta_range': r'delta:(\d+\.?\d*)\.\.(\d+\.?\d*)',
        'delta_exact': r'delta:(\d+\.?\d*)',
        'is_status': r'is:(read|unread|favorite|favorited|archived)',
        'sort': r'sort:(date|delta|score|relevance)',
        'sort_order': r'order:(asc|desc)',
        'word': r'(\w+)',
        'or_operator': r'\s+OR\s+',
        'not_operator': r'\s*-\s*(\w+)',
    }
    
    @classmethod
    def parse(cls, query: str) -> ParsedQuery:
        """Parse a search query string."""
        result = ParsedQuery()
        remaining = query
        
        # Extract phrases first (quoted text)
        phrases = re.findall(cls.PATTERNS['phrase'], remaining)
        result.phrases = phrases
        remaining = re.sub(cls.PATTERNS['phrase'], '', remaining)
        
        # Extract author
        author_match = re.search(cls.PATTERNS['author'], remaining)
        if author_match:
            result.author = author_match.group(1)
            remaining = re.sub(cls.PATTERNS['author'], '', remaining)
        
        # Extract tags
        tags = re.findall(cls.PATTERNS['tag'], remaining)
        result.tags = tags
        remaining = re.sub(cls.PATTERNS['tag'], '', remaining)
        
        # Extract feeds
        feeds = re.findall(cls.PATTERNS['feed'], remaining)
        result.feeds = feeds
        remaining = re.sub(cls.PATTERNS['feed'], '', remaining)
        
        # Extract date range
        date_range_match = re.search(cls.PATTERNS['date_range'], remaining)
        if date_range_match:
            result.date_from = date_range_match.group(1)
            result.date_to = date_range_match.group(2)
            remaining = re.sub(cls.PATTERNS['date_range'], '', remaining)
        else:
            # Extract exact date
            date_match = re.search(cls.PATTERNS['date_exact'], remaining)
            if date_match:
                result.date_from = date_match.group(1)
                result.date_to = date_match.group(1)
                remaining = re.sub(cls.PATTERNS['date_exact'], '', remaining)
        
        # Extract delta score filters
        delta_range_match = re.search(cls.PATTERNS['delta_range'], remaining)
        if delta_range_match:
            result.delta_min = float(delta_range_match.group(1))
            result.delta_max = float(delta_range_match.group(2))
            remaining = re.sub(cls.PATTERNS['delta_range'], '', remaining)
        else:
            delta_gt_match = re.search(cls.PATTERNS['delta_gt'], remaining)
            if delta_gt_match:
                result.delta_min = float(delta_gt_match.group(1))
                remaining = re.sub(cls.PATTERNS['delta_gt'], '', remaining)
            
            delta_lt_match = re.search(cls.PATTERNS['delta_lt'], remaining)
            if delta_lt_match:
                result.delta_max = float(delta_lt_match.group(1))
                remaining = re.sub(cls.PATTERNS['delta_lt'], '', remaining)
            
            delta_exact_match = re.search(cls.PATTERNS['delta_exact'], remaining)
            if delta_exact_match:
                val = float(delta_exact_match.group(1))
                result.delta_min = val
                result.delta_max = val
                remaining = re.sub(cls.PATTERNS['delta_exact'], '', remaining)
        
        # Extract status filters
        status_matches = re.findall(cls.PATTERNS['is_status'], remaining)
        for status in status_matches:
            if status in ('read',):
                result.is_read = True
            elif status in ('unread',):
                result.is_read = False
            elif status in ('favorite', 'favorited'):
                result.is_favorited = True
            elif status == 'archived':
                result.is_archived = True
        remaining = re.sub(cls.PATTERNS['is_status'], '', remaining)
        
        # Extract sort
        sort_match = re.search(cls.PATTERNS['sort'], remaining)
        if sort_match:
            result.sort_by = sort_match.group(1)
            remaining = re.sub(cls.PATTERNS['sort'], '', remaining)
        
        sort_order_match = re.search(cls.PATTERNS['sort_order'], remaining)
        if sort_order_match:
            result.sort_order = sort_order_match.group(1)
            remaining = re.sub(cls.PATTERNS['sort_order'], '', remaining)
        
        # Clean up remaining text
        remaining = re.sub(r'\s+', ' ', remaining).strip()
        
        # Handle NOT operator (words preceded by -)
        not_matches = re.findall(cls.PATTERNS['not_operator'], remaining)
        # Remove NOT terms from text query and handle separately
        for term in not_matches:
            remaining = remaining.replace(f'-{term}', '')
        
        # Handle OR operator
        if re.search(cls.PATTERNS['or_operator'], remaining, re.IGNORECASE):
            # Split by OR and join with proper syntax for backend
            parts = re.split(cls.PATTERNS['or_operator'], remaining, flags=re.IGNORECASE)
            result.text_query = ' OR '.join(p.strip() for p in parts if p.strip())
        else:
            result.text_query = remaining.strip()
        
        return result
    
    @classmethod
    def to_elasticsearch_query(cls, parsed: ParsedQuery, user_id: str) -> Dict[str, Any]:
        """Convert parsed query to Elasticsearch query DSL."""
        must_clauses = [{"term": {"user_id": user_id}}]
        filter_clauses = []
        should_clauses = []
        must_not_clauses = []
        
        # Text query
        if parsed.text_query:
            # Check for OR syntax
            if ' OR ' in parsed.text_query:
                terms = parsed.text_query.split(' OR ')
                should_clauses.append({
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": term.strip(),
                                    "fields": ["title^3", "content", "author^2", "tags.name^2.5"],
                                    "type": "best_fields"
                                }
                            }
                            for term in terms
                        ],
                        "minimum_should_match": 1
                    }
                })
            else:
                must_clauses.append({
                    "multi_match": {
                        "query": parsed.text_query,
                        "fields": ["title^3", "content", "author^2", "tags.name^2.5"],
                        "type": "best_fields"
                    }
                })
        
        # Phrases (exact match)
        for phrase in parsed.phrases:
            must_clauses.append({
                "multi_match": {
                    "query": phrase,
                    "fields": ["title^3", "content"],
                    "type": "phrase"
                }
            })
        
        # Author filter
        if parsed.author:
            filter_clauses.append({
                "match": {"author.keyword": parsed.author}
            })
        
        # Tags filter
        if parsed.tags:
            filter_clauses.append({
                "nested": {
                    "path": "tags",
                    "query": {
                        "terms": {"tags.name": parsed.tags}
                    }
                }
            })
        
        # Feeds filter
        if parsed.feeds:
            filter_clauses.append({
                "terms": {"source_name": parsed.feeds}
            })
        
        # Date range
        if parsed.date_from or parsed.date_to:
            date_range = {"range": {"published_at": {}}}
            if parsed.date_from:
                date_range["range"]["published_at"]["gte"] = parsed.date_from
            if parsed.date_to:
                date_range["range"]["published_at"]["lte"] = parsed.date_to
            filter_clauses.append(date_range)
        
        # Delta score range
        if parsed.delta_min is not None or parsed.delta_max is not None:
            delta_range = {"range": {"delta_score": {}}}
            if parsed.delta_min is not None:
                delta_range["range"]["delta_score"]["gte"] = parsed.delta_min
            if parsed.delta_max is not None:
                delta_range["range"]["delta_score"]["lte"] = parsed.delta_max
            filter_clauses.append(delta_range)
        
        # Status filters
        if parsed.is_read is not None:
            filter_clauses.append({"term": {"is_read": parsed.is_read}})
        if parsed.is_favorited is not None:
            filter_clauses.append({"term": {"is_favorited": parsed.is_favorited}})
        if parsed.is_archived is not None:
            filter_clauses.append({"term": {"is_archived": parsed.is_archived}})
        
        # Build final query
        query = {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses,
                "should": should_clauses if should_clauses else None,
                "must_not": must_not_clauses if must_not_clauses else None
            }
        }
        
        # Remove None values
        query["bool"] = {k: v for k, v in query["bool"].items() if v is not None}
        
        # Sorting
        sort_mapping = {
            "date": {"published_at": parsed.sort_order},
            "delta": {"delta_score": parsed.sort_order},
            "score": "_score",
            "relevance": "_score"
        }
        sort = sort_mapping.get(parsed.sort_by, "_score")
        
        return {"query": query, "sort": sort}


class SavedSearchAlert(SQLModel, table=True):
    """Saved search with alert functionality."""
    __tablename__ = "saved_searches"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    name: str
    query: str  # Raw query string
    parsed_query: str = Field(default="{}")  # JSON of parsed query
    
    # Alert settings
    alert_enabled: bool = Field(default=False)
    alert_frequency: str = Field(default="daily")  # hourly, daily, weekly
    alert_last_sent: Optional[datetime] = None
    alert_count: int = Field(default=0)
    
    # Results tracking
    last_result_count: int = Field(default=0)
    last_checked_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Import at end to avoid circular imports
from sqlmodel import Field, SQLModel
