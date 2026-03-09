# Genio Knowledge OS
## Stream MVP Implementation Plan
**Version:** 1.0  
**Date:** February 2026  
**Timeline:** 12 Weeks to Market  
**Module:** STREAM (Intelligent Feed Aggregator)

---

## Executive Summary

### MVP Scope

This document provides a detailed implementation plan for the **Stream module** of Genio Knowledge OS, selected as the optimal MVP entry point based on technical feasibility, economic sustainability, and user value creation.

### Key Deliverables

| Deliverable | Description |
|-------------|-------------|
| RSS/Atom Feed Aggregation | Support for 20+ feed formats |
| Semantic Deduplication | Vector-based similarity detection (>0.85 threshold) |
| Daily Brief Generation | Automated digest at user-defined time |
| "The Diff" Highlighting | Unique information per source |
| Web Application | React frontend + FastAPI backend |

### Success Criteria

| Metric | Target |
|--------|--------|
| User onboarding | <5 minutes to add first feed |
| Daily Brief delivery | Within 24 hours of signup |
| Deduplication accuracy | >95% |
| COGS per user | <$3/month |
| Beta user satisfaction | >70% report time saved |

---

## 1. Technical Stack

### 1.1 Infrastructure

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Cloud Provider** | AWS (primary) / GCP (backup) | Enterprise compliance, global regions |
| **Container Orchestration** | AWS ECS with Fargate | Serverless containers, auto-scaling |
| **CI/CD** | GitHub Actions | Integrated with repository |
| **Monitoring** | Datadog | Full observability stack |
| **Logging** | AWS CloudWatch + Datadog | Centralized logging |

### 1.2 Backend Stack

| Component | Technology | Version | Justification |
|-----------|------------|---------|---------------|
| **Language** | Python | 3.11+ | AI ecosystem, rapid development |
| **Framework** | FastAPI | 0.109+ | Async, OpenAPI, type safety |
| **ORM** | SQLAlchemy | 2.0+ | Async support, mature |
| **Task Queue** | Celery | 5.3+ | Distributed task processing |
| **Message Broker** | RabbitMQ | 3.12+ | Reliable, battle-tested |
| **Cache** | Redis | 7.2+ | Sub-millisecond response |

### 1.3 Data Layer

| Component | Technology | Version | Justification |
|-----------|------------|---------|---------------|
| **Relational DB** | PostgreSQL | 15+ | JSON support, reliability |
| **Vector DB** | Qdrant | 1.7+ | Self-hosted, 3072-dim support |
| **Graph DB** | Neo4j | 5.x | Entity relationships (post-MVP) |

### 1.4 AI Layer

| Component | Technology | Justification |
|-----------|------------|---------------|
| **AI Gateway** | LiteLLM | Model abstraction, cost tracking |
| **Embedding Model** | text-embedding-3-large (OpenAI) | 3072-dim, high quality |
| **Fast Model** | Gemini Flash / Claude Haiku | $0.10-0.50/M tokens |
| **Balanced Model** | GPT-4o-mini | $0.50-2/M tokens |

### 1.5 Frontend Stack

| Component | Technology | Version | Justification |
|-----------|------------|---------|---------------|
| **Framework** | React | 18+ | Component ecosystem |
| **Language** | TypeScript | 5.0+ | Type safety |
| **State Management** | TanStack Query | 5.x | Server state management |
| **Styling** | Tailwind CSS | 3.4+ | Rapid UI development |
| **Build** | Vite | 5.x | Fast development server |

---

## 2. Development Phases

### Phase 1: Foundation (Weeks 1-3)

#### Week 1: Infrastructure Setup

**Deliverables:**
- [ ] AWS account configuration with cost alerts
- [ ] VPC, subnets, security groups
- [ ] RDS PostgreSQL instance
- [ ] ElastiCache Redis cluster
- [ ] Qdrant deployment on ECS
- [ ] GitHub Actions CI/CD pipeline

**Infrastructure as Code:**

```yaml
# docker-compose.yml for local development
version: '3.8'

services:
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://genio:password@postgres:5432/genio
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - postgres
      - redis
      - qdrant
    volumes:
      - ./backend:/app

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A genio.worker worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://genio:password@postgres:5432/genio
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - postgres
      - redis
      - rabbitmq

  scheduler:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A genio.worker beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://genio:password@postgres:5432/genio
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - rabbitmq

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=genio
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=genio
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  rabbitmq:
    image: rabbitmq:3.12-management
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
  qdrant_data:
```

#### Week 2: Database Schema

