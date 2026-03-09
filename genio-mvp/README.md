# Genio Knowledge OS

[![CI](https://github.com/genio/genio-mvp/actions/workflows/ci.yml/badge.svg)](https://github.com/genio/genio-mvp/actions)
[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)

> AI-powered knowledge management platform with intelligent feed aggregation, document analysis, and research automation.

## 🚀 Features

### Stream (v1.0) - Feed Aggregator
- 📰 RSS/Atom feed aggregation
- 🤖 AI-powered content summarization
- 📊 Knowledge Delta scoring (novelty detection)
- 📧 Daily Brief email delivery with custom templates
- 🔍 Full-text search with Elasticsearch
- 🏷️ Advanced tagging system (hierarchical, colors)
- 💾 Saved views with filters
- 💬 Threaded article comments
- ⌨️ Vim-style keyboard shortcuts

### Library (v2.0) - Document Management
- 📄 PDF, EPUB, DOCX, TXT, Markdown support
- 🔍 OCR for scanned documents
- ✏️ Highlights and annotations
- 🔗 Semantic document chunks
- 📂 Collections and organization
- 🕸️ Personal Knowledge Graph (PKG)
- 🔎 GraphRAG semantic search

### Lab (v3.0) - Research Automation
- 🤖 Scout Agents for automated research
- 🔎 Multi-source monitoring (feeds, documents, arXiv)
- 💡 AI-generated insights and patterns
- ⏰ Scheduled research tasks
- 📈 Personal analytics dashboard

### Enterprise (v3.0+) - Team & Security
- 👥 Team collaboration with shared collections
- 🔗 Share links with permissions
- 🔐 Two-Factor Authentication (TOTP, WebAuthn)
- 🔑 SSO (Google, GitHub, Microsoft, SAML)
- 🔌 Plugin system with marketplace
- 📊 Admin dashboard with analytics
- 🎨 Customizable brief templates

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React 18)                           │
│  Stream  │  Library  │  Lab  │  Teams  │  Settings  │  Admin         │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ HTTPS/JSON
┌───────────────────────────────▼──────────────────────────────────────┐
│                      BACKEND (FastAPI)                                │
│  Auth  │  Feeds  │  Articles  │  Docs  │  Scouts  │  Search  │  AI   │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
   ┌────▼────┐      ┌──────────▼──────────┐     ┌──────▼──────┐
   │PostgreSQL│      │       Redis         │     │   Qdrant    │
   │  (Data) │      │   (Queue/Cache)      │     │  (Vectors)  │
   └─────────┘      └─────────────────────┘     └─────────────┘
                                │
                         ┌──────▼──────┐
                         │Elasticsearch│
                         │  (Search)   │
                         └─────────────┘
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, TanStack Query, D3.js |
| Backend | Python 3.12, FastAPI, SQLModel, Celery, Alembic |
| Database | PostgreSQL 15 |
| Cache/Queue | Redis 7 |
| Vector DB | Qdrant 1.7+ |
| Search | Elasticsearch 8.11+ |
| AI | OpenAI GPT-4, Google Gemini |
| Security | JWT, bcrypt, 2FA (TOTP/WebAuthn), OAuth |
| Infra | Docker, Docker Compose, AWS ECS, Terraform |

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local dev)
- Node.js 18+ (for frontend)

### 1. Clone & Setup

```bash
git clone https://github.com/genio/genio-mvp.git
cd genio-mvp
cp .env.example .env
# Edit .env with your API keys
```

### 2. Infrastructure (Docker)

```bash
docker-compose up -d postgres redis qdrant
```

### 3. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload

# Start Celery workers (in separate terminals)
celery -A app.tasks worker --loglevel=info
celery -A app.tasks beat --loglevel=info
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Access

- App: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

## 📁 Project Structure

```
genio-mvp/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # REST endpoints
│   │   ├── core/        # Config, auth, rate limit
│   │   ├── models/      # Database models
│   │   ├── tasks/       # Celery tasks
│   │   ├── library/     # Document processing
│   │   └── lab/         # Scout agents
│   ├── tests/           # Test suite
│   └── alembic/         # Database migrations
├── frontend/            # React frontend
│   ├── src/
│   │   ├── pages/       # Page components
│   │   ├── components/  # Shared components
│   │   ├── hooks/       # React Query hooks
│   │   └── services/    # API clients
├── deploy/              # Terraform configs
├── scripts/             # Utility scripts
└── docker-compose.yml   # Local infra
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test

# Load tests
cd backend
locust -f tests/load_test.py --host=http://localhost:8000

# Health check
./scripts/health-check.sh http://localhost:8000
```

