# Genio Knowledge OS - Agent Documentation

> **Project Language:** English (primary), Italian (historical discussions)  
> **Project Phase:** Production-Ready MVP  
> **Last Updated:** February 2026

---

## Project Overview

**Genio Knowledge OS** is an AI-powered knowledge management platform with three core modules:

1. **Stream** (v1.0) - Intelligent RSS/Atom feed aggregator with AI-powered daily briefs
2. **Library** (v2.0) - AI-enhanced document reader with semantic search and knowledge graphs
3. **Lab** (v3.0) - Agentic research automation with Scout agents

### Repository Structure

```
GenioCortex/
├── genio-mvp/              # Main MVP application (FastAPI + React)
│   ├── backend/            # Python FastAPI backend
│   │   ├── app/
│   │   │   ├── api/        # REST API endpoints
│   │   │   ├── core/       # Config, auth, rate limiting, security
│   │   │   ├── models/     # Database models (SQLModel)
│   │   │   ├── tasks/      # Celery background tasks
│   │   │   ├── library/    # Document processing (Library module)
│   │   │   ├── lab/        # Scout agents (Lab module)
│   │   │   ├── services/   # Business logic, AI gateway
│   │   │   └── utils/      # Utility functions
│   │   ├── alembic/        # Database migrations (14+ versions)
│   │   ├── tests/          # pytest test suite (33+ test files)
│   │   ├── pyproject.toml  # Poetry configuration
│   │   └── requirements.txt
│   ├── frontend/           # React 18 + TypeScript frontend
│   │   ├── src/
│   │   │   ├── pages/      # Route-level components
│   │   │   ├── components/ # Reusable UI components
│   │   │   ├── hooks/      # Custom React hooks (TanStack Query)
│   │   │   ├── services/   # API client functions
│   │   │   ├── types/      # TypeScript type definitions
│   │   │   └── contexts/   # React context providers
│   │   ├── package.json
│   │   ├── tsconfig.json   # Strict TypeScript config
│   │   └── vite.config.ts
│   ├── e2e/                # Playwright end-to-end tests
│   ├── deploy/             # Terraform deployment configs
│   ├── scripts/            # Operations scripts
│   ├── docs/               # Documentation
│   ├── Makefile            # Build automation
│   ├── docker-compose.yml  # Local development infrastructure
│   └── .github/workflows/  # GitHub Actions CI/CD
│
├── genio_extension/        # Browser extension (Chrome/Firefox Manifest V3)
│   ├── src/                # Extension source code
│   │   ├── manifest.json   # Extension manifest (v1.9.10)
│   │   ├── background/     # Service worker scripts
│   │   ├── content/        # Content scripts
│   │   ├── popup/          # Popup UI
│   │   ├── sidebar/        # Sidebar component
│   │   └── reader/         # Reader mode
│   ├── functions/          # Firebase Cloud Functions
│   └── package.json
│
└── [planning_docs]         # Historical PRD, MVP plans, discussions
```

---

## Technology Stack

### Backend (genio-mvp/backend)

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.12+ |
| Framework | FastAPI | 0.109.0 |
| ORM | SQLModel | 0.0.14 |
| Migrations | Alembic | 1.13.1 |
| Database | PostgreSQL | 15 |
| Cache/Queue | Redis | 7 |
| Task Queue | Celery | 5.3.6 |
| Vector DB | Qdrant | 1.7.0 |
| Search | Elasticsearch | 8.11+ |
| AI Gateway | OpenAI + Google Gemini | - |
| Document Parsing | PyMuPDF, python-docx, ebooklib | - |

### Frontend (genio-mvp/frontend)

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | 18.2.0 |
| Language | TypeScript | 5.2.2 (strict mode) |
| Build Tool | Vite | 5.0.8 |
| Styling | Tailwind CSS | 3.4.0 |
| State Management | Zustand | 4.4.7 |
| Data Fetching | TanStack Query | 5.17.0 |
| Routing | React Router DOM | 6.21.0 |
| Visualization | D3.js | 7.8.5 |
| Testing | Vitest | 1.2.0 |

### Extension (genio_extension)

| Component | Technology |
|-----------|------------|
| Platform | Chrome Extension Manifest V3 |
| Backend | Firebase (Firestore, Functions) |
| Build | Rollup |
| Parsing | Mozilla Readability, Turndown |

---

## Module Architecture

### 1. STREAM (Feed Aggregator)

**Location:** `genio-mvp/backend/app/tasks/`, `genio-mvp/backend/app/api/feeds.py`

**Key Features:**
- RSS/Atom feed aggregation (`feedparser`)
- Content extraction (`trafilatura`)
- Semantic deduplication (vector similarity >0.85)
- Knowledge Delta scoring (novelty detection)
- Daily Brief generation (Celery beat scheduled)
- "The Diff" algorithm for unique content highlighting
- Full-text search with Elasticsearch

