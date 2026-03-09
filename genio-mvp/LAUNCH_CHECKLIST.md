# Genio Knowledge OS - Launch Checklist (T074)

## Pre-Launch Verification

### Infrastructure ✅

- [ ] AWS account configured with appropriate limits
- [ ] ECS Fargate cluster created
- [ ] RDS PostgreSQL instance (db.t3.medium)
- [ ] ElastiCache Redis (cache.t3.micro)
- [ ] Qdrant deployed on EC2 (t3.medium)
- [ ] Application Load Balancer configured
- [ ] SSL certificate (ACM) installed
- [ ] Route53 DNS records configured
- [ ] VPC with public/private subnets
- [ ] Security groups configured

### Database ✅

- [ ] Production database created
- [ ] Migrations applied (`alembic upgrade head`)
- [ ] Database indexes verified (T068)
- [ ] Backup policy configured (daily snapshots)
- [ ] Connection pooling configured
- [ ] Read replica configured (optional)

### Security ✅

- [ ] JWT secret key rotated (production)
- [ ] API keys stored in AWS Secrets Manager
- [ ] Database credentials in Secrets Manager
- [ ] Security groups restrict access
- [ ] WAF configured (AWS WAF)
- [ ] DDoS protection enabled (Shield Standard)
- [ ] Dependency audit passed (`pip-audit`)
- [ ] No secrets in code (git-secrets scan)
- [ ] HTTPS enforced (redirect HTTP to HTTPS)
- [ ] CORS properly configured

### Monitoring (T073) ✅

- [ ] Datadog agent installed
- [ ] 5 SLIs dashboard created:
  - [ ] Feed fetch success rate
  - [ ] Extraction success rate
  - [ ] Embedding generation p95
  - [ ] Brief delivery success rate
  - [ ] AI budget utilization
- [ ] Alerting configured (PagerDuty/Opsgenie)
- [ ] Log aggregation configured (CloudWatch → Datadog)
- [ ] Error tracking (Sentry) integrated
- [ ] Uptime monitoring (Pingdom)

### API & Backend ✅

- [ ] All endpoints tested in staging
- [ ] Rate limiting verified
- [ ] Circuit breaker tested
- [ ] Celery workers running
- [ ] Celery beat scheduler active
- [ ] Health endpoint responding
- [ ] Metrics endpoint responding

### Frontend ✅

- [ ] Build successful (`npm run build`)
- [ ] All pages load correctly
- [ ] Authentication flow tested
- [ ] Error boundaries working
- [ ] Loading states implemented
- [ ] Mobile responsive verified

### Billing ✅

- [ ] Stripe webhook configured
- [ ] Stripe products/prices created
- [ ] Billing dashboard working
- [ ] Subscription lifecycle tested

### AI Providers ✅

- [ ] OpenAI API key valid
- [ ] Gemini API key valid
- [ ] Rate limits monitored
- [ ] Fallback logic tested

## Beta Testing (T070)

- [ ] 10-20 beta users onboarded
- [ ] Feedback form created
- [ ] Support channel established (Discord/Slack)
- [ ] Bug tracking system ready (GitHub Issues)

### Beta Feedback Collection

| User | Status | Feedback |
|------|--------|----------|
| User 1 | ☐ | |
| User 2 | ☐ | |
| User 3 | ☐ | |
| User 4 | ☐ | |
| User 5 | ☐ | |

## Launch Day Tasks

### Pre-Launch (T-2 hours)

- [ ] Final database backup
- [ ] Deploy to production
- [ ] Verify all services healthy
- [ ] Run smoke tests
- [ ] Check error rates (should be 0)

### Launch (T-0)

- [ ] DNS switched to production
- [ ] SSL certificate active
- [ ] CDN configured (CloudFront)
- [ ] Announcement scheduled

### Post-Launch (T+1 hour)

- [ ] Monitor error rates
- [ ] Check response times
- [ ] Verify user registrations working
- [ ] Confirm briefs generating
- [ ] Monitor AI budget usage

### Post-Launch (T+24 hours)

- [ ] Review daily metrics
- [ ] Check for any critical bugs
- [ ] User feedback review
- [ ] Performance baseline established

## Rollback Plan

If critical issues occur:

1. **Immediate** (0-5 min):
   - Switch DNS to maintenance page
   - Enable maintenance mode

2. **Short-term** (5-30 min):
   - Identify issue from logs
   - Deploy hotfix if available

3. **Nuclear option** (30+ min):
   - Rollback to previous version
   ```bash
   aws ecs update-service --cluster genio-production \
     --service genio-api-service --force-new-deployment
   ```

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Engineering Lead | | ☐ | |
| Product Manager | | ☐ | |
| Security Lead | | ☐ | |
| DevOps Lead | | ☐ | |

## Post-Launch Milestones

- [ ] Week 1: 100 users
- [ ] Week 2: 500 users
- [ ] Week 4: 1000 users
- [ ] Month 2: 5000 users
- [ ] Month 3: 10000 users

---

*Launch Checklist v1.0 - Genio Knowledge OS*
