"""
API service for e-reader operations.
"""
import { apiClient } from './client';

export const ereaderApi = {
  openBook: async (documentId: string): Promise<any> => {
    const response = await apiClient.post(`/ereader/books/${documentId}/open`);
    return response.data;
  },

  getContent: async (userBookId: string, chapter: number): Promise<any> => {
    const response = await apiClient.get(`/ereader/books/${userBookId}/content`, {
      params: { chapter }
    });
    return response.data;
  },

  updateProgress: async (userBookId: string, data: {
    current_position: string;
    current_page: number;
    progress_percent: number;
  }): Promise<void> => {
    await apiClient.post(`/ereader/books/${userBookId}/progress`, data);
  },

  createHighlight: async (userBookId: string, data: {
    start_cfi: string;
    end_cfi: string;
    selected_text: string;
    color: string;
    note?: string;
    chapter_title?: string;
  }): Promise<any> => {
    const response = await apiClient.post(`/ereader/books/${userBookId}/highlights`, data);
    return response.data;
  },

  generateTTS: async (data: {
    text: string;
    provider?: string;
    voice?: string;
    speed?: number;
  }): Promise<{
    audio_url: string;
    duration_seconds: number;
    provider: string;
    cached: boolean;
  }> => {
    const response = await apiClient.post('/ereader/tts/generate', data);
    return response.data;
  },

  generateFlashcards: async (userBookId: string, highlightIds: string[]): Promise<any> => {
    const response = await apiClient.post(`/ereader/flashcards/generate-deck`, {
      user_book_id: userBookId,
      highlight_ids: highlightIds
    });
    return response.data;
  },

  getStudyCards: async (deckId: string, limit: number = 20): Promise<any> => {
    const response = await apiClient.get('/ereader/flashcards/study', {
      params: { deck_id: deckId, limit }
    });
    return response.data;
  },

  reviewCard: async (cardId: string, quality: number): Promise<any> => {
    const response = await apiClient.post(`/ereader/flashcards/${cardId}/review`, {
      quality
    });
    return response.data;
  },
};

export const aiApi = {
  studyAssist: async (data: {
    book_id: string;
    action: string;
    context?: string;
    language?: string;
  }): Promise<any> => {
    const response = await apiClient.post('/ereader/ai/assist', data);
    return response.data;
  },

  summarize: async (text: string): Promise<string> => {
    const response = await apiClient.post('/ai/summarize', { text });
    return response.data.summary;
  },

  explain: async (text: string, level: 'simple' | 'detailed' = 'simple'): Promise<string> => {
    const response = await apiClient.post('/ai/explain', { text, level });
    return response.data.explanation;
  },
};