**Users Table:**

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tier VARCHAR(20) DEFAULT 'starter',
    daily_ai_budget DECIMAL(10,2) DEFAULT 2.00,
    ai_budget_used DECIMAL(10,2) DEFAULT 0.00,
    timezone VARCHAR(50) DEFAULT 'UTC',
    brief_delivery_time TIME DEFAULT '08:00',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tier ON users(tier);
```

**Feeds Table:**

```sql
CREATE TABLE feeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT UNIQUE NOT NULL,
    title VARCHAR(500),
    description TEXT,
    site_url TEXT,
    last_fetched_at TIMESTAMP,
    last_etag VARCHAR(255),
    last_modified VARCHAR(255),
    fetch_interval_minutes INT DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    content_hash VARCHAR(64),
    failure_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feeds_last_fetched ON feeds(last_fetched_at);
CREATE INDEX idx_feeds_active ON feeds(is_active);
```

**User_Feeds Junction:**

```sql
CREATE TABLE user_feeds (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    feed_id UUID REFERENCES feeds(id) ON DELETE CASCADE,
    custom_title VARCHAR(500),
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    added_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, feed_id)
);

CREATE INDEX idx_user_feeds_user ON user_feeds(user_id);
CREATE INDEX idx_user_feeds_feed ON user_feeds(feed_id);
```

**Articles Table:**

```sql
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_id UUID REFERENCES feeds(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT,
    original_title TEXT,
    content TEXT,
    content_length INT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW(),
    vector_id VARCHAR(100),
    
    -- Deduplication fields
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    cluster_id UUID,
    canonical_article_id UUID REFERENCES articles(id),
    delta_score DECIMAL(3,2),
    
    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'pending',
    -- pending -> extracted -> embedded -> clustered -> summarized -> ready
    
    -- Content fields
    summary TEXT,
    rewritten_title TEXT,
    key_entities JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_articles_feed ON articles(feed_id);
CREATE INDEX idx_articles_cluster ON articles(cluster_id);
CREATE INDEX idx_articles_status ON articles(processing_status);
CREATE INDEX idx_articles_published ON articles(published_at);
CREATE INDEX idx_articles_hash ON articles(content_hash);
CREATE INDEX idx_articles_delta ON articles(delta_score DESC);
```

**Daily_Briefs Table:**

```sql
CREATE TABLE daily_briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    brief_date DATE NOT NULL,
    title VARCHAR(500),
    summary TEXT,
    content JSONB,
    article_count INT DEFAULT 0,
    sources_covered INT DEFAULT 0,
    delivery_status VARCHAR(20) DEFAULT 'pending',
    -- pending -> generating -> ready -> sent -> failed
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    ai_cost DECIMAL(10,4) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, brief_date)
);

CREATE INDEX idx_briefs_user_date ON daily_briefs(user_id, brief_date);
CREATE INDEX idx_briefs_status ON daily_briefs(delivery_status);
```

**AI_Cost_Log Table:**

```sql
CREATE TABLE ai_cost_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    operation_type VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    input_tokens INT,
    output_tokens INT,
    cost_usd DECIMAL(10,6) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cost_log_user ON ai_cost_log(user_id);
CREATE INDEX idx_cost_log_date ON ai_cost_log(created_at);
```

#### Week 3: Core API Structure

**Project Structure:**

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings
│   ├── database.py             # DB connection
│   ├── dependencies.py         # DI container
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── feed.py
│   │   ├── article.py
│   │   └── brief.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── feed.py
│   │   ├── article.py
│   │   └── brief.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── auth.py
│   │   ├── feeds.py
│   │   ├── articles.py
│   │   └── briefs.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── feed_fetcher.py
│   │   ├── content_extractor.py
│   │   ├── embedding.py
│   │   ├── clustering.py
│   │   ├── summarization.py
│   │   └── brief_generator.py
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── feed_tasks.py
│   │   ├── article_tasks.py
│   │   └── brief_tasks.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── ai_router.py
│       ├── cost_tracker.py
│       └── vector_store.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_feeds.py
│   ├── test_articles.py
│   └── test_briefs.py
│
├── alembic/
│   └── versions/
│
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

---

### Phase 2: Ingestion Pipeline (Weeks 3-5)

#### Week 3-4: Feed Fetcher Service

**Celery Configuration:**

```python
# app/workers/celery_app.py
from celery import Celery
from celery.schedules import crontab

app = Celery('genio')

app.conf.update(
    broker_url='amqp://guest@rabbitmq//',
    result_backend='redis://redis:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=300,  # 5 minutes max
    worker_prefetch_multiplier=1,
)

