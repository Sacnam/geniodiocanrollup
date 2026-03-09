# Genio Knowledge OS - Performance Optimization Guide

## Database Optimization

### Query Optimization
```sql
-- Composite indexes for common queries
CREATE INDEX idx_articles_user_status 
ON user_article_context(user_id, is_duplicate, is_archived);
```

### Connection Pooling
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_recycle=1800
)
```

## Celery Optimization

### Task Prioritization
```python
generate_daily_brief_task.apply_async(priority=0)  # High
fetch_feed_task.apply_async(priority=5)            # Medium
extract_document_task.apply_async(priority=9)      # Low
```

## Frontend Optimization

### Code Splitting
```typescript
const ConceptMap = lazy(() => import('./components/reader/ConceptMap'));
```

## Key Metrics

| Metric | Target | Alert |
|--------|--------|-------|
| API p95 | <200ms | >300ms |
| DB Query | <50ms | >100ms |
| Embeddings | <2s | >5s |
