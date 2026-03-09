"""
Analytics service for computing reading statistics and insights.
"""
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from collections import defaultdict
import json

from sqlmodel import Session, select, func, and_

from app.db.database import engine
from app.models.article import Article, UserArticleContext
from app.models.feed import Feed, UserFeed
from app.models.tag import Tag, ArticleTag


class AnalyticsService:
    """Service for computing user analytics."""
    
    @staticmethod
    def get_reading_stats(user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get reading statistics for a time period."""
        with Session(engine) as session:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Total articles read
            read_count = session.exec(
                select(func.count(UserArticleContext.id))
                .where(
                    and_(
                        UserArticleContext.user_id == user_id,
                        UserArticleContext.is_read == True,
                        UserArticleContext.read_at >= since
                    )
                )
            ).first() or 0
            
            # Total archived
            archived_count = session.exec(
                select(func.count(UserArticleContext.id))
                .where(
                    and_(
                        UserArticleContext.user_id == user_id,
                        UserArticleContext.is_archived == True,
                        UserArticleContext.updated_at >= since
                    )
                )
            ).first() or 0
            
            # Total favorited
            favorited_count = session.exec(
                select(func.count(UserArticleContext.id))
                .where(
                    and_(
                        UserArticleContext.user_id == user_id,
                        UserArticleContext.is_favorited == True,
                        UserArticleContext.updated_at >= since
                    )
                )
            ).first() or 0
            
            # This week
            week_since = datetime.utcnow() - timedelta(days=7)
            this_week = session.exec(
                select(func.count(UserArticleContext.id))
                .where(
                    and_(
                        UserArticleContext.user_id == user_id,
                        UserArticleContext.is_read == True,
                        UserArticleContext.read_at >= week_since
                    )
                )
            ).first() or 0
            
            # This month
            month_since = datetime.utcnow() - timedelta(days=30)
            this_month = session.exec(
                select(func.count(UserArticleContext.id))
                .where(
                    and_(
                        UserArticleContext.user_id == user_id,
                        UserArticleContext.is_read == True,
                        UserArticleContext.read_at >= month_since
                    )
                )
            ).first() or 0
            
            # Average daily (avoid division by zero)
            avg_daily = read_count / days if days > 0 else 0
            
            # Calculate reading streak
            streak = AnalyticsService._calculate_reading_streak(session, user_id)
            longest_streak = AnalyticsService._calculate_longest_streak(session, user_id)
            
            # Estimate reading time (avg 3 min per article)
            total_minutes = read_count * 3
            
            return {
                "total_articles_read": read_count,
                "total_articles_archived": archived_count,
                "total_articles_favorited": favorited_count,
                "total_reading_time_minutes": total_minutes,
                "articles_read_this_week": this_week,
                "articles_read_this_month": this_month,
                "average_daily_articles": round(avg_daily, 2),
                "average_reading_time_minutes": 3,
                "reading_streak_days": streak,
                "longest_reading_streak_days": longest_streak,
                "period_days": days
            }
    
    @staticmethod
    def _calculate_reading_streak(session: Session, user_id: str) -> int:
        """Calculate current reading streak."""
        # Get read dates in descending order
        results = session.exec(
            select(func.date(UserArticleContext.read_at))
            .where(
                and_(
                    UserArticleContext.user_id == user_id,
                    UserArticleContext.is_read == True
                )
            )
            .distinct()
            .order_by(func.date(UserArticleContext.read_at).desc())
        ).all()
        
        if not results:
            return 0
        
        streak = 0
        today = date.today()
        
        # Check if read today or yesterday (streak is still active)
        last_read = results[0]
        if last_read < today - timedelta(days=1):
            return 0  # Streak broken
        
        # Count consecutive days
        expected_date = today
        for read_date in results:
            if read_date == expected_date or read_date == expected_date - timedelta(days=1):
                streak += 1
                expected_date = read_date - timedelta(days=1)
            else:
                break
        
        return streak
    
    @staticmethod
    def _calculate_longest_streak(session: Session, user_id: str) -> int:
        """Calculate longest reading streak in history."""
        results = session.exec(
            select(func.date(UserArticleContext.read_at))
            .where(
                and_(
                    UserArticleContext.user_id == user_id,
                    UserArticleContext.is_read == True
                )
            )
            .distinct()
            .order_by(func.date(UserArticleContext.read_at))
        ).all()
        
        if not results:
            return 0
        
        longest = 1
        current = 1
        
        for i in range(1, len(results)):
            if results[i] == results[i-1] + timedelta(days=1):
                current += 1
                longest = max(longest, current)
            else:
                current = 1
        
        return longest
    
    @staticmethod
    def get_delta_trends(user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get Knowledge Delta trends."""
        with Session(engine) as session:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Daily averages
            daily_results = session.exec(
                select(
                    func.date(UserArticleContext.created_at).label("date"),
                    func.avg(UserArticleContext.delta_score).label("avg_delta"),
                    func.count(UserArticleContext.id).label("count")
                )
                .where(
                    and_(
                        UserArticleContext.user_id == user_id,
                        UserArticleContext.created_at >= since
                    )
                )
                .group_by(func.date(UserArticleContext.created_at))
                .order_by(func.date(UserArticleContext.created_at))
            ).all()
            
            daily_averages = [
                {
                    "date": str(d),
                    "avg_delta": round(float(avg), 3) if avg else 0,
                    "count": count
                }
                for d, avg, count in daily_results
            ]
            
            # Overall average
            avg_delta = session.exec(
                select(func.avg(UserArticleContext.delta_score))
                .where(
                    and_(
                        UserArticleContext.user_id == user_id,
                        UserArticleContext.created_at >= since
                    )
                )
            ).first() or 0
            
            # High delta percentage
            total = session.exec(
                select(func.count(UserArticleContext.id))
                .where(
                    and_(
                        UserArticleContext.user_id == user_id,
                        UserArticleContext.created_at >= since
                    )
                )
            ).first() or 0
            
            high_delta = session.exec(
                select(func.count(UserArticleContext.id))
                .where(
                    and_(
                        UserArticleContext.user_id == user_id,
                        UserArticleContext.delta_score >= 0.7,
                        UserArticleContext.created_at >= since
                    )
                )
            ).first() or 0
            
            high_delta_pct = (high_delta / total * 100) if total > 0 else 0
            
            # Calculate trend
            trend = "stable"
            if len(daily_averages) >= 14:
                first_week = sum(d["avg_delta"] for d in daily_averages[:7]) / 7
                last_week = sum(d["avg_delta"] for d in daily_averages[-7:]) / 7
                diff = last_week - first_week
                if diff > 0.05:
                    trend = "increasing"
                elif diff < -0.05:
                    trend = "decreasing"
            
            return {
                "daily_averages": daily_averages,
                "weekly_trend": trend,
                "high_delta_percentage": round(high_delta_pct, 1),
                "average_delta_score": round(float(avg_delta), 3) if avg_delta else 0,
                "delta_improvement": round(float(last_week - first_week), 3) if len(daily_averages) >= 14 else 0
            }
    
    @staticmethod
    def get_feed_performance(user_id: str) -> List[Dict[str, Any]]:
        """Get performance metrics for each feed."""
        with Session(engine) as session:
            # Get all user feeds
            user_feeds = session.exec(
                select(Feed, UserFeed)
                .join(UserFeed, Feed.id == UserFeed.feed_id)
                .where(UserFeed.user_id == user_id)
            ).all()
            
            results = []
            for feed, user_feed in user_feeds:
                # Get articles from this feed
                articles = session.exec(
                    select(Article, UserArticleContext)
                    .join(UserArticleContext, UserArticleContext.article_id == Article.id)
                    .where(
                        and_(
                            Article.source_feed_id == feed.id,
                            UserArticleContext.user_id == user_id
                        )
                    )
                ).all()
                
                total = len(articles)
                read = sum(1 for _, ctx in articles if ctx.is_read)
                
                avg_delta = sum(ctx.delta_score for _, ctx in articles) / total if total > 0 else 0
                
                results.append({
                    "feed_id": feed.id,
                    "feed_title": feed.title or feed.url,
                    "feed_url": feed.url,
                    "articles_count": total,
                    "articles_read": read,
                    "read_ratio": round(read / total, 2) if total > 0 else 0,
                    "avg_delta_score": round(avg_delta, 3),
                    "avg_reading_time_minutes": 3,
                    "last_fetch_status": feed.status,
                    "failure_rate": 0.0  # Would need fetch history
                })
            
            # Sort by read ratio descending
            results.sort(key=lambda x: x["read_ratio"], reverse=True)
            return results
    
    @staticmethod
    def get_activity_heatmap(user_id: str, days: int = 90) -> Dict[str, Any]:
        """Get activity data for heatmap visualization."""
        with Session(engine) as session:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Get daily read counts
            results = session.exec(
                select(
                    func.date(UserArticleContext.read_at).label("date"),
                    func.count(UserArticleContext.id).label("count")
                )
                .where(
                    and_(
                        UserArticleContext.user_id == user_id,
                        UserArticleContext.is_read == True,
                        UserArticleContext.read_at >= since
                    )
                )
                .group_by(func.date(UserArticleContext.read_at))
            ).all()
            
            # Create date to count mapping
            date_counts = {str(d): count for d, count in results}
            
            # Fill in all days
            end_date = date.today()
            start_date = end_date - timedelta(days=days - 1)
            
            data = []
            max_count = max(date_counts.values()) if date_counts else 1
            
            current = start_date
            while current <= end_date:
                date_str = str(current)
                count = date_counts.get(date_str, 0)
                
                # Calculate level (0-4)
                if count == 0:
                    level = 0
                elif max_count <= 4:
                    level = count
                else:
                    level = min(4, int((count / max_count) * 4) + 1)
                
                data.append({
                    "date": date_str,
                    "count": count,
                    "level": level,
                    "articles_read": count,
                    "minutes_spent": count * 3
                })
                
                current += timedelta(days=1)
            
            return {
                "days": days,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "data": data,
                "max_count": max_count
            }
    
    @staticmethod
    def get_hourly_activity(user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get reading activity by hour."""
        with Session(engine) as session:
            since = datetime.utcnow() - timedelta(days=days)
            
            results = session.exec(
                select(
                    func.extract('hour', UserArticleContext.read_at).label("hour"),
                    func.count(UserArticleContext.id).label("count")
                )
                .where(
                    and_(
                        UserArticleContext.user_id == user_id,
                        UserArticleContext.is_read == True,
                        UserArticleContext.read_at >= since
                    )
                )
                .group_by(func.extract('hour', UserArticleContext.read_at))
            ).all()
            
            # Create hour to count mapping
            hour_counts = {int(h): count for h, count in results}
            
            # Fill in all 24 hours
            total = sum(hour_counts.values()) or 1
            
            return [
                {
                    "hour": h,
                    "count": hour_counts.get(h, 0),
                    "percentage": round(hour_counts.get(h, 0) / total * 100, 1)
                }
                for h in range(24)
            ]
    
    @staticmethod
    def get_top_tags(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most used tags with stats."""
        with Session(engine) as session:
            results = session.exec(
                select(
                    Tag.id,
                    Tag.name,
                    Tag.color,
                    func.count(ArticleTag.article_id).label("count")
                )
                .join(ArticleTag, Tag.id == ArticleTag.tag_id)
                .where(
                    and_(
                        Tag.user_id == user_id,
                        ArticleTag.user_id == user_id
                    )
                )
                .group_by(Tag.id, Tag.name, Tag.color)
                .order_by(func.count(ArticleTag.article_id).desc())
                .limit(limit)
            ).all()
            
            top_tags = []
            for tag_id, name, color, count in results:
                # Get avg delta for tagged articles
                avg_delta = session.exec(
                    select(func.avg(UserArticleContext.delta_score))
                    .join(ArticleTag, ArticleTag.article_id == UserArticleContext.article_id)
                    .where(
                        and_(
                            UserArticleContext.user_id == user_id,
                            ArticleTag.tag_id == tag_id
                        )
                    )
                ).first() or 0
                
                top_tags.append({
                    "tag_id": tag_id,
                    "tag_name": name,
                    "tag_color": color,
                    "count": count,
                    "articles_read": count,  # Simplified
                    "avg_delta_score": round(float(avg_delta), 3) if avg_delta else 0
                })
            
            return top_tags
    
    @staticmethod
    def get_insights(user_id: str) -> List[Dict[str, Any]]:
        """Generate reading insights."""
        insights = []
        
        with Session(engine) as session:
            # Most active day of week
            dow_results = session.exec(
                select(
                    func.extract('dow', UserArticleContext.read_at).label("dow"),
                    func.count(UserArticleContext.id).label("count")
                )
                .where(
                    and_(
                        UserArticleContext.user_id == user_id,
                        UserArticleContext.is_read == True
                    )
                )
                .group_by(func.extract('dow', UserArticleContext.read_at))
                .order_by(func.count(UserArticleContext.id).desc())
            ).first()
            
            if dow_results:
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                most_active_dow = int(dow_results[0])
                insights.append({
                    "type": "pattern",
                    "title": f"Most Active Day: {days[most_active_dow]}",
                    "description": f"You read the most articles on {days[most_active_dow]}s.",
                    "icon": "📅"
                })
            
            # Reading velocity trend
            stats = AnalyticsService.get_reading_stats(user_id, days=14)
            if stats["average_daily_articles"] > 5:
                insights.append({
                    "type": "achievement",
                    "title": "Power Reader",
                    "description": f"You're reading {stats['average_daily_articles']:.1f} articles per day on average!",
                    "icon": "🚀"
                })
            
            # Streak achievement
            if stats["reading_streak_days"] >= 7:
                insights.append({
                    "type": "achievement",
                    "title": f"{stats['reading_streak_days']}-Day Streak!",
                    "description": "Keep up the consistent reading habit!",
                    "icon": "🔥"
                })
            
            # High delta suggestion
            delta = AnalyticsService.get_delta_trends(user_id)
            if delta["high_delta_percentage"] < 20:
                insights.append({
                    "type": "suggestion",
                    "title": "Discover More Novel Content",
                    "description": "Only {:.1f}% of your articles have high novelty. Try exploring new sources!".format(delta["high_delta_percentage"]),
                    "icon": "💡"
                })
            
            return insights


# Global instance
analytics_service = AnalyticsService()