**Data Flow:**
```
Feed URL → fetch_feed_task() → extract_content() → generate_embedding() →
clustering() → summarize() → Daily Brief
```

### 2. LIBRARY (Document Management)

**Location:** `genio-mvp/backend/app/library/`, `genio-mvp/frontend/src/components/library/`

**Key Features:**
- Universal document parser (PDF, EPUB, DOCX, TXT, MD)
- OCR for scanned documents
- Semantic chunking by topic boundaries
- Knowledge Graph (Personal Knowledge Graph - PKG)
- GraphRAG search with citations
- Highlights and annotations

**Key Files:**
- `parsers.py` - Document parsing
- `semantic_chunker.py` - Topic-based chunking
- `graph_rag.py` - Graph-enhanced RAG
- `embeddings.py` - Vector generation
- `fsm.py` - Document processing state machine

### 3. LAB (Research Automation)

**Location:** `genio-mvp/backend/app/lab/`

**Key Features:**
- Scout Agents for automated research
- Multi-source monitoring (feeds, documents, arXiv)
- Scheduled research tasks
- AI-generated insights and pattern detection

**Key Files:**
- `scout_advanced.py` - Scout agent implementation
- `engine.py` - Research execution engine
- `models.py` - Scout data models

---

## Build and Development Commands

### Quick Start (Docker)

```bash
cd genio-mvp

# Start all infrastructure services
docker-compose up -d postgres redis qdrant elasticsearch

# Start full stack (see Makefile targets)
make dev
```

### Backend Development

```bash
cd genio-mvp/backend

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database migrations
alembic upgrade head

# Start API server (development)
uvicorn app.main:app --reload

# Start Celery worker (separate terminal)
celery -A app.tasks worker --loglevel=info

# Start Celery beat scheduler (separate terminal)
celery -A app.tasks beat --loglevel=info
```

### Frontend Development

```bash
cd genio-mvp/frontend

# Install dependencies
npm install

# Start development server
npm run dev          # Vite dev server on http://localhost:5173

# Build for production
npm run build

# Preview production build
npm run preview
```

### Extension Development

```bash
cd genio_extension

# Install dependencies
npm install

# Build extension
npm run build        # Outputs to dist/

# Deploy Firebase functions
cd functions && npm run deploy
```

### Makefile Targets (genio-mvp)

```bash
cd genio-mvp

make install       # Install all dependencies
make dev           # Start development environment
make test          # Run all tests
make test-coverage # Run tests with coverage report
make lint          # Run all linters
make lint-fix      # Fix linting issues
make build         # Build Docker images
make db-migrate    # Run database migrations
make db-reset      # Reset database
make health        # Health check
make clean         # Clean containers and volumes
make ci            # Full CI simulation (lint + test + build)
```

---

## Testing Strategy

### Backend Testing

```bash
cd genio-mvp/backend

# Run all tests
pytest -v --tb=short

# Run with coverage
pytest --cov=app --cov-report=html
# Coverage report: htmlcov/index.html

# Run specific test file
pytest tests/test_feeds.py -v

# Async tests
pytest tests/test_auth.py -v --asyncio-mode=auto
```

**Test Configuration:** `pyproject.toml`
- Test framework: pytest with pytest-asyncio
- Coverage target: 80%+ for API code
- Test database: SQLite in-memory with SQLModel
- Fixtures defined in: `tests/conftest.py`

### Frontend Testing

```bash
cd genio-mvp/frontend

# Run tests (Vitest)
npm test

# Run once (CI mode)
npm test -- --watchAll=false
```

### End-to-End Testing

```bash
cd genio-mvp/e2e

# Install dependencies
npm install

# Run tests
npx playwright test

# Run with UI
npx playwright test --ui

# Debug mode
npx playwright test --debug

# Show report
npx playwright show-report
```

### Load Testing

```bash
cd genio-mvp/backend

# Locust load testing
locust -f tests/load_test.py --host=http://localhost:8000
```

---

## Code Style Guidelines

### Python (Backend)

**Formatter:** Black (line length: 100)
**Import Sorter:** isort (black profile)
**Linter:** flake8 with specific ignores
**Type Checker:** mypy (strict mode)

```bash
# Format code
black app tests

# Check imports
isort app tests

# Lint
flake8 app tests --max-line-length=100 --ignore=E203,W503

# Type check
mypy app --ignore-missing-imports
```

**Code Style Rules:**
- Max line length: 100 characters
- Type hints required for all function definitions
- Docstrings for all public functions/classes
- Use `structlog` for structured logging
- Always use explicit error handling with Result types

