# Genio Knowledge OS - Developer Guide

Welcome to the Genio development team! This guide will help you get started with the codebase.

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/genio/genio-mvp.git
cd genio-mvp

# 2. Copy environment file
cp .env.example .env
# Edit .env with your API keys

# 3. Start infrastructure
docker-compose up -d postgres redis qdrant

# 4. Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head

# 5. Run backend
uvicorn app.main:app --reload

# 6. In new terminal, run Celery
celery -A app.tasks worker --loglevel=info
celery -A app.tasks beat --loglevel=info

# 7. Setup frontend (new terminal)
cd frontend
npm install
npm run dev

# 8. Open http://localhost:5173
```

## 📁 Project Structure

```
genio-mvp/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # REST endpoints
│   │   ├── core/        # Config, auth, middleware
│   │   ├── models/      # Database models
│   │   ├── tasks/       # Celery tasks (Stream)
│   │   ├── knowledge/   # Delta + embeddings
│   │   ├── library/     # Document processing ⭐
│   │   └── lab/         # Scout agents ⭐
│   └── tests/
├── frontend/            # React application
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── services/
└── deploy/             # Terraform configs
```

## 🔧 Development Workflow

### Branching Strategy

```
main        → Production-ready code
develop     → Integration branch
feature/*   → New features
bugfix/*    → Bug fixes
hotfix/*    → Production hotfixes
```

### Making Changes

1. **Create a branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes**
   - Write code
   - Add tests
   - Update docs

3. **Run tests**
   ```bash
   make test
   ```

4. **Commit**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/my-feature
   # Create PR on GitHub
   ```

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_library.py -v

# Run specific test
pytest tests/test_library.py::TestSemanticChunking -v
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

### Load Testing

```bash
cd backend
locust -f tests/load_test.py --host=http://localhost:8000
```

## 🐳 Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild after dependency changes
docker-compose up -d --build

# Stop everything
docker-compose down -v
```

## 📊 Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "add new table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current version
alembic current
```

## 🔐 Environment Variables

Key variables for development:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://localhost:5432/genio` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `QDRANT_URL` | Vector DB connection | `http://localhost:6333` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `JWT_SECRET_KEY` | JWT signing key | Change in production |

## 🐛 Debugging

### Backend

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()
```

### Frontend

```typescript
// Use React DevTools extension
// Or console.log for quick debugging
console.log('Debug:', variable);
```

## 📚 Key Modules

### Stream Module
- **Purpose**: RSS/Atom feed aggregation
- **Key Files**: `tasks/feed_tasks.py`, `tasks/brief_tasks.py`
- **Tests**: `tests/test_feeds.py`

### Library Module
- **Purpose**: Document management with PKG
- **Key Files**: `library/semantic_chunker.py`, `library/graph_rag.py`
- **Tests**: `tests/test_library.py`

### Lab Module
- **Purpose**: Scout agents for research
- **Key Files**: `lab/scout_advanced.py`, `lab/engine.py`
- **Tests**: `tests/test_lab.py`

## 🚀 Deployment

### Staging

```bash
# Deploy to staging
make deploy-staging
```

### Production

```bash
# Deploy to production
make deploy-prod
```

## 📖 Documentation

- [API Docs](http://localhost:8000/docs) - Swagger UI
- [OpenAPI Schema](http://localhost:8000/openapi.json)
- [Performance Guide](./PERFORMANCE_GUIDE.md)
- [Security Audit](./SECURITY_AUDIT.md)

## 🤝 Contributing

1. Check [Issues](https://github.com/genio/genio-mvp/issues) for tasks
2. Comment on issue to claim it
3. Follow coding standards (black, flake8, prettier)
4. Write tests for new features
5. Update documentation

## 🆘 Getting Help

- **Slack**: #dev-team
- **Email**: dev@genio.ai
- **Docs**: https://docs.genio.ai

---

Happy coding! 🚀
