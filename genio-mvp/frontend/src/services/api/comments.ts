"""
API service for comment operations.
"""
import { apiClient } from './client';
import type { Comment, CommentThread } from '../../types/comment';

export const commentApi = {
  getArticleComments: async (articleId: string): Promise<CommentThread> => {
    const response = await apiClient.get(`/articles/${articleId}/comments`, {
      params: { threaded: true }
    });
    return response.data;
  },

  get: async (commentId: string): Promise<Comment> => {
    const response = await apiClient.get(`/comments/${commentId}`);
    return response.data;
  },

  create: async (
    articleId: string,
    data: { content: string; parentId?: string }
  ): Promise<Comment> => {
    const response = await apiClient.post(`/articles/${articleId}/comments`, {
      content: data.content,
      parent_id: data.parentId
    });
    return response.data;
  },

  update: async (commentId: string, content: string): Promise<Comment> => {
    const response = await apiClient.put(`/comments/${commentId}`, { content });
    return response.data;
  },

  delete: async (commentId: string): Promise<void> => {
    await apiClient.delete(`/comments/${commentId}`);
  },

  like: async (commentId: string): Promise<{ likes_count: number; is_liked_by_me: boolean }> => {
    const response = await apiClient.post(`/comments/${commentId}/like`);
    return response.data;
  },

  unlike: async (commentId: string): Promise<{ likes_count: number; is_liked_by_me: boolean }> => {
    const response = await apiClient.delete(`/comments/${commentId}/like`);
    return response.data;
  },

  resolve: async (commentId: string): Promise<{ is_resolved: boolean }> => {
    const response = await apiClient.post(`/comments/${commentId}/resolve`);
    return response.data;
  },
};
