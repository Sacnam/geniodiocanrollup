# Genio MVP Implementation Plan
## Module: STREAM (Intelligent Feed Aggregator)
**Version:** 1.0  
**Date:** February 2026  
**Timeline:** 10-12 Weeks to Market

---

## Executive Summary

### Strategic Decision: Why Stream First

After analyzing the three potential entry points (Book Reader, Feed Aggregator, Report Generator), **Stream emerges as the optimal MVP** for the following reasons:

| Criteria | Stream | Library | Lab |
|----------|--------|---------|-----|
| **Time to Value** | Immediate (daily use) | Medium (requires upload) | High (requires configuration) |
| **Technical Complexity** | Medium | High (PDF parsing, OCR) | High (agent orchestration) |
| **User Acquisition** | Viral (share briefs) | Individual | Enterprise sales cycle |
| **COGS Controllability** | High (batch processing) | Medium (on-demand) | Lower (unpredictable agent costs) |
| **Data Moat Building** | Fast (every read builds graph) | Slow | Medium |
| **Monetization Path** | Clear (upgrade to unlimited) | Requires integrations | Requires enterprise sales |

### MVP Success Criteria
1. User can add RSS feeds and receive a Daily Brief within 24 hours
2. Brief contains deduplicated, summarized content with source links
3. User can explore "The Diff" to see unique angles per source
4. System operates within $3 COGS per active user per month
5. 70%+ of beta users report time saved vs. previous workflow

---

## Phase 1: Foundation (Weeks 1-3)

### 1.1 Infrastructure Setup

**Deliverables:**
- Production AWS/GCP account with cost alerts
- CI/CD pipeline (GitHub Actions)
- Staging and production environments
- Monitoring stack (Datadog/New Relic)

**Technical Specifications:**
```yaml
# docker-compose.yml for local development
version: '3.8'
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://genio:password@postgres:5432/genio
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
  
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
  
  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
```

### 1.2 Database Schema (MVP Subset)

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
```

**Feeds Table:**
```sql
CREATE TABLE feeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT UNIQUE NOT NULL,
    title VARCHAR(500),
    description TEXT,
    last_fetched_at TIMESTAMP,
    last_etag VARCHAR(255),
    fetch_interval_minutes INT DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    content_hash VARCHAR(64), -- For change detection
    failure_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feeds_last_fetched ON feeds(last_fetched_at);
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
```

**Articles Table:**
```sql
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_id UUID REFERENCES feeds(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT,
    content TEXT, -- Full extracted text
    content_length INT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW(),
    vector_id VARCHAR(100), -- Reference to Qdrant
    
    -- Deduplication fields
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    cluster_id UUID, -- Groups similar articles
    canonical_article_id UUID REFERENCES articles(id), -- Points to original
    
    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'pending',
    -- pending → extracted → summarized → clustered → ready
    
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
```

**Daily_Briefs Table:**
```sql
CREATE TABLE daily_briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    brief_date DATE NOT NULL,
    title VARCHAR(500),
    summary TEXT,
    content JSONB, -- Structured brief sections
    article_count INT DEFAULT 0,
    sources_covered INT DEFAULT 0,
    delivery_status VARCHAR(20) DEFAULT 'pending',
    -- pending → generating → ready → sent → failed
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, brief_date)
);

CREATE INDEX idx_briefs_user_date ON daily_briefs(user_id, brief_date);
```

### 1.3 Vector Database Configuration

**Qdrant Collection:**
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, OptimizersConfig

client = QdrantClient(host="localhost", port=6333)

client.create_collection(
    collection_name="articles",
    vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
    optimizers_config=OptimizersConfig(
        default_segment_number=2,
        memmap_threshold_kb=20000,
        indexing_threshold_kb=10000
    )
)

# Payload schema (metadata stored with vectors)
# {
#   "article_id": "uuid",
#   "feed_id": "uuid", 
#   "published_at": "timestamp",
#   "title": "string",
#   "cluster_id": "uuid",
#   "content_hash": "string"
# }
```

---

## Phase 2: Core Ingestion Pipeline (Weeks 3-5)

