"""
API service for tag operations.
"""
import { apiClient } from './client';
import type { Tag, TagCreate, TagUpdate, TagCloudItem } from '../../types/tag';

export const tagApi = {
  // CRUD operations
  getAll: async (search?: string): Promise<Tag[]> => {
    const params = search ? { search } : {};
    const response = await apiClient.get('/tags', { params });
    return response.data;
  },

  get: async (id: string): Promise<Tag> => {
    const response = await apiClient.get(`/tags/${id}`);
    return response.data;
  },

  create: async (data: TagCreate): Promise<Tag> => {
    const response = await apiClient.post('/tags', data);
    return response.data;
  },

  update: async (id: string, data: TagUpdate): Promise<Tag> => {
    const response = await apiClient.put(`/tags/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/tags/${id}`);
  },

  // Autocomplete
  autocomplete: async (query: string, limit?: number): Promise<Tag[]> => {
    const response = await apiClient.get('/tags/autocomplete', {
      params: { q: query, limit }
    });
    return response.data;
  },

  // Tag cloud
  getCloud: async (minCount?: number): Promise<TagCloudItem[]> => {
    const response = await apiClient.get('/tags/cloud', {
      params: { min_count: minCount }
    });
    return response.data;
  },

  // Article tagging
  getArticleTags: async (articleId: string): Promise<Tag[]> => {
    const response = await apiClient.get(`/tags/articles/${articleId}/tags`);
    return response.data;
  },

  tagArticle: async (articleId: string, tagId: string): Promise<void> => {
    await apiClient.post(`/tags/articles/${articleId}/tags`, { tag_id: tagId });
  },

  untagArticle: async (articleId: string, tagId: string): Promise<void> => {
    await apiClient.delete(`/tags/articles/${articleId}/tags/${tagId}`);
  },

  // Document tagging
  getDocumentTags: async (documentId: string): Promise<Tag[]> => {
    const response = await apiClient.get(`/tags/documents/${documentId}/tags`);
    return response.data;
  },

  tagDocument: async (documentId: string, tagId: string): Promise<void> => {
    await apiClient.post(`/tags/documents/${documentId}/tags`, { tag_id: tagId });
  },

  untagDocument: async (documentId: string, tagId: string): Promise<void> => {
    await apiClient.delete(`/tags/documents/${documentId}/tags/${tagId}`);
  },

  // Bulk operations
  bulkTagArticles: async (
    articleIds: string[],
    tagId: string,
    action: 'add' | 'remove'
  ): Promise<{ processed_count: number }> => {
    const response = await apiClient.post('/tags/batch/articles/tags', {
      article_ids: articleIds,
      tag_id: tagId,
      action
    });
    return response.data;
  },
};
