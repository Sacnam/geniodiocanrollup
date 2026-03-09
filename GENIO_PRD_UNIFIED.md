# Genio Knowledge OS
## Product Requirements Document (PRD) — v3.1 Optimized
**Version:** 3.1  
**Date:** February 2026  
**Status:** Implementation-Ready  
**Optimizations Applied:** B01, B02, B09, B10, B11, B12 (see Architecture Audit)

---

## Executive Summary

### Product Vision
Genio is a cloud-first knowledge assimilation platform — a "Cognitive Operating System" that transforms information overload into actionable intelligence through feed aggregation, document analysis, and AI-powered report generation.

### Core Value Proposition
**"From Information Overload to Actionable Intelligence"**

### Architecture Constraint

> [!CAUTION]
> **CLOUD-FIRST ONLY.** All AI inference in production-grade cloud environments. No local/on-device AI.

### Strategic Positioning

| Aspect | Specification |
|--------|---------------|
| **Target Market** | Knowledge professionals (researchers, analysts, investors, consultants) |
| **Pricing Model** | B2B SaaS: $15 / $30 / $75 per user/month |
| **Competitive Moat** | Personal Knowledge Graph + Knowledge Delta algorithm |
| **Unit Economics** | 82-91% gross margin via shared ingestion + intelligent routing |
| **North Star Metric** | Knowledge Velocity — high-signal insights consumed per unit time |

---

## 1. Problem Analysis

| Dimension | Quantification | Impact |
|-----------|----------------|--------|
| **Volume** | 50+ sources/day | Cognitive overload |
| **Fragmentation** | RSS, email, PDFs, YouTube, podcasts | Context switching |
| **Redundancy** | 70-80% duplicate content | Wasted attention |
| **Format Lock-in** | 2hr videos, 50pg PDFs | Inefficient consumption |

### Economic Constraint

| Processing Approach | COGS/User/Month | Verdict |
|---------------------|------------------|---------|
| Real-time AI on all content | $50+ | **REJECTED** |
| Batch processing + caching | $2-6 | **APPROVED** |
| Local/on-device AI | N/A | **REJECTED** |

---

## 2. Product Architecture

### Three-Module System

```
┌────────────────┬────────────────┬─────────────────┐
│    STREAM      │    LIBRARY     │      LAB        │
│  (Aggregator)  │  (E-Reader)   │ (Report Gen)    │
├────────────────┼────────────────┼─────────────────┤
│ RSS/YouTube    │ EPUB/PDF/DOCX  │ Agentic Search  │
│ Newsletters    │ Semantic Nav   │ Periodic Reports│
│ Daily Brief    │ Knowledge Map  │ Claim Verify    │
│ Deduplication  │ Liquid Format  │ Cross-Doc RAG   │
└────────────────┴────────────────┴─────────────────┘
        │                │                │
        ▼                ▼                ▼
  ┌──────────┐    ┌──────────┐    ┌──────────┐
  │Librarian │    │  Reader  │    │  Scout   │
  │(Ingest)  │    │  (Parse) │    │(Discover)│
  └──────────┘    └──────────┘    └──────────┘
```

> [!NOTE]
> **MVP = Stream module only.** Library and Lab specifications are in `GENIO_PRODUCT_ROADMAP.md`. This PRD defines the full platform vision; the MVP document narrows scope.

### Module Summary (For Scoping Only)

| Module | Purpose | MVP? | Timeline |
|--------|---------|------|----------|
| **Stream** | Eliminate noise via dedup + AI summarization | **YES** | Weeks 1-12 |
| **Library** | Maximize comprehension of long-form docs | No | Weeks 19-36 |
| **Lab** | Autonomous research via Scout agents | No | Weeks 37-54 |

---

## 3. Stream Module — Detailed Specification (MVP)

### Core Features

| Feature | Specification | Technical Approach |
|---------|---------------|-------------------|
| **Source Aggregation** | RSS, Atom, YouTube, Newsletters, Substack | feedparser + IMAP |
| **Anti-Clickbait** | Title rewriting to factual statements | Gemini Flash (post-MVP) |
| **Semantic Deduplication** | Cluster articles on same topic | Vector similarity ≥0.85 |
| **Daily Brief** | Structured digest at user-defined time | Batch + staggered delivery |
| **The Diff** | Unique info per source vs cluster | Delta detection |
| **Audio Brief** | TTS for commute consumption | ElevenLabs (post-MVP) |

