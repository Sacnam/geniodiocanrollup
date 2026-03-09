import { api } from './api';

export interface PKGNode {
  id: string;
  node_type: 'concept' | 'atom' | 'document';
  name: string;
  definition?: string;
  confidence: number;
  knowledge_state: 'known' | 'gap' | 'learning';
  relationships: {
    target_id: string;
    type: string;
    confidence: number;
  }[];
}

export interface PKGEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: string;
  confidence: number;
}

export interface GraphData {
  nodes: PKGNode[];
  edges: PKGEdge[];
}

export interface Highlight {
  id: string;
  document_id: string;
  start_offset: number;
  end_offset: number;
  text: string;
  note?: string;
  color: string;
  created_at: string;
}

export interface GraphRAGResult {
  answer: string;
  sources: {
    document_id: string;
    title: string;
    excerpt: string;
    relevance_score: number;
  }[];
  concepts: string[];
  citations: string[];
}

export interface OverlayItem {
  id: string;
  type: 'concept' | 'definition' | 'connection' | 'note';
  text: string;
  position: { x: number; y: number };
  related_nodes?: string[];
}

export const libraryApi = {
  // PKG
  getGraph: async (): Promise<GraphData> => {
    const { data } = await api.get('/library/pkg/graph');
    return data;
  },

  getNode: async (nodeId: string): Promise<PKGNode> => {
    const { data } = await api.get(`/library/pkg/nodes/${nodeId}`);
    return data;
  },

  // GraphRAG
  query: async (query: string): Promise<GraphRAGResult> => {
    const { data } = await api.post('/library/pkg/query', { query });
    return data;
  },

  // Highlights
  getHighlights: async (documentId: string): Promise<Highlight[]> => {
    const { data } = await api.get(`/library/documents/${documentId}/highlights`);
    return data;
  },

  createHighlight: async (highlight: Omit<Highlight, 'id' | 'created_at'>): Promise<Highlight> => {
    const { data } = await api.post('/library/highlights', highlight);
    return data;
  },

  deleteHighlight: async (highlightId: string): Promise<void> => {
    await api.delete(`/library/highlights/${highlightId}`);
  },

  // Augmented Reader
  getOverlays: async (documentId: string, segmentText: string): Promise<OverlayItem[]> => {
    const { data } = await api.post('/library/documents/overlays', {
      document_id: documentId,
      segment_text: segmentText,
    });
    return data;
  },

  getRelatedConcepts: async (documentId: string, textRange: string): Promise<PKGNode[]> => {
    const { data } = await api.post('/library/documents/related-concepts', {
      document_id: documentId,
      text_range: textRange,
    });
    return data;
  },
};
