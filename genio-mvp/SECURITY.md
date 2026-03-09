# Security Guidelines (T066)

## Overview

This document outlines the security practices and configurations for Genio Knowledge OS.

## Security Checklist

### Authentication & Authorization

- ✅ JWT tokens with 30min expiration
- ✅ Refresh tokens with 7-day expiration
- ✅ Password hashing with bcrypt
- ✅ Rate limiting (100 req/min authenticated, 20/min unauthenticated)
- ✅ CORS configured for specific origins only

### Data Protection

- ✅ Database encryption at rest (RDS)
- ✅ TLS 1.2+ for all connections
- ✅ No sensitive data in logs
- ✅ Secrets stored in AWS Secrets Manager
- ✅ File upload restrictions (type, size)

### API Security

- ✅ Input validation (Pydantic)
- ✅ SQL injection prevention (SQLModel/ORM)
- ✅ XSS prevention (React escaping)
- ✅ CSRF protection (not needed with JWT)

### Infrastructure Security

- ✅ Private subnets for databases
- ✅ Security groups restrict access
- ✅ No direct database exposure
- ✅ WAF for common attacks
- ✅ DDoS protection (AWS Shield)

## Dependency Audit

Run regularly:

```bash
# Backend
cd backend
pip-audit

# Frontend
cd frontend
npm audit
```

## Secrets Management

### Required Secrets (AWS Secrets Manager)

```json
{
  "genio/production/database-url": "postgresql://...",
  "genio/production/jwt-secret": "...",
  "genio/production/openai-api-key": "sk-...",
  "genio/production/gemini-api-key": "...",
  "genio/production/stripe-secret-key": "sk_live_...",
  "genio/production/sendgrid-api-key": "SG..."
}
```

### Environment Variables (Non-sensitive)

```bash
# .env.production
DEBUG=false
CORS_ORIGINS=https://genio.ai,https://app.genio.ai
MONTHLY_AI_BUDGET_USD=3.0
BRIEF_STAGGER_MINUTES=60
```

## File Upload Security

- Max size: 50MB
- Allowed types: PDF, TXT, MD
- Storage: S3 with private ACL
- Virus scanning: (future enhancement)

## API Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| /auth/* | 10 | 1 min |
| /api/* (auth) | 100 | 1 min |
| /api/* (anon) | 20 | 1 min |
| /documents/upload | 5 | 1 min |

## Incident Response

### Severity Levels

1. **Critical**: Data breach, system down
2. **High**: Auth bypass, payment issue
3. **Medium**: Rate limit bypass
4. **Low**: Info disclosure

### Response Steps

1. Identify scope
2. Contain (disable affected components)
3. Investigate (logs, metrics)
4. Fix and deploy
5. Post-mortem

## Security Contacts

- Security Team: security@genio.ai
- On-call: +1-XXX-XXX-XXXX
