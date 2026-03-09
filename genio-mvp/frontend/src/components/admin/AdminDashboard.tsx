"""
Admin dashboard for system monitoring and management.
"""
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Users, Activity, Database, Server, AlertTriangle,
  TrendingUp, Cpu, HardDrive, Mail, Shield
} from 'lucide-react';
import { adminApi } from '../../services/api/admin';

export function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  
  const { data: stats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminApi.getStats(),
  });
  
  const { data: health } = useQuery({
    queryKey: ['admin-health'],
    queryFn: () => adminApi.getHealth(),
    refetchInterval: 30000,
  });
  
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'system', label: 'System', icon: Server },
    { id: 'security', label: 'Security', icon: Shield },
  ];
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-muted-foreground">
            {health?.status === 'healthy' ? 'All Systems Operational' : 'Issues Detected'}
          </span>
        </div>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          icon={<Users className="w-5 h-5 text-blue-500" />}
          label="Total Users"
          value={stats?.total_users || 0}
          trend={stats?.user_growth}
        />
        <StatCard
          icon={<Database className="w-5 h-5 text-green-500" />}
          label="Articles"
          value={stats?.total_articles || 0}
          trend={stats?.article_growth}
        />
        <StatCard
          icon={<Mail className="w-5 h-5 text-purple-500" />}
          label="Briefs Sent"
          value={stats?.briefs_sent_today || 0}
          subtext="Today"
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5 text-orange-500" />}
          label="API Requests"
          value={stats?.api_requests_minute || 0}
          subtext="Per minute"
        />
      </div>
      
      {/* Tabs */}
      <div className="border-b">
        <div className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>
      
      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && <OverviewTab stats={stats} health={health} />}
        {activeTab === 'users' && <UsersTab />}
        {activeTab === 'system' && <SystemTab health={health} />}
        {activeTab === 'security' && <SecurityTab />}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, trend, subtext }: any) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-3 mb-2">
        {icon}
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value.toLocaleString()}</div>
      {trend !== undefined && (
        <div className={`text-xs ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
        </div>
      )}
      {subtext && <div className="text-xs text-muted-foreground">{subtext}</div>}
    </div>
  );
}

function OverviewTab({ stats, health }: any) {
  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Recent Activity */}
      <div className="card">
        <h3 className="font-semibold mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {stats?.recent_activity?.map((activity: any, i: number) => (
            <div key={i} className="flex items-center gap-3 text-sm">
              <span className="text-muted-foreground">
                {new Date(activity.time).toLocaleTimeString()}
              </span>
              <span>{activity.description}</span>
            </div>
          )) || <p className="text-muted-foreground">No recent activity</p>}
        </div>
      </div>
      
      {/* Service Health */}
      <div className="card">
        <h3 className="font-semibold mb-4">Service Health</h3>
        <div className="space-y-2">
          {health?.services?.map((service: any) => (
            <div key={service.name} className="flex items-center justify-between">
              <span className="text-sm">{service.name}</span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">
                  {service.latency}ms
                </span>
                <span className={`w-2 h-2 rounded-full ${
                  service.status === 'up' ? 'bg-green-500' : 'bg-red-500'
                }`} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function UsersTab() {
  const { data: users } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminApi.getUsers(),
  });
  
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">User Management</h3>
        <input
          type="text"
          placeholder="Search users..."
          className="input text-sm"
        />
      </div>
      <table className="w-full">
        <thead>
          <tr className="border-b text-sm">
            <th className="text-left py-2">User</th>
            <th className="text-left py-2">Tier</th>
            <th className="text-left py-2">Status</th>
            <th className="text-left py-2">Joined</th>
            <th className="text-right py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {users?.map((user: any) => (
            <tr key={user.id} className="border-b last:border-0">
              <td className="py-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
                    {user.name?.charAt(0) || user.email.charAt(0)}
                  </div>
                  <div>
                    <div className="font-medium">{user.name || 'Unnamed'}</div>
                    <div className="text-sm text-muted-foreground">{user.email}</div>
                  </div>
                </div>
              </td>
              <td className="py-3">
                <span className={`text-xs px-2 py-1 rounded ${
                  user.tier === 'enterprise' ? 'bg-purple-100 text-purple-700' :
                  user.tier === 'professional' ? 'bg-blue-100 text-blue-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {user.tier}
                </span>
              </td>
              <td className="py-3">
                <span className={`text-xs ${user.is_active ? 'text-green-600' : 'text-red-600'}`}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td className="py-3 text-sm text-muted-foreground">
                {new Date(user.created_at).toLocaleDateString()}
              </td>
              <td className="py-3 text-right">
                <button className="text-sm text-primary hover:underline">
                  Manage
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SystemTab({ health }: any) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="w-4 h-4" />
            <span className="text-sm text-muted-foreground">CPU Usage</span>
          </div>
          <div className="text-2xl font-bold">{health?.cpu_usage || 0}%</div>
          <div className="w-full h-2 bg-muted rounded-full mt-2">
            <div
              className="h-full bg-primary rounded-full"
              style={{ width: `${health?.cpu_usage || 0}%` }}
            />
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center gap-2 mb-2">
            <HardDrive className="w-4 h-4" />
            <span className="text-sm text-muted-foreground">Memory</span>
          </div>
          <div className="text-2xl font-bold">{health?.memory_usage || 0}%</div>
          <div className="w-full h-2 bg-muted rounded-full mt-2">
            <div
              className="h-full bg-primary rounded-full"
              style={{ width: `${health?.memory_usage || 0}%` }}
            />
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center gap-2 mb-2">
            <Database className="w-4 h-4" />
            <span className="text-sm text-muted-foreground">DB Size</span>
          </div>
          <div className="text-2xl font-bold">{health?.db_size_mb || 0} MB</div>
        </div>
      </div>
      
      {/* Queue Status */}
      <div className="card">
        <h3 className="font-semibold mb-4">Background Job Queues</h3>
        <div className="grid grid-cols-4 gap-4">
          {health?.queues?.map((queue: any) => (
            <div key={queue.name} className="p-3 bg-muted rounded-lg">
              <div className="text-sm font-medium">{queue.name}</div>
              <div className="text-2xl font-bold">{queue.pending}</div>
              <div className="text-xs text-muted-foreground">pending</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function SecurityTab() {
  const { data: security } = useQuery({
    queryKey: ['admin-security'],
    queryFn: () => adminApi.getSecurityStats(),
  });
  
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <div className="card border-red-200 bg-red-50">
          <div className="flex items-center gap-2 text-red-700">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">Failed Logins (24h)</span>
          </div>
          <div className="text-3xl font-bold text-red-700 mt-2">
            {security?.failed_logins_24h || 0}
          </div>
        </div>
        
        <div className="card">
          <div className="text-sm text-muted-foreground">2FA Enabled</div>
          <div className="text-3xl font-bold mt-2">
            {security?.two_factor_enabled || 0}
          </div>
          <div className="text-xs text-muted-foreground">users</div>
        </div>
        
        <div className="card">
          <div className="text-sm text-muted-foreground">Active Sessions</div>
          <div className="text-3xl font-bold mt-2">
            {security?.active_sessions || 0}
          </div>
        </div>
      </div>
      
      {/* Recent Security Events */}
      <div className="card">
        <h3 className="font-semibold mb-4">Recent Security Events</h3>
        <div className="space-y-2">
          {security?.recent_events?.map((event: any, i: number) => (
            <div key={i} className="flex items-center gap-3 p-2 bg-muted rounded">
              <span className={`w-2 h-2 rounded-full ${
                event.severity === 'high' ? 'bg-red-500' :
                event.severity === 'medium' ? 'bg-yellow-500' :
                'bg-blue-500'
              }`} />
              <span className="text-sm">{event.description}</span>
              <span className="text-xs text-muted-foreground ml-auto">
                {new Date(event.time).toLocaleString()}
              </span>
            </div>
          )) || <p className="text-muted-foreground">No recent events</p>}
        </div>
      </div>
    </div>
  );
}
