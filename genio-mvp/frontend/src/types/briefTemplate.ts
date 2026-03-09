"""
TypeScript types for brief templates.
"""

export type BriefLayout = 'compact' | 'standard' | 'detailed' | 'executive' | 'magazine';

export type BriefSectionType = 
  | 'headlines' 
  | 'high_delta' 
  | 'trending' 
  | 'saved_searches' 
  | 'category_spotlight' 
  | 'reading_list' 
  | 'smart_suggestions';

export interface BriefSectionConfig {
  type: BriefSectionType;
  title?: string;
  position: number;
  enabled: boolean;
  maxItems: number;
  filterTags: string[];
  filterDeltaMin?: number;
  sortBy: 'delta_score' | 'date' | 'trending';
}

export interface BriefTemplate {
  id: string;
  name: string;
  description?: string;
  isDefault: boolean;
  isActive: boolean;
  layout: BriefLayout;
  maxArticles: number;
  minDeltaScore: number;
  deliveryTime: string;
  deliveryDays: number[];
  sections: BriefSectionConfig[];
  generatedCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface BriefTemplateCreate {
  name: string;
  description?: string;
  layout: BriefLayout;
  maxArticles: number;
  minDeltaScore: number;
  deliveryTime: string;
  deliveryDays: number[];
}

export interface BriefTemplateUpdate {
  name?: string;
  description?: string;
  layout?: BriefLayout;
  isActive?: boolean;
  maxArticles?: number;
  minDeltaScore?: number;
  deliveryTime?: string;
  deliveryDays?: number[];
  sections?: BriefSectionConfig[];
}

export interface BriefPreview {
  templateId: string;
  generatedAt: string;
  sections: Array<{
    type: string;
    title: string;
    articles: any[];
  }>;
  totalArticles: number;
  estimatedReadTimeMinutes: number;
}
