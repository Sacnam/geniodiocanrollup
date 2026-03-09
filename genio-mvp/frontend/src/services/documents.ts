/**
 * Document service for Library module.
 */
import { api } from './api';

export interface Document {
  id: string;
  title?: string;
  original_filename: string;
  doc_type: 'pdf' | 'text' | 'markdown';
  status: 'uploaded' | 'extracting' | 'extracted' | 'indexing' | 'ready' | 'error';
  excerpt?: string;
  author?: string;
  page_count?: number;
  word_count?: number;
  tags: string[];
  created_at: string;
}

export interface DocumentListResponse {
  items: Document[];
  total: number;
  page: number;
  page_size: number;
}

export interface Highlight {
  id: string;
  char_start: number;
  char_end: number;
  highlighted_text: string;
  note?: string;
  color: string;
  page_number?: number;
  created_at: string;
}

class DocumentService {
  async listDocuments(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    search?: string;
  }): Promise<DocumentListResponse> {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) query.append(key, String(value));
      });
    }
    return api.request(`/documents?${query}`);
  }

  async getDocument(id: string): Promise<Document> {
    return api.request(`/documents/${id}`);
  }

  async getDocumentContent(id: string): Promise<{
    status: string;
    content?: string;
    title?: string;
    word_count?: number;
  }> {
    return api.request(`/documents/${id}/content`);
  }

  async uploadDocument(file: File): Promise<{
    id: string;
    filename: string;
    status: string;
    message: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${api.baseUrl}/documents/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail);
    }

    return response.json();
  }

  async deleteDocument(id: string): Promise<void> {
    return api.request(`/documents/${id}`, { method: 'DELETE' });
  }

  // Highlights
  async listHighlights(documentId: string): Promise<Highlight[]> {
    return api.request(`/documents/${documentId}/highlights`);
  }

  async createHighlight(
    documentId: string,
    highlight: {
      char_start: number;
      char_end: number;
      highlighted_text: string;
      note?: string;
      color?: string;
      page_number?: number;
    }
  ): Promise<Highlight> {
    return api.request(`/documents/${documentId}/highlights`, {
      method: 'POST',
      body: JSON.stringify(highlight),
    });
  }
}

export const documentService = new DocumentService();
