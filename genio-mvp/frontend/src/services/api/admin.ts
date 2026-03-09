"""
Admin API service.
"""
import { apiClient } from './client';

export const adminApi = {
  getStats: async (): Promise<any> => {
    const response = await apiClient.get('/admin/stats');
    return response.data;
  },

  getHealth: async (): Promise<any> => {
    const response = await apiClient.get('/admin/health');
    return response.data;
  },

  getUsers: async (): Promise<any[]> => {
    const response = await apiClient.get('/admin/users');
    return response.data;
  },

  getSecurityStats: async (): Promise<any> => {
    const response = await apiClient.get('/admin/security');
    return response.data;
  },

  updateUser: async (userId: string, data: any): Promise<any> => {
    const response = await apiClient.put(`/admin/users/${userId}`, data);
    return response.data;
  },

  getSystemConfig: async (): Promise<any> => {
    const response = await apiClient.get('/admin/config');
    return response.data;
  },

  updateSystemConfig: async (config: any): Promise<any> => {
    const response = await apiClient.put('/admin/config', config);
    return response.data;
  },
};