### 2.1 Feed Fetcher Service

**Architecture:** Celery Beat scheduler + Celery workers

**Task: fetch_feed(feed_id)**
```python
import feedparser
import requests
from bs4 import BeautifulSoup
from celery import Celery
from datetime import datetime, timedelta

app = Celery('genio')

@app.task(bind=True, max_retries=3)
def fetch_feed(self, feed_id: str):
    """
    Fetch and parse RSS/Atom feed.
    Extract article metadata and full content.
    """
    feed = Feed.objects.get(id=feed_id)
    
    try:
        # Parse feed with conditional GET (ETag support)
        headers = {}
        if feed.last_etag:
            headers['If-None-Match'] = feed.last_etag
        
        parsed = feedparser.parse(feed.url, request_headers=headers)
        
        if parsed.status == 304:  # Not modified
            feed.last_fetched_at = datetime.utcnow()
            feed.save()
            return {"status": "not_modified"}
        
        new_articles = 0
        for entry in parsed.entries[:50]:  # Process max 50 per fetch
            # Check if already exists
            url = entry.get('link', '')
            if not url or Article.objects.filter(url=url).exists():
                continue
            
            # Extract published date
            published = parse_date(entry.get('published_parsed') or 
                                   entry.get('updated_parsed'))
            if published and published < datetime.utcnow() - timedelta(days=7):
                continue  # Skip old articles
            
            # Create article record
            article = Article.objects.create(
                feed_id=feed_id,
                url=url,
                title=clean_text(entry.get('title', '')),
                published_at=published,
                processing_status='pending'
            )
            
            # Queue content extraction
            extract_article_content.delay(article.id)
            new_articles += 1
        
        # Update feed metadata
        feed.last_fetched_at = datetime.utcnow()
        feed.last_etag = parsed.get('etag', '')
        feed.failure_count = 0
        feed.save()
        
        return {"status": "success", "new_articles": new_articles}
        
    except Exception as exc:
        feed.failure_count += 1
        if feed.failure_count >= 5:
            feed.is_active = False  # Auto-disable failing feeds
        feed.save()
        raise self.retry(exc=exc, countdown=300)
```

**Task: extract_article_content(article_id)**
```python
@app.task(bind=True, max_retries=2)
def extract_article_content(self, article_id: str):
    """
    Extract full article text from URL.
    Uses trafilatura for content extraction.
    """
    article = Article.objects.get(id=article_id)
    
    try:
        import trafilatura
        
        # Fetch with timeout and headers
        headers = {
            'User-Agent': 'GenioBot/1.0 (Content Aggregator)'
        }
        
        downloaded = trafilatura.fetch_url(article.url, headers=headers)
        
        if downloaded:
            extracted = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                deduplicate=True,
                target_language='en'  # Configure per user
            )
            
            if extracted and len(extracted) > 200:
                article.content = extracted
                article.content_length = len(extracted)
                article.content_hash = hashlib.sha256(extracted.encode()).hexdigest()[:64]
                article.processing_status = 'extracted'
                article.save()
                
                # Queue next steps
                generate_embedding.delay(article.id)
                return {"status": "extracted", "length": len(extracted)}
        
        # Fallback: mark as failed extraction
        article.processing_status = 'extraction_failed'
        article.save()
        return {"status": "failed"}
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### 2.2 Embedding Generation

**Task: generate_embedding(article_id)**
```python
@app.task
def generate_embedding(article_id: str):
    """
    Generate vector embedding for article content.
    Uses text-embedding-3-large via LiteLLM.
    """
    article = Article.objects.get(id=article_id)
    
    # Prepare text: title + first 8000 chars of content
    text = f"{article.title}\n\n{article.content[:8000]}"
    
    try:
        from litellm import embedding
        
        response = embedding(
            model="text-embedding-3-large",
            input=text,
            dimensions=3072
        )
        
        vector = response.data[0].embedding
        
        # Store in Qdrant
        qdrant_client.upsert(
            collection_name="articles",
            points=[{
                "id": str(article.id),
                "vector": vector,
                "payload": {
                    "article_id": str(article.id),
                    "feed_id": str(article.feed_id),
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                    "title": article.title[:200],
                    "content_hash": article.content_hash
                }
            }]
        )
        
        article.vector_id = str(article.id)
        article.processing_status = 'embedded'
        article.save()
        
        # Trigger clustering
        find_similar_articles.delay(article.id)
        
        return {"status": "embedded", "vector_id": article.vector_id}
        
    except Exception as e:
        article.processing_status = 'embedding_failed'
        article.save()
        raise
