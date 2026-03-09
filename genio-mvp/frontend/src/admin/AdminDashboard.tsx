import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Users, 
  FileText, 
  Activity, 
  Settings, 
  Shield,
  TrendingUp,
  AlertTriangle,
  DollarSign,
  Database,
  Server,
  RefreshCw
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { adminApi } from './adminApi';
import { UserManagement } from './UserManagement';
import { SystemHealth } from './SystemHealth';
import { AICostsPanel } from './AICostsPanel';
import { FeatureFlagsPanel } from './FeatureFlagsPanel';

type AdminTab = 'overview' | 'users' | 'health' | 'costs' | 'features' | 'settings';

export const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: adminApi.getStats,
  });

  const tabs = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'health', label: 'System Health', icon: Activity },
    { id: 'costs', label: 'AI Costs', icon: DollarSign },
    { id: 'features', label: 'Feature Flags', icon: Shield },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'users':
        return <UserManagement />;
      case 'health':
        return <SystemHealth />;
      case 'costs':
        return <AICostsPanel />;
      case 'features':
        return <FeatureFlagsPanel />;
      case 'settings':
        return <SettingsPanel />;
      default:
        return <OverviewPanel stats={stats} isLoading={isLoading} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-purple-600" />
              <div>
                <h1 className="text-2xl font-bold">Admin Dashboard</h1>
                <p className="text-sm text-gray-500">Genio Platform Administration</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                ● System Operational
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Sidebar */}
          <div className="col-span-12 lg:col-span-2">
            <nav className="space-y-1">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as AdminTab)}
                  className={`
                    w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors
                    ${activeTab === tab.id 
                      ? 'bg-purple-100 text-purple-700' 
                      : 'text-gray-600 hover:bg-gray-100'
                    }
                  `}
                >
                  <tab.icon className="w-5 h-5" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Main Content */}
          <div className="col-span-12 lg:col-span-10">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

// Overview Panel Component
const OverviewPanel: React.FC<{ stats: any; isLoading: boolean }> = ({ stats, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  const statCards = [
    { 
      label: 'Total Users', 
      value: stats?.total_users || 0, 
      icon: Users, 
      trend: '+12%',
      color: 'blue' 
    },
    { 
      label: 'Active Feeds', 
      value: stats?.active_feeds || 0, 
      icon: FileText, 
      trend: '+5%',
      color: 'green' 
    },
    { 
      label: 'Articles Today', 
      value: stats?.articles_today || 0, 
      icon: TrendingUp, 
      trend: '+23%',
      color: 'purple' 
    },
    { 
      label: 'AI Cost Today', 
      value: `$${(stats?.ai_cost_today || 0).toFixed(2)}`, 
      icon: DollarSign, 
      trend: '-8%',
      color: 'orange' 
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((card, idx) => (
          <div key={idx} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{card.label}</p>
                <p className="text-2xl font-bold mt-1">{card.value}</p>
              </div>
              <div className={`p-3 bg-${card.color}-100 rounded-lg`}>
                <card.icon className={`w-6 h-6 text-${card.color}-600`} />
              </div>
            </div>
            <p className={`text-sm mt-2 ${card.trend.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
              {card.trend} from last week
            </p>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <QuickActionButton icon={Users} label="Add User" />
          <QuickActionButton icon={Database} label="Backup DB" />
          <QuickActionButton icon={Server} label="Scale Workers" />
          <QuickActionButton icon={AlertTriangle} label="View Alerts" />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {[
            { action: 'User registered', detail: 'john@example.com', time: '2 min ago' },
            { action: 'Feed processed', detail: 'Hacker News - 50 articles', time: '5 min ago' },
            { action: 'Brief delivered', detail: 'To 150 users', time: '15 min ago' },
            { action: 'AI cost alert', detail: 'Approaching 80% threshold', time: '1 hour ago' },
          ].map((activity, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium">{activity.action}</p>
                <p className="text-sm text-gray-500">{activity.detail}</p>
              </div>
              <span className="text-sm text-gray-400">{activity.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const QuickActionButton: React.FC<{ icon: any; label: string }> = ({ icon: Icon, label }) => (
  <button className="flex flex-col items-center gap-2 p-4 border rounded-lg hover:bg-gray-50 transition-colors">
    <Icon className="w-6 h-6 text-purple-600" />
    <span className="text-sm font-medium">{label}</span>
  </button>
);

// Settings Panel Component
const SettingsPanel: React.FC = () => (
  <div className="bg-white rounded-lg shadow p-6">
    <h3 className="font-semibold mb-6">Platform Settings</h3>
    
    <div className="space-y-6">
      <SettingItem
        title="Maintenance Mode"
        description="Put the platform in maintenance mode"
        type="toggle"
      />
      <SettingItem
        title="New User Registration"
        description="Allow new users to register"
        type="toggle"
        defaultChecked
      />
      <SettingItem
        title="AI Processing"
        description="Enable AI-powered features"
        type="toggle"
        defaultChecked
      />
      <SettingItem
        title="Daily Brief Time"
        description="Default time for daily briefs"
        type="select"
        options={['08:00', '09:00', '10:00', '18:00']}
      />
      <SettingItem
        title="Max AI Cost per User"
        description="Monthly AI budget limit ($)"
        type="number"
        defaultValue={3}
      />
    </div>
  </div>
);

const SettingItem: React.FC<any> = ({ title, description, type, ...props }) => (
  <div className="flex items-center justify-between py-4 border-b last:border-0">
    <div>
      <p className="font-medium">{title}</p>
      <p className="text-sm text-gray-500">{description}</p>
    </div>
    <div>
      {type === 'toggle' && (
        <input 
          type="checkbox" 
          className="w-5 h-5 rounded"
          defaultChecked={props.defaultChecked}
        />
      )}
      {type === 'select' && (
        <select className="border rounded-lg px-3 py-2">
          {props.options.map((opt: string) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      )}
      {type === 'number' && (
        <input 
          type="number" 
          defaultValue={props.defaultValue}
          className="border rounded-lg px-3 py-2 w-24"
        />
      )}
    </div>
  </div>
);
