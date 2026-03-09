# Genio Knowledge OS - Developer Guide

Quick reference for developers working on the Genio platform.

## 🚀 Quick Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f elasticsearch

# Database migrations
cd backend
alembic upgrade head          # Apply migrations
alembic downgrade -1          # Rollback one
alembic revision --autogenerate -m "description"

# Run tests
cd backend && pytest -v
cd frontend && npm test

# Code formatting
cd backend && black app tests
cd backend && isort app tests
cd frontend && npm run lint
```

## 📁 Key Directories

### Backend (`/backend/app`)
```
app/
├── api/              # REST API endpoints
├── models/           # Database models (SQLModel)
├── services/         # Business logic
├── tasks/            # Celery background tasks
├── core/             # Config, auth, security
├── library/          # Document processing
└── lab/              # Scout agents
```

### Frontend (`/frontend/src`)
```
src/
├── components/       # React components
│   ├── admin/        # Admin panel
│   ├── settings/     # Settings pages
│   └── *.tsx         # Feature components
├── hooks/            # Custom React hooks
├── services/api/     # API clients
├── types/            # TypeScript types
└── pages/            # Route pages
```

## 🔌 API Endpoints Reference

### Core
```
GET    /api/v1/feeds
POST   /api/v1/feeds
GET    /api/v1/articles
POST   /api/v1/articles/{id}/read
GET    /api/v1/briefs
```

### Enterprise Features
```
# Tags
GET    /api/v1/tags
POST   /api/v1/tags
POST   /api/v1/tags/articles/{id}/tags

# Saved Views
GET    /api/v1/views
POST   /api/v1/views
GET    /api/v1/views/{id}/apply

# Search
GET    /api/v1/search
GET    /api/v1/search/semantic
GET    /api/v1/search/suggest

# Comments
GET    /api/v1/articles/{id}/comments
POST   /api/v1/articles/{id}/comments
POST   /api/v1/comments/{id}/like

# Teams
GET    /api/v1/teams
POST   /api/v1/teams
POST   /api/v1/teams/{id}/invite

# 2FA
GET    /api/v1/2fa/status
POST   /api/v1/2fa/setup-totp
POST   /api/v1/2fa/verify-totp-setup

# Plugins
GET    /api/v1/plugins/marketplace
POST   /api/v1/plugins/install
POST   /api/v1/plugins/{id}/execute
```

## 🗄️ Database Models

### Core Models
```python
User                    # User accounts
Feed / UserFeed         # RSS feeds
Article                 # Shared article pool
UserArticleContext      # Per-user article state
Document                # Uploaded documents
```

### Enterprise Models
```python
Tag / ArticleTag        # Hierarchical tagging
SavedView               # Saved filter views
Comment                 # Threaded comments
BriefTemplate           # Customizable briefs
Team / TeamMember       # Collaboration
TwoFactorAuth           # 2FA configuration
Plugin / UserPlugin     # Plugin system
```

## 🔧 Common Tasks

### Adding a New API Endpoint

1. Create model in `app/models/`:
```python
class MyFeature(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
```

2. Create API file in `app/api/`:
```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/my-feature")
async def get_feature():
    return {"status": "ok"}
```

3. Register in `app/main.py`:
```python
from app.api import my_feature
app.include_router(my_feature.router, prefix="/api/v1/my-feature")
```

4. Create migration:
```bash
alembic revision --autogenerate -m "add my_feature"
alembic upgrade head
```

### Adding a Frontend Component

1. Create component in `frontend/src/components/`:
```tsx
export function MyComponent() {
  return <div>My Component</div>;
}
```

2. Add API service in `frontend/src/services/api/`:
```typescript
export const myFeatureApi = {
  get: async () => {
    const response = await apiClient.get('/my-feature');
    return response.data;
  }
};
```

3. Add type in `frontend/src/types/`:
```typescript
export interface MyFeature {
  id: string;
  name: string;
}
```

## 🧪 Testing

### Backend Tests
```python
# tests/test_my_feature.py
def test_my_feature(client: TestClient):
    response = client.get("/api/v1/my-feature")
    assert response.status_code == 200
```

### Frontend Tests
```typescript
// MyComponent.test.tsx
import { render, screen } from '@testing-library/react';

test('renders component', () => {
  render(<MyComponent />);
  expect(screen.getByText('My Component')).toBeInTheDocument();
});
```

## 🔍 Debugging

### Backend
```python
# Add logging
import logging
logger = logging.getLogger(__name__)
logger.info("Debug message")

# Add breakpoint
import pdb; pdb.set_trace()
```

### Frontend
```typescript
// Add console logging
console.log('Debug:', data);

// React DevTools
// Use browser extension for component inspection
```

### Elasticsearch
```bash
# Check index health
curl http://localhost:9200/_cluster/health

# List indices
curl http://localhost:9200/_cat/indices

# Search
curl http://localhost:9200/genio_articles/_search?q=title:test
```

### Database
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U genio -d genio

# Common queries
\dt                    # List tables
\d table_name          # Describe table
SELECT * FROM users;   # Query data
```

## 📊 Performance Monitoring

### Backend Metrics
```
GET /metrics           # Prometheus metrics
GET /health            # Health check
```

### Key Metrics to Watch
- Request latency (p50, p95, p99)
- Database query time
- Elasticsearch search latency
- Redis cache hit rate
- Celery queue depth

## 🔐 Security Checklist

- [ ] All endpoints have authentication
- [ ] Input validation using Pydantic
- [ ] SQL injection prevention (SQLModel)
- [ ] XSS protection (output sanitization)
- [ ] Rate limiting configured
- [ ] CORS properly set
- [ ] Secrets in environment variables
- [ ] No hardcoded credentials

## 🚀 Deployment

### Production Checklist
- [ ] Environment variables set
- [ ] Database migrations run
- [ ] Elasticsearch indexes created
- [ ] SSL certificates configured
- [ ] Backups scheduled
- [ ] Monitoring enabled
- [ ] Log aggregation configured

### Docker Production Build
```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Push to registry
docker push genio/backend:latest
docker push genio/frontend:latest

# Deploy
./scripts/production-deploy.sh
```

## 📞 Getting Help

- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Logs: `docker-compose logs -f`
- Issues: Check `IMPLEMENTATION_CHECKLIST.md`

---

**Happy coding! 🚀**
