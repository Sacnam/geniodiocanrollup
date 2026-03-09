# Genio Knowledge Platform
## Product Requirements Document (PRD)
**Version:** 1.0  
**Date:** February 2026  
**Status:** Final  
**Classification:** Implementation-Ready

---

## Executive Summary

### Product Vision
Genio is an intelligent knowledge assimilation platform that transforms how professionals consume, synthesize, and act upon information. It functions as a unified system combining feed aggregation, document analysis, and AI-powered report generation—enabling users to rapidly distinguish signal from noise and receive personalized knowledge artifacts.

### Core Value Proposition
**"From Information Overload to Actionable Intelligence"**

Genio externalizes the cognitive labor of information processing, allowing knowledge workers to focus on synthesis and decision-making rather than manual aggregation and filtering.

### Strategic Positioning
- **Target Market:** Knowledge professionals (researchers, analysts, investors, consultants)
- **Pricing Model:** B2B SaaS with usage-based tiers ($30-100/user/month)
- **Competitive Moat:** User's accumulated Personal Knowledge Graph (high switching costs)
- **Unit Economics Target:** 75%+ gross margin through shared ingestion and intelligent routing

---

## 1. Problem Analysis

### 1.1 The Epistemic Crisis
Modern knowledge workers face a paradox of abundance:
- **Volume:** Average professional consumes 50+ information sources daily
- **Fragmentation:** Content scattered across RSS, email newsletters, PDFs, YouTube, podcasts
- **Redundancy:** 70-80% of news content is duplicate or low-signal
- **Format Lock-in:** Valuable insights trapped in suboptimal containers (2-hour videos, 50-page PDFs)

### 1.2 Current Solutions Fail
| Solution Type | Limitation |
|--------------|------------|
| Traditional RSS Readers | Dumb aggregation, no synthesis |
| Read-later Apps (Pocket, Instapaper) | Static storage, no connections |
| Generic AI Chatbots | No persistent memory, hallucination risk |
| Enterprise Search (Glean) | Internal-only, expensive, complex setup |

### 1.3 Economic Constraints
Based on cost analysis at 2026 cloud AI pricing:
- **Unsustainable:** Real-time AI processing on all content ($50+/user/month COGS)
- **Required:** Batch processing with intelligent caching and tiered model routing
- **Target COGS:** <$6/user/month for power users at $30 subscription

---

## 2. Product Architecture

### 2.1 Three-Module System

```
┌─────────────────────────────────────────────────────────────────┐
│                        GENIO PLATFORM                            │
├─────────────────┬─────────────────┬─────────────────────────────┤
│     STREAM      │     LIBRARY     │           LAB               │
│   (Aggregator)  │   (E-Reader)    │    (Report Generator)       │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ • RSS/YouTube   │ • EPUB/PDF      │ • Agentic Search            │
│ • Newsletters   │ • Semantic Nav  │ • Periodic Reports          │
│ • Daily Brief   │ • Knowledge Map │ • Cross-Document Analysis   │
│ • Deduplication │ • Liquid Format │ • Claim Verification        │
└─────────────────┴─────────────────┴─────────────────────────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
   ┌─────────────┐      ┌─────────────┐
   │  Librarian  │      │    Scout    │
   │  (Ingest)   │      │  (Discover) │
   └─────────────┘      └─────────────┘
```

### 2.2 Module Specifications

#### MODULE 1: STREAM (Intelligent Feed Aggregator)
**Purpose:** Eliminate noise from high-velocity information sources

**Core Features:**

| Feature | Specification | Technical Approach |
|---------|---------------|-------------------|
| Source Aggregation | RSS, Atom, YouTube channels, Email newsletters, Substack | Standard protocols + IMAP integration |
| Anti-Clickbait | Title rewriting to factual statements | Lightweight LLM (Gemini Flash/Claude Haiku) |
| Semantic Deduplication | Group 50 articles on same topic into single cluster | Vector similarity >0.85 threshold |
| Daily Brief | Single structured digest delivered at user-defined time | Batch processing at 6 AM user time |
| The Diff | Highlight unique information in each source vs. cluster | Delta detection algorithm |