# Scheduled tasks
app.conf.beat_schedule = {
    'fetch-all-feeds': {
        'task': 'app.workers.feed_tasks.fetch_all_feeds',
        'schedule': 300.0,  # Every 5 minutes
    },
    'generate-daily-briefs': {
        'task': 'app.workers.brief_tasks.generate_daily_briefs',
        'schedule': crontab(hour='*', minute='0'),  # Every hour
    },
    'cleanup-old-articles': {
        'task': 'app.workers.article_tasks.cleanup_old_articles',
        'schedule': crontab(hour='3', minute='0'),  # 3 AM UTC
    },
}
```

**Feed Fetcher Task:**

```python
# app/workers/feed_tasks.py
import feedparser
import hashlib
from datetime import datetime, timedelta
from celery import shared_task
from sqlmodel import Session, select

from app.database import get_session
from app.models import Feed, Article
from app.workers.article_tasks import extract_article_content


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def fetch_all_feeds(self):
    """Fetch all active feeds that need updating."""
    with next(get_session()) as session:
        # Get feeds that need fetching
        cutoff = datetime.utcnow() - timedelta(minutes=60)
        
        feeds = session.exec(
            select(Feed).where(
                Feed.is_active == True,
                (Feed.last_fetched_at == None) | (Feed.last_fetched_at < cutoff)
            )
        ).all()
        
        results = []
        for feed in feeds:
            try:
                result = fetch_feed.delay(str(feed.id))
                results.append(str(feed.id))
            except Exception as e:
                feed.failure_count += 1
                if feed.failure_count >= 5:
                    feed.is_active = False
                session.add(feed)
        
        session.commit()
        return {"queued": len(results), "feed_ids": results}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_feed(self, feed_id: str):
    """Fetch and parse a single RSS/Atom feed."""
    with next(get_session()) as session:
        feed = session.get(Feed, feed_id)
        if not feed:
            return {"status": "not_found"}
        
        try:
            # Conditional GET with ETag/Last-Modified
            headers = {}
            if feed.last_etag:
                headers['If-None-Match'] = feed.last_etag
            if feed.last_modified:
                headers['If-Modified-Since'] = feed.last_modified
            
            parsed = feedparser.parse(
                feed.url,
                request_headers=headers,
                etag=feed.last_etag,
                modified=feed.last_modified
            )
            
            # Handle 304 Not Modified
            if hasattr(parsed, 'status') and parsed.status == 304:
                feed.last_fetched_at = datetime.utcnow()
                session.add(feed)
                session.commit()
                return {"status": "not_modified"}
            
            # Parse feed metadata
            if not feed.title and parsed.feed.get('title'):
                feed.title = parsed.feed.get('title', '')[:500]
            if not feed.description and parsed.feed.get('description'):
                feed.description = parsed.feed.get('description', '')
            if not feed.site_url and parsed.feed.get('link'):
                feed.site_url = parsed.feed.get('link')
            
            # Process entries
            new_articles = 0
            for entry in parsed.entries[:50]:  # Max 50 per fetch
                url = entry.get('link', '')
                if not url:
                    continue
                
                # Check for existing article
                existing = session.exec(
                    select(Article).where(Article.url == url)
                ).first()
                if existing:
                    continue
                
                # Parse published date
                published = None
                if entry.get('published_parsed'):
                    published = datetime(*entry.published_parsed[:6])
                elif entry.get('updated_parsed'):
                    published = datetime(*entry.updated_parsed[:6])
                
                # Skip old articles (>7 days)
                if published and published < datetime.utcnow() - timedelta(days=7):
                    continue
                
                # Create article
                article = Article(
                    feed_id=feed.id,
                    url=url,
                    title=clean_text(entry.get('title', '')),
                    original_title=entry.get('title', ''),
                    published_at=published,
                    processing_status='pending'
                )
                session.add(article)
                session.flush()  # Get ID
                
                # Queue content extraction
                extract_article_content.delay(str(article.id))
                new_articles += 1
            
            # Update feed metadata
            feed.last_fetched_at = datetime.utcnow()
            feed.last_etag = getattr(parsed, 'etag', None)
            feed.last_modified = getattr(parsed, 'modified', None)
            feed.failure_count = 0
            
            session.add(feed)
            session.commit()
            
            return {"status": "success", "new_articles": new_articles}
            
        except Exception as e:
            feed.failure_count += 1
            if feed.failure_count >= 5:
                feed.is_active = False
            session.add(feed)
            session.commit()
            raise self.retry(exc=e)


def clean_text(text: str) -> str:
    """Clean HTML and whitespace from text."""
    import re
    from html import unescape
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Unescape HTML entities
    text = unescape(text)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text.strip()