### Knowledge Delta Algorithm (Core IP)

```
ALGORITHM: Knowledge Delta Detection
INPUT:  article_vector V_new (1536-dim)
OUTPUT: {delta_score, cluster_id, status}

1. neighbors = qdrant.search(V_new, k=10, time_filter=7d)
2. best = max(neighbors, key=score)

3. IF best.score >= 0.90 → DUPLICATE  (delta=0.0, cluster=best.cluster)
   IF best.score >= 0.85 → RELATED   (delta=1-best.score, cluster=best.cluster)
   IF best.score <  0.85 → NOVEL     (delta=1-best.score, cluster=new_id())

4. RETURN {delta_score, cluster_id, status}
```

> [!IMPORTANT]
> **B01 Applied:** Embeddings use 1536-dim (text-embedding-3-small or text-embedding-3-large with `dimensions=1536`). 80% cost reduction vs 3072-dim, <2% retrieval quality loss per MTEB benchmarks.

### Daily Brief Pipeline

```
TRIGGER: Staggered per user (user_id % 60 = minute offset within hour)

1. AGGREGATE: articles from last 24h, status='ready', sorted by delta_score DESC
2. CLUSTER:   group by cluster_id, select canonical per cluster
3. GENERATE:  top 15 stories → Gemini Flash → {summary, key_stories, the_diff}
4. DELIVER:   in-app + email (SendGrid), track delivery_status
5. TRACK:     log ai_budget_used, article_count, open_rate
```

> [!TIP]
> **B07 Applied:** Briefs staggered within each timezone hour to eliminate thundering herd. Users receive briefs within ±30min of configured time.

---

## 4. Technical Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                             │
│   React 18 SPA (TypeScript + TanStack Query)                │
│   Login │ Feed Manager │ Brief Reader │ Settings + Budget    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS / JSON
                         ▼
