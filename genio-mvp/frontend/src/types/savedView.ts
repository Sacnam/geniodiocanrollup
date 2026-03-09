"""
TypeScript types for saved views system.
"""

export interface FilterConfig {
  search?: string;
  tags?: string[];
  tag_operator?: 'any' | 'all';
  feeds?: string[];
  content_types?: string[];
  is_read?: boolean;
  is_favorited?: boolean;
  is_archived?: boolean;
  date_from?: string;
  date_to?: string;
  delta_score_min?: number;
  delta_score_max?: number;
  word_count_min?: number;
  word_count_max?: number;
  sort_by?: 'published_at' | 'delta_score' | 'created_at';
  sort_order?: 'asc' | 'desc';
  per_page?: number;
}

export interface SavedView {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  filters: FilterConfig;
  is_default: boolean;
  is_pinned: boolean;
  position: number;
  share_enabled: boolean;
  use_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateSavedViewRequest {
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  filters?: FilterConfig;
  is_default?: boolean;
  position?: number;
}

export interface UpdateSavedViewRequest {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
  filters?: FilterConfig;
  is_default?: boolean;
  is_pinned?: boolean;
  position?: number;
}
