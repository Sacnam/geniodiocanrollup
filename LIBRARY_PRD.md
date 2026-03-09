# Genio Knowledge OS — Library Module
## Product Requirements Document (PRD) — v1.0
**Version:** 1.0  
**Date:** February 2026  
**Status:** Implementation-Ready  
**Prerequisite:** Stream MVP (v2.1) deployed and stable  
**Parent PRD:** `GENIO_PRD_UNIFIED.md` (platform architecture, NFRs, business model)

> [!NOTE]
> This document specifies the **Library module only**. Platform-wide architecture, tech stack, and non-functional requirements → `GENIO_PRD_UNIFIED.md`. Stream module → `GENIO_MVP_UNIFIED.md`.

---

## Executive Summary

### Module Vision
The Library module transforms Genio from a feed aggregator into an **Augmented Reading and Knowledge Construction platform**. It ingests long-form documents (EPUB, PDF, DOCX), builds a Personal Knowledge Graph (PKG) per user, and provides AI-powered cognitive scaffolding that reduces extraneous cognitive load to near-zero.

### Core Value Proposition
**"From Passive Reading to Active Knowledge Construction"**

### Strategic Positioning

| Aspect | Specification |
|--------|---------------|
| **Target Users** | Researchers, analysts, PhD students, consultants, lifelong learners |
| **Input Formats** | EPUB, PDF, DOCX, Markdown, HTML (long-form) |
| **Core IP** | Semantic Chunking + GraphRAG + Dynamic Concept Maps + Knowledge Delta |
| **Competitive Moat** | Personal Knowledge Graph with cross-document reasoning |
| **North Star Metric** | Comprehension Velocity — concepts mastered per unit time |
| **Timeline** | Weeks 19-36 (post-Stream v1.5) |

---

## 1. Problem Analysis

| Dimension | Quantification | Impact |
|-----------|----------------|--------|
| **Activation Energy** | 70% abandon dense non-fiction within 50 pages | Lost learning potential |
| **Cognitive Overload** | Working memory holds ~4 chunks simultaneously | Comprehension failure on dense text |
| **Format Lock-in** | PDFs, EPUBs render text but offer zero structural support | Passive consumption |
| **Information Silos** | Knowledge trapped in individual documents | No cross-document reasoning |
| **Redundancy** | 60-80% overlap across related books/papers | Wasted reading time |

### Design Principle

> [!IMPORTANT]
> **Extraneous Cognitive Load → 0.** The Library's entire architecture targets reducing extraneous load (effort of processing presentation) while maximizing germane load (effort of learning and schema construction). Every feature must pass the test: "Does this free working memory for understanding?"

---

## 2. Module Architecture

### System Context

```
┌─────────────── GENIO KNOWLEDGE OS ───────────────┐
│                                                    │
│   STREAM (v1.0)    LIBRARY (v2.0)    LAB (v3.0)  │
│   ┌──────────┐    ┌──────────────┐   ┌─────────┐ │
│   │ Feed     │    │ Document     │   │ Scout   │ │
│   │ Ingest   │    │ Ingest +     │   │ Agent + │ │
│   │ + Brief  │    │ Reader +     │   │ Reports │ │
│   │          │    │ Concept Maps │   │         │ │
│   └────┬─────┘    └──────┬───────┘   └────┬────┘ │
│        │                 │                │       │
│        ▼                 ▼                ▼       │
│   ┌──────────────────────────────────────────┐   │
│   │       SHARED KNOWLEDGE LAYER              │   │
│   │  PostgreSQL │ Qdrant │ Redis │ LiteLLM   │   │
│   │  Knowledge Atoms │ PKG │ Delta Scoring    │   │
│   └──────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

> [!TIP]
> The Library module **reuses the shared infrastructure** deployed for Stream (PostgreSQL, Qdrant, Redis, LiteLLM). New components: Document Parser pipeline, PKG graph layer, Reader UI.

### Core Components

| Component | Purpose | New/Reused |
|-----------|---------|------------|
| Document Parser | EPUB/PDF/DOCX → Markdown + semantic structure | **NEW** |
| Semantic Chunker | Cosine-boundary chunking into Knowledge Atoms | **NEW** |
| Graph Extractor | Entity + relationship extraction → PKG | **NEW** |
| Knowledge Delta | Per-user novelty scoring against PKG | EXTENDED from Stream |
| Concept Map Engine | Dynamic dependency graph visualization | **NEW** |
| Liquid Text Renderer | Adaptive UI (Augmented TOC, Semantic Zoom) | **NEW** |
| Qdrant (vectors) | Embedding storage + semantic search | REUSED |
| PostgreSQL | Document metadata, user state, reading progress | REUSED |
| Redis | Hot-tier caching for active documents | REUSED |
| LiteLLM | AI gateway for extraction + summarization | REUSED |

---

## 3. Core Features — Detailed Specification

### 3.1 Document Ingestion Pipeline

```
PIPELINE: Document Ingestion (Library)

