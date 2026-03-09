"""
TypeScript types for full-text search.
"""

export interface SearchResult {
  id: string;
  type: 'article' | 'document';
  title: string;
  content?: string;
  excerpt?: string;
  author?: string;
  published_at?: string;
  tags: Array<{
    id: string;
    name: string;
    color?: string;
  }>;
  source_name?: string;
  delta_score: number;
  is_read: boolean;
  is_favorited: boolean;
  _score?: number;
  semantic_score?: number;
  highlight?: {
    title?: string[];
    content?: string[];
    excerpt?: string[];
  };
}

export interface SearchFilters {
  is_read?: boolean;
  is_favorited?: boolean;
  is_archived?: boolean;
  tags?: string[];
  feeds?: string[];
  author?: string;
  date_from?: string;
  date_to?: string;
  delta_score_min?: number;
  sort_by?: 'relevance' | 'published_at' | 'delta_score' | 'created_at';
  sort_order?: 'asc' | 'desc';
}

export interface SearchFacet {
  name: string;
  count: number;
}

export interface SearchFacets {
  tags: SearchFacet[];
  feeds: SearchFacet[];
  date_histogram: Array<{
    date: string;
    count: number;
  }>;
}

export interface SearchResponse {
  items: SearchResult[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  took_ms: number;
  facets: SearchFacets;
  error?: string;
}

export interface SemanticSearchResponse {
  items: Array<SearchResult & { semantic_score: number }>;
  total: number;
  page: number;
  per_page: number;
  took_ms: number;
}
