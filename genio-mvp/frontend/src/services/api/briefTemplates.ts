"""
API service for brief template operations.
"""
import { apiClient } from './client';
import type { BriefTemplate, BriefTemplateCreate, BriefTemplateUpdate } from '../../types/briefTemplate';

export const briefTemplateApi = {
  getAll: async (includeInactive = false): Promise<BriefTemplate[]> => {
    const response = await apiClient.get('/brief-templates', {
      params: { include_inactive: includeInactive }
    });
    return response.data;
  },

  get: async (id: string): Promise<BriefTemplate> => {
    const response = await apiClient.get(`/brief-templates/${id}`);
    return response.data;
  },

  create: async (data: Partial<BriefTemplateCreate>): Promise<BriefTemplate> => {
    const response = await apiClient.post('/brief-templates', data);
    return response.data;
  },

  update: async (id: string, data: Partial<BriefTemplateUpdate>): Promise<BriefTemplate> => {
    const response = await apiClient.put(`/brief-templates/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/brief-templates/${id}`);
  },

  setDefault: async (id: string): Promise<{ status: string; template_id: string }> => {
    const response = await apiClient.post(`/brief-templates/${id}/set-default`);
    return response.data;
  },

  preview: async (id: string): Promise<any> => {
    const response = await apiClient.post(`/brief-templates/${id}/preview`);
    return response.data;
  },

  getLayouts: async (): Promise<Array<{ id: string; name: string; description: string }>> => {
    const response = await apiClient.get('/brief-templates/layouts/available');
    return response.data;
  },
};
