import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { adminApi } from './adminApi';

export const AICostsPanel: React.FC = () => {
  const [days, setDays] = useState(7);
  const { data: costs, isLoading } = useQuery({
    queryKey: ['admin', 'ai-costs', days],
    queryFn: () => adminApi.getAICosts({ days }),
  });

  if (isLoading) {
    return <div className="p-8 text-center">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">AI Cost Breakdown</h3>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="border rounded-lg px-3 py-2"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Total Cost */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-500">Total Cost</p>
            <p className="text-3xl font-bold">${costs?.total?.toFixed(2) || '0.00'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Avg per User</p>
            <p className="text-3xl font-bold">${costs?.avg_per_user?.toFixed(2) || '0.00'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Total Requests</p>
            <p className="text-3xl font-bold">{costs?.total_requests?.toLocaleString() || '0'}</p>
          </div>
        </div>
      </div>

      {/* Daily Breakdown */}
      <div className="bg-white rounded-lg shadow">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-4 text-sm font-medium text-gray-600">Date</th>
              <th className="text-left p-4 text-sm font-medium text-gray-600">Embeddings</th>
              <th className="text-left p-4 text-sm font-medium text-gray-600">Summaries</th>
              <th className="text-left p-4 text-sm font-medium text-gray-600">Scout</th>
              <th className="text-left p-4 text-sm font-medium text-gray-600">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {costs?.daily?.map((day: any, idx: number) => (
              <tr key={idx}>
                <td className="p-4">{day.date}</td>
                <td className="p-4">${day.embeddings?.toFixed(2)}</td>
                <td className="p-4">${day.summaries?.toFixed(2)}</td>
                <td className="p-4">${day.scout?.toFixed(2)}</td>
                <td className="p-4 font-medium">${day.total?.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
