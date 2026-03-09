# Genio Incident Response Runbook

## Severity Levels

| Level | Description | Examples | Response Time |
|-------|-------------|----------|---------------|
| P0 | Critical outage | All users affected, data loss | 15 min |
| P1 | Major degradation | Core features broken | 1 hour |
| P2 | Minor issues | Non-critical bugs, performance | 4 hours |
| P3 | Low priority | UI glitches, cosmetic | 24 hours |

## Alert Routing

```
Datadog Alert → PagerDuty → On-call Engineer
                    ↓
            Slack #incidents
                    ↓
            Runbook (this doc)
```

## Common Incidents

### 1. API Down (P0)

**Symptoms**: `/health` returns 503, users can't access app

**Diagnosis**:
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs -f api --tail=100

# Check database connectivity
docker-compose exec api python -c "from app.db import check_db; check_db()"
```

**Resolution**:
1. Check if database is up: `docker-compose ps db`
2. If DB is down: `docker-compose restart db`
3. If OOM: Scale ECS task memory
4. If stuck: `docker-compose restart api`

### 2. Embedding Queue Backlog (P1)

**Symptoms**: Articles stuck in `EMBEDDING` status, queue depth >1000

**Diagnosis**:
```bash
# Check Celery queue depth
docker-compose exec redis redis-cli LLEN celery

# Check worker status
docker-compose logs worker --tail=50

# Check OpenAI API status
curl https://status.openai.com/api/v2/status.json
```

**Resolution**:
1. Scale workers: `docker-compose up -d --scale worker=5`
2. Check OpenAI rate limits in dashboard
3. If circuit breaker is open: Wait 60s for auto-recovery
4. Force circuit reset: `python scripts/ops/cli.py reset-circuit embedding`

### 3. High AI Costs (P1)

**Symptoms**: Daily cost >$500, budget utilization >80%

**Diagnosis**:
```bash
# Check cost breakdown
python scripts/ops/cli.py ai-costs --days=1

# Check feature flags
python scripts/ops/cli.py feature-flag ai.graph_rag
```

**Resolution**:
1. Enable L2 degradation: `python scripts/ops/cli.py feature-flag perf.degradation_level --percentage=50`
2. Disable expensive features temporarily:
   ```bash
   python scripts/ops/cli.py feature-flag ai.graph_rag --disable
   python scripts/ops/cli.py feature-flag scout.advanced_mode --disable
   ```
3. Increase batch sizes in config

### 4. Feed Fetch Failures (P2)

**Symptoms**: Feed success rate <95%

**Diagnosis**:
```bash
# Check failing feeds
python scripts/ops/cli.py stats

# Check specific feed logs
docker-compose logs beat | grep ERROR
```

**Resolution**:
1. Disable problematic feeds:
   ```bash
   python scripts/ops/cli.py disable-feed <feed_id>
   ```
2. Clear feed cache: `docker-compose exec redis redis-cli DEL feed:*`
3. Force refresh: `python scripts/ops/cli.py refresh-feed <feed_id>`

### 5. Qdrant Performance Degradation (P2)

**Symptoms**: Vector search p95 >500ms

**Diagnosis**:
```bash
# Check Qdrant metrics
curl http://localhost:6333/metrics

# Check collection info
curl http://localhost:6333/collections/articles
```

**Resolution**:
1. Increase `ef` parameter temporarily
2. Check disk space: `df -h`
3. Restart Qdrant if memory leak suspected

## Escalation

| Time | Action |
|------|--------|
| 0 min | Acknowledge alert, start runbook |
| 15 min | If not resolved, escalate to senior engineer |
| 30 min | If P0, page engineering manager |
| 1 hour | If P0, call CTO |

## Post-Incident

Within 24 hours of resolution:
1. Write incident summary in Slack #incidents
2. Create post-mortem document
3. Schedule post-mortem meeting (within 48h for P0/P1)
4. Create tickets for preventive actions

## War Room

```bash
# Start war room session
python scripts/ops/war-room.py --incident-id=INC-2026-02-17-001

# This opens:
# - Shared tmux session
# - Pre-loaded dashboards
# - Incident notes template
```