## 🏢 Enterprise Features

### Advanced Tagging System
- **Hierarchical tags** with parent-child relationships
- **Color coding** with customizable palettes
- **Tag cloud** visualization
- **Bulk tagging** operations
- **Tag statistics** and frequency analysis

### Full-Text Search
- **Elasticsearch** integration for fast, scalable search
- **Semantic search** using vector embeddings
- **Advanced operators**: `author:`, `tag:`, `date:`, `delta:>`
- **Faceted search** with aggregations
- **Search suggestions** and autocomplete

### Team Collaboration
- **Teams** with role-based access control
- **Shared collections** for curated content
- **Share links** with password protection and expiration
- **Comment threads** on articles
- **Real-time activity feeds**

### Security
- **Two-Factor Authentication**: TOTP (Google Authenticator), WebAuthn (Security Keys)
- **SSO Integration**: Google, GitHub, Microsoft, SAML
- **Session management** and revocation
- **Audit logging** for compliance

### Analytics Dashboard
- **Reading statistics**: articles read, time spent, streaks
- **Knowledge Delta trends**: novelty scoring over time
- **Feed performance** metrics
- **Activity heatmap**: GitHub-style contribution graph
- **AI-generated insights** and suggestions

### Plugin System
- **Marketplace** for discovering plugins
- **6 Plugin types**: Source, Processor, Exporter, Notifier, Analyzer, Integration
- **Hook system** for extending functionality
- **Webhook endpoints** for external integrations

## 🚢 Deployment

### Automated Setup

```bash
# Complete setup with all enterprise features
./scripts/setup_complete_app.sh
```

### Staging

```bash
cd deploy
terraform workspace select staging
terraform apply
./production-deploy.sh
```

### Production

See [LAUNCH_CHECKLIST.md](LAUNCH_CHECKLIST.md) for detailed steps.

### Environment Variables

Required for enterprise features:

```bash
# AI Services
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Search
ELASTICSEARCH_URL=http://localhost:9200

# Email
SENDGRID_API_KEY=SG-...

# OAuth (SSO)
GOOGLE_CLIENT_ID=...
GITHUB_CLIENT_ID=...
MICROSOFT_CLIENT_ID=...

# Security
JWT_SECRET_KEY=minimum-32-characters-secret
```

```bash
# Automated deployment
./deploy/production-deploy.sh

# Or manual steps:
# 1. Run tests
# 2. Build images
# 3. Push to ECR
# 4. Update ECS services
# 5. Verify health
```

## 📊 Monitoring

### SLIs (Service Level Indicators)

| Metric | Target | Alert |
|--------|--------|-------|
| Feed fetch success | >98% | <95% |
| Extraction success | >95% | <90% |
| Embedding p95 | <2s | >5s |
| Brief delivery | >99% | <95% |
| AI budget usage | <80% | >90% |

### Health Check

```bash
curl http://api.genio.ai/health
```

### Metrics

```bash
curl http://api.genio.ai/metrics
```

## 💰 Cost Optimizations

| Optimization | Savings |
|--------------|---------|
| 1536-dim embeddings (B01) | 80% vs 3072-dim |
| Shared article pool (B04) | 60-80% dedup |
| Batch embeddings (B13) | 30-50% fewer calls |
| Staggered delivery (B07) | 10x peak reduction |
| Graceful degradation (B12) | Continuous service |

Target: <$3 AI cost/user/month

## 🔐 Security

See [SECURITY.md](SECURITY.md) for details.

- JWT authentication
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection
- Secrets management (AWS Secrets Manager)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

Proprietary - Genio Team

## 🆘 Support

- Documentation: https://docs.genio.ai
- Issues: https://github.com/genio/genio-mvp/issues
- Email: support@genio.ai

---

Built with ❤️ by the Genio Team