```

**Cost Control:** Track embedding costs per user
```python
def track_embedding_cost(user_id: str, text_length: int):
    """
    Track AI costs for budget enforcement.
    text-embedding-3-large: $0.13 per 1M tokens
    """
    estimated_tokens = text_length / 4  # Rough estimate
    cost = (estimated_tokens / 1_000_000) * 0.13
    
    User.objects.filter(id=user_id).update(
        ai_budget_used=F('ai_budget_used') + cost
    )
```

---

## Phase 3: Deduplication & Clustering (Weeks 5-6)

### 3.1 Clustering Algorithm

**Task: find_similar_articles(article_id)**
```python
@app.task
def find_similar_articles(article_id: str):
    """
    Find semantically similar articles for deduplication.
    Uses vector similarity search.
    """
    article = Article.objects.get(id=article_id)
    
    # Get vector from Qdrant
    vector_result = qdrant_client.retrieve(
        collection_name="articles",
        ids=[str(article_id)],
        with_vectors=True
    )
    
    if not vector_result:
        return
    
    vector = vector_result[0].vector
    
    # Search for similar articles (published within 7 days)
    time_filter = datetime.utcnow() - timedelta(days=7)
    
    similar = qdrant_client.search(
        collection_name="articles",
        query_vector=vector,
        limit=10,
        score_threshold=0.85,  # High similarity threshold
        query_filter={
            "must": [
                {"key": "published_at", "range": {"gte": time_filter.isoformat()}},
                {"key": "article_id", "match": {"except": [str(article_id)]}}
            ]
        }
    )
    
    if similar:
        # Get highest similarity match
        best_match = similar[0]
        
        if best_match.score >= 0.90:
            # Very similar - mark as duplicate
            similar_article_id = best_match.payload['article_id']
            article.cluster_id = Article.objects.get(id=similar_article_id).cluster_id
            article.canonical_article_id = similar_article_id
            article.processing_status = 'duplicate'
            article.save()
            
        elif best_match.score >= 0.85:
            # Related - add to cluster
            similar_article_id = best_match.payload['article_id']
            similar_article = Article.objects.get(id=similar_article_id)
            
            if similar_article.cluster_id:
                article.cluster_id = similar_article.cluster_id
            else:
                # Create new cluster
                cluster_id = uuid.uuid4()
                similar_article.cluster_id = cluster_id
                similar_article.save()
                article.cluster_id = cluster_id
            
            article.processing_status = 'clustered'
            article.save()
    else:
        # No similar articles - standalone
        article.cluster_id = uuid.uuid4()  # Self-cluster
        article.processing_status = 'clustered'
        article.save()
    
    # Queue summarization
    generate_summary.delay(article_id)
```

### 3.2 Summarization

**Task: generate_summary(article_id)**
```python
@app.task
def generate_summary(article_id: str):
    """
    Generate AI summary of article.
    Uses tiered model routing based on content length.
    """
    article = Article.objects.get(id=article_id)
    
    # Skip if duplicate
    if article.canonical_article_id:
        article.summary = "See: " + article.canonical_article_id
        article.processing_status = 'ready'
        article.save()
        return
    
    # Check user budget
    user = article.feed.users.first()  # Get associated user
    if user.ai_budget_used >= user.daily_ai_budget:
        article.processing_status = 'ready'  # Skip AI, use first 200 chars
        article.summary = article.content[:300] + "..." if article.content else None
        article.save()
        return
    
    try:
        from litellm import completion
        
        # Route based on content length
        if len(article.content) < 2000:
            model = "gemini/gemini-1.5-flash"  # Fast & cheap
        else:
            model = "gpt-4o-mini"  # Better quality
        
        prompt = f"""Summarize this article in 2-3 sentences. Be factual and neutral.
        Title: {article.title}
        Content: {article.content[:6000]}
        
        Summary:"""
        
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Track cost
        cost = response._hidden_params.get('response_cost', 0.001)
        track_ai_cost(user.id, cost)
        
        article.summary = summary
        article.processing_status = 'ready'
        article.save()
        
        return {"status": "summarized", "model": model}
        
    except Exception as e:
        # Fallback to excerpt
        article.summary = article.content[:300] + "..." if article.content else None
        article.processing_status = 'ready'
        article.save()
        raise
