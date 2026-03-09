/**
 * Scout Agent service for Lab module.
 */
import { api } from './api';

export interface Scout {
  id: string;
  name: string;
  description?: string;
  research_question: string;
  keywords: string[];
  sources: string[];
  schedule: string;
  status: 'idle' | 'running' | 'paused' | 'error';
  is_active: boolean;
  total_findings: number;
  unread_findings: number;
  last_run_at?: string;
  next_run_at?: string;
  created_at: string;
}

export interface ScoutFinding {
  id: string;
  source_type: string;
  source_title: string;
  source_url: string;
  relevance_score: number;
  explanation: string;
  matched_keywords: string[];
  key_insights: string[];
  is_read: boolean;
  is_saved: boolean;
  created_at: string;
}

class ScoutService {
  async listScouts(): Promise<Scout[]> {
    return api.request('/scouts');
  }

  async getScout(id: string): Promise<Scout> {
    return api.request(`/scouts/${id}`);
  }

  async createScout(data: {
    name: string;
    description?: string;
    research_question: string;
    keywords: string[];
    sources: string[];
    schedule: string;
    min_relevance_score?: number;
  }): Promise<Scout> {
    return api.request('/scouts', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateScout(id: string, updates: Partial<Scout>): Promise<Scout> {
    return api.request(`/scouts/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deleteScout(id: string): Promise<void> {
    return api.request(`/scouts/${id}`, { method: 'DELETE' });
  }

  async runScout(id: string): Promise<{ message: string; scout_id: string }> {
    return api.request(`/scouts/${id}/run`, { method: 'POST' });
  }

  // Findings
  async listFindings(
    scoutId: string,
    params?: { unread_only?: boolean; saved_only?: boolean }
  ): Promise<ScoutFinding[]> {
    const query = new URLSearchParams();
    if (params?.unread_only) query.append('unread_only', 'true');
    if (params?.saved_only) query.append('saved_only', 'true');
    return api.request(`/scouts/${scoutId}/findings?${query}`);
  }

  async saveFinding(id: string): Promise<void> {
    return api.request(`/scouts/findings/${id}/save`, { method: 'POST' });
  }

  async dismissFinding(id: string): Promise<void> {
    return api.request(`/scouts/findings/${id}/dismiss`, { method: 'POST' });
  }

  // Insights
  async getInsights(scoutId: string): Promise<Array<{
    id: string;
    insight_type: string;
    title: string;
    description: string;
    confidence_score: number;
    created_at: string;
  }>> {
    return api.request(`/scouts/${scoutId}/insights`);
  }

  // Verification
  async verifyClaim(scoutId: string, claim: string): Promise<{
    finding_id: string;
    verified: boolean;
    sources_used: number;
  }> {
    return api.request(`/scouts/${scoutId}/verify`, {
      method: 'POST',
      body: JSON.stringify({ claim }),
    });
  }
}

export const scoutService = new ScoutService();
