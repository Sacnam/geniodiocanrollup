# Security Audit Report - Genio Knowledge OS Backend

**Data:** 2026-02-18  
**Scope:** `genio-mvp/backend/app`  
**Severity Scale:** CRITICAL | HIGH | MEDIUM | LOW | INFO

---

## Executive Summary

Sono state identificate **7 vulnerabilità di sicurezza**, di cui **2 CRITICHE** e **3 HIGH**. Il sistema richiede interventi immediati prima del deployment in produzione.

---

## 🔴 CRITICAL VULNERABILITIES

### 1. SEC-001: Hardcoded JWT Secret Key
**File:** `app/api/auth.py:20`  
**Severità:** CRITICAL  
**CVSS:** 9.8

```python
# VULNERABLE CODE
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
```

**Rischio:** Chiave JWT hardcoded permette a chiunque di generare token validi per qualsiasi utente, bypassando completamente l'autenticazione.

**Fix:**
```python
from app.core.config import settings

# Use settings from environment
SECRET_KEY = settings.get_jwt_secret_key()
ALGORITHM = settings.JWT_ALGORITHM
```

---

### 2. SEC-002: CORS Too Permissive
**File:** `app/main.py:42-47`  
**Severità:** CRITICAL  
**CVSS:** 8.5

```python
# VULNERABLE CODE
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Defaults to localhost in dev
    allow_credentials=True,
    allow_methods=["*"],      # ← TOO PERMISSIVE
    allow_headers=["*"],      # ← TOO PERMISSIVE
)
```

**Rischio:** In produzione con `CORS_ORIGINS=["*"]` o configurato male, permette richieste cross-origin da qualsiasi dominio con credenziali.

**Fix:**
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],  # Specific methods
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],  # Specific headers
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=600,
)
```

---

## 🟠 HIGH SEVERITY VULNERABILITIES

### 3. SEC-003: Missing Security Headers
**File:** `app/main.py`  
**Severità:** HIGH

**Mancano headers di sicurezza:**
- `Content-Security-Policy` (CSP)
- `X-Frame-Options` (Clickjacking protection)
- `X-Content-Type-Options` (MIME sniffing)
- `X-XSS-Protection`
- `Strict-Transport-Security` (HSTS)
- `Referrer-Policy`

**Fix:** Creare middleware per security headers:
```python
# app/core/security_headers.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://api.genio.ai;"
        )
        
        # HSTS (only in production with HTTPS)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
```

E aggiungere in `main.py`:
```python
from app.core.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

---

### 4. SEC-004: In-Memory Rate Limiting (Not Production-Ready)
**File:** `app/core/rate_limit.py:26`  
**Severità:** HIGH

```python
# VULNERABLE CODE - In-memory storage
self.buckets: Dict[str, Tuple[float, float]] = {}
```

**Rischio:** Il rate limiting usa memoria locale. Con più istanze/container, il rate limit è bypassabile (ogni istanza ha il proprio contatore).

**Fix:** Usare Redis per rate limiting distribuito:
```python
# app/core/rate_limit_redis.py
import redis
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str):
        super().__init__(app)
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)
        
        key = f"ratelimit:{self._get_client_id(request)}"
        
        # Increment counter with expiry
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)
        results = pipe.execute()
        count = results[0]
        
        limit = self._get_limit(request)
        
        if count > limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response
```

---

### 5. SEC-005: No Password Strength Validation
**File:** `app/api/auth.py:35-38`  
**Severità:** HIGH

```python
# VULNERABLE CODE
class UserRegister(BaseModel):
    email: EmailStr
    password: str  # ← No validation!
    name: Optional[str] = None
```

**Rischio:** Password deboli ("123456", "password") sono accettate.

**Fix:**
```python
from pydantic import BaseModel, EmailStr, field_validator
import re

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
```

---

## 🟡 MEDIUM SEVERITY VULNERABILITIES

### 6. SEC-006: Missing Input Sanitization for User Content
**File:** `app/api/documents.py`, `app/api/scouts.py`  
**Severità:** MEDIUM

**Rischio:** Contenuto HTML/JS caricato dagli utenti non viene sanitizzato, potenziale XSS storage.

**Fix:** Aggiungere sanitizzazione:
```python
# app/core/sanitizer.py
import bleach
from html import escape

def sanitize_html(content: str, allowed_tags: list = None) -> str:
    """Sanitize HTML content from users."""
    if allowed_tags is None:
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3']
    
    allowed_attributes = {
        '*': ['class'],
        'a': ['href', 'title'],
    }
    
    return bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )

def sanitize_text(text: str) -> str:
    """Escape HTML entities in text."""
    return escape(text)
```