```

#### Week 4-5: Content Extraction & Embedding

**Content Extractor Task:**

```python
# app/workers/article_tasks.py
import hashlib
import trafilatura
from celery import shared_task
from sqlmodel import Session

from app.database import get_session
from app.models import Article
from app.workers.embedding_tasks import generate_embedding


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def extract_article_content(self, article_id: str):
    """Extract full article text from URL."""
    with next(get_session()) as session:
        article = session.get(Article, article_id)
        if not article:
            return {"status": "not_found"}
        
        try:
            headers = {
                'User-Agent': 'GenioBot/1.0 (Knowledge Aggregator; +https://genio.ai)'
            }
            
            downloaded = trafilatura.fetch_url(article.url, headers=headers)
            
            if downloaded:
                extracted = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=False,
                    deduplicate=True,
                    target_language='en'
                )
                
                if extracted and len(extracted) > 200:
                    article.content = extracted
                    article.content_length = len(extracted)
                    article.content_hash = hashlib.sha256(
                        extracted.encode()
                    ).hexdigest()[:64]
                    article.processing_status = 'extracted'
                    session.add(article)
                    session.commit()
                    
                    # Queue embedding
                    generate_embedding.delay(str(article.id))
                    
                    return {"status": "extracted", "length": len(extracted)}
            
            # Extraction failed
            article.processing_status = 'extraction_failed'
            session.add(article)
            session.commit()
            return {"status": "failed"}
            
        except Exception as e:
            raise self.retry(exc=e)
```

**Embedding Generation Task:**

```python
# app/workers/embedding_tasks.py
from celery import shared_task
from sqlmodel import Session
from litellm import embedding

from app.database import get_session
from app.models import Article
from app.utils.vector_store import QdrantClient
from app.utils.cost_tracker import track_ai_cost


@shared_task(bind=True, max_retries=2)
def generate_embedding(self, article_id: str):
    """Generate vector embedding for article content."""
    with next(get_session()) as session:
        article = session.get(Article, article_id)
        if not article:
            return {"status": "not_found"}
        
        # Prepare text: title + first 8000 chars
        text = f"{article.title}\n\n{article.content[:8000]}"
        
        try:
            response = embedding(
                model="text-embedding-3-large",
                input=text,
                dimensions=3072
            )
            
            vector = response.data[0].embedding
            
            # Store in Qdrant
            client = QdrantClient()
            client.upsert(
                collection_name="articles",
                point_id=str(article.id),
                vector=vector,
                payload={
                    "article_id": str(article.id),
                    "feed_id": str(article.feed_id),
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                    "title": article.title[:200] if article.title else None,
                    "content_hash": article.content_hash
                }
            )
            
            # Update article
            article.vector_id = str(article.id)
            article.processing_status = 'embedded'
            session.add(article)
            session.commit()
            
            # Track cost
            tokens = response.usage.total_tokens
            cost = (tokens / 1_000_000) * 0.13  # $0.13/M tokens
            track_ai_cost(session, article.feed.users[0].id, 'embedding', cost)
            
            # Queue clustering
            from app.workers.clustering_tasks import find_similar_articles
            find_similar_articles.delay(str(article.id))
            
            return {"status": "embedded", "vector_id": article.vector_id}
            
        except Exception as e:
            article.processing_status = 'embedding_failed'
            session.add(article)
            session.commit()
            raise self.retry(exc=e)
```

---

### Phase 3: Deduplication & Clustering (Weeks 5-6)

#### Clustering Algorithm:

```python
# app/workers/clustering_tasks.py
import uuid
from datetime import datetime, timedelta
from celery import shared_task
from sqlmodel import Session, select

from app.database import get_session
from app.models import Article
from app.utils.vector_store import QdrantClient
from app.workers.summarization_tasks import generate_summary