```

---

## Phase 4: Daily Brief Generation (Weeks 6-8)

### 4.1 Brief Generator Service

**Scheduled Task: generate_daily_briefs()**
```python
from celery.schedules import crontab

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run at 6 AM in each user's timezone
    sender.add_periodic_task(
        crontab(hour='6', minute='0'),
        generate_daily_briefs.s()
    )

@app.task
def generate_daily_briefs():
    """
    Generate daily briefs for all active users.
    Respects user timezone.
    """
    from django.utils import timezone
    
    current_hour = timezone.now().hour
    
    # Find users where it's 6 AM in their timezone
    users = User.objects.filter(
        is_active=True,
        brief_delivery_time__hour=current_hour
    )
    
    for user in users:
        generate_user_brief.delay(user.id)
```

**Task: generate_user_brief(user_id)**
```python
@app.task
def generate_user_brief(user_id: str):
    """
    Generate personalized daily brief for a user.
    """
    user = User.objects.get(id=user_id)
    today = date.today()
    
    # Check if already generated
    if DailyBrief.objects.filter(user=user, brief_date=today).exists():
        return
    
    # Get user's active feeds
    feed_ids = UserFeed.objects.filter(
        user=user, 
        is_active=True
    ).values_list('feed_id', flat=True)
    
    # Get articles from last 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    articles = Article.objects.filter(
        feed_id__in=feed_ids,
        published_at__gte=cutoff,
        processing_status='ready',
        canonical_article_id__isnull=True  # Only originals, not duplicates
    ).order_by('-published_at')[:100]  # Max 100 for processing
    
    if not articles.exists():
        # Create empty brief
        DailyBrief.objects.create(
            user=user,
            brief_date=today,
            title="No new articles today",
            content={"sections": []},
            delivery_status='ready'
        )
        return
    
    # Group by cluster (deduplication)
    clusters = {}
    for article in articles:
        cluster_id = article.cluster_id or str(article.id)
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append(article)
    
    # Build brief sections
    sections = []
    for cluster_id, cluster_articles in clusters.items():
        canonical = cluster_articles[0]
        
        section = {
            "title": canonical.rewritten_title or canonical.title,
            "summary": canonical.summary,
            "sources": [
                {
                    "name": article.feed.title or article.feed.url,
                    "url": article.url,
                    "is_canonical": article.id == canonical.id
                }
                for article in cluster_articles[:5]  # Max 5 sources
            ],
            "published_at": canonical.published_at.isoformat() if canonical.published_at else None
        }
        sections.append(section)
    
    # Sort by importance (for MVP: by recency)
    sections.sort(key=lambda x: x['published_at'], reverse=True)
    
    # Limit to top 15 stories
    sections = sections[:15]
    
    # Generate brief title using AI (if budget allows)
    title = f"Daily Brief for {today.strftime('%B %d, %Y')}"
    
    if user.ai_budget_used < user.daily_ai_budget * 0.8:
        try:
            from litellm import completion
            
            prompt = f"""Generate a brief, engaging title for a daily news brief.
            Topics covered: {', '.join([s['title'][:50] for s in sections[:5]])}
            
            Title (max 60 chars):"""
            
            response = completion(
                model="gemini/gemini-1.5-flash",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=30
            )
            title = response.choices[0].message.content.strip().strip('"')
            track_ai_cost(user.id, 0.0001)
        except:
            pass
    
    # Create brief record
    brief = DailyBrief.objects.create(
        user=user,
        brief_date=today,
        title=title,
        content={"sections": sections},
        article_count=len(articles),
        sources_covered=len(clusters),
        delivery_status='ready'
    )
    
    # Send email
    send_brief_email.delay(brief.id)
