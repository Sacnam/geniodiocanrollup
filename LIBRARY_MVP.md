# Genio Knowledge OS — Library Module
## MVP Specification — v1.0
**Version:** 1.0  
**Date:** February 2026  
**Module:** LIBRARY (Augmented Reading & Knowledge Construction)  
**Timeline:** 18 Weeks (Weeks 19-36)  
**Prerequisite:** Stream MVP deployed and stable

> [!NOTE]
> This document defines **scope and acceptance criteria only** for the Library MVP. Architecture and features → `LIBRARY_PRD.md`. Sprint tasks → `LIBRARY_IMPLEMENTATION_PLAN.md`. Platform NFRs → `GENIO_PRD_UNIFIED.md`.

---

## 1. MVP Feature Selection Rationale

The Library MVP targets the highest-impact features that solve the core problem: **reducing cognitive overload when reading dense, long-form documents.**

| Criterion (Weight) | Document Ingest | Concept Map | Cross-Doc Reasoning | Scout Agent |
|----|----|----|-----|-----|
| Immediate user value (25%) | 9 | 9 | 7 | 6 |
| Technical feasibility (20%) | 8 | 7 | 5 | 4 |
| Dependency on Stream infra (15%) | 9 | 7 | 7 | 3 |
| Differentiation (20%) | 7 | 9 | 8 | 9 |
| AI cost efficiency (10%) | 8 | 7 | 5 | 3 |
| Data moat building (10%) | 9 | 9 | 8 | 7 |
| **Weighted Score** | **8.35** | **8.15** | **6.50** | **5.10** |

**Decision:** Library MVP includes Document Ingestion + Concept Map + Augmented Reader. Cross-document reasoning included as P1 feature. Scout Agent deferred to Lab module (v3.0).

---

## 2. Feature Scope

### In-Scope (14 Features)

| # | Feature | Priority | Sprint |
|---|---------|----------|--------|
| L01 | Document upload (EPUB, PDF, DOCX) | P0 | S1 |
| L02 | Format detection + Markdown conversion | P0 | S1 |
| L03 | Semantic Chunking (cosine-boundary) | P0 | S1-S2 |
| L04 | Batch embedding generation (1536-dim, shared infrastructure) | P0 | S2 |
| L05 | Document-level Knowledge Delta scoring | P0 | S2 |
| L06 | Graph extraction (entity + relationship triples) | P0 | S2-S3 |
| L07 | PKG storage (PostgreSQL JSONB) | P0 | S3 |
| L08 | Augmented TOC (concept density heatmap) | P0 | S3-S4 |
| L09 | Document Reader (full-text, chapter navigation, reading progress) | P0 | S3-S4 |
| L10 | Dynamic Concept Map (D3.js interactive graph) | P0 | S4-S5 |
| L11 | Non-Linear Navigation (concept → aggregate mentions) | P1 | S5-S6 |
| L12 | JIT Context Injection (hover → micro-summary overlay) | P1 | S6 |
| L13 | Semantic Zoom (3-level detail: summary/theses/full) | P1 | S6-S7 |
| L14 | Cross-document query (hybrid vector + graph search) | P1 | S7-S8 |

### Deferred (Post-Library-MVP)

| Feature | Target Version | Reason |
|---------|---------------|--------|
| Liquid Output (chapter → checklist/timeline) | v2.5 | Lower priority for MVP |
| Scout Agent (verify, counter-arguments) | v3.0 | Lab module dependency |
| CRDT sync (multi-device reading state) | v2.5 | Complexity |
| Chart Transducer (chart images → data tables) | v2.5 | Specialized ML pipeline |
| Formula Engine (LaTeX extraction) | v2.5 | Niche use case |
| Voice annotations | v3.0 | Audio pipeline |
| Semantic Density Filter (dim low-density text) | v2.5 | UX refinement |

---

## 3. Acceptance Criteria

### L01: Document Upload
```gherkin
GIVEN an authenticated user
WHEN they upload a PDF file (<100 MB, <1000 pages)
THEN the file is stored in S3/Supabase Storage
AND a document record is created with status='uploaded'
AND processing is queued as a background task

GIVEN an authenticated user with 50 documents (Starter tier)
WHEN they attempt to upload another document
THEN the upload is rejected with "Document limit reached" message
AND an upgrade prompt is shown
```

