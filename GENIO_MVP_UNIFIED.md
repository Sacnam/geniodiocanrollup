# Genio Knowledge OS
## MVP Specification — v2.1 Optimized
**Version:** 2.1  
**Date:** February 2026  
**Module:** STREAM (Intelligent Feed Aggregator)  
**Timeline:** 12 Weeks to Market  
**Optimizations Applied:** B01, B03, B04, B10, B13 (see Architecture Audit)

> [!NOTE]
> This document defines **scope and acceptance criteria only**. Architecture and NFRs → `GENIO_PRD_UNIFIED.md`. Sprint tasks → `GENIO_IMPLEMENTATION_PLAN_FINAL.md`.

---

## 1. MVP Module Selection Rationale

| Criterion (Weight) | Stream | Library | Lab |
|----|----|----|-----|
| Immediate user value (25%) | 9.5 | 7 | 6 |
| Technical complexity (20%) | 8 | 6 | 4 |
| Market differentiation (20%) | 8 | 7 | 9 |
| Revenue potential (15%) | 8 | 6 | 5 |
| AI cost efficiency (10%) | 8 | 5 | 4 |
| Data moat building (10%) | 9 | 8 | 6 |
| **Weighted Score** | **8.60** | **6.55** | **5.50** |

**Decision: Stream module first.** Highest weighted score. Builds the ingestion pipeline and Knowledge Graph shared by all modules.

---

## 2. Feature Scope

### In-Scope (12 Features)

| # | Feature | Priority | Sprint |
|---|---------|----------|--------|
| F01 | User auth (email + Google OAuth) | P0 | S1 |
| F02 | OPML import | P0 | S1-S2 |
| F03 | Feed CRUD (add, edit, categorize, delete) | P0 | S2-S3 |
| F04 | Adaptive feed fetching (5-60 min) | P0 | S2 |
| F05 | Content extraction (Readability) | P0 | S2 |
| F06 | Shared embedding generation (1536-dim, batched) | P0 | S2-S3 |
| F07 | Knowledge Delta detection | P0 | S3 |
| F08 | Per-user novelty scoring | P0 | S3 |
| F09 | Feed article listing (read, archive, share) | P0 | S3-S4 |
| F10 | Daily Brief generation (staggered) | P0 | S4 |
| F11 | Brief delivery (in-app + email) | P0 | S4-S5 |
| F12 | AI budget tracking + graceful degradation | P1 | S5 |

### Deferred (Post-MVP)

| Feature | Target Version | Reason |
|---------|---------------|--------|
| YouTube transcription | v1.5 | Requires Whisper pipeline |
| Audio Brief (TTS) | v1.5 | ElevenLabs dependency |
| Anti-Clickbait rewriting | v1.5 | Low priority for MVP |
| Email newsletter ingestion | v1.5 | IMAP complexity |
| Library module (PDF/EPUB) | v2.0 | Full module |
| Lab module (Scout agents) | v3.0 | Full module |

---

## 3. Acceptance Criteria

### F01: Authentication
```gherkin
GIVEN a new user
WHEN they register with email and password
THEN a JWT is returned with 24h expiry
AND their account is created in PostgreSQL

GIVEN a user with Google account
WHEN they authenticate via OAuth 2.0
THEN a JWT is returned AND their profile is auto-populated
```

### F02: OPML Import
```gherkin
GIVEN user uploads a valid OPML file
WHEN the file is parsed
THEN all feeds are created with original categories preserved
AND duplicates (by feed URL) are skipped with count reported

GIVEN an OPML file with >200 feeds
WHEN imported
THEN processing completes in <30 seconds
```

### F03: Feed Management
```gherkin
GIVEN an authenticated user
WHEN they add a feed URL
THEN the system validates the URL, resolves RSS/Atom, stores it
AND the first fetch is queued immediately

GIVEN a user with active feeds
WHEN they delete a feed
THEN the feed is soft-deleted
AND associated user_article_context records are purged after 30 days
```

### F04: Adaptive Feed Fetching (B03 Applied)
```gherkin
GIVEN a feed with avg_update_interval=6 hours
WHEN the scheduler evaluates fetch timing
THEN fetch_interval is set to 60 minutes

GIVEN a feed with avg_update_interval=15 minutes
WHEN the scheduler evaluates fetch timing
THEN fetch_interval is set to 5 minutes

GIVEN a feed that returns HTTP 404 or 5xx for 5 consecutive fetches
THEN the feed is auto-disabled AND the user is notified
```

### F05: Content Extraction
```gherkin
GIVEN a raw article URL
WHEN content extraction runs
THEN the full text is extracted (Readability algorithm)
AND HTML is cleaned to plain text
AND articles <200 characters are flagged as low-quality

GIVEN a paywall-blocked URL
WHEN extraction returns <100 characters
THEN status is set to 'extraction_failed'
AND the article is stored with title + excerpt only
```

