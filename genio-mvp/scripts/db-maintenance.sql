-- Database Maintenance Script (T068)
-- Run weekly for optimal performance

-- 1. Analyze tables for query planner
ANALYZE users;
ANALYZE feeds;
ANALYZE articles;
ANALYZE user_article_context;
ANALYZE briefs;
ANALYZE documents;
ANALYZE scout_agents;
ANALYZE scout_findings;

-- 2. Check for slow queries (requires pg_stat_statements extension)
-- SELECT query, calls, mean_time, rows
-- FROM pg_stat_statements
-- ORDER BY mean_time DESC
-- LIMIT 10;

-- 3. Index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 4. Find unused indexes (candidates for removal)
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexname NOT LIKE '%pkey%'
ORDER BY schemaname, tablename, indexname;

-- 5. Table bloat estimate (simplified)
SELECT 
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    round(100 * n_dead_tup::numeric / nullif(n_live_tup + n_dead_tup, 0), 2) as dead_tuple_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;

-- 6. Connection count monitoring
SELECT 
    datname,
    count(*)
FROM pg_stat_activity
WHERE datname = 'genio'
GROUP BY datname;

-- 7. Long-running queries (kill if needed: SELECT pg_terminate_backend(pid))
SELECT 
    pid,
    now() - query_start as duration,
    query
FROM pg_stat_activity
WHERE state = 'active'
AND now() - query_start > interval '5 minutes';
