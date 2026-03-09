"""
TypeScript types for analytics dashboard.
"""

export interface ReadingStats {
  total_articles_read: number;
  total_articles_archived: number;
  total_articles_favorited: number;
  total_reading_time_minutes: number;
  articles_read_this_week: number;
  articles_read_this_month: number;
  average_daily_articles: number;
  average_reading_time_minutes: number;
  reading_streak_days: number;
  longest_reading_streak_days: number;
  period_days: number;
}

export interface DeltaTrends {
  daily_averages: Array<{
    date: string;
    avg_delta: number;
    count: number;
  }>;
  weekly_trend: 'increasing' | 'decreasing' | 'stable';
  high_delta_percentage: number;
  average_delta_score: number;
  delta_improvement: number;
}

export interface FeedPerformance {
  feed_id: string;
  feed_title: string;
  feed_url: string;
  articles_count: number;
  articles_read: number;
  read_ratio: number;
  avg_delta_score: number;
  avg_reading_time_minutes: number;
  last_fetch_status: string;
  failure_rate: number;
}

export interface ActivityDay {
  date: string;
  count: number;
  level: number;
  articles_read: number;
  minutes_spent: number;
}

export interface ActivityHeatmapData {
  days: number;
  start_date: string;
  end_date: string;
  data: ActivityDay[];
  max_count: number;
}

export interface HourlyActivity {
  hour: number;
  count: number;
  percentage: number;
}

export interface TopTag {
  tag_id: string;
  tag_name: string;
  tag_color?: string;
  count: number;
  articles_read: number;
  avg_delta_score: number;
}

export interface ReadingInsight {
  type: 'trend' | 'suggestion' | 'achievement' | 'pattern';
  title: string;
  description: string;
  metric?: string;
  value?: any;
  icon?: string;
}

export interface AnalyticsDashboard {
  period: string;
  generated_at: string;
  reading_stats: ReadingStats;
  delta_trends: DeltaTrends;
  feed_performance: FeedPerformance[];
  activity_heatmap: ActivityHeatmapData;
  hourly_activity: HourlyActivity[];
  top_tags: TopTag[];
  insights: ReadingInsight[];
}