INPUT:  file (EPUB/PDF/DOCX) OR URL (long-form HTML)
OUTPUT: {document_id, atoms[], graph_nodes[], embeddings[]}

1. FORMAT DETECTION
   → EPUB:  epublib parser → Markdown (preserves chapters, headings)
   → PDF:   Unstructured.io / marker-pdf → Markdown (preserves tables, layout)
   → DOCX:  python-docx → Markdown (preserves structure)
   → HTML:  Readability → Markdown (extract article body)

2. SEMANTIC CHUNKING (see §3.2)
   → text → Knowledge Atoms (coherent semantic units)

3. GRAPH EXTRACTION (see §3.3)
   → atoms → entities + relationships → PKG nodes/edges

4. EMBEDDING GENERATION
   → atoms → batch embed (1536-dim, text-embedding-3-small)
   → store in Qdrant with metadata: {atom_id, doc_id, chapter, position}

5. NOVELTY SCORING (reuses Knowledge Delta from Stream)
   → per atom: delta_score against user's existing PKG

6. INDEX CONSTRUCTION
   → Augmented TOC with concept density heatmap
   → Chapter-level summary (Gemini Flash)
```

> [!IMPORTANT]
> PDF parsing uses layout-aware extraction (Unstructured.io or marker-pdf). Multi-column PDFs, embedded charts, and formulas are preserved as structured Markdown. Charts are extracted as data tables where possible.

### 3.2 Semantic Chunking Algorithm

```
ALGORITHM: Semantic Chunking (Cosine-Boundary)

INPUT:  sentences[] from document
OUTPUT: atoms[] (coherent semantic units)

1. FOR i IN range(1, len(sentences)):
     embed[i] = embed_model(sentences[i])

2. FOR i IN range(1, len(sentences)):
     similarity[i] = cosine_sim(embed[i-1], embed[i])

3. threshold = mean(similarity) - k * std(similarity)
   // k=1.5 default; dynamic per document density

4. FOR i IN range(1, len(sentences)):
     IF (1 - similarity[i]) > threshold:
       PLACE chunk boundary at position i

5. POST-PROCESS:
     - Merge chunks < 100 chars into neighbors
     - Split chunks > 2000 chars at nearest sentence boundary
     - Tag each atom: {chunk_index, semantic_density, chapter_ref}

6. RETURN atoms[]
```

> Semantic density = Information Gain relative to document mean. High-density atoms introduce new graph nodes or modify relationships; low-density atoms are anecdotal/rhetorical.

### 3.3 Personal Knowledge Graph (PKG)

#### Graph Schema

```
NODES:
  Concept    {id, name, definition, source_docs[], confidence}
  Atom       {id, text, doc_id, chapter, embedding_id, density}
  Document   {id, title, author, format, ingested_at}
  User       {id, reading_history[], known_concepts[]}

EDGES:
  DEPENDS_ON   (Concept → Concept)      // logical dependency
  SUPPORTS     (Atom → Concept)         // evidence
  CONTRADICTS  (Concept ↔ Concept)      // conflict
  AUTHORED_BY  (Document → Author)
  CONTAINS     (Document → Atom)
  KNOWS        (User → Concept, {confidence, last_seen})
```

#### Graph Extraction Pipeline

```
ALGORITHM: Graph Extraction (per document)

INPUT:  atoms[] (from Semantic Chunker)
OUTPUT: graph_updates {new_nodes, new_edges, merged_nodes}

