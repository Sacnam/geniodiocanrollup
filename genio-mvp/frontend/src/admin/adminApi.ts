import { api } from '../services/api';

export const adminApi = {
  // Stats
  getStats: async () => {
    const { data } = await api.get('/admin/stats');
    return data;
  },

  // Users
  getUsers: async (params?: { limit?: number; offset?: number; search?: string }) => {
    const { data } = await api.get('/admin/users', { params });
    return data;
  },

  updateUserTier: async (userId: string, tier: string) => {
    const { data } = await api.post(`/admin/users/${userId}/tier`, { tier });
    return data;
  },

  disableUser: async (userId: string) => {
    const { data } = await api.post(`/admin/users/${userId}/disable`);
    return data;
  },

  // Health
  getHealth: async () => {
    const { data } = await api.get('/admin/health');
    return data;
  },

  // AI Costs
  getAICosts: async (params?: { days?: number }) => {
    const { data } = await api.get('/admin/ai-costs', { params });
    return data;
  },

  // Feature Flags
  getFeatureFlags: async () => {
    const { data } = await api.get('/admin/feature-flags');
    return data;
  },

  updateFeatureFlag: async (key: string, updates: any) => {
    const { data } = await api.patch(`/admin/feature-flags/${key}`, updates);
    return data;
  },
};