┌─────────────────────────────────────────────────────────────┐
│   API LAYER — FastAPI (Python 3.12)                          │
│   /auth/*  /feeds/*  /briefs/*  /user/*  /health            │
│   Middleware: CORS │ JWT │ Rate Limit │ Request Logger       │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ WORKER LAYER │ │  DATA LAYER  │ │ EXTERNAL APIs│
│              │ │              │ │              │
│ Celery       │ │ PostgreSQL 15│ │ OpenAI       │
│ + Celery Beat│ │ Redis 7      │ │ Google Gemini│
│              │ │ Qdrant       │ │ SendGrid     │
│ (Redis       │ │              │ │              │
│  as broker)  │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

> [!IMPORTANT]
> **B11 Applied:** Redis serves as both cache AND Celery broker for MVP. RabbitMQ deferred to >10k users when message durability guarantees become critical.

### Technology Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| Language | Python 3.12 | AI ecosystem maturity |
| API | FastAPI 0.109+ | Async, Pydantic v2, auto-docs |
| ORM | SQLModel 0.0.14+ | SQLAlchemy + Pydantic |
| Task Queue | Celery 5.3+ | Distributed task processing |
| Broker | **Redis 7** (MVP) | Dual-purpose: cache + broker |
| Relational DB | PostgreSQL 15+ | JSONB, RLS, proven |
| Vector DB | Qdrant 1.7+ | Self-hosted, metadata filtering |
| AI Gateway | LiteLLM | Multi-provider, cost tracking |
| Embedding | text-embedding-3-small | **1536-dim**, $0.02/M tokens |
| Fast LLM | Gemini Flash | $0.10/M tokens |
| Balanced LLM | GPT-4o-mini | $0.50/M tokens |
| Frontend | React 18 + TypeScript | Component ecosystem |
| Data Fetching | TanStack Query 5+ | Cache, dedup, background refetch |
| Email | SendGrid | Deliverability, tracking |
| CI/CD | GitHub Actions | Repo-integrated |
| Monitoring | Datadog | Full observability |
| Container | Docker + ECS Fargate | Serverless, auto-scaling |

### AI Cost Management

#### Intelligent Router (B02 Optimized)

```python
class IntelligentRouter:
    """Routes via query embedding similarity to intent centroids.
    Zero additional AI cost — reuses existing embedding model."""

    INTENT_CENTROIDS = {
        ModelTier.FAST: precomputed_centroid_summary,      # summaries, TL;DR
        ModelTier.BALANCED: precomputed_centroid_analysis,  # comparisons
        ModelTier.REASONING: precomputed_centroid_research, # verification
    }

    def route(self, query_embedding: list[float], budget_remaining: float) -> ModelTier:
        if budget_remaining < 0.10:
            return ModelTier.BUDGET_EXCEEDED

        similarities = {
            tier: cosine_sim(query_embedding, centroid)
            for tier, centroid in self.INTENT_CENTROIDS.items()
        }
        return max(similarities, key=similarities.get)
```

#### Graceful Degradation (B12 Applied)

| Budget Remaining | Level | Behavior |
|-----------------|-------|----------|
| >50% | **L1: Full AI** | Model-generated summary + delta analysis |
| 20-50% | **L2: Reduced AI** | Cached/global summaries + generic clustering |
| <20% | **L3: No AI** | Title + first 300 chars excerpt + source link |

#### Cost Allocation per Tier

| Tier | Price | AI Budget | Overrun Handling |
|------|-------|-----------|------------------|
| Starter | $15/mo | $2.00 | Hard cap → L3 degradation |
| Professional | $30/mo | $5.00 | Grace period → L2 → L3 |
| Enterprise | $75/mo | $15.00 | Auto-bill overages |

### Data Models

#### Knowledge Atom

```json
{
  "atom_id": "uuid-v4",
  "source_id": "document-ref",
  "content_hash": "sha256",
  "raw_text": "string (max 2000 chars)",
  "embedding_vector": [1536 floats],
  "metadata": {
    "chunk_index": 0,
    "semantic_density": 0.85,
    "entities": ["entity-1", "entity-2"]
  },
  "truth_state": {
    "status": "verified|disputed|retracted|unknown",
    "confidence": 0.92,
    "sources": ["source-1", "source-2"]
  }
}
```

#### Shared Article Pool (B04 Applied)

```
articles (GLOBAL)              user_article_context (PER-USER)
┌──────────────────────┐       ┌──────────────────────────┐
│ id (PK)              │       │ user_id (FK)             │
│ feed_id (FK)         │       │ article_id (FK)          │
│ url (UNIQUE)         │       │ delta_score (0.0-1.0)    │
│ title                │◄──────│ read_status              │
│ content              │       │ cluster_id (user-scoped) │
│ content_hash         │       │ is_duplicate             │
│ embedding_vector_id  │       │ created_at               │
│ global_summary       │       └──────────────────────────┘
│ processing_status    │
│ published_at         │
└──────────────────────┘
```

> Articles are deduplicated globally (by URL + content_hash). Embeddings generated once. Delta scoring and clustering are per-user context, enabling personalized novelty detection without redundant AI calls.

---

## 5. Non-Functional Requirements

### Performance

| Metric | Target |
|--------|--------|
| API p95 latency | <200ms |
| Brief generation | <5 min/user |
| Vector search | <50ms (1536-dim with HNSW) |
| Feed fetch cycle | Adaptive 5-60 min |

### Scalability

| Dimension | Year 1 | Year 3 |
|-----------|--------|--------|
| Active users | 10,000 | 100,000 |
| Articles/day | 500,000 | 5,000,000 |
| Vector DB entries | 50M | 500M |

### Availability

| Metric | Target |
|--------|--------|
| Uptime SLA | 99.9% |
| Brief delivery | >99% |
| RTO | <1 hour |
| RPO | <5 minutes |

### Security

| Requirement | Implementation |
|-------------|----------------|
| Data at rest | AES-256 |
| Data in transit | TLS 1.3 |
| Auth | JWT + OAuth 2.0 (Google) |
| Authorization | RBAC + row-level security |
| Secrets | AWS Secrets Manager |

---

## 6. Success Metrics

### North Star
**Knowledge Velocity** — high-signal insights consumed per unit time

### KPIs

| Metric | Target | Method |
|--------|--------|--------|
| DAU | 40% of MAU | Analytics |
| Session Duration | 12+ min | Analytics |
| Knowledge Delta Coverage | >80% novel | Algorithm monitoring |
| User Retention (M3) | >60% | Cohort analysis |
| AI Cost per User | <$3 (MVP), <$6 (full) | Cost monitoring |
| Hallucination Rate | <0.1% | Sampling audit |
| NPS | >40 | Surveys |

---

## 7. Business Model

### Pricing

| Feature | Starter $15 | Pro $30 | Enterprise $75 |
|---------|-------------|---------|-----------------|
| Sources | 20 feeds | Unlimited | Unlimited + API |
| Daily Brief | 1/day | 3/day | Unlimited |
| Library Storage | 1 GB | 10 GB | Unlimited |
| Scout Reports | 5/mo | 20/mo | Unlimited |
| AI Budget | $2 | $5 | Custom |

### Unit Economics (Pro Tier — Stream MVP)

| Component | Cost |
|-----------|------|
| Feed fetching (shared) | $0.10 |
| Content extraction | $0.15 |
| Embeddings (shared, 1536-dim) | **$0.08** |
| Article summaries | $1.00 |
| Daily Brief generation | $0.30 |
| Clustering queries | $0.15 |
| Storage | $0.25 |
| **Total MVP COGS** | **$2.03** |
| **Revenue** | **$30.00** |
| **Gross Margin** | **93.2%** |

> [!TIP]
> B01 optimization reduced embedding cost from $0.50 to $0.08/user/month. Total COGS dropped from $2.58 to $2.03.

### Cost Optimization Strategies

| Strategy | Savings |
|----------|---------|
| Shared article pool (B04) | 60-80% on embedding calls |
| 1536-dim embeddings (B01) | 80% on embedding cost |
| Redis as broker (B11) | $50-100/mo infra |
| Batch embedding API (B13) | 30-50% fewer API calls |
| Staggered brief gen (B07) | 10x peak compute reduction |
| Tiered caching | 50% on vector queries |

---

## 8. Risk Analysis

| Risk | Prob. | Impact | Mitigation |
|------|-------|--------|------------|
| AI API cost spike | Medium | High | Budget caps, model fallbacks, caching, L1→L2→L3 degradation |
| AI API outage | Medium | High | Circuit breaker (B05), excerpt fallback, sweeper retry |
| Hallucination in outputs | Medium | Critical | Extraction-only, source attribution, confidence scores |
| Feed parsing failures | Medium | Medium | Retry + multiple parsers + auto-disable after 5 failures |
| Vector DB latency | Low | High | HNSW tuning, 1536-dim (B01), partitioning |
| Competition (Big Tech) | High | Medium | Knowledge Delta differentiation, workflow lock-in |
| Copyright claims | Medium | High | BYOL model, no redistribution, fair use summaries |

---

## 9. Compliance

| Requirement | Implementation |
|-------------|----------------|
| SOC 2 Type II | Before Enterprise launch |
| GDPR | EU residency, right to deletion |
| Content rights | No redistribution; transformative summaries only |
| User ownership | User owns uploaded content |

---

## 10. Implementation Roadmap

> **Detailed sprint breakdown → `GENIO_IMPLEMENTATION_PLAN_FINAL.md`**

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Foundation | Weeks 1-2 | Infra, DB, CI/CD, design system |
| Ingestion + Frontend Shell | Weeks 3-4 | Feed pipeline + mock UI |
| Intelligence + Feed UI | Weeks 5-6 | Clustering, summaries + real feed manager |
| Brief Engine + Brief UI | Weeks 7-8 | Brief gen, email + brief reader |
| Integration + Polish | Weeks 9-10 | Full E2E integration, settings, budget |
| Testing + Launch | Weeks 11-12 | Load testing, beta, Stripe, launch |

> **Post-MVP roadmap → `GENIO_PRODUCT_ROADMAP.md`**

| Version | Module | Timeline |
|---------|--------|----------|
| v1.5 | Stream+ (YouTube, Audio, Anti-Clickbait) | Weeks 13-18 |
| v2.0 | Library (PDF, RAG, CRDT sync) | Weeks 19-36 |
| v3.0 | Lab (Scout agents, claim verification) | Weeks 37-54 |

---

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| Knowledge Atom | Minimum unit of semantic information |
| Knowledge Delta | Novelty score (0.0-1.0) |
| Scout | Autonomous research agent |
| Daily Brief | Automated curated digest |
| The Diff | Unique information highlighting |
| Agentic Router | Model selection by query complexity |

### API Integrations

**Required:** OpenAI (text-embedding-3-small, GPT-4o-mini), Google Gemini (Flash), Qdrant, PostgreSQL, SendGrid  
**Optional:** Anthropic (Claude), Serper/Tavily (search), ElevenLabs (TTS), Zotero (academic)

---

*Canonical PRD v3.1. Supersedes v3.0, v2.0, and PRD-Kimi v1.0. SSOT for vision, architecture, and NFRs.*
