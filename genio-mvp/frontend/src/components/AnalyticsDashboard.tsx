"""
Personal analytics dashboard with reading stats and insights.
"""
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart3, TrendingUp, Clock, BookOpen, Flame,
  Calendar, Tag, Zap, Award, Download
} from 'lucide-react';
import { analyticsApi } from '../services/api/analytics';
import { ActivityHeatmap } from './ActivityHeatmap';
import { HourlyChart } from './HourlyChart';
import type { AnalyticsDashboard } from '../types/analytics';

interface AnalyticsDashboardProps {
  className?: string;
}

const PERIODS = [
  { value: '7d', label: '7 Days' },
  { value: '30d', label: '30 Days' },
  { value: '90d', label: '3 Months' },
  { value: '1y', label: '1 Year' },
];

export function AnalyticsDashboard({ className = '' }: AnalyticsDashboardProps) {
  const [period, setPeriod] = useState('30d');
  
  const { data, isLoading } = useQuery<AnalyticsDashboard>({
    queryKey: ['analytics', period],
    queryFn: () => analyticsApi.getDashboard(period),
  });
  
  if (isLoading || !data) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/4" />
          <div className="grid grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-muted rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }
  
  const { reading_stats, delta_trends, feed_performance, activity_heatmap, 
          hourly_activity, top_tags, insights } = data;
  
  return (
    <div className={`space-y-8 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="w-6 h-6" />
            Analytics Dashboard
          </h1>
          <p className="text-muted-foreground">
            Track your reading habits and knowledge growth
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Period Selector */}
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="input"
          >
            {PERIODS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
          
          <button
            onClick={() => analyticsApi.export('json')}
            className="btn btn-secondary"
          >
            <Download className="w-4 h-4 mr-1" />
            Export
          </button>
        </div>
      </div>
      
      {/* Insights */}
      {insights.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {insights.slice(0, 3).map((insight, i) => (
            <div
              key={i}
              className={`p-4 rounded-lg border ${
                insight.type === 'achievement' 
                  ? 'bg-yellow-50 border-yellow-200' 
                  : insight.type === 'suggestion'
                  ? 'bg-blue-50 border-blue-200'
                  : 'bg-muted'
              }`}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{insight.icon}</span>
                <div>
                  <h3 className="font-medium">{insight.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {insight.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Key Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={<BookOpen className="w-5 h-5 text-blue-500" />}
          label="Articles Read"
          value={reading_stats.total_articles_read}
          subtext={`${reading_stats.average_daily_articles}/day avg`}
        />
        <StatCard
          icon={<Clock className="w-5 h-5 text-green-500" />}
          label="Reading Time"
          value={`${Math.round(reading_stats.total_reading_time_minutes / 60)}h`}
          subtext={`${reading_stats.total_reading_time_minutes} min total`}
        />
        <StatCard
          icon={<Flame className="w-5 h-5 text-orange-500" />}
          label="Current Streak"
          value={`${reading_stats.reading_streak_days} days`}
          subtext={`Best: ${reading_stats.longest_reading_streak_days} days`}
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5 text-purple-500" />}
          label="Avg Delta"
          value={delta_trends.average_delta_score.toFixed(2)}
          subtext={
            delta_trends.weekly_trend === 'increasing' 
              ? '↗ Trending up' 
              : delta_trends.weekly_trend === 'decreasing'
              ? '↘ Trending down'
              : '→ Stable'
          }
        />
      </div>
      
      {/* Activity Heatmap */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Activity Heatmap
          </h3>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>Less</span>
            <div className="flex gap-0.5">
              {[0, 1, 2, 3, 4].map((level) => (
                <div
                  key={level}
                  className={`w-3 h-3 rounded-sm ${
                    level === 0 ? 'bg-muted' :
                    level === 1 ? 'bg-green-200' :
                    level === 2 ? 'bg-green-300' :
                    level === 3 ? 'bg-green-400' :
                    'bg-green-500'
                  }`}
                />
              ))}
            </div>
            <span>More</span>
          </div>
        </div>
        <ActivityHeatmap data={activity_heatmap} />
      </div>
      
      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Activity */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Reading by Hour
          </h3>
          <HourlyChart data={hourly_activity} />
        </div>
        
        {/* Top Tags */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Tag className="w-4 h-4" />
            Top Tags
          </h3>
          <div className="space-y-2">
            {top_tags.length === 0 ? (
              <p className="text-muted-foreground text-sm">No tags used yet</p>
            ) : (
              top_tags.map((tag) => (
                <div
                  key={tag.tag_id}
                  className="flex items-center justify-between p-2 rounded hover:bg-muted/50"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: tag.tag_color || '#666' }}
                    />
                    <span>{tag.tag_name}</span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {tag.count} articles
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
      
      {/* Feed Performance */}
      <div className="card">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Feed Performance
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 text-sm font-medium">Feed</th>
                <th className="text-right py-2 text-sm font-medium">Articles</th>
                <th className="text-right py-2 text-sm font-medium">Read</th>
                <th className="text-right py-2 text-sm font-medium">Read Ratio</th>
                <th className="text-right py-2 text-sm font-medium">Avg Delta</th>
              </tr>
            </thead>
            <tbody>
              {feed_performance.map((feed) => (
                <tr key={feed.feed_id} className="border-b last:border-0">
                  <td className="py-3">
                    <div className="font-medium truncate max-w-xs">
                      {feed.feed_title}
                    </div>
                  </td>
                  <td className="text-right py-3">{feed.articles_count}</td>
                  <td className="text-right py-3">{feed.articles_read}</td>
                  <td className="text-right py-3">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary"
                          style={{ width: `${feed.read_ratio * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-muted-foreground w-10">
                        {Math.round(feed.read_ratio * 100)}%
                      </span>
                    </div>
                  </td>
                  <td className="text-right py-3">
                    <span className={
                      feed.avg_delta_score >= 0.7 ? 'text-green-600' :
                      feed.avg_delta_score >= 0.4 ? 'text-yellow-600' :
                      'text-muted-foreground'
                    }>
                      {feed.avg_delta_score.toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  subtext: string;
}

function StatCard({ icon, label, value, subtext }: StatCardProps) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-3 mb-2">
        {icon}
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-muted-foreground">{subtext}</div>
    </div>
  );
}