### L02: Format Detection + Conversion
```gherkin
GIVEN an uploaded EPUB file
WHEN the parser processes it
THEN chapters, headings, and paragraph structure are preserved in Markdown
AND images are extracted and stored separately

GIVEN an uploaded multi-column PDF
WHEN the parser processes it
THEN text is extracted in reading order (not column order)
AND tables are converted to Markdown tables
AND processing_status transitions to 'parsed'

GIVEN a corrupted or password-protected PDF
WHEN parsing fails
THEN processing_status is set to 'parse_failed'
AND the user is notified with the failure reason
```

### L03: Semantic Chunking
```gherkin
GIVEN a parsed document with 500 sentences
WHEN semantic chunking runs
THEN the document is split into Knowledge Atoms at topic boundaries
AND each atom contains 100-2000 characters
AND no atom splits mid-sentence
AND each atom has: {chunk_index, chapter_ref, semantic_density}

GIVEN a document with uniform topic (no clear boundaries)
WHEN chunking runs with default threshold (k=1.5)
THEN atoms are created at fixed 500-word intervals as fallback
```

### L04: Batch Embedding
```gherkin
GIVEN 100 Knowledge Atoms from a document
WHEN embedding generation runs
THEN a single batch API call generates 100 embeddings (1536-dim)
AND all embeddings are stored in Qdrant with metadata {atom_id, doc_id, chapter}
AND the total API cost is tracked per user via LiteLLM

GIVEN an atom whose content_hash already exists in Qdrant
WHEN processing encounters it
THEN no new embedding is generated (reuse existing)
```

### L05: Document-Level Knowledge Delta
```gherkin
GIVEN a new document with 300 atoms
WHEN Knowledge Delta runs against the user's PKG
THEN each atom receives a delta_score (0.0-1.0)
AND the document receives a novelty_score = mean(high-density atom deltas)

GIVEN a document with novelty_score < 0.15
THEN the user sees "This document is mostly familiar to you (85% overlap)"
AND redundant chapters are flagged in the Augmented TOC

GIVEN a document with novelty_score > 0.70
THEN the user sees "This document contains significant new material"
AND novel concepts are highlighted in the Concept Map
```

### L06: Graph Extraction
```gherkin
GIVEN 10 Knowledge Atoms batched for extraction
WHEN the LLM processes them
THEN it returns (Subject, Predicate, Object) triples with confidence scores
AND each triple is validated: subject ≠ object, predicate ∈ allowed set

GIVEN an extracted entity "Bayesian Priors"
WHEN entity resolution runs against existing PKG
THEN IF cosine_sim > 0.90 with existing node → MERGE
AND IF cosine_sim < 0.90 → CREATE new node

GIVEN an extraction that returns >50 triples for a 10-atom batch
THEN only the top 50 by confidence are retained (noise filter)
```

### L07: PKG Storage
```gherkin
GIVEN a user's PKG with 500 concept nodes
WHEN a graph query requests "all concepts DEPENDS_ON 'Inflation'"
THEN the query returns results in <100ms via PostgreSQL recursive CTE

GIVEN a user uploads a new document
WHEN graph extraction completes
THEN new nodes/edges are merged into the existing PKG
AND node counts and relationship counts are updated
```

### L08: Augmented TOC
```gherkin
GIVEN a document with 12 chapters
WHEN the Augmented TOC renders
THEN each chapter shows: title, atom count, average semantic density
AND a heatmap color (green=high density, gray=low density) is applied
AND chapters with mean delta_score < 0.15 are labeled "(mostly known)"

GIVEN a user clicks a chapter in the Augmented TOC
THEN the reader scrolls to that chapter
AND reading_progress is updated
```

### L09: Document Reader
```gherkin
GIVEN an authenticated user opening a document
WHEN the reader loads
THEN full text renders with chapter navigation sidebar
AND current reading position is restored from last session
AND a progress bar shows % of document read

GIVEN a user reads to the end of Chapter 5
WHEN they close the reader
THEN reading_state is saved: {last_chapter: 5, last_atom: 142, progress: 0.42}

GIVEN a user highlights text in the reader
THEN the highlight is stored with: {atom_id, start_offset, end_offset, color, note}
```

### L10: Dynamic Concept Map
```gherkin
GIVEN a document with 80 extracted concepts
WHEN the Concept Map renders
THEN nodes are displayed with color-coding: 🟢 Known, 🟡 Gap, 🔴 Contradiction
AND edges show relationship types (DEPENDS_ON, SUPPORTS, CONTRADICTS)
AND the layout uses force-directed graph (D3.js)

GIVEN a user clicks a concept node in the map
THEN the reader reflows to show all atoms containing that concept
AND the concept is highlighted in context

GIVEN a concept node is marked as "Gap" (not in user PKG)
WHEN the user hovers over it
THEN a tooltip shows: concept name, definition preview, "Learn more" link
```