@shared_task
def find_similar_articles(article_id: str):
    """Find semantically similar articles for deduplication."""
    with next(get_session()) as session:
        article = session.get(Article, article_id)
        if not article:
            return {"status": "not_found"}
        
        # Get vector from Qdrant
        client = QdrantClient()
        vector_result = client.retrieve(
            collection_name="articles",
            ids=[str(article_id)],
            with_vectors=True
        )
        
        if not vector_result:
            return {"status": "no_vector"}
        
        vector = vector_result[0].vector
        
        # Search for similar articles (within 7 days)
        time_filter = datetime.utcnow() - timedelta(days=7)
        
        similar = client.search(
            collection_name="articles",
            query_vector=vector,
            limit=10,
            score_threshold=0.85,
            query_filter={
                "must": [
                    {
                        "key": "published_at",
                        "range": {"gte": time_filter.isoformat()}
                    },
                    {
                        "key": "article_id",
                        "match": {"except": [str(article_id)]}
                    }
                ]
            }
        )
        
        if similar:
            best_match = similar[0]
            
            if best_match.score >= 0.90:
                # Very similar - mark as duplicate
                similar_article_id = best_match.payload['article_id']
                similar_article = session.get(Article, similar_article_id)
                
                article.cluster_id = similar_article.cluster_id
                article.canonical_article_id = similar_article_id
                article.delta_score = 0.0
                article.processing_status = 'duplicate'
                session.add(article)
                session.commit()
                
                return {"status": "duplicate", "similarity": best_match.score}
            
            elif best_match.score >= 0.85:
                # Related - add to cluster
                similar_article_id = best_match.payload['article_id']
                similar_article = session.get(Article, similar_article_id)
                
                if similar_article.cluster_id:
                    article.cluster_id = similar_article.cluster_id
                else:
                    # Create new cluster
                    cluster_id = uuid.uuid4()
                    similar_article.cluster_id = cluster_id
                    session.add(similar_article)
                    article.cluster_id = cluster_id
                
                article.delta_score = 1 - best_match.score
                article.processing_status = 'clustered'
                session.add(article)
                session.commit()
                
                # Queue summarization
                generate_summary.delay(str(article.id))
                
                return {"status": "clustered", "similarity": best_match.score}
        
        else:
            # No similar articles - standalone
            article.cluster_id = uuid.uuid4()
            article.delta_score = 1.0
            article.processing_status = 'clustered'
            session.add(article)
            session.commit()
            
            # Queue summarization
            generate_summary.delay(str(article.id))
            
            return {"status": "standalone"}
```

---

### Phase 4: Daily Brief Generation (Weeks 6-8)

#### Brief Generator Service:

```python
# app/workers/brief_tasks.py
from datetime import datetime, date, timedelta
from celery import shared_task
from sqlmodel import Session, select
from litellm import completion

from app.database import get_session
from app.models import User, Article, DailyBrief
from app.utils.cost_tracker import track_ai_cost


@shared_task
def generate_daily_briefs():
    """Generate daily briefs for all users whose time matches."""
    with next(get_session()) as session:
        # Get current hour
        current_hour = datetime.utcnow().hour
        
        # Find users where it's their brief delivery time
        # (simplified - in production, handle timezones properly)
        users = session.exec(
            select(User).where(
                User.is_active == True,
                User.brief_delivery_time.hour == current_hour
            )
        ).all()
        
        for user in users:
            generate_user_brief.delay(str(user.id))


@shared_task(bind=True, max_retries=2)
def generate_user_brief(self, user_id: str):
    """Generate daily brief for a single user."""
    with next(get_session()) as session:
        user = session.get(User, user_id)
        if not user:
            return {"status": "not_found"}
        
        # Check if brief already exists for today
        today = date.today()
        existing = session.exec(
            select(DailyBrief).where(
                DailyBrief.user_id == user.id,
                DailyBrief.brief_date == today
            )
        ).first()
        
        if existing:
            return {"status": "already_exists"}
        
        # Get user's feeds
        user_feed_ids = [uf.feed_id for uf in user.user_feeds if uf.is_active]
        
        # Get articles from last 24 hours
        yesterday = datetime.utcnow() - timedelta(hours=24)
        
        articles = session.exec(
            select(Article)
            .where(
                Article.feed_id.in_(user_feed_ids),
                Article.processing_status == 'ready',
                Article.published_at >= yesterday
            )
            .order_by(Article.delta_score.desc())
            .limit(50)
        ).all()
        
        if not articles:
            return {"status": "no_articles"}
        
        # Group by cluster
        clusters = {}
        for article in articles:
            if article.cluster_id not in clusters:
                clusters[article.cluster_id] = []
            clusters[article.cluster_id].append(article)
        
        # Select top articles (one per cluster)
        top_articles = []
        for cluster_id, cluster_articles in clusters.items():
            # Sort by delta_score, take highest
            cluster_articles.sort(key=lambda a: a.delta_score or 0, reverse=True)
            top_articles.append(cluster_articles[0])
        
        # Sort all by delta_score
        top_articles.sort(key=lambda a: a.delta_score or 0, reverse=True)
        top_articles = top_articles[:10]  # Max 10 articles
        
        # Generate brief content
        brief_content = generate_brief_content(session, user, top_articles)
        
        # Create brief record
        brief = DailyBrief(
            user_id=user.id,
            brief_date=today,
            title=f"Daily Brief - {today.strftime('%B %d, %Y')}",
            summary=brief_content['summary'],
            content=brief_content['sections'],
            article_count=len(top_articles),
            sources_covered=len(set(a.feed_id for a in top_articles)),
            delivery_status='ready',
            ai_cost=brief_content['cost']
        )
        session.add(brief)
        session.commit()
        
        # Queue delivery
        deliver_brief.delay(str(brief.id))
        
        return {"status": "generated", "article_count": len(top_articles)}


