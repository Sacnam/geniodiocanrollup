"""
API service for full-text search operations.
"""
import { apiClient } from './client';
import type { SearchResponse, SearchFilters, SearchResult } from '../../types/search';

export const searchApi = {
  search: async (params: {
    q: string;
    page?: number;
    per_page?: number;
    highlight?: boolean;
    fuzzy?: boolean;
    sort_by?: 'relevance' | 'published_at' | 'delta_score' | 'created_at';
  } & SearchFilters): Promise<SearchResponse> => {
    const response = await apiClient.get('/search', { params });
    return response.data;
  },

  semanticSearch: async (params: {
    q: string;
    page?: number;
    per_page?: number;
  } & SearchFilters): Promise<SearchResponse> => {
    const response = await apiClient.get('/search/semantic', { params });
    return response.data;
  },

  suggest: async (query: string): Promise<string[]> => {
    const response = await apiClient.get('/search/suggest', {
      params: { q: query }
    });
    return response.data.suggestions;
  },

  getStats: async () => Promise<{
    total_indexed: number;
    total_index_size_mb: number;
    last_index_update: string;
  }> => {
    const response = await apiClient.get('/search/stats');
    return response.data;
  },

  reindex: async (): Promise<{ message: string; task_id: string }> => {
    const response = await apiClient.post('/search/reindex');
    return response.data;
  },
};
