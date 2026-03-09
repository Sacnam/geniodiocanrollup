import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { libraryApi, type Highlight, type GraphRAGResult } from '../services/library';

export const usePKGGraph = () => {
  return useQuery({
    queryKey: ['pkg', 'graph'],
    queryFn: libraryApi.getGraph,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useGraphRAG = () => {
  return useMutation<GraphRAGResult, Error, string>({
    mutationFn: libraryApi.query,
  });
};

export const useHighlights = (documentId: string) => {
  return useQuery({
    queryKey: ['highlights', documentId],
    queryFn: () => libraryApi.getHighlights(documentId),
    enabled: !!documentId,
  });
};

export const useCreateHighlight = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: libraryApi.createHighlight,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['highlights', variables.document_id] });
    },
  });
};

export const useDeleteHighlight = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: libraryApi.deleteHighlight,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['highlights'] });
    },
  });
};

export const useOverlays = (documentId: string, segmentText: string) => {
  return useQuery({
    queryKey: ['overlays', documentId, segmentText],
    queryFn: () => libraryApi.getOverlays(documentId, segmentText),
    enabled: !!documentId && !!segmentText && segmentText.length > 50,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};
