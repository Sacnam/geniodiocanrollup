import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from './adminApi';
import { Toggle } from '../components/ui/Toggle';

export const FeatureFlagsPanel: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: flags, isLoading } = useQuery({
    queryKey: ['admin', 'feature-flags'],
    queryFn: adminApi.getFeatureFlags,
  });

  const updateMutation = useMutation({
    mutationFn: ({ key, updates }: { key: string; updates: any }) =>
      adminApi.updateFeatureFlag(key, updates),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'feature-flags'] }),
  });

  if (isLoading) {
    return <div className="p-8 text-center">Loading...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <h3 className="font-semibold">Feature Flags</h3>
        <p className="text-sm text-gray-500 mt-1">Control feature rollout and A/B testing</p>
      </div>

      <div className="divide-y">
        {flags?.map((flag: any) => (
          <div key={flag.key} className="p-6 flex items-center justify-between">
            <div>
              <p className="font-medium">{flag.name}</p>
              <p className="text-sm text-gray-500">{flag.description}</p>
              <p className="text-xs text-gray-400 mt-1">{flag.key}</p>
            </div>
            <div className="flex items-center gap-4">
              {flag.rules?.some((r: any) => r.strategy === 'PERCENTAGE') && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Rollout:</span>
                  <select
                    value={flag.rules.find((r: any) => r.strategy === 'PERCENTAGE')?.percentage || 0}
                    onChange={(e) => updateMutation.mutate({
                      key: flag.key,
                      updates: { percentage: Number(e.target.value) }
                    })}
                    className="border rounded px-2 py-1 text-sm"
                  >
                    <option value={0}>0%</option>
                    <option value={10}>10%</option>
                    <option value={25}>25%</option>
                    <option value={50}>50%</option>
                    <option value={100}>100%</option>
                  </select>
                </div>
              )}
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={!flag.archived}
                  onChange={(e) => updateMutation.mutate({
                    key: flag.key,
                    updates: { enabled: e.target.checked }
                  })}
                  className="w-5 h-5 rounded"
                />
                <span className="text-sm">Enabled</span>
              </label>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