**Example:**
```python
from typing import Optional
from pydantic import BaseModel

class FeedCreate(BaseModel):
    """Schema for creating a new feed."""
    url: HttpUrl
    title: Optional[str] = None
    category: Optional[str] = "Uncategorized"

async def fetch_feed(url: str) -> Result[Feed, FetchError]:
    """Fetch and parse RSS/Atom feed.
    
    Args:
        url: The feed URL to fetch
        
    Returns:
        Result containing Feed on success, FetchError on failure
    """
    # Implementation
```

### TypeScript/React (Frontend)

**Linter:** ESLint with TypeScript parser
**Formatter:** Built into ESLint
**Strict TypeScript:** Enabled

```bash
# Lint
npm run lint

# Type check
npx tsc --noEmit
```

**Code Style Rules:**
- Strict TypeScript mode (`strict: true`)
- No unused locals/parameters
- Functional components with hooks
- Custom hooks for data fetching (TanStack Query)
- Zustand for global state

**Example:**
```typescript
import { useQuery } from '@tanstack/react-query';

interface Feed {
  id: string;
  url: string;
  title: string;
}

export function useFeeds() {
  return useQuery({
    queryKey: ['feeds'],
    queryFn: async () => {
      const response = await api.get<Feed[]>('/feeds');
      return response.data;
    },
  });
}
```

---

## Database Schema

### Core Tables (PostgreSQL)

Key models defined in `genio-mvp/backend/app/models/`:

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    tier VARCHAR(20) DEFAULT 'starter',
    ai_budget_used DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Feeds
CREATE TABLE feeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT UNIQUE NOT NULL,
    title VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',
    last_fetched_at TIMESTAMP,
    failure_count INT DEFAULT 0
);

-- Articles (shared pool)
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_id UUID REFERENCES feeds(id),
    url TEXT NOT NULL,
    title TEXT,
    content TEXT,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    cluster_id UUID,
    processing_status VARCHAR(20) DEFAULT 'pending',
    vector_id VARCHAR(100)
);

-- Documents (Library)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    title VARCHAR(500),
    content TEXT,
    doc_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending'
);
```

### Migrations

```bash
cd genio-mvp/backend

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Reset to base
alembic downgrade base
```

---

## Security Considerations

### Authentication & Authorization

- **JWT tokens** with 30-minute expiration
- **Refresh tokens** with 7-day expiration
- **Password hashing** with bcrypt
- **Rate limiting:** 100 req/min (authenticated), 20/min (unauthenticated)
- **CORS** configured for specific origins only

### API Security

- Input validation with Pydantic models
- SQL injection prevention (SQLModel ORM)
- CORS configured for specific origins only
- File upload restrictions (PDF, TXT, MD, max 50MB)
- Security headers middleware
- Circuit breaker pattern for external services

### Secrets Management

**Required Environment Variables (Production):**
```bash
JWT_SECRET_KEY=<secure-random-key>
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
SENDGRID_API_KEY=SG...
STRIPE_SECRET_KEY=sk_live_...
```

**AWS Secrets Manager (Production):**
- `genio/production/database-url`
- `genio/production/jwt-secret`
- `genio/production/openai-api-key`
- `genio/production/gemini-api-key`

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| /auth/* | 10 | 1 min |
| /api/* (auth) | 100 | 1 min |
| /api/* (anon) | 20 | 1 min |
| /documents/upload | 5 | 1 min |

---

## Deployment

### Docker Build

```bash
# Build backend image
cd genio-mvp/backend
docker build -t genio-api:latest .

# Build frontend image
cd genio-mvp/frontend
docker build -t genio-frontend:latest .
```

### Infrastructure (Terraform)

```bash
cd genio-mvp/deploy

# Select workspace
terraform workspace select staging
terraform workspace select production

# Deploy
terraform apply
```

### Production Deployment

```bash
cd genio-mvp

# Automated deployment
./deploy/production-deploy.sh

# Or manual:
# 1. Run tests
make ci

# 2. Build images
make build-prod

# 3. Push to registry
# 4. Update ECS services
# 5. Verify health
make health
```

### Environment Files

**Development:** `.env` (gitignored)
```bash
DEBUG=true
DATABASE_URL=postgresql://genio:genio_password@localhost:5432/genio
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
JWT_SECRET_KEY=dev-secret-key
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

**Production:** Environment variables only (no .env file)
```bash
DEBUG=false
CORS_ORIGINS=https://genio.ai,https://app.genio.ai
MONTHLY_AI_BUDGET_USD=3.0
BRIEF_STAGGER_MINUTES=60
```

---

## Monitoring & Observability

### Health Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics

# OpenAPI schema
curl http://localhost:8000/openapi.json
```

### Service Level Indicators

| Metric | Target | Alert |
|--------|--------|-------|
| Feed fetch success | >98% | <95% |
| Extraction success | >95% | <90% |
| Embedding p95 | <2s | >5s |
| Brief delivery | >99% | <95% |
| AI budget usage | <80% | >90% |

---

## Project-Specific Conventions

### AI Cost Tracking

All AI calls must track costs via `track_ai_cost()`:

```python
from app.services.ai_service import track_ai_cost

# After AI call
track_ai_cost(
    user_id=user.id,
    model="gpt-4o",
    input_tokens=prompt_tokens,
    output_tokens=completion_tokens,
    cost_usd=calculated_cost
)
```

### Task Routing (Celery)

Tasks are routed to specific queues:

```python
# Task routing config
task_routes = {
    "app.tasks.feed_tasks.*": {"queue": "feeds"},
    "app.tasks.article_tasks.*": {"queue": "articles"},
    "app.tasks.brief_tasks.*": {"queue": "briefs"},
    "app.tasks.sweeper.*": {"queue": "maintenance"},
}
```

### Vector Similarity Thresholds

- **Deduplication:** cosine similarity > 0.85
- **Semantic chunking:** similarity drop < 0.75

### File Organization

**Backend:**
- `api/` - REST endpoint handlers
- `core/` - Configuration, auth, middleware, security
- `models/` - Database models (SQLModel)
- `tasks/` - Celery background tasks
- `library/` - Document processing (Library module)
- `lab/` - Scout agents (Lab module)
- `services/` - External service integrations, AI gateway
- `knowledge/` - Knowledge graph, embeddings
- `realtime/` - WebSocket handlers

**Frontend:**
- `pages/` - Route-level components
- `components/` - Reusable UI components
  - `admin/` - Admin panel components
  - `settings/` - Settings components
  - `library/` - Library module components
  - `ereader/` - E-reader components
- `hooks/` - Custom React hooks (data fetching)
- `services/` - API client functions
- `types/` - TypeScript type definitions
- `contexts/` - React context providers

---

## CI/CD Pipeline

### GitHub Actions Workflow

**File:** `.github/workflows/ci.yml`

**Triggers:**
- Push to `main`, `develop` branches
- Pull requests to `main`

**Jobs:**
1. **Backend:** Lint (flake8), Format (black), Type check (mypy), Test (pytest)
2. **Frontend:** Lint, Build, Type check
3. **Docker:** Build backend and frontend images

### Local CI Simulation

```bash
cd genio-mvp
make ci    # Runs: lint test build
```

---

## Important Notes for AI Agents

1. **Cost Consciousness:** Every AI call must track costs. The system has a monthly AI budget per user ($3/month).

2. **Task Idempotency:** Celery tasks must be idempotent - they may be retried on failure.

3. **No Edge AI:** All inference happens in the cloud via AI gateway (OpenAI/Gemini).

4. **Vector Dimensions:** Use 1536-dimensional embeddings (OpenAI text-embedding-3-small) for cost optimization.

5. **Error Handling:** Always use explicit error handling. Never use bare `except:` clauses.

6. **Database Sessions:** Use dependency injection for database sessions in FastAPI endpoints.

7. **Type Safety:** Strict TypeScript and mypy are enforced - no `any` types.

8. **Git Workflow:**
   - `main` - Production-ready
   - `develop` - Integration branch
   - `feature/*` - New features
   - `bugfix/*` - Bug fixes

9. **Security First:**
   - All endpoints must have authentication unless explicitly public
   - Validate all inputs with Pydantic models
   - Use parameterized queries (SQLModel ORM)
   - Sanitize user-generated content

10. **Enterprise Features:** Many features (2FA, SSO, Teams, Plugins) are behind feature flags. Check `app/core/feature_flags.py`.

---

## Glossary

| Term | Definition |
|------|------------|
| **Knowledge Atom** | Minimum unit of semantic information |
| **Knowledge Delta** | Novelty score (0.0-1.0) indicating new information |
| **Scout** | Autonomous research agent for discovery |
| **Daily Brief** | Automated digest of curated content |
| **The Diff** | Highlighting unique information across sources |
| **GraphRAG** | RAG with knowledge graph traversal |
| **Semantic Chunking** | Splitting by topic boundaries, not token counts |
| **PKG** | Personal Knowledge Graph |
| **FSM** | Finite State Machine (document processing) |

---

## Contact & References

- **MVP Implementation:** See `genio-mvp/README.md`
- **Security Guide:** See `genio-mvp/SECURITY.md`
- **Developer Guide:** See `genio-mvp/DEVELOPER_GUIDE.md`
- **Deployment Runbook:** See `genio-mvp/runbooks/`

---

*This document serves as the canonical reference for AI coding agents working on the Genio Knowledge OS project.*
