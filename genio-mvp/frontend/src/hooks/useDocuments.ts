/**
 * React Query hooks for documents.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { documentService } from '../services/documents';

export const useDocuments = (params?: {
  page?: number;
  page_size?: number;
  status?: string;
  search?: string;
}) => {
  return useQuery({
    queryKey: ['documents', params],
    queryFn: () => documentService.listDocuments(params),
  });
};

export const useDocument = (id: string) => {
  return useQuery({
    queryKey: ['document', id],
    queryFn: () => documentService.getDocument(id),
    enabled: !!id,
  });
};

export const useDocumentContent = (id: string) => {
  return useQuery({
    queryKey: ['document-content', id],
    queryFn: () => documentService.getDocumentContent(id),
    enabled: !!id,
  });
};

export const useUploadDocument = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (file: File) => documentService.uploadDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};

export const useDeleteDocument = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => documentService.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};

export const useDocumentHighlights = (documentId: string) => {
  return useQuery({
    queryKey: ['document-highlights', documentId],
    queryFn: () => documentService.listHighlights(documentId),
    enabled: !!documentId,
  });
};

export const useCreateHighlight = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({
      documentId,
      highlight,
    }: {
      documentId: string;
      highlight: Parameters<typeof documentService.createHighlight>[1];
    }) => documentService.createHighlight(documentId, highlight),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['document-highlights', variables.documentId],
      });
    },
  });
};