```

### 4.2 Email Delivery

**Task: send_brief_email(brief_id)**
```python
@app.task
def send_brief_email(brief_id: str):
    """
    Send daily brief via email.
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    
    brief = DailyBrief.objects.get(id=brief_id)
    user = brief.user
    
    # Render email template
    html_content = render_to_string('emails/daily_brief.html', {
        'brief': brief,
        'user': user,
        'sections': brief.content['sections']
    })
    
    text_content = render_to_string('emails/daily_brief.txt', {
        'brief': brief,
        'user': user,
        'sections': brief.content['sections']
    })
    
    try:
        send_mail(
            subject=brief.title,
            message=text_content,
            from_email='brief@genio.app',
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False
        )
        
        brief.delivery_status = 'sent'
        brief.delivered_at = datetime.utcnow()
        brief.save()
        
    except Exception as e:
        brief.delivery_status = 'failed'
        brief.save()
        raise
```

---

## Phase 5: Web Application (Weeks 7-10)

### 5.1 Backend API (FastAPI)

**Main Application Structure:**
```python
# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Genio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.genio.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(feeds.router, prefix="/feeds", tags=["feeds"])
app.include_router(briefs.router, prefix="/briefs", tags=["briefs"])
app.include_router(user.router, prefix="/user", tags=["user"])
```

**Feeds Endpoints:**
```python
# feeds.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List

router = APIRouter()

class FeedCreate(BaseModel):
    url: HttpUrl
    category: str = "general"

class FeedResponse(BaseModel):
    id: str
    url: str
    title: str
    category: str
    is_active: bool
    last_fetched_at: datetime
    unread_count: int

@router.post("/", response_model=FeedResponse)
async def add_feed(
    feed_data: FeedCreate,
    user: User = Depends(get_current_user)
):
    """Add a new RSS feed for the user."""
    
    # Validate RSS feed
    try:
        parsed = feedparser.parse(str(feed_data.url))
        if not parsed.entries:
            raise HTTPException(400, "Invalid or empty RSS feed")
    except Exception:
        raise HTTPException(400, "Could not parse RSS feed")
    
    # Get or create feed
    feed, created = Feed.objects.get_or_create(
        url=str(feed_data.url),
        defaults={
            'title': parsed.feed.get('title', 'Unknown Feed'),
            'description': parsed.feed.get('description', '')
        }
    )
    
    # Link to user
    user_feed, created = UserFeed.objects.get_or_create(
        user=user,
        feed=feed,
        defaults={'category': feed_data.category}
    )
    
    if not created:
        raise HTTPException(409, "Feed already added")
    
    # Trigger immediate fetch
    fetch_feed.delay(str(feed.id))
    
    return FeedResponse(
        id=str(feed.id),
        url=feed.url,
        title=feed.title,
        category=user_feed.category,
        is_active=feed.is_active,
        last_fetched_at=feed.last_fetched_at,
        unread_count=0
    )

@router.get("/", response_model=List[FeedResponse])
async def list_feeds(user: User = Depends(get_current_user)):
    """List all feeds for the current user."""
    user_feeds = UserFeed.objects.filter(user=user, is_active=True)
    
    return [
        FeedResponse(
            id=str(uf.feed.id),
            url=uf.feed.url,
            title=uf.custom_title or uf.feed.title,
            category=uf.category,
            is_active=uf.feed.is_active,
            last_fetched_at=uf.feed.last_fetched_at,
            unread_count=Article.objects.filter(
                feed=uf.feed,
                published_at__gte=user.last_active_at
            ).count()
        )
        for uf in user_feeds
    ]
```

**Briefs Endpoints:**
```python
# briefs.py
from fastapi import APIRouter, Depends
from typing import List, Optional

router = APIRouter()

class BriefSummary(BaseModel):
    id: str
    date: date
    title: str
    article_count: int
    sources_covered: int
    is_read: bool

class BriefDetail(BriefSummary):
    sections: List[dict]

@router.get("/", response_model=List[BriefSummary])
async def list_briefs(
    limit: int = 30,
    user: User = Depends(get_current_user)
):
    """List daily briefs for the user."""
    briefs = DailyBrief.objects.filter(user=user).order_by('-brief_date')[:limit]
    
    return [
        BriefSummary(
            id=str(b.id),
            date=b.brief_date,
            title=b.title,
            article_count=b.article_count,
            sources_covered=b.sources_covered,
            is_read=b.opened_at is not None
        )
        for b in briefs
    ]

@router.get("/today", response_model=BriefDetail)
async def get_today_brief(user: User = Depends(get_current_user)):
    """Get today's brief."""
    today = date.today()
    
    try:
        brief = DailyBrief.objects.get(user=user, brief_date=today)
    except DailyBrief.DoesNotExist:
        raise HTTPException(404, "Brief not yet generated")
    
    # Mark as opened
    if not brief.opened_at:
        brief.opened_at = datetime.utcnow()
        brief.save()
    
    return BriefDetail(
        id=str(brief.id),
        date=brief.brief_date,
        title=brief.title,
        article_count=b.article_count,
        sources_covered=b.sources_covered,
        is_read=True,
        sections=brief.content.get('sections', [])
    )