**Knowledge Delta Algorithm:**
```
Input: New article vector, User's existing article vectors
1. Retrieve top-5 nearest neighbors from vector DB
2. Calculate max cosine similarity: max_sim = max(neighbors.similarity)
3. If max_sim > 0.85: Article is redundant → Skip or mark low priority
4. If max_sim < 0.85: Calculate delta_score = 1 - max_sim
5. Return: Article with delta_score (0.0-1.0) indicating novelty
```

**Output Formats:**
- Structured text digest
- Audio Brief (TTS) for commute consumption
- Bullet-point executive summary

---

#### MODULE 2: LIBRARY (AI-Enhanced Document Reader)
**Purpose:** Maximize comprehension and retention from long-form content

**Core Features:**

| Feature | Specification | Technical Approach |
|---------|---------------|-------------------|
| Universal Parser | PDF, EPUB, DOCX, HTML | Cloud OCR (Azure Document Intelligence) for complex PDFs |
| Semantic Chunking | Split by topic boundaries, not arbitrary token counts | Sentence embedding similarity drops <0.75 |
| Navigation Heatmap | Visual indicator of concept novelty per section | Compare against user's Knowledge Graph |
| Query Interface | Natural language questions against document | RAG with citation highlighting |
| Cross-Reference | Find connections to user's library | Graph traversal on entity extraction |

**Semantic Chunking Algorithm:**
```
1. Split document into paragraphs
2. Generate embeddings for each paragraph (3072-dim)
3. Calculate cosine similarity between consecutive paragraphs
4. If similarity < 0.75 → Insert chunk boundary
5. Merge small chunks (<100 words) with neighbors
6. Store chunks as "Knowledge Atoms" with metadata
```

**Reader Interface Requirements:**
- Split-pane: Document left, AI insights right
- Hover citations: Show source evidence on demand
- Highlight persistence: Sync across devices via CRDT

---

#### MODULE 3: LAB (Agentic Report Generator)
**Purpose:** Autonomous research and synthesis on user's behalf

**Core Features:**

| Feature | Specification | Technical Approach |
|---------|---------------|-------------------|
| Scout Agent | Proactive research on scheduled topics | Cron-triggered agent with search APIs |
| Source Coverage | Monitor 20-50 sources per report | Configurable whitelist per agent |
| Pattern Detection | Identify trends across sources | Clustering + temporal analysis |
| Report Templates | Weekly sector brief, Monthly trend report, Quarterly deep-dive | Prompt templates with user customization |
| Claim Verification | Cross-check assertions against sources | Extract-compare-highlight pipeline |

**Scout Agent Workflow:**
```
Trigger: Scheduled (e.g., Fridays 8 AM) or User Command

Phase 1: Ingest
- Fetch all content from configured sources (last 7 days)
- Run through Librarian pipeline (parse → chunk → embed)

Phase 2: Filter
- Apply user-defined exclusion keywords
- Filter by relevance to topic (vector similarity >0.70)
- Remove duplicates (similarity >0.90)

Phase 3: Analysis
- Extract key claims (named entity recognition + dependency parsing)
- Identify contradictions between sources
- Detect emerging patterns (frequency analysis)

Phase 4: Synthesis
- Generate structured report (Markdown)
- Include: Summary, Key Developments, Contradictions, Source Links
- Apply user style preferences (length, tone, detail level)

Phase 5: Delivery
- Email to user with PDF attachment
- Store in Library with full provenance
```

---

## 3. Technical Architecture

### 3.1 Cloud-First Infrastructure

**Constraint Compliance:** NO local/edge AI. All inference in cloud for reliability and cost control.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Web App   │  │   Desktop   │  │      Mobile App         │ │
│  │  (React)    │  │   (Tauri)   │  │   (React Native)        │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
└─────────┼────────────────┼─────────────────────┼───────────────┘
          │                │                     │
          └────────────────┴──────────┬──────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API GATEWAY (Kong/AWS)                     │
