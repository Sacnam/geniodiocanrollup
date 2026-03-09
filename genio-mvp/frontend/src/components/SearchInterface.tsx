"""
Full-text search interface with Elasticsearch integration.
"""
import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search, X, Filter, Calendar, Tag, User, SlidersHorizontal,
  Sparkles, Loader2, ChevronDown, Hash
} from 'lucide-react';
import { searchApi } from '../services/api/search';
import { useDebounce } from '../hooks/useDebounce';
import type { SearchResult, SearchFilters, SearchFacets } from '../types/search';

interface SearchInterfaceProps {
  onResultClick?: (result: SearchResult) => void;
  className?: string;
}

export function SearchInterface({ onResultClick, className = '' }: SearchInterfaceProps) {
  const [query, setQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [page, setPage] = useState(1);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const debouncedQuery = useDebounce(query, 300);
  
  // Keyboard shortcut: / to focus search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === 'Escape') {
        setQuery('');
        inputRef.current?.blur();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['search', debouncedQuery, filters, page],
    queryFn: () => searchApi.search({
      q: debouncedQuery,
      page,
      per_page: 20,
      highlight: true,
      ...filters
    }),
    enabled: debouncedQuery.length > 0,
    staleTime: 60000,
  });
  
  const hasActiveFilters = Object.values(filters).some(v => v !== undefined && v !== '');
  
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setPage(1);
          }}
          placeholder="Search articles, documents... (Press / to focus)"
          className="input w-full pl-10 pr-20"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {isLoading && <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />}
          {query && (
            <button
              onClick={() => setQuery('')}
              className="p-1 hover:bg-muted rounded"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded transition-colors ${
              hasActiveFilters || showFilters
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-muted'
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Filters Panel */}
      {showFilters && (
        <SearchFiltersPanel
          filters={filters}
          onChange={setFilters}
          facets={data?.facets}
        />
      )}
      
      {/* Results */}
      {debouncedQuery && (
        <div className="space-y-4">
          {data && (
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>
                {data.total.toLocaleString()} results 
                {data.took_ms > 0 && `(in ${data.took_ms}ms)`}
              </span>
              <div className="flex gap-2">
                <select
                  value={filters.sort_by || 'relevance'}
                  onChange={(e) => setFilters({ ...filters, sort_by: e.target.value as any })}
                  className="text-sm bg-transparent border rounded px-2 py-1"
                >
                  <option value="relevance">Relevance</option>
                  <option value="published_at">Date</option>
                  <option value="delta_score">Knowledge Delta</option>
                </select>
              </div>
            </div>
          )}
          
          {error && (
            <div className="text-destructive p-4 text-center">
              Search failed. Please try again.
            </div>
          )}
          
          <div className="space-y-3">
            {data?.items.map((result) => (
              <SearchResultCard
                key={result.id}
                result={result}
                onClick={() => onResultClick?.(result)}
                query={debouncedQuery}
              />
            ))}
          </div>
          
          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex justify-center gap-2 pt-4">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn btn-secondary btn-sm"
              >
                Previous
              </button>
              <span className="px-3 py-1 text-sm text-muted-foreground">
                Page {page} of {data.total_pages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
                disabled={page >= data.total_pages}
                className="btn btn-secondary btn-sm"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
      
      {!debouncedQuery && (
        <div className="text-center py-12 text-muted-foreground">
          <Search className="w-16 h-16 mx-auto mb-4 opacity-20" />
          <p className="text-lg font-medium">Search your knowledge base</p>
          <p className="text-sm mt-1">
            Try: <kbd className="px-1 py-0.5 bg-muted rounded text-xs">artificial intelligence</kbd>
            {' '}or{' '}
            <kbd className="px-1 py-0.5 bg-muted rounded text-xs">"exact phrase"</kbd>
          </p>
        </div>
      )}
    </div>
  );
}

interface SearchResultCardProps {
  result: SearchResult;
  onClick?: () => void;
  query: string;
}

function SearchResultCard({ result, onClick, query }: SearchResultCardProps) {
  const hasHighlight = result.highlight && (
    result.highlight.title || result.highlight.content
  );
  
  return (
    <div
      onClick={onClick}
      className="p-4 bg-card border rounded-lg hover:border-primary/50 cursor-pointer transition-all group"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Title */}
          <h3 className="font-medium text-lg leading-tight mb-1">
            {hasHighlight && result.highlight?.title ? (
              <span 
                dangerouslySetInnerHTML={{ 
                  __html: result.highlight.title[0] 
                }} 
              />
            ) : (
              result.title
            )}
          </h3>
          
          {/* Meta */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
            {result.source_name && (
              <span className="flex items-center gap-1">
                <Hash className="w-3 h-3" />
                {result.source_name}
              </span>
            )}
            {result.author && (
              <span className="flex items-center gap-1">
                <User className="w-3 h-3" />
                {result.author}
              </span>
            )}
            {result.published_at && (
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {new Date(result.published_at).toLocaleDateString()}
              </span>
            )}
          </div>
          
          {/* Content Snippet */}
          <p className="text-sm text-muted-foreground line-clamp-2">
            {hasHighlight && result.highlight?.content ? (
              <span 
                dangerouslySetInnerHTML={{ 
                  __html: result.highlight.content[0] 
                }} 
              />
            ) : (
              result.excerpt || result.content?.substring(0, 200)
            )}
          </p>
          
          {/* Tags */}
          {result.tags && result.tags.length > 0 && (
            <div className="flex gap-1 mt-2 flex-wrap">
              {result.tags.map((tag) => (
                <span
                  key={tag.id}
                  className="text-xs px-2 py-0.5 rounded-full"
                  style={{
                    backgroundColor: `${tag.color}20`,
                    color: tag.color,
                  }}
                >
                  {tag.name}
                </span>
              ))}
            </div>
          )}
        </div>
        
        {/* Score/Delta indicator */}
        <div className="flex flex-col items-end gap-1">
          {result.delta_score > 0.7 && (
            <span className="flex items-center gap-1 text-xs text-yellow-600">
              <Sparkles className="w-3 h-3" />
              High Δ
            </span>
          )}
          {result._score && (
            <span className="text-xs text-muted-foreground">
              Score: {result._score.toFixed(2)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

interface SearchFiltersPanelProps {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  facets?: SearchFacets;
}

function SearchFiltersPanel({ filters, onChange, facets }: SearchFiltersPanelProps) {
  return (
    <div className="p-4 bg-muted/50 rounded-lg space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Read Status */}
        <div>
          <label className="label text-xs">Status</label>
          <select
            value={filters.is_read === undefined ? '' : String(filters.is_read)}
            onChange={(e) => {
              const val = e.target.value;
              onChange({
                ...filters,
                is_read: val === '' ? undefined : val === 'true'
              });
            }}
            className="input text-sm"
          >
            <option value="">Any</option>
            <option value="false">Unread</option>
            <option value="true">Read</option>
          </select>
        </div>
        
        {/* Favorited */}
        <div>
          <label className="label text-xs">Favorites</label>
          <select
            value={filters.is_favorited === undefined ? '' : String(filters.is_favorited)}
            onChange={(e) => {
              const val = e.target.value;
              onChange({
                ...filters,
                is_favorited: val === '' ? undefined : val === 'true'
              });
            }}
            className="input text-sm"
          >
            <option value="">Any</option>
            <option value="true">Favorited</option>
            <option value="false">Not favorited</option>
          </select>
        </div>
        
        {/* Date Range */}
        <div>
          <label className="label text-xs">From Date</label>
          <input
            type="date"
            value={filters.date_from || ''}
            onChange={(e) => onChange({ ...filters, date_from: e.target.value || undefined })}
            className="input text-sm"
          />
        </div>
        
        <div>
          <label className="label text-xs">To Date</label>
          <input
            type="date"
            value={filters.date_to || ''}
            onChange={(e) => onChange({ ...filters, date_to: e.target.value || undefined })}
            className="input text-sm"
          />
        </div>
      </div>
      
      {/* Facet Filters */}
      {facets && (
        <div className="grid grid-cols-2 gap-4">
          {facets.tags?.length > 0 && (
            <div>
              <label className="label text-xs flex items-center gap-1">
                <Tag className="w-3 h-3" />
                Tags
              </label>
              <div className="flex flex-wrap gap-1 mt-1">
                {facets.tags.slice(0, 10).map((tag) => (
                  <button
                    key={tag.name}
                    onClick={() => {
                      const currentTags = filters.tags || [];
                      const newTags = currentTags.includes(tag.name)
                        ? currentTags.filter(t => t !== tag.name)
                        : [...currentTags, tag.name];
                      onChange({ ...filters, tags: newTags.length > 0 ? newTags : undefined });
                    }}
                    className={`text-xs px-2 py-1 rounded-full transition-colors ${
                      filters.tags?.includes(tag.name)
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    {tag.name} ({tag.count})
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {facets.feeds?.length > 0 && (
            <div>
              <label className="label text-xs flex items-center gap-1">
                <Hash className="w-3 h-3" />
                Sources
              </label>
              <div className="flex flex-wrap gap-1 mt-1">
                {facets.feeds.slice(0, 10).map((feed) => (
                  <button
                    key={feed.name}
                    onClick={() => {
                      const currentFeeds = filters.feeds || [];
                      const newFeeds = currentFeeds.includes(feed.name)
                        ? currentFeeds.filter(f => f !== feed.name)
                        : [...currentFeeds, feed.name];
                      onChange({ ...filters, feeds: newFeeds.length > 0 ? newFeeds : undefined });
                    }}
                    className={`text-xs px-2 py-1 rounded-full transition-colors ${
                      filters.feeds?.includes(feed.name)
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    {feed.name} ({feed.count})
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