```

### 5.2 Frontend (React)

**Key Components:**

```typescript
// components/FeedList.tsx
import { useQuery } from '@tanstack/react-query';

export function FeedList() {
  const { data: feeds, isLoading } = useQuery({
    queryKey: ['feeds'],
    queryFn: () => api.get('/feeds').then(r => r.data)
  });

  if (isLoading) return <Skeleton count={5} />;

  return (
    <div className="space-y-2">
      {feeds?.map(feed => (
        <FeedCard key={feed.id} feed={feed} />
      ))}
      <AddFeedButton />
    </div>
  );
}

// components/DailyBrief.tsx
export function DailyBrief() {
  const { data: brief } = useQuery({
    queryKey: ['brief', 'today'],
    queryFn: () => api.get('/briefs/today').then(r => r.data)
  });

  if (!brief) return <EmptyState />;

  return (
    <div className="max-w-3xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">{brief.title}</h1>
        <p className="text-gray-500">
          {brief.article_count} articles from {brief.sources_covered} sources
        </p>
      </header>
      
      <div className="space-y-6">
        {brief.sections.map((section, idx) => (
          <BriefSection key={idx} section={section} />
        ))}
      </div>
    </div>
  );
}

// components/BriefSection.tsx
export function BriefSection({ section }: { section: BriefSection }) {
  const [showSources, setShowSources] = useState(false);

  return (
    <article className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-2">{section.title}</h2>
      <p className="text-gray-700 mb-4">{section.summary}</p>
      
      <button 
        onClick={() => setShowSources(!showSources)}
        className="text-sm text-blue-600"
      >
        {section.sources.length} sources
      </button>
      
      {showSources && (
        <div className="mt-4 space-y-2">
          {section.sources.map((source, idx) => (
            <a 
              key={idx}
              href={source.url}
              target="_blank"
              rel="noopener"
              className="block text-sm text-gray-600 hover:text-gray-900"
            >
              {source.name} {source.is_canonical && "(original)"}
            </a>
          ))}
        </div>
      )}
    </article>
  );
}
```

---

## Phase 6: Testing & Launch (Weeks 10-12)

### 6.1 Testing Strategy

**Unit Tests (pytest):**
```python
# tests/test_clustering.py
def test_similarity_clustering():
    """Test that similar articles are clustered together."""
    article1 = create_article(title="AI Breakthrough", content="New AI model released...")
    article2 = create_article(title="New AI Model Announced", content="Scientists release AI...")
    
    generate_embedding(article1.id)
    generate_embedding(article2.id)
    
    find_similar_articles(article2.id)
    
    article2.refresh_from_db()
    assert article2.cluster_id is not None
    assert article2.score >= 0.85