def generate_brief_content(session, user, articles):
    """Generate brief content using AI."""
    
    # Prepare article summaries
    article_texts = []
    for i, article in enumerate(articles, 1):
        article_texts.append(
            f"{i}. {article.title}\n"
            f"   Source: {article.feed.title}\n"
            f"   Summary: {article.summary or 'No summary available'}\n"
            f"   Novelty Score: {article.delta_score:.0%}"
        )
    
    prompt = f"""Generate a daily news brief for a knowledge professional.

ARTICLES:
{chr(10).join(article_texts)}

Create a brief with:
1. EXECUTIVE SUMMARY (2-3 sentences highlighting the most important developments)
2. KEY STORIES (bullet points for each article, focusing on what's NEW)
3. THE DIFF (highlight unique angles or contradictions between sources)

Format as JSON:
{{
  "summary": "...",
  "key_stories": ["...", "..."],
  "the_diff": "..."
}}
"""
    
    response = completion(
        model="gemini/gemini-1.5-flash",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=800,
        temperature=0.3
    )
    
    content = response.choices[0].message.content
    import json
    parsed = json.loads(content)
    
    # Track cost
    cost = response._hidden_params.get('response_cost', 0.0004)
    track_ai_cost(session, user.id, 'brief_generation', cost)
    
    return {
        'summary': parsed.get('summary', ''),
        'sections': {
            'key_stories': parsed.get('key_stories', []),
            'the_diff': parsed.get('the_diff', '')
        },
        'cost': cost
    }


@shared_task
def deliver_brief(brief_id: str):
    """Deliver brief to user via email and in-app notification."""
    with next(get_session()) as session:
        brief = session.get(DailyBrief, brief_id)
        if not brief:
            return {"status": "not_found"}
        
        # TODO: Implement email delivery
        # TODO: Implement push notification
        
        brief.delivery_status = 'sent'
        brief.delivered_at = datetime.utcnow()
        session.add(brief)
        session.commit()
        
        return {"status": "delivered"}
```

---

### Phase 5: Web Application (Weeks 7-10)

#### Week 7-8: Backend API

**API Endpoints:**

```python
# app/api/feeds.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Feed, UserFeed
from app.schemas import FeedCreate, FeedRead, FeedList

router = APIRouter(prefix="/feeds", tags=["feeds"])


