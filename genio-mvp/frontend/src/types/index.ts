export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  tier: 'starter' | 'professional' | 'enterprise';
}

export interface Feed {
  id: string;
  url: string;
  title?: string;
  custom_title?: string;
  category: string;
  is_active: boolean;
  last_fetched_at?: string;
  failure_count: number;
}

export interface Article {
  id: string;
  title?: string;
  excerpt: string;
  url: string;
  source: string;
  published_at?: string;
  delta_score: number;
  delta_status: 'novel' | 'related' | 'duplicate';
  is_read: boolean;
  is_starred: boolean;
}

export interface BriefSection {
  title: string;
  summary: string;
  articles: Article[];
}

export interface Brief {
  id: string;
  date: string;
  title: string;
  subtitle?: string;
  executive_summary?: string;
  sections: BriefSection[];
  article_count: number;
  sources_count: number;
  ai_generated: boolean;
  is_read: boolean;
}

export interface BudgetStatus {
  total: number;
  used: number;
  remaining: number;
  percentage_remaining: number;
  level: 'L1' | 'L2' | 'L3';
}
