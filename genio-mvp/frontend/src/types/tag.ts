"""
TypeScript types for tagging system.
"""

export interface Tag {
  id: string;
  name: string;
  slug: string;
  color?: string;
  icon?: string;
  description?: string;
  usage_count: number;
  created_at: string;
}

export interface TagCloudItem {
  id: string;
  name: string;
  slug: string;
  color?: string;
  icon?: string;
  count: number;
}

export interface TagCreate {
  name: string;
  color?: string;
  icon?: string;
  description?: string;
  parent_id?: string;
}

export interface TagUpdate {
  name?: string;
  color?: string;
  icon?: string;
  description?: string;
  parent_id?: string;
}

export interface ArticleTagLink {
  article_id: string;
  tag_id: string;
  created_at: string;
}

export interface DocumentTagLink {
  document_id: string;
  tag_id: string;
  created_at: string;
}
