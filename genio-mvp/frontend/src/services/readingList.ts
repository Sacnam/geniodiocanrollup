import { api } from './api';

export interface ReadingListItem {
  id: string;
  url: string;
  title: string;
  excerpt?: string;
  image_url?: string;
  source_name?: string;
  content?: string;
  word_count?: number;
  is_read: boolean;
  is_archived: boolean;
  priority: number;
  tags?: string;
  notes?: string;
  created_at: string;
  read_at?: string;
}

export const readingListApi = {
  getItems: async (params?: { filter?: string; search?: string; limit?: number }) => {
    const { data } = await api.get('/reading-list/list', { params });
    return data;
  },

  saveItem: async (item: { url: string; title?: string; excerpt?: string; notes?: string }) => {
    const { data } = await api.post('/reading-list/save', item);
    return data;
  },

  updateItem: async (id: string, updates: Partial<ReadingListItem>) => {
    const { data } = await api.patch(`/reading-list/${id}`, updates);
    return data;
  },

  deleteItem: async (id: string) => {
    await api.delete(`/reading-list/${id}`);
  },

  getStats: async () => {
    const { data } = await api.get('/reading-list/stats');
    return data;
  },

  extractContent: async (id: string) => {
    const { data } = await api.post(`/reading-list/${id}/extract`);
    return data;
  },
};
