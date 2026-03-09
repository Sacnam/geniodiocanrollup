# Genio Deployment Runbook

## Pre-Deployment Checklist

- [ ] All tests passing in CI
- [ ] Database migrations reviewed
- [ ] Feature flags configured
- [ ] Rollback plan documented
- [ ] Monitoring dashboards verified
- [ ] On-call engineer notified

## Deployment Windows

| Environment | Window | Lead Time |
|-------------|--------|-----------|
| Staging | Anytime | 0 min |
| Production | Tue-Thu, 10:00-16:00 UTC | 2 hours |
| Hotfix | Anytime (with approval) | 0 min |

## Standard Deployment

### 1. Staging Deployment

```bash
# Deploy to staging
./scripts/deploy.sh --env=staging --version=1.2.3

# Run smoke tests
./scripts/smoke-tests.sh staging

# Verify monitoring
open https://datadoghq.com/dashboard/genio-staging
```

### 2. Production Deployment

```bash
# 1. Announce in #deployments
# 2. Enable maintenance mode (optional)
./scripts/maintenance.sh on

# 3. Database migrations (if needed)
./scripts/migrate.sh --env=production

# 4. Deploy with blue-green strategy
./scripts/deploy.sh --env=production --version=1.2.3 --strategy=blue-green

# 5. Verify health
./scripts/health-check.sh production

# 6. Disable maintenance mode
./scripts/maintenance.sh off

# 7. Monitor for 30 minutes
watch -n 5 './scripts/health-check.sh production'

# 8. Announce completion
```

## Rollback Procedure

```bash
# Emergency rollback
./scripts/rollback.sh --env=production --to=1.2.2

# Database rollback (only if migration failed)
./scripts/migrate.sh --env=production --rollback

# Clear cache
./scripts/cache-clear.sh production
```

## Database Migrations

### Safe Migrations (Zero-Downtime)

1. **Add column** (nullable or with default)
2. **Create index concurrently** 
3. **Backfill data** (in batches)
4. **Make column non-nullable** (if needed)
5. **Drop old column** (in next release)

### Dangerous Migrations (Requires Maintenance Window)

- Renaming columns
- Adding unique constraints on large tables
- Changing column types
- Heavy data migrations

## Feature Flag Deployment

```bash
# Deploy with feature off
./scripts/deploy.sh --env=production --version=1.2.3

# Enable for 5% of users
python scripts/ops/cli.py feature-flag new-feature --percentage=5

# Monitor for 1 hour
# If no issues, increase to 25%
python scripts/ops/cli.py feature-flag new-feature --percentage=25

# Continue rollout: 50% → 75% → 100%
```

## Health Verification

```bash
# Check all components
python scripts/ops/health-dashboard.py

# Expected output:
# ✅ API: 200 OK (p50: 45ms)
# ✅ Worker: 3/3 running, queue: 12
# ✅ DB: 15ms latency
# ✅ Redis: 2ms latency  
# ✅ Qdrant: 120ms search p95
```

## Post-Deployment

- Monitor error rates for 2 hours
- Check AI cost metrics
- Verify brief generation schedule
- Review performance dashboards

## Emergency Contacts

| Role | Contact |
|------|---------|
| On-call Engineer | PagerDuty |
| Engineering Manager | Slack DM |
| CTO | Phone: +1-XXX-XXX-XXXX |
| AWS Support | Console Case |
