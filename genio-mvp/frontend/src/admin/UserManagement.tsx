import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, MoreVertical, Shield, UserX, UserCheck } from 'lucide-react';
import { adminApi } from './adminApi';

export const UserManagement: React.FC = () => {
  const [search, setSearch] = useState('');
  const queryClient = useQueryClient();
  
  const { data: users, isLoading } = useQuery({
    queryKey: ['admin', 'users', search],
    queryFn: () => adminApi.getUsers({ search, limit: 50 }),
  });

  const updateTierMutation = useMutation({
    mutationFn: ({ userId, tier }: { userId: string; tier: string }) =>
      adminApi.updateUserTier(userId, tier),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] }),
  });

  const disableUserMutation = useMutation({
    mutationFn: (userId: string) => adminApi.disableUser(userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] }),
  });

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">User Management</h3>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search users..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 border rounded-lg text-sm"
            />
          </div>
        </div>
      </div>

      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="text-left p-4 text-sm font-medium text-gray-600">User</th>
            <th className="text-left p-4 text-sm font-medium text-gray-600">Tier</th>
            <th className="text-left p-4 text-sm font-medium text-gray-600">Status</th>
            <th className="text-left p-4 text-sm font-medium text-gray-600">Created</th>
            <th className="p-4"></th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {isLoading ? (
            <tr><td colSpan={5} className="p-8 text-center">Loading...</td></tr>
          ) : (
            users?.items.map((user: any) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="p-4">
                  <div>
                    <p className="font-medium">{user.email}</p>
                    <p className="text-sm text-gray-500">{user.first_name} {user.last_name}</p>
                  </div>
                </td>
                <td className="p-4">
                  <select
                    value={user.tier}
                    onChange={(e) => updateTierMutation.mutate({ userId: user.id, tier: e.target.value })}
                    className="text-sm border rounded px-2 py-1"
                  >
                    <option value="FREE">Free</option>
                    <option value="PROFESSIONAL">Professional</option>
                    <option value="ENTERPRISE">Enterprise</option>
                  </select>
                </td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {user.is_active ? 'Active' : 'Disabled'}
                  </span>
                </td>
                <td className="p-4 text-sm text-gray-500">
                  {new Date(user.created_at).toLocaleDateString()}
                </td>
                <td className="p-4">
                  <div className="flex gap-2">
                    <button
                      onClick={() => disableUserMutation.mutate(user.id)}
                      className="p-2 hover:bg-gray-100 rounded"
                      title={user.is_active ? 'Disable user' : 'Enable user'}
                    >
                      {user.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                    </button>
                  </div>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
