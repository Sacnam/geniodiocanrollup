/**
 * React Query hooks for Scout agents.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { scoutService } from '../services/scouts';

export const useScouts = () => {
  return useQuery({
    queryKey: ['scouts'],
    queryFn: () => scoutService.listScouts(),
  });
};

export const useScout = (id: string) => {
  return useQuery({
    queryKey: ['scout', id],
    queryFn: () => scoutService.getScout(id),
    enabled: !!id,
  });
};

export const useCreateScout = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: scoutService.createScout,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scouts'] });
    },
  });
};

export const useUpdateScout = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Parameters<typeof scoutService.updateScout>[1] }) =>
      scoutService.updateScout(id, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['scouts'] });
      queryClient.invalidateQueries({ queryKey: ['scout', variables.id] });
    },
  });
};

export const useDeleteScout = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: scoutService.deleteScout,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scouts'] });
    },
  });
};

export const useRunScout = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: scoutService.runScout,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scouts'] });
    },
  });
};

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
