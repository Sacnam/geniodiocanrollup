import React, { useState } from 'react';
import { CreditCard, DollarSign, Mail, User, Globe, Bell, Shield } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useBriefPreferences, useMe, useUpdateBriefPreferences } from '../hooks/useApi';

interface Plan {
  id: string;
  name: string;
  description: string;
  price_monthly: number;
  price_yearly: number;
  features: string[];
}

const PLANS: Plan[] = [
  {
    id: 'starter',
    name: 'Starter',
    description: 'Perfect for individuals',
    price_monthly: 500,
    price_yearly: 4800,
    features: ['Up to 50 feeds', '$2 AI budget/month', 'Daily brief email'],
  },
  {
    id: 'professional',
    name: 'Professional',
    description: 'For power users',
    price_monthly: 1500,
    price_yearly: 14400,
    features: ['Unlimited feeds', '$10 AI budget/month', 'Priority processing', 'API access'],
  },
];

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const { data: profile } = useMe();
  const { data: preferences, isLoading: prefsLoading } = useBriefPreferences();
  const updatePrefs = useUpdateBriefPreferences();
  
  const [activeTab, setActiveTab] = useState<'profile' | 'billing' | 'preferences' | 'notifications'>('profile');
  
  // Budget calculation (mock data - would come from API)
  const monthlyBudget = 3.0;
  const budgetUsed = 1.25;
  const budgetRemaining = monthlyBudget - budgetUsed;
  const budgetPercent = (budgetUsed / monthlyBudget) * 100;
  
  // Degradation level based on budget
  const getDegradationLevel = () => {
    const pct = budgetRemaining / monthlyBudget;
    if (pct > 0.5) return { level: 1, label: 'Full AI', color: 'bg-green-500' };
    if (pct > 0.2) return { level: 2, label: 'Reduced AI', color: 'bg-yellow-500' };
    return { level: 3, label: 'Minimal AI', color: 'bg-red-500' };
  };
  
  const degradation = getDegradationLevel();

  const handlePrefChange = (key: string, value: any) => {
    updatePrefs.mutate({ [key]: value });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">Settings</h1>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex gap-8">
          {/* Sidebar */}
          <aside className="w-64 flex-shrink-0">
            <nav className="space-y-1">
              <button
                onClick={() => setActiveTab('profile')}
                className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg text-left ${
                  activeTab === 'profile' ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <User className="w-5 h-5" />
                Profile
              </button>
              <button
                onClick={() => setActiveTab('billing')}
                className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg text-left ${
                  activeTab === 'billing' ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <CreditCard className="w-5 h-5" />
                Billing & Budget
              </button>
              <button
                onClick={() => setActiveTab('preferences')}
                className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg text-left ${
                  activeTab === 'preferences' ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Globe className="w-5 h-5" />
                Preferences
              </button>
              <button
                onClick={() => setActiveTab('notifications')}
                className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg text-left ${
                  activeTab === 'notifications' ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Bell className="w-5 h-5" />
                Notifications
              </button>
            </nav>
          </aside>

          {/* Content */}
          <main className="flex-1">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="space-y-6">
                <section className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <User className="w-5 h-5" />
                    Profile Information
                  </h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Email
                      </label>
                      <input
                        type="email"
                        value={profile?.email || ''}
                        disabled
                        className="w-full px-3 py-2 border rounded-lg bg-gray-50"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Name
                      </label>
                      <input
                        type="text"
                        value={profile?.name || ''}
                        className="w-full px-3 py-2 border rounded-lg"
                      />
                    </div>
                  </div>
                </section>

                <section className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    Security
                  </h2>
                  <button className="text-blue-600 hover:text-blue-700 font-medium">
                    Change Password
                  </button>
                </section>
              </div>
            )}

            {/* Billing Tab */}
            {activeTab === 'billing' && (
              <div className="space-y-6">
                {/* AI Budget Card */}
                <section className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <DollarSign className="w-5 h-5" />
                    AI Budget
                  </h2>
                  
                  <div className="mb-6">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-600">Monthly Usage</span>
                      <span className="text-sm font-medium">
                        ${budgetUsed.toFixed(2)} / ${monthlyBudget.toFixed(2)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          budgetPercent > 80 ? 'bg-red-500' : budgetPercent > 50 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(budgetPercent, 100)}%` }}
                      />
                    </div>
                    <p className="text-sm text-gray-500 mt-2">
                      ${budgetRemaining.toFixed(2)} remaining this month
                    </p>
                  </div>

                  {/* Degradation Level */}
                  <div className="border rounded-lg p-4 bg-gray-50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Current Service Level</span>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium text-white ${degradation.color}`}>
                        L{degradation.level}: {degradation.label}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {degradation.level === 1 && 'Full AI features active. All summaries and analysis enabled.'}
                      {degradation.level === 2 && 'Reduced AI usage. Some advanced features may be limited.'}
                      {degradation.level === 3 && 'Minimal AI mode. Only basic features available.'}
                    </p>
                  </div>
                </section>

                {/* Subscription Plans */}
                <section className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <CreditCard className="w-5 h-5" />
                    Subscription
                  </h2>
                  
                  <div className="grid md:grid-cols-2 gap-4">
                    {PLANS.map((plan) => (
                      <div
                        key={plan.id}
                        className={`border-2 rounded-lg p-4 ${
                          plan.id === 'starter' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                        }`}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="font-semibold">{plan.name}</h3>
                            <p className="text-sm text-gray-600">{plan.description}</p>
                          </div>
                          {plan.id === 'starter' && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                              Current
                            </span>
                          )}
                        </div>
                        <p className="text-2xl font-bold mb-4">
                          ${(plan.price_monthly / 100).toFixed(0)}
                          <span className="text-sm font-normal text-gray-600">/month</span>
                        </p>
                        <ul className="space-y-2 mb-4">
                          {plan.features.map((feature, idx) => (
                            <li key={idx} className="text-sm text-gray-600 flex items-center gap-2">
                              <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                              {feature}
                            </li>
                          ))}
                        </ul>
                        {plan.id !== 'starter' && (
                          <button className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                            Upgrade
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            )}

            {/* Preferences Tab */}
            {activeTab === 'preferences' && (
              <div className="space-y-6">
                <section className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Globe className="w-5 h-5" />
                    Daily Brief Preferences
                  </h2>
                  
                  {prefsLoading ? (
                    <div className="animate-pulse">Loading...</div>
                  ) : (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Preferred Time
                        </label>
                        <input
                          type="time"
                          value={preferences?.preferred_time || '08:00'}
                          onChange={(e) => handlePrefChange('preferred_time', e.target.value)}
                          className="px-3 py-2 border rounded-lg"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Timezone
                        </label>
                        <select
                          value={preferences?.timezone || 'UTC'}
                          onChange={(e) => handlePrefChange('timezone', e.target.value)}
                          className="w-full px-3 py-2 border rounded-lg"
                        >
                          <option value="UTC">UTC</option>
                          <option value="America/New_York">Eastern Time</option>
                          <option value="America/Chicago">Central Time</option>
                          <option value="America/Denver">Mountain Time</option>
                          <option value="America/Los_Angeles">Pacific Time</option>
                          <option value="Europe/London">London</option>
                          <option value="Europe/Paris">Paris</option>
                          <option value="Asia/Tokyo">Tokyo</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Max Articles per Brief
                        </label>
                        <input
                          type="number"
                          min={5}
                          max={50}
                          value={preferences?.max_articles || 15}
                          onChange={(e) => handlePrefChange('max_articles', parseInt(e.target.value))}
                          className="w-24 px-3 py-2 border rounded-lg"
                        />
                      </div>
                    </div>
                  )}
                </section>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <section className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Mail className="w-5 h-5" />
                    Email Notifications
                  </h2>
                  
                  <div className="space-y-4">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={preferences?.email_delivery !== false}
                        onChange={(e) => handlePrefChange('email_delivery', e.target.checked)}
                        className="w-5 h-5 rounded"
                      />
                      <div>
                        <p className="font-medium">Daily Brief Email</p>
                        <p className="text-sm text-gray-600">Receive your daily brief via email</p>
                      </div>
                    </label>
                  </div>
                </section>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};
