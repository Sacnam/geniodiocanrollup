/**
 * Genio Bridge - Connects Extension to Genio Backend API
 * 
 * This module provides an adapter between the existing Firebase-based
 * extension and the new FastAPI backend.
 */

class GenioBridge {
  constructor() {
    this.apiUrl = 'https://api.genio.ai';
    // this.apiUrl = 'http://localhost:8000'; // Development
    this.apiKey = null;
    this.jwtToken = null;
    this.enabled = false;
  }

  /**
   * Initialize the bridge with stored credentials
   */
  async init() {
    const stored = await chrome.storage.local.get([
      'genioApiUrl',
      'genioApiKey', 
      'genioEnabled',
      'firebaseToken'
    ]);
    
    this.apiUrl = stored.genioApiUrl || this.apiUrl;
    this.apiKey = stored.genioApiKey;
    this.enabled = stored.genioEnabled || false;
    this.jwtToken = stored.firebaseToken; // Use Firebase token for auth
    
    console.log('[GenioBridge] Initialized, enabled:', this.enabled);
    return this.enabled;
  }

  /**
   * Enable/disable Genio backend
   */
  async setEnabled(enabled) {
    this.enabled = enabled;
    await chrome.storage.local.set({ genioEnabled: enabled });
  }

  /**
   * Set API credentials
   */
  async setCredentials(apiUrl, apiKey) {
    this.apiUrl = apiUrl;
    this.apiKey = apiKey;
    await chrome.storage.local.set({
      genioApiUrl: apiUrl,
      genioApiKey: apiKey
    });
  }

  /**
   * Get auth headers for API requests
   */
  _getHeaders() {
    const headers = {
      'Content-Type': 'application/json'
    };
    
    if (this.jwtToken) {
      headers['Authorization'] = `Bearer ${this.jwtToken}`;
    } else if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }
    
    return headers;
  }

  /**
   * Make authenticated API request
   */
  async _request(endpoint, options = {}) {
    if (!this.enabled) {
      throw new Error('Genio backend not enabled');
    }

    const url = `${this.apiUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this._getHeaders(),
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error ${response.status}: ${error}`);
    }

    return response.json();
  }

  // ==================== LIBRARY API ====================

  /**
   * Save article/page to Genio Library
   */
  async saveDocument({ url, title, content, excerpt, source }) {
    return this._request('/api/v1/library/documents', {
      method: 'POST',
      body: JSON.stringify({
        url,
        title,
        content,
        excerpt: excerpt || content?.substring(0, 500),
        source: source || 'extension'
      })
    });
  }

  /**
   * List documents from Genio Library
   */
  async listDocuments({ search, limit = 20, offset = 0 } = {}) {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', limit);
    params.append('offset', offset);
    
    return this._request(`/api/v1/library/documents?${params}`);
  }

  /**
   * Get single document
   */
  async getDocument(documentId) {
    return this._request(`/api/v1/library/documents/${documentId}`);
  }

  /**
   * Delete document
   */
  async deleteDocument(documentId) {
    return this._request(`/api/v1/library/documents/${documentId}`, {
      method: 'DELETE'
    });
  }

  // ==================== KNOWLEDGE GRAPH API ====================

  /**
   * Get user's Personal Knowledge Graph
   */
  async getKnowledgeGraph() {
    return this._request('/api/v1/library/pkg/graph');
  }

  /**
   * Get specific node from PKG
   */
  async getNode(nodeId) {
    return this._request(`/api/v1/library/pkg/nodes/${nodeId}`);
  }

  /**
   * Query using GraphRAG (hybrid search)
   */
  async graphRAGQuery(query, options = {}) {
    return this._request('/api/v1/library/pkg/query', {
      method: 'POST',
      body: JSON.stringify({
        query,
        max_results: options.maxResults || 10,
        include_documents: options.includeDocuments !== false,
        include_concepts: options.includeConcepts !== false
      })
    });
  }

  // ==================== HIGHLIGHTS API ====================

  /**
   * Save highlight
   */
  async saveHighlight({ documentId, text, startOffset, endOffset, color = 'yellow', note }) {
    return this._request('/api/v1/library/highlights', {
      method: 'POST',
      body: JSON.stringify({
        document_id: documentId,
        text,
        start_offset: startOffset,
        end_offset: endOffset,
        color,
        note
      })
    });
  }

  /**
   * Get highlights for document
   */
  async getHighlights(documentId) {
    return this._request(`/api/v1/library/documents/${documentId}/highlights`);
  }

  // ==================== AUGMENTED READER API ====================

  /**
   * Get contextual overlays for document segment
   */
  async getOverlays(documentId, segmentText) {
    return this._request('/api/v1/library/documents/overlays', {
      method: 'POST',
      body: JSON.stringify({
        document_id: documentId,
        segment_text: segmentText
      })
    });
  }

  /**
   * Get related concepts for text range
   */
  async getRelatedConcepts(documentId, textRange) {
    return this._request('/api/v1/library/documents/related-concepts', {
      method: 'POST',
      body: JSON.stringify({
        document_id: documentId,
        text_range: textRange
      })
    });
  }

  // ==================== UTILITY ====================

  /**
   * Check if backend is available
   */
  async healthCheck() {
    try {
      const response = await fetch(`${this.apiUrl}/health`);
      return response.ok;
    } catch (e) {
      return false;
    }
  }

  /**
   * Sync Firebase data to Genio backend
   * (One-way sync for migration)
   */
  async syncFromFirebase(firebaseData) {
    // Batch upload existing Firebase data to Genio
    const batch = firebaseData.map(item => ({
      url: item.url,
      title: item.title,
      content: item.content,
      created_at: item.createdAt?.toISOString()
    }));

    // Upload in batches of 10
    const results = [];
    for (let i = 0; i < batch.length; i += 10) {
      const chunk = batch.slice(i, i + 10);
      for (const doc of chunk) {
        try {
          const result = await this.saveDocument(doc);
          results.push({ success: true, id: result.id });
        } catch (e) {
          results.push({ success: false, error: e.message });
        }
      }
    }

    return results;
  }
}

// Singleton instance
const genioBridge = new GenioBridge();

// Initialize on load
genioBridge.init();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { GenioBridge, genioBridge };
}

// Make available globally for extension
if (typeof window !== 'undefined') {
  window.GenioBridge = GenioBridge;
  window.genioBridge = genioBridge;
}