1. LLM EXTRACTION (Gemini Flash via LiteLLM):
   FOR batch IN chunk(atoms, size=10):
     prompt = "Extract (Subject, Predicate, Object) triples from these texts.
               Return JSON: [{subject, predicate, object, confidence}]"
     triples = llm.generate(prompt, batch)

2. ENTITY RESOLUTION:
   FOR triple IN triples:
     existing = qdrant.search(embed(triple.subject), k=5)
     IF max(existing.score) > 0.90:
       MERGE with existing node  // e.g., "Bayesian Priors" ≈ "Bayesian Prior"
     ELSE:
       CREATE new Concept node

3. EDGE CREATION:
   CREATE edge(subject_node, predicate, object_node)
   // predicates: DEPENDS_ON, SUPPORTS, CONTRADICTS, EXTENDS, EXEMPLIFIES

4. DELTA SCORING:
   FOR new_node IN graph_updates.new_nodes:
     IF NOT user.KNOWS(new_node):
       delta_score = 1.0 - max_similarity(new_node, user.known_concepts)
       flag_for_concept_map_highlight(new_node, delta_score)

5. RETURN graph_updates
```

### 3.4 Dynamic Concept Map

The Concept Map is the primary navigation interface for the Library module. It replaces pagination with semantic navigation.

#### Hierarchical Layers

| Layer | Content | Derived From |
|-------|---------|--------------|
| **Axiomatic Roots** | Fundamental premises the author builds upon | Graph nodes with 0 incoming DEPENDS_ON edges |
| **Derivative Theses** | Concepts logically dependent on roots | Graph traversal (1+ hops from roots) |
| **Supporting Evidence** | Data points, examples, citations | Atoms tagged as SUPPORTS |
| **User Knowledge Gaps** | Concepts not in user's PKG | Delta scoring against KNOWS edges |

#### Visualization Spec

```
CONCEPT MAP UI:

┌─────────────────────────────────────────────────┐
│  [Document Title]                                │
│                                                  │
│  ┌─────┐      ┌──────────┐      ┌──────────┐  │
│  │Root │──────│Thesis A  │──────│Evidence 1│  │
│  │(🟢) │      │(🟡 gap!) │      │(📊)      │  │
│  └─────┘      └────┬─────┘      └──────────┘  │
│                     │                           │
│               ┌─────▼─────┐                     │
│               │Thesis B   │                     │
│               │(🟢 known) │                     │
│               └───────────┘                     │
│                                                  │
│  Legend: 🟢 Known  🟡 Gap  🔴 Contradiction     │
└─────────────────────────────────────────────────┘

- Click concept → reflow document to show all mentions (Non-Linear Navigation)
- Hover gap → Just-in-Time contextual explanation overlay
- Edge labels show relationship type (DEPENDS_ON, CONTRADICTS, etc.)
```

### 3.5 Augmented Reader UI

| Feature | Specification | Technical Approach |
|---------|---------------|-------------------|
| **Augmented TOC** | Heatmap of concept density per chapter | Semantic density scores per atom, aggregated by chapter |
| **Semantic Zoom** | Expand/collapse text detail levels | 3 levels: summary → key theses → full text |
| **Liquid Output** | Transform chapter into checklist, timeline, or Q&A | LLM transformation via template prompts |
| **Non-Linear Navigation** | Click concept → aggregate all mentions | Qdrant search by concept embedding, ranked by position |
| **JIT Context Injection** | Hover unfamiliar term → micro-summary | Check user PKG; if KNOWS edge missing → generate overlay |
| **Reading Progress** | Per-chapter, per-concept tracking | PostgreSQL: user_reading_state table |
| **Highlights & Notes** | User annotations linked to PKG nodes | CRDT-compatible for future sync |
| **Semantic Density Filter** | Dim low-density text, highlight core theses | density_score threshold; collapsible anecdotal sections |

### 3.6 Knowledge Delta for Documents

The Knowledge Delta algorithm (from Stream) is extended for long-form documents:

```
ALGORITHM: Document-Level Knowledge Delta

INPUT:  new_document atoms[], user_pkg
OUTPUT: {document_novelty_score, novel_concepts[], redundant_chapters[]}

1. FOR atom IN atoms:
     atom.delta = compute_delta(atom.embedding, user_pkg, k=10)

2. document_novelty = mean(atom.delta FOR atom IN atoms WHERE atom.density > 0.5)

