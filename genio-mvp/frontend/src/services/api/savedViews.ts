"""
API service for saved views operations.
"""
import { apiClient } from './client';
import type { SavedView, FilterConfig } from '../../types/savedView';

export const savedViewApi = {
  getAll: async (includeSystem = true): Promise<SavedView[]> => {
    const response = await apiClient.get('/views', {
      params: { include_system: includeSystem }
    });
    return response.data;
  },

  get: async (id: string): Promise<SavedView> => {
    const response = await apiClient.get(`/views/${id}`);
    return response.data;
  },

  create: async (data: Partial<SavedView>): Promise<SavedView> => {
    const response = await apiClient.post('/views', data);
    return response.data;
  },

  update: async (id: string, data: Partial<SavedView>): Promise<SavedView> => {
    const response = await apiClient.put(`/views/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/views/${id}`);
  },

  setDefault: async (id: string): Promise<SavedView> => {
    const response = await apiClient.post(`/views/${id}/default`);
    return response.data;
  },

  reorder: async (viewIds: string[]): Promise<void> => {
    await apiClient.put('/views/reorder', { view_ids: viewIds });
  },

  share: async (id: string): Promise<{ share_token: string; share_url: string }> => {
    const response = await apiClient.post(`/views/${id}/share`);
    return response.data;
  },

  getShared: async (token: string): Promise<SavedView> => {
    const response = await apiClient.get(`/views/shared/${token}`);
    return response.data;
  },

  apply: async (id: string): Promise<{ items: any[]; total: number }> => {
    const response = await apiClient.get(`/views/${id}/apply`);
    return response.data;
  },
};