```

**Integration Tests:**
- End-to-end feed fetch → brief delivery (using test RSS feeds)
- Email delivery verification
- API authentication flows

**Load Testing:**
```python
# Simulate 1000 users receiving briefs simultaneously
locust -f load_test.py --users 1000 --spawn-rate 100
```

### 6.2 Beta Launch Checklist

**Week 10: Closed Beta**
- [ ] 50 hand-selected beta users (researchers, analysts)
- [ ] Daily monitoring of AI costs
- [ ] Feedback collection via Typeform
- [ ] Bug tracking in Linear/GitHub Issues

**Week 11: Iterate**
- [ ] Fix critical bugs
- [ ] Optimize slow queries
- [ ] Adjust clustering thresholds based on feedback
- [ ] Improve email deliverability

**Week 12: Public Launch**
- [ ] Landing page with pricing
- [ ] Stripe integration for payments
- [ ] Help center documentation
- [ ] Announcement on relevant communities

---

## 7. Resource Estimates

### 7.1 Team Composition

| Role | Count | Duration | Notes |
|------|-------|----------|-------|
| Backend Engineer (Python) | 1 | Full project | API, pipeline, AI integration |
| Frontend Engineer (React) | 1 | Weeks 7-12 | Can start after API defined |
| DevOps/Platform | 0.5 | Weeks 1-3, 10-12 | Infrastructure, monitoring |
| Product/Design | 0.5 | Throughout | UX flows, email templates |

### 7.2 Infrastructure Costs (Monthly)

**Development:**
```
AWS/GCP compute (dev):        $200
PostgreSQL (RDS/Cloud SQL):   $150
Redis (ElastiCache):          $50
Qdrant (managed):             $100
Email service (SendGrid):     $50
────────────────────────────────
Development Total:            $550/month
```

**Production (per 1000 active users):**
```
ECS/Fargate compute:          $400
PostgreSQL (db.r6g.xlarge):   $350
Redis:                        $100
Qdrant (2-node cluster):      $300
S3/CloudFront:                $100
SendGrid (100k emails):       $80
AI APIs (controlled):         $3,000
────────────────────────────────
Production Total:             $4,330/month

Revenue at $30/user:          $30,000/month
Gross Margin:                 85.5%
```

### 7.3 AI Cost Projections

**Per User Per Month:**
```
Daily Brief generation:       $0.80  (20 articles × $0.04 avg)
Article embeddings:           $0.50  (50 articles × $0.01)
Summaries (deduplicated):     $1.00  (25 summaries × $0.04)
Clustering queries:           $0.20  (Qdrant is cheap)
────────────────────────────────
Total AI Cost per User:       $2.50/month

Buffer (20%):                 $0.50
Target AI Budget:             $3.00/month (Pro tier)
```

---

## 8. Post-MVP Roadmap

### Month 4-6: Library Integration
- PDF/EPUB upload and parsing
- Document chat interface
- Semantic navigation
- Cross-reference with Stream content

### Month 7-9: Scout Agent
- Scheduled report generation
- Source configuration UI
- Template builder
- PDF report export

### Month 10-12: Enterprise Features
- Team workspaces
- Shared knowledge bases
- Admin controls
- SSO integration
- On-premise option (if demand exists)

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| AI costs exceed projections | Hard budget caps per user, graceful degradation |
| Feed parsing failures | Multiple fallback parsers, manual override |
| Email deliverability issues | Dedicated IP, SPF/DKIM, reputation monitoring |
| Clustering quality poor | Human feedback loop, adjustable thresholds |
| Competitor launches similar product | Focus on UX polish and customer success |

---

## 10. Success Metrics for MVP

**Week 12 Targets:**
- 100+ registered users
- 60% daily active rate
- <$5 COGS per active user
- 4.0+ NPS score
- 50+ user-added feeds

**Month 3 Targets:**
- 500+ paying users
- 70% retention (week 1 to week 4)
- $15,000 MRR
- 2-minute average session time

---

**Document Control:**
- Author: Technical Architecture Team
- Approved By: Product Lead, CFO
- Next Review: Post-Launch Week 4
- Distribution: Engineering, Product, Executive Team