### L11: Non-Linear Navigation
```gherkin
GIVEN a user clicks concept "Inflation" in the Concept Map
WHEN navigation triggers
THEN all atoms containing "Inflation" are aggregated into a continuous stream
AND atoms are ordered by position in document
AND the stream renders in <1 second

GIVEN a user in Non-Linear view clicks "Return to linear"
THEN the reader restores the original document flow
AND cursor position returns to the atom they were reading
```

### L12: JIT Context Injection
```gherkin
GIVEN a user hovers over term "Bayesian Priors" for >500ms
WHEN the system checks the user's PKG
THEN IF user KNOWS "Bayesian Statistics" → no overlay (assume knowledge)
AND IF user does NOT KNOW → generate micro-summary overlay via LLM
AND the overlay explains the term in the context of the current sentence

GIVEN a JIT overlay is generated
THEN it is cached in Redis for 24h (same term, same document context)
AND cost is tracked against user's AI budget
```

### L13: Semantic Zoom
```gherkin
GIVEN a chapter with 40 atoms
WHEN user selects Zoom Level 1 (Summary)
THEN only the chapter summary (1-2 paragraphs) is shown

WHEN user selects Zoom Level 2 (Key Theses)
THEN only atoms with semantic_density > 0.7 are shown
AND low-density atoms are collapsed with "[expand]" markers

WHEN user selects Zoom Level 3 (Full Text)
THEN all atoms are shown (default view)
```

### L14: Cross-Document Query
```gherkin
GIVEN a user with 5 documents in their library
WHEN they query "How does Author A's view on inflation compare to Author B's?"
THEN the system performs:
  1. Vector search across all user's atoms (Qdrant, k=20)
  2. Graph traversal: find concepts related to "inflation" in PKG (2-hop)
  3. Reciprocal Rank Fusion of results
  4. LLM synthesis: generate comparative answer with citations

GIVEN a cross-document query
THEN the response includes inline citations: [Doc Title, Chapter, Atom ID]
AND response time is <5 seconds
```

---

## 4. Unit Economics

> [!NOTE]
> Full cost model → `LIBRARY_PRD.md` §4. Summary below for MVP context.

| Component | Cost/User/Month |
|-----------|----------------|
| Document ingestion (10 docs × $0.045) | $0.45 |
| Reading sessions (30 × $0.010) | $0.30 |
| Embedding storage (Qdrant, incremental) | $0.15 |
| Document file storage (S3) | $0.10 |
| Graph queries (PostgreSQL) | $0.05 |
| **Total Library COGS** | **$1.05** |

| Tier | Revenue | Stream COGS | Library COGS | Total COGS | Margin |
|------|---------|-------------|-------------|------------|--------|
| Starter ($15) | $15.00 | $2.03 | $1.05 | $3.08 | **79.5%** |
| Professional ($30) | $30.00 | $2.03 | $1.05 | $3.08 | **89.7%** |
| Enterprise ($75) | $75.00 | $2.03 | $1.05 | $3.08 | **95.9%** |

---

## 5. Milestone Gates

Each milestone is a **binary pass/fail** gate. All criteria must pass.

| Gate | Week | Criteria |
|------|------|----------|
| **L-M1: Parser Pipeline** | W20 | 3 formats parsed (EPUB+PDF+DOCX), Markdown output correct, files stored |
| **L-M2: Semantic Engine** | W22 | Atoms generated, embeddings stored, delta scores computed |
| **L-M3: Knowledge Graph** | W24 | Triples extracted, PKG nodes/edges created, entity resolution working |
| **L-M4: Reader + TOC** | W28 | Full document renders, Augmented TOC with heatmap, reading progress saved |
| **L-M5: Concept Map** | W30 | Interactive D3.js graph, click→navigate, gap/known coloring |
| **L-M6: Intelligence** | W32 | JIT overlays, Semantic Zoom, Non-Linear Navigation, cross-doc query |
| **L-M7: Integration** | W34 | Full E2E, budget tracking, settings, API integration tests |
| **L-M8: Launch** | W36 | Load test passed, beta feedback integrated, Library module live |

---

*Library MVP Spec v1.0. SSOT for scope and acceptance criteria. Architecture → `LIBRARY_PRD.md`. Tasks → `LIBRARY_IMPLEMENTATION_PLAN.md`.*
