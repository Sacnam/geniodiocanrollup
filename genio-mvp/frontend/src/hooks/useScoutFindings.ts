/**
 * React Query hooks for Scout Findings and Insights
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { scoutService } from '../services/scouts';

export const useScoutFindings = (
  scoutId: string,
  params?: { unread_only?: boolean; saved_only?: boolean }
) => {
  return useQuery({
    queryKey: ['scout-findings', scoutId, params],
    queryFn: () => scoutService.listFindings(scoutId, params),
    enabled: !!scoutId,
  });
};

export const useScoutInsights = (scoutId: string) => {
  return useQuery({
    queryKey: ['scout-insights', scoutId],
    queryFn: () => scoutService.getInsights(scoutId),
    enabled: !!scoutId,
  });
};

export const useSaveFinding = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: scoutService.saveFinding,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scout-findings'] });
    },
  });
};

export const useDismissFinding = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: scoutService.dismissFinding,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scout-findings'] });
    },
  });
};
