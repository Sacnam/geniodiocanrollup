#!/bin/bash
#
# Genio Knowledge OS - Maintenance Script
# Run daily maintenance tasks
#

set -e

log() {
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $1"
}

cd /app

log "Starting daily maintenance..."

# 1. Database maintenance
log "Running database maintenance..."
docker-compose exec -T postgres psql -U genio -c "VACUUM ANALYZE;"
docker-compose exec -T postgres psql -U genio -c "REINDEX DATABASE genio;"

# 2. Cleanup old analytics snapshots
log "Cleaning up old analytics..."
docker-compose exec -T backend python -c "
from app.db.database import engine
from sqlmodel import Session, select
from datetime import datetime, timedelta
from app.models.analytics import AnalyticsSnapshot

with Session(engine) as session:
    cutoff = datetime.utcnow() - timedelta(days=365)
    old = session.exec(
        select(AnalyticsSnapshot).where(AnalyticsSnapshot.snapshot_date < cutoff.date())
    ).all()
    for snap in old:
        session.delete(snap)
    session.commit()
    print(f'Deleted {len(old)} old snapshots')
"

# 3. Cleanup old execution logs
log "Cleaning up old execution logs..."
docker-compose exec -T backend python -c "
from app.db.database import engine
from sqlmodel import Session, select
from datetime import datetime, timedelta
from app.models.plugin import PluginExecutionLog

with Session(engine) as session:
    cutoff = datetime.utcnow() - timedelta(days=90)
    old = session.exec(
        select(PluginExecutionLog).where(PluginExecutionLog.created_at < cutoff)
    ).all()
    for log in old:
        session.delete(log)
    session.commit()
    print(f'Deleted {len(old)} old execution logs')
"

# 4. Elasticsearch optimization
log "Optimizing Elasticsearch indices..."
curl -X POST "localhost:9200/genio_articles/_forcemerge?max_num_segments=1" || true

# 5. Redis memory optimization
log "Optimizing Redis memory..."
docker-compose exec -T redis redis-cli MEMORY PURGE

# 6. Cleanup old share links
log "Cleaning up expired share links..."
docker-compose exec -T backend python -c "
from app.db.database import engine
from sqlmodel import Session, select
from datetime import datetime
from app.models.sharing import ShareLink

with Session(engine) as session:
    expired = session.exec(
        select(ShareLink).where(
            ShareLink.expires_at < datetime.utcnow(),
            ShareLink.is_active == True
        )
    ).all()
    for link in expired:
        link.is_active = False
        session.add(link)
    session.commit()
    print(f'Deactivated {len(expired)} expired share links')
"

# 7. Update search index
log "Reindexing recent articles..."
docker-compose exec -T backend python -c "
from app.tasks.search_tasks import reindex_user_content
from app.db.database import engine
from sqlmodel import Session, select
from app.models.user import User

with Session(engine) as session:
    users = session.exec(select(User)).all()
    for user in users[:10]:  # Batch: 10 users per day
        reindex_user_content.delay(user.id)
    print(f'Queued reindex for {len(users[:10])} users')
"

# 8. Generate daily report
log "Generating daily report..."
docker-compose exec -T backend python -c "
from app.services.analytics_service import analytics_service
from app.db.database import engine
from sqlmodel import Session, select
from app.models.user import User
from datetime import datetime

with Session(engine) as session:
    users = session.exec(select(User)).all()
    total_articles = sum(
        analytics_service.get_reading_stats(u.id, days=1)['total_articles_read']
        for u in users
    )
    print(f'Daily report: {len(users)} users, {total_articles} articles read')
"

# 9. Health check
log "Running health checks..."
curl -f http://localhost:8000/health || exit 1

log "Maintenance complete!"

# Send notification
if [ -n "$SLACK_WEBHOOK" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Daily maintenance completed successfully\"}" \
        $SLACK_WEBHOOK
fi