3. novel_concepts = [
     concept FOR concept IN extracted_concepts
     IF NOT user_pkg.KNOWS(concept) OR user_pkg.KNOWS(concept).confidence < 0.5
   ]

4. redundant_chapters = [
     chapter FOR chapter IN chapters
     IF mean(atom.delta FOR atom IN chapter.atoms) < 0.15
   ]

5. PRESENT to user:
   - "This book is 72% novel to you"
   - "Chapters 3, 7 contain mostly known material — consider skimming"
   - "12 new concepts identified — highlighted in Concept Map"
```

### 3.7 Cross-Document Reasoning (GraphRAG)

| Capability | Specification |
|-----------|---------------|
| **Multi-Document Query** | "How does Author A's argument relate to Author B's?" |
| **Query Method** | Hybrid: Qdrant vector search (broad) + PKG graph traversal (2-hop, structured) |
| **Result Fusion** | Reciprocal Rank Fusion of vector + graph results |
| **Contradiction Detection** | Automatic flagging when new CONTRADICTS edges are created |
| **Citation Chain** | Trace evidence path: Claim → Supporting Atom → Source Document |
| **Context Window** | Active document in long-context (128k tokens); PKG for global context |

---

## 4. Technical Architecture

### Document Processing Pipeline

```
┌──────────────────────────────────────────────────────────┐
│                   DOCUMENT INGESTION FSM                  │
│                                                           │
│ UPLOADED → PARSING → CHUNKING → EXTRACTING → EMBEDDING → │
│           (format)  (semantic)  (graph)      (vectors)    │
│                                                           │
│ → SCORING → INDEXING → READY                             │
│   (delta)   (TOC+map)                                     │
│                                                           │
│ Each stage has *_FAILED state + sweeper (max 3 retries)  │
└──────────────────────────────────────────────────────────┘
```

### Technology Stack (Library-Specific Additions)

| Component | Technology | Justification |
|-----------|-----------|---------------|
| PDF Parser | marker-pdf / Unstructured.io | Layout-aware; preserves tables, headings |
| EPUB Parser | ebooklib + BeautifulSoup | Standard EPUB processing |
| DOCX Parser | python-docx | Native DOCX support |
| Semantic Chunking | Custom (cosine-boundary) | Content-aware boundaries |
| Graph Storage | PostgreSQL (JSONB + recursive CTEs) | No new infra; graph queries via SQL |
| Graph Visualization | D3.js / React Flow | Interactive concept maps in browser |
| Concept Map | Server-side: LLM extraction; Client-side: D3.js | Dynamic, interactive |
| Reading State | PostgreSQL | Per-user, per-document, per-chapter |
| Document Storage | S3 / Supabase Storage | Original files preserved |

> [!IMPORTANT]
> **No Neo4j at MVP.** The PKG graph is stored in PostgreSQL using JSONB columns and recursive CTEs for traversal. This avoids introducing a new database. Migration to Neo4j is deferred to >10k users when graph query complexity exceeds PostgreSQL's comfort zone.

### Data Models

#### Document

```json
{
  "document_id": "uuid-v4",
  "user_id": "uuid-v4",
  "title": "string",
  "author": "string",
  "format": "epub|pdf|docx|html",
  "file_hash": "sha256",
  "file_url": "s3://...",
  "total_atoms": 450,
  "total_chapters": 12,
  "novelty_score": 0.72,
  "processing_status": "ready|parsing|chunking|...|failed",
  "ingested_at": "timestamp",
  "last_read_at": "timestamp"
}
```

#### Knowledge Atom (Extended from Stream)

```json
{
  "atom_id": "uuid-v4",
  "document_id": "uuid-v4",
  "content_hash": "sha256",
  "raw_text": "string (max 2000 chars)",
  "embedding_vector_id": "qdrant-point-id",
  "metadata": {
    "chunk_index": 15,
    "chapter_ref": "Chapter 3: Markets",
    "semantic_density": 0.85,
    "position_in_doc": 0.23,
    "entities": ["inflation", "monetary-policy"],
    "is_core_thesis": true
  },
  "delta_score": 0.78
}
```

#### PKG Node

```json
{
  "node_id": "uuid-v4",
  "user_id": "uuid-v4",
  "concept_name": "Bayesian Priors",
  "definition": "Prior probability distribution in Bayesian inference...",
  "source_atoms": ["atom-1", "atom-2"],
  "source_documents": ["doc-1"],
  "confidence": 0.85,
  "relationships": [
    {"target": "node-xyz", "type": "DEPENDS_ON", "confidence": 0.92},
    {"target": "node-abc", "type": "SUPPORTS", "confidence": 0.78}
  ],
  "user_knowledge_state": "known|gap|learning",
  "last_seen": "timestamp"
}
```

### AI Cost Management

#### Model Usage per Document (Power User)

| Operation | Frequency | Model | Tokens (In/Out) | Est. Cost |
|-----------|-----------|-------|-----------------|-----------|
| Semantic Chunking | 1× per doc (embed all sentences) | text-embedding-3-small | ~50k in | $0.001 |
| Graph Extraction | 1× per doc (batch of 10 atoms) | Gemini Flash | ~200k / 20k | $0.025 |
| Chapter Summaries | 1× per doc (12 chapters avg) | Gemini Flash | ~120k / 12k | $0.015 |
| Document Embedding | 1× per doc (450 atoms batched) | text-embedding-3-small | ~200k in | $0.004 |
| JIT Context Overlay | ~20× per reading session | Gemini Flash | ~20k / 5k | $0.005 |
| Liquid Output Transform | ~3× per session | Gemini Flash | ~30k / 10k | $0.005 |
| **Total per Document Ingest** | | | | **~$0.045** |
| **Total per Reading Session** | | | | **~$0.010** |

#### Monthly COGS (Power User: 10 docs + 30 sessions)

| Component | Cost |
|-----------|------|
| Document ingestion (10 × $0.045) | $0.45 |
| Reading sessions (30 × $0.010) | $0.30 |
| Embedding storage (Qdrant) | $0.15 |
| Document storage (S3) | $0.10 |
| Graph queries (PostgreSQL) | $0.05 |
| **Total Library COGS** | **$1.05** |

> [!TIP]
> Combined Stream + Library COGS: $2.03 + $1.05 = **$3.08/user/month**. At $30/mo Pro tier, gross margin remains **89.7%**.

### Graceful Degradation (Extends Stream B12)

| Budget Level | Library Behavior |
|-------------|-----------------|
| **L1: Full AI** (>50%) | Full graph extraction, JIT overlays, Liquid Output |
| **L2: Reduced AI** (20-50%) | Pre-computed summaries only, no JIT overlays, cached concept maps |
| **L3: No AI** (<20%) | Plain reader (TOC + text), no graph features, reading progress only |

---

## 5. Non-Functional Requirements (Library-Specific)

> Full NFR framework → `GENIO_PRD_UNIFIED.md` §5. Library-specific additions below.

### Performance

| Metric | Target |
|--------|--------|
| PDF parse + chunk (100-page) | <60 seconds |
| Graph extraction (100-page) | <120 seconds |
| Concept Map render | <2 seconds |
| JIT overlay response | <500ms |
| Non-Linear Navigation reflow | <1 second |
| Document search (across library) | <200ms |

### Scalability

| Dimension | Year 1 | Year 3 |
|-----------|--------|--------|
| Documents per user | 200 | 2,000 |
| PKG nodes per user | 5,000 | 50,000 |
| Cross-document queries | 100/day | 1,000/day |

### Document Limits

| Constraint | Limit |
|-----------|-------|
| Max file size | 100 MB |
| Max pages (PDF) | 1,000 |
| Max documents per user (Starter) | 50 |
| Max documents per user (Pro) | 500 |
| Max documents per user (Enterprise) | Unlimited |

---

## 6. Success Metrics

### North Star
**Comprehension Velocity** — concepts mastered per unit time

### KPIs

| Metric | Target | Method |
|--------|--------|--------|
| Documents completed (>80% read) | 3×  vs. baseline | Reading progress tracking |
| Concept Map interactions/session | >10 | Analytics |
| JIT overlay usage | >5/session | Analytics |
| Cross-document queries | >2/week | API logging |
| Knowledge Delta reduction | >30% after 3 months | PKG density growth |
| NPS (Library module) | >45 | Survey |
| Abandonment rate (dense docs) | <30% (vs. 70% baseline) | Cohort analysis |

---

## 7. Dual-Agent Architecture (Library Context)

### The Librarian (Inbound Agent)

| Responsibility | Specification |
|---------------|---------------|
| **Trigger** | Document upload or feed ingestion |
| **Actions** | Parse → Chunk → Extract Graph → Embed → Score Delta |
| **Write Authority** | Full write to Core PKG (user's library) |
| **Output** | Augmented TOC, Concept Map, Delta Summary, Weekly Briefing |

### The Scout (Outbound Agent) — Post-MVP

| Responsibility | Specification |
|---------------|---------------|
| **Trigger** | Explicit ("Scout, verify this") or Implicit (dwell detection on controversial claim) |
| **Actions** | Decompose query → Parallel search → Evaluate authority → Synthesize → Inject margin note |
| **Write Authority** | Periphery only (Suggestions/Notes layer, not Core PKG) |
| **Output** | Counter-Argument Cards, Margin Notes with citations |
| **Conflict Resolution** | If Scout finding contradicts Librarian's core record → flag for user resolution |

> [!WARNING]
> The Scout is **post-Library-MVP** (Lab module dependency). The Library MVP includes only the Librarian agent. Scout integration is planned for v3.0 (Lab module).

---

## 8. Risk Analysis (Library-Specific)

| Risk | Prob. | Impact | Mitigation |
|------|-------|--------|------------|
| PDF parsing quality (scanned/OCR) | High | High | Fallback to raw text; flag low-quality parses; user notification |
| Graph extraction hallucination | Medium | High | Verifier pass: re-check extracted triples against source atoms |
| Large document processing time | Medium | Medium | Background processing with progress bar; max 1000 pages |
| PKG graph explosion (too many nodes) | Medium | Medium | Pruning: merge low-confidence nodes; cap at 50k nodes/user |
| Cross-document query latency | Low | Medium | Pre-computed community summaries; indexed graph traversal |
| Copyright concerns (full text storage) | Medium | High | User-uploaded only (BYOL); no redistribution; encrypted at rest |

---

## 9. Implementation Roadmap

> **Detailed sprint breakdown → `LIBRARY_IMPLEMENTATION_PLAN.md`**

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Foundation + Parser | Weeks 19-20 | Document ingestion, format detection, Markdown conversion |
| Semantic Chunking + Embedding | Weeks 21-22 | Chunker, batch embedding, Delta scoring for docs |
| Graph Extraction + PKG | Weeks 23-24 | Entity extraction, graph storage, concept map data |
| Reader UI + Concept Map | Weeks 25-28 | Augmented TOC, Semantic Zoom, D3.js concept map |
| Intelligence + Navigation | Weeks 29-32 | JIT overlays, Non-Linear Nav, Liquid Output, cross-doc queries |
| Integration + Polish | Weeks 33-34 | Full E2E, budget integration, settings |
| Testing + Launch | Weeks 35-36 | Load test, beta, Library module goes live |

---

## 10. Glossary (Library-Specific)

| Term | Definition |
|------|------------|
| **Knowledge Atom** | Minimum unit of semantic information (coherent thought, ≤2000 chars) |
| **Personal Knowledge Graph (PKG)** | Per-user graph of concepts, relationships, and knowledge state |
| **Semantic Density** | Information Gain score: how much new knowledge an atom adds to the graph |
| **Concept Map** | Interactive visualization of PKG nodes and their dependencies |
| **Axiomatic Root** | A concept with no incoming DEPENDS_ON edges (foundational premise) |
| **Knowledge Gap** | A concept present in the document but absent from the user's PKG |
| **JIT Context Injection** | On-demand micro-explanation of unfamiliar terms, personalized to user's background |
| **Liquid Output** | AI-powered transformation of text into alternative formats (checklist, timeline, Q&A) |
| **Non-Linear Navigation** | Concept-first navigation: click a concept → aggregate all mentions across document |
| **Semantic Zoom** | Three-level text detail: summary → key theses → full text |

---

*Library PRD v1.0. SSOT for Library module vision, features, and architecture. Platform architecture → `GENIO_PRD_UNIFIED.md`. MVP scope → `LIBRARY_MVP.md`. Sprint tasks → `LIBRARY_IMPLEMENTATION_PLAN.md`.*
