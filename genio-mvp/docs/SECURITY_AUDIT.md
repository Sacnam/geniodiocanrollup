# Security Audit Checklist

## Pre-Production Security Review

### Authentication & Authorization
- [ ] JWT secrets rotated (min 256-bit)
- [ ] Token expiration: Access 30min, Refresh 7days
- [ ] Rate limiting: 100 req/min auth, 20/min unauth
- [ ] CORS configured for specific origins only

### Data Protection
- [ ] Database encryption at rest (RDS)
- [ ] TLS 1.2+ for all connections
- [ ] Secrets in AWS Secrets Manager (not env vars)
- [ ] File upload validation (type, size, content)

### API Security
- [ ] Input validation (Pydantic schemas)
- [ ] SQL injection prevention (ORM only)
- [ ] XSS prevention (React escaping)
- [ ] No sensitive data in logs

### Infrastructure
- [ ] Private subnets for databases
- [ ] Security groups restrict access
- [ ] WAF configured (AWS WAF)
- [ ] DDoS protection enabled

### Dependencies
```bash
# Run audits
pip-audit
npm audit

# Check for secrets
git-secrets --scan
```

### Penetration Testing
- [ ] OWASP ZAP scan
- [ ] Authentication bypass attempts
- [ ] Injection testing
- [ ] File upload abuse

## Sign-off

| Check | Status | Signed By |
|-------|--------|-----------|
| Auth Security | ☐ | |
| Data Protection | ☐ | |
| API Security | ☐ | |
| Infra Security | ☐ | |
| Dependency Audit | ☐ | |
| Penetration Test | ☐ | |

---

*Security Audit v1.0 - Genio Knowledge OS*
