/**
 * React hooks for API integration with TanStack Query.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, Feed, Article, Brief } from '../services/api';

// Auth hooks
export const useLogin = () => {
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      api.login(email, password),
  });
};

export const useRegister = () => {
  return useMutation({
    mutationFn: ({ email, password, name }: { email: string; password: string; name?: string }) =>
      api.register(email, password, name),
  });
};

export const useLogout = () => {
  return useMutation({
    mutationFn: () => api.logout(),
  });
};

export const useMe = () => {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => api.getMe(),
    retry: false,
  });
};

// Feed hooks
export const useFeeds = (category?: string, status?: string) => {
  return useQuery({
    queryKey: ['feeds', category, status],
    queryFn: () => api.listFeeds(category, status),
  });
};

export const useCreateFeed = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (feedData: { url: string; title?: string; category?: string }) =>
      api.createFeed(feedData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
};

export const useUpdateFeed = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<Feed> }) =>
      api.updateFeed(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
};

export const useDeleteFeed = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => api.deleteFeed(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
};

export const useRefreshFeed = () => {
  return useMutation({
    mutationFn: (id: string) => api.refreshFeed(id),
  });
};

export const useImportOpml = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (file: File) => api.importOpml(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
};

export const useCategories = () => {
  return useQuery({
    queryKey: ['categories'],
    queryFn: () => api.listCategories(),
  });
};

// Article hooks
export const useArticles = (params?: {
  page?: number;
  page_size?: number;
  min_delta?: number;
  max_delta?: number;
  is_read?: boolean;
  is_archived?: boolean;
  feed_id?: string;
  search?: string;
}) => {
  return useQuery({
    queryKey: ['articles', params],
    queryFn: () => api.listArticles(params),
  });
};

export const useArticle = (id: string) => {
  return useQuery({
    queryKey: ['article', id],
    queryFn: () => api.getArticle(id),
    enabled: !!id,
  });
};

export const useUpdateArticle = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: { is_read?: boolean; is_archived?: boolean } }) =>
      api.updateArticle(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });
};

export const useMarkRead = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => api.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      queryClient.invalidateQueries({ queryKey: ['articleStats'] });
    },
  });
};

export const useArchiveArticle = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => api.archiveArticle(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });
};

export const useArticleStats = () => {
  return useQuery({
    queryKey: ['articleStats'],
    queryFn: () => api.getArticleStats(),
  });
};

export const useBudgetStatus = () => {
  return useQuery({
    queryKey: ['budgetStatus'],
    queryFn: () => api.getBudgetStatus(),
  });
};

export const useBillingPlans = () => {
  return useQuery({
    queryKey: ['billingPlans'],
    queryFn: () => api.getBillingPlans(),
  });
};

// Brief hooks
export const useBriefs = (page?: number, page_size?: number) => {
  return useQuery({
    queryKey: ['briefs', page, page_size],
    queryFn: () => api.listBriefs(page, page_size),
  });
};

export const useTodaysBrief = () => {
  return useQuery({
    queryKey: ['brief', 'today'],
    queryFn: () => api.getTodaysBrief(),
  });
};

export const useBrief = (id: string) => {
  return useQuery({
    queryKey: ['brief', id],
    queryFn: () => api.getBrief(id),
    enabled: !!id,
  });
};

export const useBriefPreferences = () => {
  return useQuery({
    queryKey: ['briefPreferences'],
    queryFn: () => api.getBriefPreferences(),
  });
};

export const useUpdateBriefPreferences = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (prefs: Parameters<typeof api.updateBriefPreferences>[0]) =>
      api.updateBriefPreferences(prefs),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['briefPreferences'] });
    },
  });
};
