"""
API service for keyboard shortcuts.
"""
import { apiClient } from './client';
import type { ShortcutsConfig, ShortcutBinding } from '../../types/shortcuts';

export const shortcutApi = {
  getAll: async (context?: string): Promise<ShortcutsConfig> => {
    const params = context ? { context } : {};
    const response = await apiClient.get('/shortcuts', { params });
    return response.data;
  },

  update: async (
    category: string,
    action: string,
    data: Partial<ShortcutBinding>
  ): Promise<ShortcutBinding> => {
    const response = await apiClient.put(`/shortcuts/${category}/${action}`, data);
    return response.data;
  },

  reset: async (): Promise<{ status: string; shortcuts: ShortcutsConfig }> => {
    const response = await apiClient.post('/shortcuts/reset');
    return response.data;
  },

  validate: async (shortcuts: ShortcutsConfig): Promise<{ valid: boolean; conflicts: any[] }> => {
    const response = await apiClient.post('/shortcuts/validate', shortcuts);
    return response.data;
  },

  export: async (): Promise<{ version: string; shortcuts: ShortcutsConfig; exported_at: string }> => {
    const response = await apiClient.get('/shortcuts/export');
    return response.data;
  },

  import: async (data: { version: string; shortcuts: ShortcutsConfig }): Promise<any> => {
    const response = await apiClient.post('/shortcuts/import', data);
    return response.data;
  },

  getCheatsheet: async (): Promise<Array<{ category: string; shortcuts: Array<{ action: string; key: string; description: string }> }>> => {
    const response = await apiClient.get('/shortcuts/cheatsheet');
    return response.data;
  },

  toggleVimMode: async (enabled: boolean): Promise<{ vim_mode_enabled: boolean }> => {
    const response = await apiClient.post('/shortcuts/toggle-vim-mode', null, {
      params: { enabled }
    });
    return response.data;
  },
};