│         • Rate limiting • Authentication • Request routing       │
└─────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
│   INGESTION     │        │    CORE API     │        │   AGENT ENGINE  │
│    SERVICE      │        │   (FastAPI)     │        │   (Celery/      │
│   (Python)      │        │                 │        │   RabbitMQ)     │
│                 │        │                 │        │                 │
│ • Document      │        │ • User mgmt     │        │ • Scout tasks   │
│   parsing       │        │ • Library CRUD  │        │ • Report gen    │
│ • OCR pipeline  │        │ • Search API    │        │ • Scheduling    │
│ • Transcription │        │ • Billing       │        │                 │
└────────┬────────┘        └────────┬────────┘        └────────┬────────┘
         │                          │                          │
         └──────────────────────────┴──────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   VECTOR DB     │      │   GRAPH DB      │      │   RELATIONAL    │
│  (Pinecone/     │      │   (Neo4j)       │      │     DB          │
│   Qdrant)       │      │                 │      │  (PostgreSQL)   │
│                 │      │                 │      │                 │
│ • 3072-dim      │      │ • Entities      │      │ • User data     │
│   embeddings    │      │ • Relationships │      │ • Billing       │
│ • Metadata      │      │ • Citation      │      │ • Job queues    │
│   filtering     │      │   graphs        │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI MODEL LAYER                              │
│                                                                  │
│  Tier 1 (Fast/Cheap):    Tier 2 (Balanced):    Tier 3 (Deep):   │
│  • Gemini Flash          • GPT-4o              • Claude 3.5     │
│  • Claude Haiku          • Mistral Large       Sonnet           │
│  • Mistral Small         • Gemini 1.5 Pro      • GPT-4o         │
│                            ($0.50-2/M tokens)  ($3-15/M tokens) │
│  ($0.10-0.50/M tokens)                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 AI Cost Management Protocol

**The Agentic Router:**
All AI requests pass through a classification layer:

```python
class AgenticRouter:
    """Routes requests to appropriate model tier based on complexity and budget."""
    
    def route(self, query: str, user_budget_remaining: float) -> ModelTier:
        # Budget guardrail
        if user_budget_remaining < 0.10:
            return ModelTier.LOCAL_FALLBACK  # Return error or cached response
        
        # Rule-based heuristics (zero latency)
        if self._is_simple_summary(query):
            return ModelTier.FAST  # Gemini Flash
        
        if self._contains_keywords(query, ["analyze", "compare", "verify", "contradiction"]):
            return ModelTier.REASONING  # GPT-4o/Claude
        
        if self._is_research_task(query):
            return ModelTier.DEEP_RESEARCH  # Claude 3.5 Sonnet + search tools
        
        # Default fallback
        return ModelTier.BALANCED
```

**Cost Allocation per User Tier:**

| Tier | Monthly Price | AI Budget | Coverage |
|------|--------------|-----------|----------|
| Starter | $15 | $2.00 | 200 briefs OR 20 reports |
| Professional | $30 | $5.00 | 500 briefs OR 50 reports |
| Enterprise | $75 | $15.00 | Unlimited reports |

### 3.3 Data Models

#### Knowledge Atom (Core Unit)
```json
{
  "atom_id": "uuid-v4",
  "source_id": "document-reference",
  "content_hash": "sha256-of-text",
  "raw_text": "string (max 2000 chars)",
  "embedding_vector": [3072 floats],
  "metadata": {
    "chunk_index": 0,
    "position": {"start": 0, "end": 1500},
    "semantic_density": 0.85,
    "entities": ["entity-1", "entity-2"]
  },
  "truth_state": {
    "status": "verified|disputed|retracted|unknown",
    "confidence": 0.92,
    "sources": ["source-id-1", "source-id-2"]
  },
  "user_context": {
    "novelty_score": 0.75,
    "read_status": "unread|skimmed|read",
    "notes": ["note-uuid"]
  }
}
```