@router.post("/", response_model=FeedRead)
def add_feed(
    feed_data: FeedCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Add a new RSS feed."""
    # Check if feed already exists
    existing = session.exec(
        select(Feed).where(Feed.url == feed_data.url)
    ).first()
    
    if existing:
        # Link to user
        user_feed = UserFeed(
            user_id=current_user.id,
            feed_id=existing.id,
            custom_title=feed_data.custom_title,
            category=feed_data.category
        )
        session.add(user_feed)
        session.commit()
        return existing
    
    # Create new feed
    feed = Feed(url=feed_data.url)
    session.add(feed)
    session.commit()
    
    # Link to user
    user_feed = UserFeed(
        user_id=current_user.id,
        feed_id=feed.id,
        custom_title=feed_data.custom_title,
        category=feed_data.category
    )
    session.add(user_feed)
    session.commit()
    
    # Trigger immediate fetch
    from app.workers.feed_tasks import fetch_feed
    fetch_feed.delay(str(feed.id))
    
    return feed


@router.get("/", response_model=FeedList)
def list_feeds(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """List user's feeds."""
    user_feeds = session.exec(
        select(UserFeed).where(UserFeed.user_id == current_user.id)
    ).all()
    
    feeds = []
    for uf in user_feeds:
        feed = session.get(Feed, uf.feed_id)
        feeds.append({
            **feed.dict(),
            "custom_title": uf.custom_title,
            "category": uf.category
        })
    
    return {"feeds": feeds, "total": len(feeds)}


@router.delete("/{feed_id}")
def remove_feed(
    feed_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Remove a feed from user's list."""
    user_feed = session.exec(
        select(UserFeed).where(
            UserFeed.user_id == current_user.id,
            UserFeed.feed_id == feed_id
        )
    ).first()
    
    if not user_feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    session.delete(user_feed)
    session.commit()
    
    return {"status": "removed"}
```

#### Week 9-10: Frontend Application

**Project Structure:**

```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── FeedList.tsx
│   │   ├── AddFeedModal.tsx
│   │   ├── ArticleCard.tsx
│   │   ├── DailyBrief.tsx
│   │   └── ConfidenceIndicator.tsx
│   │
│   ├── hooks/
│   │   ├── useFeeds.ts
│   │   ├── useArticles.ts
│   │   └── useBriefs.ts
│   │
│   ├── api/
│   │   ├── client.ts
│   │   ├── feeds.ts
│   │   ├── articles.ts
│   │   └── briefs.ts
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Feeds.tsx
│   │   ├── Brief.tsx
│   │   └── Settings.tsx
│   │
│   ├── App.tsx
│   └── main.tsx
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

**Key Components:**

```tsx
// src/components/DailyBrief.tsx
import { useQuery } from '@tanstack/react-query';
import { getTodaysBrief } from '../api/briefs';
import { ConfidenceIndicator } from './ConfidenceIndicator';

export function DailyBrief() {
  const { data: brief, isLoading } = useQuery({
    queryKey: ['brief', 'today'],
    queryFn: getTodaysBrief,
  });

  if (isLoading) {
    return <BriefSkeleton />;
  }

  if (!brief) {
    return (
      <div className="p-6 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No brief available yet. Check back later!</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">{brief.title}</h1>
        <p className="text-gray-500">
          {brief.article_count} articles from {brief.sources_covered} sources
        </p>
      </header>

      <section className="bg-white rounded-lg p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-3">Executive Summary</h2>
        <p className="text-gray-700">{brief.summary}</p>
      </section>

      <section className="bg-white rounded-lg p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-3">Key Stories</h2>
        <ul className="space-y-4">
          {brief.content.key_stories.map((story, i) => (
            <li key={i} className="flex items-start gap-3">
              <ConfidenceIndicator score={0.85} />
              <span>{story}</span>
            </li>
          ))}
        </ul>
      </section>

      {brief.content.the_diff && (
        <section className="bg-amber-50 rounded-lg p-6 border border-amber-200">
          <h2 className="text-lg font-semibold mb-3 text-amber-800">
            The Diff
          </h2>
          <p className="text-amber-900">{brief.content.the_diff}</p>
        </section>
      )}
    </div>
  );
}
```

---

### Phase 6: Polish & Launch (Weeks 10-12)

#### Week 10: Testing

| Test Type | Coverage Target | Tools |
|-----------|-----------------|-------|
| Unit Tests | 80% | pytest |
| Integration Tests | 70% | pytest + testcontainers |
| E2E Tests | Critical paths | Playwright |
| Load Tests | 100 concurrent users | Locust |

#### Week 11: Optimization

| Optimization | Target | Method |
|--------------|--------|--------|
| API Response Time | <200ms p95 | Caching, query optimization |
| Brief Generation | <30s | Parallel processing |
| Feed Fetching | <5s per feed | Connection pooling |

#### Week 12: Launch Preparation

| Task | Description |
|------|-------------|
| Security Audit | OWASP Top 10 review |
| Documentation | API docs, user guide |
| Monitoring Setup | Alerts, dashboards |
| Backup Procedures | DB backups, disaster recovery |
| Launch Checklist | DNS, SSL, CDN, rate limiting |

---

## 3. AI Cost Management Protocol

### 3.1 Budget Enforcement

```python
# app/utils/cost_tracker.py
from sqlmodel import Session
from app.models import User, AICostLog


def track_ai_cost(
    session: Session,
    user_id: str,
    operation_type: str,
    cost_usd: float,
    model: str = None,
    input_tokens: int = None,
    output_tokens: int = None
):
    """Track AI cost and update user budget."""
    
    # Log the cost
    log = AICostLog(
        user_id=user_id,
        operation_type=operation_type,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd
    )
    session.add(log)
    
    # Update user's used budget
    user = session.get(User, user_id)
    user.ai_budget_used += cost_usd
    session.add(user)
    
    session.commit()
    
    # Check if over budget
    if user.ai_budget_used > user.daily_ai_budget:
        # Send alert
        send_budget_alert(user)
    
    return user.ai_budget_used


def check_budget(user: User) -> bool:
    """Check if user has remaining AI budget."""
    return user.ai_budget_used < user.daily_ai_budget


def get_budget_remaining(user: User) -> float:
    """Get remaining AI budget."""
    return max(0, user.daily_ai_budget - user.ai_budget_used)
```

### 3.2 Model Selection Logic

```python
# app/utils/ai_router.py
from enum import Enum
from typing import Optional


class ModelTier(Enum):
    FAST = "fast"           # Gemini Flash, Claude Haiku
    BALANCED = "balanced"   # GPT-4o-mini
    REASONING = "reasoning" # GPT-4o, Claude 3.5 Sonnet


class AgenticRouter:
    """Routes AI requests to appropriate model tier."""
    
    MODEL_MAP = {
        ModelTier.FAST: "gemini/gemini-1.5-flash",
        ModelTier.BALANCED: "gpt-4o-mini",
        ModelTier.REASONING: "gpt-4o"
    }
    
    COST_MAP = {
        ModelTier.FAST: 0.10,      # $/M tokens
        ModelTier.BALANCED: 0.50,
        ModelTier.REASONING: 5.00
    }
    
    def __init__(self, budget_remaining: float):
        self.budget_remaining = budget_remaining
    
    def route(self, query: str) -> Optional[ModelTier]:
        """Determine appropriate model tier for query."""
        
        # Budget check
        if self.budget_remaining < 0.10:
            return None  # Budget exceeded
        
        # Simple summarization
        if self._is_simple_summary(query):
            return ModelTier.FAST
        
        # Complex reasoning
        if self._contains_keywords(query, ["analyze", "compare", "verify"]):
            return ModelTier.REASONING
        
        # Default
        return ModelTier.BALANCED
    
    def _is_simple_summary(self, query: str) -> bool:
        patterns = ["summarize", "what is", "key points", "tl;dr"]
        return any(p in query.lower() for p in patterns)
    
    def _contains_keywords(self, query: str, keywords: list) -> bool:
        return any(k in query.lower() for k in keywords)
    
    def get_model(self, tier: ModelTier) -> str:
        return self.MODEL_MAP[tier]
    
    def estimate_cost(self, tier: ModelTier, tokens: int) -> float:
        return (tokens / 1_000_000) * self.COST_MAP[tier]
```

---

## 4. Validation Criteria

### 4.1 Technical Validation

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| Feed parsing success | >95% | Monitor failure_count |
| Content extraction | >90% | Track extraction_failed status |
| Embedding generation | >99% | Monitor embedding_failed status |
| Brief delivery | >99% | Track delivery_status |
| API uptime | >99.5% | Datadog monitoring |

### 4.2 Business Validation

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| User activation | >70% add feed within 24h | Analytics |
| Daily Brief open rate | >50% | Email tracking |
| Week 1 retention | >60% | Cohort analysis |
| NPS score | >30 | In-app survey |
| COGS per user | <$3/month | Cost tracking |

### 4.3 Quality Validation

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| Deduplication accuracy | >95% | Manual audit |
| Summary quality | >80% positive | User feedback |
| Hallucination rate | <1% | Source verification |
| Citation accuracy | >99% | Link verification |

---

## 5. Resource Requirements

### 5.1 Team Composition

| Role | Count | Duration |
|------|-------|----------|
| Backend Engineer | 2 | 12 weeks |
| Frontend Engineer | 1 | 8 weeks |
| DevOps Engineer | 1 | 4 weeks |
| Product Manager | 1 | 12 weeks |
| QA Engineer | 1 | 4 weeks |

### 5.2 Infrastructure Costs (Monthly)

| Component | Cost | Notes |
|-----------|------|-------|
| AWS ECS | $200 | 2 Fargate tasks |
| RDS PostgreSQL | $100 | db.t3.medium |
| ElastiCache Redis | $50 | cache.t3.micro |
| Qdrant (ECS) | $100 | 1 task |
| RabbitMQ (ECS) | $50 | 1 task |
| CloudWatch | $30 | Logs + metrics |
| **Total** | **$530** | Pre-launch |

---

## 6. Risk Mitigation

### 6.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Feed parsing failures | Medium | Medium | Multiple parsers, retry logic |
| Vector DB latency | Low | High | Partitioning, caching |
| AI API rate limits | Medium | High | Request queuing, fallback models |

### 6.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low user adoption | Medium | High | Generous free tier, viral features |
| High churn | Medium | Medium | Daily Brief habit formation |
| Cost overruns | Low | High | Budget caps, monitoring alerts |

---

## 7. Post-MVP Roadmap

| Version | Feature | Timeline |
|---------|---------|----------|
| v1.1 | YouTube transcription | +4 weeks |
| v1.2 | Email newsletter ingestion | +3 weeks |
| v1.3 | Audio Brief (TTS) | +2 weeks |
| v2.0 | Library module | +18 weeks |
| v3.0 | Lab module | +20 weeks |

---

## Document Control

| Field | Value |
|-------|-------|
| Author | Engineering Team |
| Status | Implementation-Ready |
| Last Updated | February 2026 |
| Next Review | Weekly during development |

---

*This document serves as the detailed implementation plan for Genio Stream MVP.*