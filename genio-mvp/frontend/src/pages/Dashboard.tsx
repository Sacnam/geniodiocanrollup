import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { BookOpen, Rss, Zap } from 'lucide-react';
import { feedsApi, briefsApi, userApi } from '../services/api';
import type { BudgetStatus } from '../types';

export default function Dashboard() {
  const { data: feeds } = useQuery({ queryKey: ['feeds'], queryFn: () => feedsApi.list().then(r => r.data) });
  const { data: brief } = useQuery({ queryKey: ['brief', 'today'], queryFn: () => briefsApi.today().then(r => r.data), retry: false });
  const { data: budget } = useQuery({ queryKey: ['budget'], queryFn: () => userApi.getBudget().then(r => r.data as BudgetStatus) });

  const budgetColor = budget?.level === 'L1' ? 'text-green-600' : budget?.level === 'L2' ? 'text-amber-600' : 'text-red-600';

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card flex items-center gap-4">
          <div className="p-3 bg-blue-100 rounded-lg"><Rss className="w-6 h-6 text-blue-600" /></div>
          <div><p className="text-sm text-gray-600">Active Feeds</p><p className="text-2xl font-bold">{feeds?.length || 0}</p></div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="p-3 bg-purple-100 rounded-lg"><BookOpen className="w-6 h-6 text-purple-600" /></div>
          <div><p className="text-sm text-gray-600">Today's Brief</p><p className="text-2xl font-bold">{brief ? brief.article_count : '-'}</p></div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="p-3 bg-green-100 rounded-lg"><Zap className={`w-6 h-6 ${budgetColor}`} /></div>
          <div><p className="text-sm text-gray-600">AI Budget</p><p className="text-2xl font-bold">{budget ? `${Math.round(budget.percentage_remaining)}%` : '-'}</p></div>
        </div>
      </div>

      {brief ? (
        <div className="card">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-xl font-semibold">{brief.title}</h2>
              <p className="text-gray-600">{brief.subtitle}</p>
            </div>
            <Link to="/brief" className="btn-primary text-sm">Read Brief</Link>
          </div>
          {brief.executive_summary && <p className="text-gray-700">{brief.executive_summary}</p>}
        </div>
      ) : (
        <div className="card text-center py-12">
          <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No brief yet today</h3>
          <p className="text-gray-600 mt-2">Your daily brief will be generated soon</p>
          <Link to="/feeds" className="btn-primary inline-block mt-4">Add Feeds</Link>
        </div>
      )}
    </div>
  );
}