#### Document Entity
```json
{
  "entity_id": "uuid",
  "entity_type": "person|organization|concept|molecule|event",
  "canonical_name": "string",
  "aliases": ["string"],
  "first_seen": "iso-timestamp",
  "mentions": ["atom-id-1", "atom-id-2"],
  "relationships": [
    {"target": "entity-x", "type": "cites|contradicts|supports|related"}
  ]
}
```

#### Scout Report
```json
{
  "report_id": "uuid",
  "user_id": "uuid",
  "scout_config": {
    "name": "Climate Tech Weekly",
    "sources": ["feed-1", "feed-2", "feed-3"],
    "schedule": "0 8 * * 5",
    "template": "weekly-brief"
  },
  "generated_at": "iso-timestamp",
  "content": {
    "summary": "markdown",
    "sections": [
      {"title": "Key Developments", "content": "..."},
      {"title": "Contradictions Found", "content": "..."}
    ],
    "sources": ["source-1", "source-2"],
    "citations": [{"claim": "...", "source": "..."}]
  },
  "delivery_status": "pending|sent|failed"
}
```

---

## 4. User Journeys

### 4.1 Primary Persona: Research Analyst (Sarah)

**Demographics:** 32, works at mid-size VC firm, follows 40+ sources, overwhelmed by volume

**Journey 1: Morning Brief**
```
8:00 AM - Receives "Daily Brief" email with 8 key stories (filtered from 200 sources)
8:05 AM - Skims on phone during commute (audio option available)
8:30 AM - Opens Genio web app at desk
8:32 AM - Clicks on story about battery tech, sees "The Diff" showing what's new
8:35 AM - Saves to Library for deeper reading
```

**Journey 2: Deep Research**
```
2:00 PM - Opens 50-page industry report in Library
2:05 PM - Asks: "Compare market share projections in this doc vs. Q3 report"
2:07 PM - System shows side-by-side table with citations
2:15 PM - Highlights contradictory claims
2:20 PM - Exports annotated report to share with team
```

**Journey 3: Scout Automation**
```
Friday 8:00 AM - Receives automated "Climate Tech Weekly" report
Friday 8:15 AM - Reviews synthesized findings from 30 sources
Friday 8:30 AM - Clicks on interesting claim, jumps to source evidence
Friday 9:00 AM - Forwards report to investment committee
```

### 4.2 Secondary Persona: Academic Researcher (Dr. Chen)

**Use Case:** Literature review acceleration
- Uploads 100 papers
- Asks Scout to find contradictions in methodology
- Generates matrix comparing sample sizes across studies
- Exports formatted citations

---

## 5. Success Metrics

### 5.1 North Star Metric
**Knowledge Velocity:** Number of high-signal insights consumed per unit time
- Proxy metric: Daily active users opening Daily Brief + Time spent in Library

### 5.2 Key Performance Indicators

| Metric | Target | Measurement |
|--------|--------|-------------|
| Daily Active Users (DAU) | 40% of MAU | Analytics |
| Avg. Session Duration | 12+ minutes | Analytics |
| Knowledge Delta Coverage | >80% novel content | Algorithm monitoring |
| Report Generation Success | >95% | Job tracking |
| User Retention (Month 3) | >60% | Cohort analysis |
| AI Cost per User | <$6/month | Cost monitoring |
| Net Promoter Score | >40 | Surveys |

### 5.3 Quality Gates

**Daily Brief Quality:**
- Zero duplicates (verified via similarity check)
- 100% of claims linkable to source
- Read time <10 minutes for full brief

**Library Experience:**
- Document ingestion <30 seconds per 100 pages
- Query response <3 seconds
- Citation accuracy >99%

**Scout Reports:**
- All claims with source attribution
- Hallucination rate <0.1% (verified via sampling)
- Coverage: >90% of configured sources scanned

---

## 6. Business Model & Unit Economics

### 6.1 Pricing Tiers