---

### 7. SEC-007: Potential Path Traversal in File Upload
**File:** `app/api/documents.py:81-140`  
**Severità:** MEDIUM

```python
# VULNERABLE CODE
ext = os.path.splitext(file.filename)[1].lower()
unique_filename = f"{uuid.uuid4()}{ext}"
file_path = os.path.join(UPLOAD_DIR, unique_filename)  # ← Could be exploited
```

Sebbene usi `uuid.uuid4()`, il filename originale non viene validato.

**Fix:**
```python
import os
import mimetypes
from pathlib import Path

ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.md', '.docx', '.epub'}
MAX_FILENAME_LENGTH = 255

def safe_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove path components
    filename = os.path.basename(filename)
    
    # Get extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extension {ext} not allowed")
    
    # Truncate if too long
    if len(filename) > MAX_FILENAME_LENGTH:
        filename = filename[:MAX_FILENAME_LENGTH]
    
    return f"{uuid.uuid4()}{ext}"
```

---

## 🟢 LOW SEVERITY / INFO

### 8. SEC-008: Missing Security.txt / Disclosure Policy
**Severità:** LOW  
**Fix:** Aggiungere endpoint `/.well-known/security.txt`:
```
Contact: security@genio.ai
Expires: 2027-02-18T00:00:00.000Z
Acknowledgments: https://genio.ai/security/hall-of-fame
Policy: https://genio.ai/security/policy
```

---

### 9. SEC-009: Rate Limit Headers Expose System Info
**File:** `app/core/rate_limit.py:108-110`  
**Severità:** INFO

Headers esposti potrebbero aiutare attaccanti a capire i limiti.

---

### 10. SEC-010: No Request ID for Tracing
**Severità:** INFO  
**Raccomandazione:** Aggiungere header `X-Request-ID` per tracciamento richieste:
```python
# In middleware
request_id = str(uuid.uuid4())
request.state.request_id = request_id
response.headers["X-Request-ID"] = request_id
```

---

## 🔧 IMPLEMENTATION CHECKLIST

### Immediate Actions (Before Production)
- [ ] Fix SEC-001: Remove hardcoded SECRET_KEY
- [ ] Fix SEC-002: Restrict CORS methods/headers
- [ ] Fix SEC-003: Add security headers middleware
- [ ] Fix SEC-005: Add password strength validation

### Short-term (1-2 weeks)
- [ ] Fix SEC-004: Implement Redis-based rate limiting
- [ ] Fix SEC-006: Add input sanitization
- [ ] Fix SEC-007: Fix path traversal potential

### Long-term
- [ ] Implement SEC-008: Security.txt
- [ ] Add WAF (Web Application Firewall)
- [ ] Setup automated security scanning (SAST/DAST)
- [ ] Regular penetration testing

---

## 🛡️ ADDITIONAL SECURITY RECOMMENDATIONS

### 1. Environment Security
```bash
# .env.production example
DEBUG=false
JWT_SECRET_KEY=<64-char-random-string>
CORS_ORIGINS=https://app.genio.ai,https://www.genio.ai
DATABASE_URL=postgresql://genio:${DB_PASSWORD}@${DB_HOST}:5432/genio
# Never commit .env files!
```

### 2. Database Connection Security
```python
# app/core/database.py
# Use SSL for database connections
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={
        "sslmode": "require",
        "sslrootcert": "/path/to/ca-cert.pem"
    } if not settings.DEBUG else {}
)
```

### 3. API Key Rotation
```python
# Add to settings
API_KEY_ROTATION_DAYS: int = 90
JWT_KEY_ROTATION_DAYS: int = 30
```

### 4. Audit Logging
```python
# app/core/audit.py
class AuditLogger:
    def log_auth_event(self, user_id: str, event: str, ip: str, user_agent: str):
        """Log authentication events."""
        pass
    
    def log_access_denied(self, resource: str, user_id: str, reason: str):
        """Log access control violations."""
        pass
```

---

## 📊 SECURITY METRICS TO MONITOR

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Failed auth attempts / IP / 5min | < 5 | > 10 |
| Rate limit violations / min | < 10 | > 50 |
| Error rate (5xx) | < 0.1% | > 1% |
| JWT validation failures | < 1% | > 5% |
| Unusual access patterns | - | Anomaly detected |

---

## 🔐 COMPLIANCE NOTES

- **GDPR:** Implement data retention policies, right to deletion
- **OWASP Top 10:** Address all relevant vulnerabilities
- **SOC 2:** Implement audit trails, access controls
- **PCI DSS:** If handling payments, ensure compliance

---

**Report Generated By:** Security Audit Tool  
**Next Review:** 2026-03-18
