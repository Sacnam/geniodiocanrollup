/**
 * API client for Genio backend.
 * Connects to real FastAPI endpoints.
 * 
 * FIX (FE-001): Implemented refresh token locking to prevent race conditions
 * when multiple concurrent requests receive 401 responses.
 */

// Validate API URL in production
const API_BASE_URL = (() => {
  const url = import.meta.env.VITE_API_URL;

  // In production, VITE_API_URL must be set
  if (!url) {
    if (import.meta.env.PROD) {
      throw new Error(
        'VITE_API_URL environment variable is required in production. ' +
        'Please set it in your build environment.'
      );
    }
    // Only use localhost fallback in development
    console.warn(
      'VITE_API_URL not set, using localhost fallback. ' +
      'This should not happen in production!'
    );
    return 'http://localhost:8000';
  }
  return url;
})();

class ApiClient {
  baseUrl: string;
  private token: string | null = null;

  /**
   * FIX (FE-001): Refresh token lock to prevent race conditions.
   * 
   * When multiple requests fail with 401 simultaneously (e.g., loading a dashboard
   * with multiple widgets), we need to ensure only ONE refresh request is made.
   * All other requests should wait for the same refresh promise.
   */
  private refreshPromise: Promise<boolean> | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.loadToken();
  }

  private loadToken() {
    this.token = localStorage.getItem('access_token');
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    // Clear any pending refresh promise
    this.refreshPromise = null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // FIX (FE-001): Use refresh token lock to prevent multiple refresh attempts
      const refreshed = await this.refreshTokenWithLock();
      if (refreshed) {
        // Retry request with new token
        headers['Authorization'] = `Bearer ${this.token}`;
        const retryResponse = await fetch(url, {
          ...options,
          headers,
        });
        return this.handleResponse<T>(retryResponse);
      } else {
        this.clearToken();
        window.location.href = '/login';
        throw new Error('Session expired');
      }
    }

    return this.handleResponse<T>(response);
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  /**
   * FIX (FE-001): Refresh token with locking mechanism.
   * 
   * This ensures that when multiple concurrent requests all receive 401:
   * 1. Only ONE refresh request is sent to the server
   * 2. All other requests wait for the same refresh promise
   * 3. Once resolved, all waiting requests use the new token
   * 
   * @returns Promise<boolean> - true if refresh succeeded, false otherwise
   */
  private async refreshTokenWithLock(): Promise<boolean> {
    // If a refresh is already in progress, wait for it
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    // Start a new refresh and store the promise
    this.refreshPromise = this.doRefreshToken();

    try {
      const result = await this.refreshPromise;
      return result;
    } finally {
      // Clear the promise after it resolves
      this.refreshPromise = null;
    }
  }

  /**
   * Internal method that performs the actual token refresh.
   * Should only be called through refreshTokenWithLock().
   */
  private async doRefreshToken(): Promise<boolean> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        this.setToken(data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        return true;
      }
    } catch (error) {
      // Log refresh errors in development
      if (import.meta.env.DEV) {
        console.error('Token refresh failed:', error);
      }
    }
    return false;
  }

  /**
   * @deprecated Use refreshTokenWithLock instead.
   * Kept for backward compatibility but will be removed.
   */
  private async refreshToken(): Promise<boolean> {
    return this.refreshTokenWithLock();
  }

  // Auth
  async login(email: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail);
    }

    const data = await response.json();
    this.setToken(data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  }

  async register(email: string, password: string, name?: string) {
    const data = await this.request<{
      access_token: string;
      refresh_token: string;
      token_type: string;
    }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    });

    this.setToken(data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  }

  async logout() {
    await this.request('/auth/logout', { method: 'POST' });
    this.clearToken();
  }

  async getMe() {
    return this.request<{
      id: string;
      email: string;
      name: string;
      is_active: boolean;
      created_at: string;
    }>('/auth/me');
  }

  async forgotPassword(email: string) {
    return this.request<{ message: string }>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async resetPassword(token: string, password: string) {
    return this.request<{ message: string }>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, password }),
    });
  }

  // Feeds
  async listFeeds(category?: string, status?: string) {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (status) params.append('status', status);

    return this.request<Feed[]>(`/feeds?${params}`);
  }

  async createFeed(feedData: { url: string; title?: string; category?: string }) {
    return this.request<Feed>('/feeds', {
      method: 'POST',
      body: JSON.stringify(feedData),
    });
  }

  async updateFeed(feedId: string, updates: Partial<Feed>) {
    return this.request<Feed>(`/feeds/${feedId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deleteFeed(feedId: string) {
    return this.request<void>(`/feeds/${feedId}`, { method: 'DELETE' });
  }

  async refreshFeed(feedId: string) {
    return this.request<{ message: string; feed_id: string }>(`/feeds/${feedId}/refresh`, {
      method: 'POST',
    });
  }

  async importOpml(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/feeds/import/opml`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Import failed' }));
      throw new Error(error.detail);
    }

    return response.json();
  }

  async listCategories() {
    return this.request<{ category: string; count: number }[]>('/feeds/categories/list');
  }

  // Articles
  async listArticles(params?: {
    page?: number;
    page_size?: number;
    min_delta?: number;
    max_delta?: number;
    is_read?: boolean;
    is_archived?: boolean;
    feed_id?: string;
    search?: string;
  }) {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) query.append(key, String(value));
      });
    }

    return this.request<{
      items: Article[];
      total: number;
      page: number;
      page_size: number;
    }>(`/articles?${query}`);
  }

  async getArticle(articleId: string) {
    return this.request<Article>(`/articles/${articleId}`);
  }

  async updateArticle(articleId: string, updates: { is_read?: boolean; is_archived?: boolean }) {
    return this.request<void>(`/articles/${articleId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async markRead(articleId: string) {
    return this.request<void>(`/articles/${articleId}/read`, { method: 'POST' });
  }

  async markUnread(articleId: string) {
    return this.request<void>(`/articles/${articleId}/unread`, { method: 'POST' });
  }

  async archiveArticle(articleId: string) {
    return this.request<void>(`/articles/${articleId}/archive`, { method: 'POST' });
  }

  async getArticleStats() {
    return this.request<{
      unread_count: number;
      high_novelty_count: number;
      medium_novelty_count: number;
      today_count: number;
    }>('/articles/stats/overview');
  }

  async getBudgetStatus() {
    return this.request<{
      monthly_budget: number;
      budget_used: number;
      budget_remaining: number;
      percentage_used: number;
      degradation_level: number;
    }>('/articles/budget/status');
  }

  // Billing
  async getBillingPlans() {
    return this.request<Array<{
      id: string;
      name: string;
      description: string;
      price_monthly: number;
      price_yearly: number;
      features: string[];
    }>>('/billing/plans');
  }

  async createCheckoutSession(priceId: string, successUrl: string, cancelUrl: string) {
    return this.request<{ session_id: string; url: string }>('/billing/checkout', {
      method: 'POST',
      body: JSON.stringify({ price_id: priceId, success_url: successUrl, cancel_url: cancelUrl }),
    });
  }

  async getSubscription() {
    return this.request<{
      id: string;
      status: string;
      current_period_end: number;
      cancel_at_period_end: boolean;
      plan_name: string;
    } | null>('/billing/subscription');
  }

  // Briefs
  async listBriefs(page?: number, page_size?: number) {
    const params = new URLSearchParams();
    if (page) params.append('page', String(page));
    if (page_size) params.append('page_size', String(page_size));

    return this.request<{
      items: Brief[];
      total: number;
      page: number;
      page_size: number;
    }>(`/briefs?${params}`);
  }

  async getTodaysBrief() {
    return this.request<Brief | null>('/briefs/today');
  }

  async getBrief(briefId: string) {
    return this.request<Brief>(`/briefs/${briefId}`);
  }

  async getBriefPreferences() {
    return this.request<{
      preferred_time: string;
      timezone: string;
      days_of_week: number[];
      max_articles: number;
      email_delivery: boolean;
    }>('/briefs/preferences');
  }

  async updateBriefPreferences(prefs: {
    preferred_time?: string;
    timezone?: string;
    days_of_week?: number[];
    max_articles?: number;
    email_delivery?: boolean;
  }) {
    return this.request<void>('/briefs/preferences', {
      method: 'PUT',
      body: JSON.stringify(prefs),
    });
  }

  async regenerateBrief(briefId: string) {
    return this.request<void>(`/briefs/${briefId}/regenerate`, { method: 'POST' });
  }

  // Credits
  async getWalletStatus(): Promise<WalletStatus> {
    return this.request<WalletStatus>('/credits/wallet');
  }

  async getCreditPackages(): Promise<CreditPackageInfo[]> {
    return this.request<CreditPackageInfo[]>('/credits/packages');
  }

  async purchaseCredits(pkg: string, successUrl: string, cancelUrl: string) {
    return this.request<{
      session_id: string;
      url: string;
      package: string;
      credits: number;
      bonus_credits: number;
    }>('/credits/purchase', {
      method: 'POST',
      body: JSON.stringify({
        package: pkg,
        success_url: successUrl,
        cancel_url: cancelUrl,
      }),
    });
  }

  async getCreditTransactions(limit: number = 20, offset: number = 0): Promise<CreditTransaction[]> {
    return this.request<CreditTransaction[]>(`/credits/transactions?limit=${limit}&offset=${offset}`);
  }

  async getCreditUsageStats(days: number = 30): Promise<UsageStats> {
    return this.request<UsageStats>(`/credits/usage?days=${days}`);
  }

  async checkCanAfford(operation: string, quantity: number = 1) {
    return this.request<{
      can_afford: boolean;
      credits_needed: number;
      current_balance: number;
    }>(`/credits/check/${operation}?quantity=${quantity}`);
  }

  async validateReferralCode(code: string) {
    return this.request<{
      valid: boolean;
      referrer_name: string | null;
      bonus_credits: number;
    }>(`/credits/referral/validate/${code}`);
  }

  async recordDailyStreak() {
    return this.request<{
      current_streak: number;
      bonus_credits_awarded: number;
    }>('/credits/streak/record', { method: 'POST' });
  }
}

// Types
export interface Feed {
  id: string;
  url: string;
  title?: string;
  category: string;
  status: 'active' | 'error' | 'disabled';
  last_fetched_at?: string;
  article_count: number;
  failure_count: number;
  fetch_interval_minutes: number;
}

export interface Article {
  id: string;
  title?: string;
  url: string;
  source_feed_title?: string;
  published_at?: string;
  excerpt?: string;
  content?: string;
  global_summary?: string;
  delta_score: number;
  is_read: boolean;
  is_archived: boolean;
  cluster_id?: string;
  is_duplicate: boolean;
  created_at: string;
}

export interface Brief {
  id: string;
  title: string;
  scheduled_for: string;
  delivered_at?: string;
  delivery_status: string;
  is_quiet_day: boolean;
  sections: BriefSection[];
  article_count: number;
  sources_cited: string[];
  created_at: string;
}

export interface BriefSection {
  type: string;
  title: string;
  content: string;
  articles: { id: string; title?: string }[];
}

// Credit System Types
export interface WalletStatus {
  balance: number;
  total_earned: number;
  total_spent: number;
  monthly_allocation: number;
  allocation_resets_at: string | null;
  current_streak: number;
  longest_streak: number;
  referral_code: string;
  referral_credits_earned: number;
  has_low_balance: boolean;
  is_exhausted: boolean;
}

export interface CreditPackageInfo {
  id: string;
  name: string;
  credits: number;
  bonus_credits: number;
  price_cents: number;
  price_formatted: string;
  features_unlocked: string[];
  validity_days: number;
}

export interface CreditTransaction {
  id: number;
  type: string;
  operation: string | null;
  amount: number;
  balance_after: number;
  description: string | null;
  created_at: string;
}

export interface UsageStats {
  period_days: number;
  total_spent: number;
  total_earned: number;
  net_change: number;
  by_operation: Record<string, { count: number; credits: number }>;
  average_daily_spend: number;
  projected_monthly_spend: number;
}

export const api = new ApiClient(API_BASE_URL);