| Feature | Starter $15/mo | Pro $30/mo | Enterprise $75/user/mo |
|---------|---------------|------------|----------------------|
| Sources | 20 feeds | Unlimited | Unlimited + API |
| Daily Brief | 1 per day | 3 per day | Unlimited |
| Library Storage | 1 GB | 10 GB | Unlimited |
| Scout Reports | 5/month | 20/month | Unlimited + Custom |
| AI Budget | $2/month | $5/month | Custom |
| Support | Email | Priority | Dedicated |

### 6.2 Unit Economics (Per Professional Tier User)

**Monthly COGS Breakdown:**
```
Storage (10GB Vector DB):        $0.33
Compute (Daily Brief batch):     $0.45
AI Inference (avg usage):        $3.50
API Calls (search/embedding):    $0.80
Bandwidth/CDN:                   $0.20
──────────────────────────────────────
Total COGS:                      $5.28

Revenue:                         $30.00
Gross Margin:                    82.4%
```

### 6.3 Cost Optimization Strategies

1. **Shared Ingestion:** Process popular feeds once, serve to all users
2. **Tiered Caching:** Hot content in Redis (1hr), warm in vector DB, cold in S3
3. **Model Downgrading:** Route 80% of queries to fast/cheap models
4. **Batch Processing:** Aggregate Scout jobs during low-demand hours

---

## 7. Risk Analysis & Mitigation

### 7.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| AI API cost spike | Medium | High | Budget caps, model fallbacks, caching |
| Vector DB performance | Low | High | Partitioning, HNSW indexing, read replicas |
| Hallucination in reports | Medium | Critical | Source attribution, human verification loop |
| Data loss | Low | Critical | Multi-region backups, CRDT sync |

### 7.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Big Tech competition | High | Medium | Focus on workflow integration, not just features |
| Copyright claims | Medium | High | BYOL model, no content redistribution |
| Enterprise sales cycle | High | Medium | Land with teams, expand to org |

---

## 8. Compliance & Security

### 8.1 Data Privacy
- SOC 2 Type II certification required
- GDPR compliant (EU users)
- End-to-end encryption for sensitive documents
- Zero-knowledge option for Enterprise (client holds keys)

### 8.2 Content Rights
- User must own or have license to uploaded content
- No redistribution of full-text content
- Fair use for transformative summaries
- Publisher partnership program for authenticated access

---

## 9. Appendix

### 9.1 Glossary
- **Knowledge Atom:** Minimum unit of semantic information
- **Knowledge Delta:** Novelty score indicating new information vs. user's existing knowledge
- **Scout:** Autonomous research agent
- **Librarian:** Content ingestion and organization agent
- **Daily Brief:** Automated digest of curated content
- **The Diff:** Highlighting unique information across sources

### 9.2 Technology Stack Summary

| Component | Technology | Justification |
|-----------|------------|---------------|
| Backend API | Python/FastAPI | AI ecosystem, rapid development |
| Frontend | React + TypeScript | Type safety, component reusability |
| Desktop | Tauri v2 | Native performance, small bundle size |
| Vector DB | Qdrant/Pinecone | Managed service, scalable |
| Graph DB | Neo4j | Relationship traversal, Cypher queries |
| Relational DB | PostgreSQL | Proven, JSON support |
| Cache | Redis | Sub-millisecond response |
| Queue | Celery + RabbitMQ | Reliable task processing |
| AI Gateway | LiteLLM | Model abstraction, cost tracking |
| Hosting | AWS/GCP | Enterprise compliance |

### 9.3 API Integrations

**Required:**
- OpenAI API (GPT-4o, GPT-4o-mini)
- Anthropic API (Claude 3.5 Haiku/Sonnet)
- Google Gemini API
- Pinecone/Qdrant Vector DB
- PostgreSQL

**Optional:**
- Serper/Tavily (web search)
- Firecrawl (web scraping)
- ElevenLabs (TTS for audio briefs)
- Zotero API (academic workflow)

---

**Document Control:**
- Author: Product Strategy Team
- Reviewers: Engineering Lead, CFO, Legal
- Next Review: Post-MVP Launch
- Distribution: Internal Only
