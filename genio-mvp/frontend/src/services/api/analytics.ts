"""
API service for analytics operations.
"""
import { apiClient } from './client';
import type { AnalyticsDashboard, ReadingStats, DeltaTrends, FeedPerformance, ActivityHeatmap, HourlyActivity, TopTag, ReadingInsight } from '../../types/analytics';

export const analyticsApi = {
  getDashboard: async (period: string = '30d'): Promise<AnalyticsDashboard> => {
    const response = await apiClient.get('/analytics/dashboard', {
      params: { period }
    });
    return response.data;
  },

  getReadingStats: async (days?: number): Promise<ReadingStats> => {
    const response = await apiClient.get('/analytics/reading-stats', {
      params: { days }
    });
    return response.data;
  },

  getDeltaTrends: async (days?: number): Promise<DeltaTrends> => {
    const response = await apiClient.get('/analytics/delta-trends', {
      params: { days }
    });
    return response.data;
  },

  getFeedPerformance: async (): Promise<FeedPerformance[]> => {
    const response = await apiClient.get('/analytics/feed-performance');
    return response.data;
  },

  getActivityHeatmap: async (days?: number): Promise<ActivityHeatmap> => {
    const response = await apiClient.get('/analytics/activity-heatmap', {
      params: { days }
    });
    return response.data;
  },

  getHourlyActivity: async (days?: number): Promise<HourlyActivity[]> => {
    const response = await apiClient.get('/analytics/hourly-activity', {
      params: { days }
    });
    return response.data;
  },

  getTopTags: async (limit?: number): Promise<TopTag[]> => {
    const response = await apiClient.get('/analytics/top-tags', {
      params: { limit }
    });
    return response.data;
  },

  getInsights: async (): Promise<ReadingInsight[]> => {
    const response = await apiClient.get('/analytics/insights');
    return response.data;
  },

  export: async (format: 'json' | 'csv' = 'json'): Promise<any> => {
    const response = await apiClient.get('/analytics/export', {
      params: { format }
    });
    return response.data;
  },
};