### F06: Shared Embedding (B01, B04, B13 Applied)
```gherkin
GIVEN 50 new articles from the same feed
WHEN embedding generation runs
THEN a single batch API call with 50 inputs is sent
AND all 50 embeddings (1536-dim) are stored in Qdrant
AND each article_id maps to its embedding_vector_id

GIVEN an article with URL already in global article pool
WHEN processing encounters it
THEN no new embedding is generated (reuse existing)
```

### F07: Knowledge Delta Detection
```gherkin
GIVEN a new article embedding
WHEN Knowledge Delta runs
THEN it queries k=10 neighbors in Qdrant (time_filter=7d)
AND classifies: DUPLICATE (≥0.90), RELATED (≥0.85), NOVEL (<0.85)
AND stores {delta_score, cluster_id, status}

GIVEN a DUPLICATE article (score ≥0.90)
THEN it does NOT appear in user feed or Daily Brief
```

### F08: Per-User Novelty Scoring
```gherkin
GIVEN a NOVEL article (delta <0.85)
WHEN user_article_context is computed
THEN delta_score reflects novelty against THIS user's read history
AND the article is ranked in the user's feed by delta_score DESC
```

### F09: Feed Article Listing
```gherkin
GIVEN an authenticated user viewing their feed
WHEN articles load
THEN they are paginated (20 per page), sorted by delta_score DESC
AND each shows: title, source, published_at, delta_score badge, 2-line excerpt

GIVEN a user clicks an article
THEN full content loads AND read_status is set to 'read'
```

### F10: Daily Brief Generation (B07 Applied)
```gherkin
GIVEN a user with timezone 'Europe/Rome' and brief_time='08:00'
WHEN the staggered scheduler triggers (user_id % 60 = minute offset)
THEN a brief is generated from top 15 NOVEL articles
AND the brief includes: executive summary, key stories, the_diff section

GIVEN a user with <3 novel articles in last 24h
THEN the brief is replaced with "Quiet Day" summary (no AI call)
```

### F11: Brief Delivery
```gherkin
GIVEN a generated brief
WHEN delivery triggers
THEN the brief is available in-app via /briefs/* endpoint
AND an email copy is sent via SendGrid
AND delivery_status is tracked (sent/delivered/opened)
```

### F12: AI Budget + Graceful Degradation (B12 Applied)
```gherkin
GIVEN a Starter user with $2.00 AI budget
WHEN budget_remaining > 50%
THEN all features operate at L1 (Full AI)

WHEN budget_remaining is between 20-50%
THEN features degrade to L2 (cached summaries, generic clustering)

WHEN budget_remaining < 20%
THEN features degrade to L3 (title + excerpt, no AI calls)
AND user sees "AI budget low" banner with upgrade prompt
```

---

## 4. Unit Economics

> [!NOTE]
> Full cost model → `GENIO_PRD_UNIFIED.md` §7. Summary below for MVP context.

| Component | Cost/User/Month |
|-----------|-----------------|
| Feed fetching (shared pool) | $0.10 |
| Content extraction | $0.15 |
| Embeddings (1536-dim, batched, shared) | $0.08 |
| Article summaries (Gemini Flash) | $1.00 |
| Daily Brief generation | $0.30 |
| Clustering queries | $0.15 |
| Storage (Postgres + Qdrant + Redis) | $0.25 |
| **Total MVP COGS** | **$2.03** |

| Tier | Revenue | COGS | Margin |
|------|---------|------|--------|
| Starter ($15) | $15.00 | $2.03 | **86.5%** |
| Professional ($30) | $30.00 | $2.03 | **93.2%** |
| Enterprise ($75) | $75.00 | $2.03 | **97.3%** |

---

## 5. Milestone Gates

Each milestone is a **binary pass/fail** gate. All criteria must pass.

| Gate | Week | Criteria |
|------|------|----------|
| **M1: Foundation** | W2 | CI green, Postgres + Qdrant + Redis up, /health 200 |
| **M2: Ingestion Pipeline** | W4 | 100 feeds fetched, articles extracted, embeddings stored |
| **M3: Intelligence** | W6 | Delta scores computed, duplicates filtered, summaries generated |
| **M4: Brief Engine** | W8 | Briefs generated, staggered delivery, email sent |
| **M5: Integration** | W10 | Full E2E functional, budget tracking active, settings working |
| **M6: Launch** | W12 | Load test passed, beta feedback integrated, Stripe live |

---

*MVP Spec v2.1. SSOT for scope and acceptance criteria. Architecture → PRD. Tasks → Implementation Plan.*
