import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { CheckCircle, XCircle, AlertTriangle, Server, Database, Activity } from 'lucide-react';
import { adminApi } from './adminApi';

export const SystemHealth: React.FC = () => {
  const { data: health, isLoading } = useQuery({
    queryKey: ['admin', 'health'],
    queryFn: adminApi.getHealth,
    refetchInterval: 30000,
  });

  if (isLoading) {
    return <div className="p-8 text-center">Loading...</div>;
  }

  const services = [
    { name: 'API', status: health?.api?.status, latency: health?.api?.latency },
    { name: 'Database', status: health?.database?.status, latency: health?.database?.latency },
    { name: 'Redis', status: health?.redis?.status, latency: health?.redis?.latency },
    { name: 'Qdrant', status: health?.qdrant?.status, latency: health?.qdrant?.latency },
    { name: 'Celery Workers', status: health?.celery?.status, workers: health?.celery?.workers },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {services.map((service) => (
          <div key={service.name} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${
                  service.status === 'healthy' ? 'bg-green-100' : 'bg-red-100'
                }`}>
                  {service.status === 'healthy' ? (
                    <CheckCircle className={`w-5 h-5 ${
                      service.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                    }`} />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600" />
                  )}
                </div>
                <div>
                  <p className="font-medium">{service.name}</p>
                  <p className={`text-sm ${
                    service.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {service.status}
                  </p>
                </div>
              </div>
              {service.latency && (
                <span className="text-sm text-gray-500">{service.latency}ms</span>
              )}
              {service.workers && (
                <span className="text-sm text-gray-500">{service.workers} workers</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Queue Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold mb-4">Celery Queue Status</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-2xl font-bold text-blue-600">{health?.queue?.pending || 0}</p>
            <p className="text-sm text-gray-600">Pending</p>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <p className="text-2xl font-bold text-yellow-600">{health?.queue?.processing || 0}</p>
            <p className="text-sm text-gray-600">Processing</p>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <p className="text-2xl font-bold text-red-600">{health?.queue?.failed || 0}</p>
            <p className="text-sm text-gray-600">Failed</p>
          </div>
        </div>
      </div>
    </div>
  );
};
