# Genio Knowledge OS — Library Module
## Implementation Plan v1.0
**Version:** 1.0  
**Date:** February 2026  
**Timeline:** 18 Weeks (Weeks 19-36) — Backend + Frontend in Parallel  
**Prerequisite:** Stream MVP deployed and stable

> [!NOTE]
> This document defines **tasks and dependencies only**. Architecture → `LIBRARY_PRD.md`. Scope/criteria → `LIBRARY_MVP.md`. Platform NFRs → `GENIO_PRD_UNIFIED.md`.

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LIBRARY MODULE ARCHITECTURE                   │
│                                                                  │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ DOCUMENT │  │ SEMANTIC   │  │ GRAPH    │  │ READER UI    │ │
│  │ PARSER   │──│ CHUNKER    │──│ ENGINE   │──│ + CONCEPT    │ │
│  │ [W19-20] │  │ [W21-22]   │  │ [W23-24] │  │ MAP [W25-32] │ │
│  └────┬─────┘  └────┬───────┘  └────┬─────┘  └──────┬───────┘ │
│       │              │               │               │          │
│       ▼              ▼               ▼               ▼          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SHARED KNOWLEDGE LAYER (from Stream)        │  │
│  │  PostgreSQL │ Qdrant │ Redis │ LiteLLM │ S3 Storage     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  BACKEND TRACK:  Parser → Chunker → Graph → Intelligence       │
│  FRONTEND TRACK: Shell → Reader → TOC → ConceptMap → Nav       │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Stages & Recovery

```
DOCUMENT PROCESSING FSM:

  UPLOADED ──→ PARSING ──→ CHUNKING ──→ EXTRACTING ──→ EMBEDDING
     │           │ₓ          │ₓ            │ₓ            │ₓ
     │      PARSE_FAILED CHUNK_FAILED EXTRACT_FAILED EMBED_FAILED
     │           │           │             │              │
     └───────────┴───────────┴─────────────┴──────────────┘
                         SWEEPER (max 3 retries, then FAILED)

  EMBEDDING ──→ SCORING ──→ INDEXING ──→ READY
                   │ₓ          │ₓ
              SCORE_FAILED INDEX_FAILED
```

---

## 2. Development Sprints

### Sprint L1: Foundation + Document Parser (Weeks 19-20)

#### Backend Track

| Task | Description | Done When |
|------|-------------|-----------|
| B-L01 | Create `library_documents` schema: `documents`, `document_chapters`, `processing_queue` tables | Tables exist in PostgreSQL; FK constraints verified |
| B-L02 | Document upload endpoint: `POST /api/library/documents/upload` | File stored in S3, document record created, queue entry added |
| B-L03 | File validation middleware: size (<100 MB), format (EPUB/PDF/DOCX), virus scan stub | Invalid files rejected with correct error codes |
| B-L04 | EPUB parser: `ebooklib` + `BeautifulSoup` → Markdown | 3 sample EPUBs parsed; chapters, headings, images preserved |
| B-L05 | PDF parser: `marker-pdf` → Markdown | 3 sample PDFs parsed; tables, headings, multi-column handled |
| B-L06 | DOCX parser: `python-docx` → Markdown | 3 sample DOCX files parsed; structure preserved |
| B-L07 | Format detection router: file extension + magic bytes | Correct parser invoked for each format; unknown format rejected |
| B-L08 | Processing FSM: UPLOADED → PARSING → PARSED / PARSE_FAILED | State transitions logged; sweeper retries on failure (max 3) |
| B-L09 | Document list endpoint: `GET /api/library/documents` | Returns user's documents with status, pagination, sort by date |
| B-L10 | Document delete endpoint: `DELETE /api/library/documents/:id` | File removed from S3, DB records soft-deleted, Qdrant vectors cleaned |

#### Frontend Track

| Task | Description | Done When |
|------|-------------|-----------|
| F-L01 | Library workspace shell: sidebar navigation, document grid view | Route `/library` renders grid of document cards |
| F-L02 | Document upload UI: drag-and-drop + file picker | File uploads trigger API call; progress bar shown |
| F-L03 | Document card component: title, author, format badge, processing status | Cards display metadata; status updates in real-time (polling) |
| F-L04 | Processing status indicator: animated states (uploading → parsing → ...) | User sees current processing stage with estimated time |
| F-L05 | Document tier limit UI: counter badge, upgrade prompt | Starter users see "12/50 documents used" |

#### 🎯 Milestone L-M1: Parser Pipeline (Week 20)

| Criterion | Verification | Pass/Fail |
|-----------|-------------|-----------|
| EPUB parsing preserves chapters and headings | Parse 3 EPUBs, diff against manual extraction | ☐ |
| PDF parsing handles multi-column layouts | Parse academic paper with 2-column layout | ☐ |
| DOCX parsing preserves structure | Parse formatted DOCX, verify Markdown | ☐ |
| FSM handles parse failures gracefully | Inject corrupt file, verify retry + FAILED state | ☐ |
| Document upload E2E | Upload → S3 storage → DB record → grid display | ☐ |

---

### Sprint L2: Semantic Chunking + Embedding (Weeks 21-22)

#### Backend Track

| Task | Description | Done When |
|------|-------------|-----------|
| B-L11 | Sentence splitter: spaCy `sentencizer` for sentence boundaries | 1000-sentence doc splits correctly; no mid-word breaks |
| B-L12 | All-sentence embedding: batch embed via text-embedding-3-small | 500 sentences embedded in <10 seconds |
| B-L13 | Cosine-boundary chunking algorithm (k=1.5 threshold) | Chunks align with topic boundaries on 3 test documents |
| B-L14 | Post-processing: merge <100 char, split >2000 char | No atom outside 100-2000 char range after processing |
| B-L15 | Semantic density scoring per atom | Each atom has density score (0.0-1.0) |
| B-L16 | Atom batch embedding → Qdrant upsert with metadata | Vector count matches atom count; metadata queryable |
| B-L17 | Content-hash deduplication: skip re-embedding for identical atoms | Re-upload of same document skips embedding step |
| B-L18 | FSM transitions: PARSED → CHUNKING → CHUNKED → EMBEDDING → EMBEDDED | All state transitions logged; failures handled |
| B-L19 | Knowledge Delta for documents: extend Stream delta scoring to atom-level | Each atom has delta_score; document has novelty_score |
| B-L20 | Delta chapter summary: identify redundant chapters (mean delta < 0.15) | Redundant chapters flagged in API response |

#### Frontend Track

| Task | Description | Done When |
|------|-------------|-----------|
| F-L06 | Document detail view stub: metadata, processing timeline, atom count | Route `/library/:id` renders document metadata |
| F-L07 | Knowledge Delta badge: "72% novel to you" on document card | Novelty score color-coded on card |
| F-L08 | Processing progress: per-stage bar (chunking → embedding → ...) | User sees granular progress during processing |

#### 🎯 Milestone L-M2: Semantic Engine (Week 22)

| Criterion | Verification | Pass/Fail |
|-----------|-------------|-----------|
| Chunking produces coherent semantic units | Manual review of 50 atoms from test document | ☐ |
| No atom outside 100-2000 char range | Assert on full test corpus | ☐ |
| Embeddings stored with correct metadata | Qdrant query by doc_id returns all atoms | ☐ |
| Delta scores computed per atom and document | API returns novelty_score for uploaded document | ☐ |
| Deduplication prevents re-embedding | Upload same doc twice; verify vector count unchanged | ☐ |

---

### Sprint L3: Graph Extraction + PKG (Weeks 23-24)

#### Backend Track

| Task | Description | Done When |
|------|-------------|-----------|
| B-L21 | Graph extraction prompt engineering: (S, P, O) triples from atom batches | LLM returns structured JSON triples with confidence |
| B-L22 | Batch extraction pipeline: 10 atoms/batch via Gemini Flash | 450-atom doc processed in <120 seconds |
| B-L23 | Verifier pass: re-check extracted triples against source atom text | Hallucinated triples filtered (confidence < 0.5 removed) |
| B-L24 | Entity resolution: embed concept names → cosine match against existing PKG | Duplicates merged (>0.90 similarity); new nodes created below threshold |
| B-L25 | PKG schema: `pkg_nodes`, `pkg_edges` tables (PostgreSQL JSONB) | Tables created; recursive CTE for 2-hop traversal works in <100ms |
| B-L26 | PKG merge pipeline: new doc → extract → resolve → merge into user's PKG | Upload doc → PKG grows; node/edge counts updated |
| B-L27 | Noise filter: cap at 50 triples per 10-atom batch | Excessive extractions trimmed |
| B-L28 | User knowledge state tracking: KNOWS edge between user and concept | User's known concepts updated after reading |
| B-L29 | FSM transitions: EMBEDDED → EXTRACTING → EXTRACTED → SCORING → INDEXED | State transitions complete; document reaches READY |
| B-L30 | PKG query API: `GET /api/library/pkg/concepts?doc_id=X` | Returns concepts with relationships for a document |

#### Frontend Track

| Task | Description | Done When |
|------|-------------|-----------|
| F-L09 | PKG stats panel: "Your Knowledge Graph: 234 concepts, 567 relationships" | Renders total PKG stats on Library dashboard |
| F-L10 | Concept list view: searchable list of extracted concepts per document | User can browse and search concepts |

#### 🎯 Milestone L-M3: Knowledge Graph (Week 24)

| Criterion | Verification | Pass/Fail |
|-----------|-------------|-----------|
| Triples extracted with >80% accuracy vs. manual labels | Evaluate 100 triples against ground truth | ☐ |
| Entity resolution merges duplicates correctly | Inject "Bayesian Prior" and "Bayesian Priors" → merged | ☐ |
| Recursive CTE traversal returns correct 2-hop results | Query known graph, verify path correctness | ☐ |
| PKG merges correctly across 2 documents | Upload 2 related docs, verify overlapping concepts merge | ☐ |
| Full pipeline: upload → READY state in <3 minutes (100-page doc) | Time E2E pipeline | ☐ |

---

### Sprint L4: Reader UI + Augmented TOC (Weeks 25-28)

#### Backend Track

| Task | Description | Done When |
|------|-------------|-----------|
| B-L31 | Reading state API: `POST/GET /api/library/documents/:id/reading-state` | Save/restore: {last_chapter, last_atom, progress, scroll_position} |
| B-L32 | Chapter summary endpoint: pre-computed summaries via Gemini Flash | Each chapter has 1-2 paragraph summary, cached in PostgreSQL |
| B-L33 | Augmented TOC data endpoint: chapter density + delta aggregation | Returns per-chapter: {title, atom_count, avg_density, avg_delta} |
| B-L34 | Highlights API: `POST/GET/DELETE /api/library/documents/:id/highlights` | Store: {atom_id, start_offset, end_offset, color, note} |
| B-L35 | Document content API: return atoms for a chapter range | Paginated atom retrieval by chapter; supports lazy loading |

#### Frontend Track

| Task | Description | Done When |
|------|-------------|-----------|
| F-L11 | Reader layout: sidebar (TOC) + main area (content) + toolbar | Route `/library/:id/read` renders reader shell |
| F-L12 | Full-text renderer: atoms → styled HTML with chapter breaks | Text renders with typography (Inter font, 1.6 line-height, max-width 65ch) |
| F-L13 | Chapter navigation: sidebar with clickable chapters | Click chapter → smooth scroll to content |
| F-L14 | Reading progress bar: % completed, time remaining estimate | Progress bar updates as user scrolls; persists across sessions |
| F-L15 | Augmented TOC heatmap: color-coded chapter density | Each chapter entry has density color bar (green/amber/gray) |
| F-L16 | Delta indicators in TOC: "(mostly known)" for low-delta chapters | Visual label on chapters with avg_delta < 0.15 |
| F-L17 | Highlight system: select text → color picker → save note | Highlights persist; clickable in sidebar |
| F-L18 | Reading state persistence: auto-save on scroll, restore on open | Close and reopen → same position restored |
| F-L19 | Chapter summary popup: click info icon → summary overlay | Pre-computed summary renders in modal |
| F-L20 | Responsive reader: adapts to desktop (sidebar) / tablet (overlay TOC) | Test on 1024px and 768px viewports |

#### 🎯 Milestone L-M4: Reader + TOC (Week 28)

| Criterion | Verification | Pass/Fail |
|-----------|-------------|-----------|
| Full document renders without layout glitches | 3 documents across formats (EPUB/PDF/DOCX) | ☐ |
| Augmented TOC shows density heatmap | Visual comparison: hot chapters vs. cold chapters | ☐ |
| Reading state persists across sessions | Open → scroll → close → reopen → same position | ☐ |
| Highlights save and display correctly | Create 5 highlights, close reader, reopen → all visible | ☐ |
| Responsive layout works on 1024px and 768px | Browser resize test | ☐ |

---

### Sprint L5: Dynamic Concept Map (Weeks 29-30)

#### Backend Track

| Task | Description | Done When |
|------|-------------|-----------|
| B-L36 | Concept Map data endpoint: nodes + edges + user knowledge state | Returns JSON: {nodes[], edges[], gaps[], known[]} |
| B-L37 | Layout algorithm: topological sort for DEPENDS_ON hierarchy | Axiomatic roots at top, derivatives below |
| B-L38 | Concept → atom mapping endpoint: which atoms contain this concept | Returns sorted atom list for concept |
| B-L39 | Gap detection: concepts in doc but not in user's KNOWS edges | Gaps flagged with delta_score |

#### Frontend Track

| Task | Description | Done When |
|------|-------------|-----------|
| F-L21 | D3.js force-directed graph: nodes + edges rendering | Graph renders with smooth physics simulation |
| F-L22 | Node color-coding: 🟢 Known, 🟡 Gap, 🔴 Contradiction | Visual state matches user PKG |
| F-L23 | Edge labels: DEPENDS_ON, SUPPORTS, CONTRADICTS | Labels render on hover/click |
| F-L24 | Node click → reader navigation: click concept → show all mentions | Click concept → reader reflows to aggregated atoms |
| F-L25 | Concept Map toolbar: zoom, pan, reset, filter by relationship type | Controls responsive and accessible |
| F-L26 | Concept Map integration in reader: split view (map + text) | Toggle button shows/hides concept map panel |
| F-L27 | Gap hover tooltip: concept name + definition preview | Tooltip renders in <100ms |

#### 🎯 Milestone L-M5: Concept Map (Week 30)

| Criterion | Verification | Pass/Fail |
|-----------|-------------|-----------|
| Graph renders with correct node colors | 5 documents with varied knowledge states | ☐ |
| Click concept → reader reflows to mentions | Click 3 concepts, verify atom aggregation | ☐ |
| Force-directed layout avoids overlapping nodes | Visual inspection on 80-node graph | ☐ |
| Gap detection matches expected results | Manual comparison: known user concepts vs. doc concepts | ☐ |
| Renders in <2 seconds for 80-node graph | Performance timing | ☐ |

---

### Sprint L6: Intelligence Features (Weeks 31-32)

#### Backend Track

| Task | Description | Done When |
|------|-------------|-----------|
| B-L40 | JIT Context endpoint: `POST /api/library/jit-context` → micro-summary | Returns explanation contextualized to current sentence + user PKG |
| B-L41 | JIT caching: Redis cache with key = hash(term + doc_context_hash) | Second hover on same term returns cached result (TTL: 24h) |
| B-L42 | Semantic Zoom data: 3 detail levels per chapter | API returns atoms filtered by density threshold per zoom level |
| B-L43 | Non-Linear Navigation endpoint: concept → sorted atom aggregate | Returns all atoms containing concept, ordered by doc position |
| B-L44 | Cross-document search: hybrid Qdrant vector + PKG graph query | Returns fused results from vector search + 2-hop graph traversal |
| B-L45 | Cross-document synthesis: LLM generates comparative answer with citations | Response includes inline citations: [Title, Chapter] |
| B-L46 | AI budget tracking: track Library AI costs per user via LiteLLM | Cost telemetry logged; graceful degradation thresholds enforced |
| B-L47 | Graceful degradation: L2/L3 modes for Library (reduced AI / no AI) | Budget <20% → reader-only mode, no JIT, no graphs |

#### Frontend Track

| Task | Description | Done When |
|------|-------------|-----------|
| F-L28 | JIT overlay: hover term (>500ms dwell) → popover with explanation | Overlay renders with context-aware explanation |
| F-L29 | Semantic Zoom controls: 3-level toggle (Summary / Theses / Full) | Each level shows correct atom subset |
| F-L30 | Non-Linear Navigation mode: concept view → aggregated atom stream | "Return to linear" button restores original flow |
| F-L31 | Cross-document query UI: search bar → results with citations | Results display with source document badges |
| F-L32 | Budget indicator: Library AI budget usage in settings | User sees "AI Budget: 72% remaining" |

#### 🎯 Milestone L-M6: Intelligence (Week 32)

| Criterion | Verification | Pass/Fail |
|-----------|-------------|-----------|
| JIT overlay returns context-aware explanation | Hover 5 terms; verify explanations are contextual | ☐ |
| JIT cache prevents redundant API calls | Hover same term twice; verify only 1 LLM call | ☐ |
| Semantic Zoom correctly filters atoms by density | Toggle levels; verify atom visibility matches density threshold | ☐ |
| Cross-document query returns cited results | Query across 3 docs; verify citations are correct | ☐ |
| Graceful degradation activates at budget thresholds | Mock budget at 10%; verify Library drops to reader-only | ☐ |

---

### Sprint L7: Integration + Polish (Weeks 33-34)

#### Backend Track

| Task | Description | Done When |
|------|-------------|-----------|
| B-L48 | Stream → Library bridge: "Save to Library" on Stream article cards | Stream item saved as Library document; parsed + ingested |
| B-L49 | Library settings API: document limits, AI budget allocation, notifications | Settings CRUD endpoints functional |
| B-L50 | API rate limiting: per-user throttle on Library endpoints | 100 req/min on read; 10 req/min on write/AI endpoints |
| B-L51 | Error handling audit: all endpoints return consistent error responses | Standardized error format: {code, message, details} |
| B-L52 | Database index optimization: analyze slow queries, add covering indexes | All critical queries <50ms at P95 |
| B-L53 | Telemetry: Library usage events (upload, read, concept_click, jit_hover) | Events logged to analytics pipeline |

#### Frontend Track

| Task | Description | Done When |
|------|-------------|-----------|
| F-L33 | Library dashboard: recent documents, PKG growth chart, reading streak | Dashboard renders with cards and charts |
| F-L34 | "Save to Library" button on Stream cards | Button triggers document save + ingest pipeline |
| F-L35 | Library settings page: storage usage, AI budget, notification prefs | Settings page functional with save/reset |
| F-L36 | Empty state designs: no documents, no concepts, no highlights | Friendly empty states with call-to-action |
| F-L37 | Loading states: skeleton screens for reader, concept map, TOC | Skeletons match final layout dimensions |
| F-L38 | Error states: parse failed, processing timeout, AI unavailable | User-friendly error messages with retry options |
| F-L39 | Accessibility pass: keyboard nav, ARIA labels, color contrast | WCAG 2.1 AA on all new components |

#### 🎯 Milestone L-M7: Integration (Week 34)

| Criterion | Verification | Pass/Fail |
|-----------|-------------|-----------|
| Stream → Library save works E2E | Save 3 Stream articles → Library; verify parsing | ☐ |
| All API endpoints return consistent errors | Trigger 10 error conditions; verify response format | ☐ |
| Critical DB queries <50ms at P95 | Load test with 200 concurrent users | ☐ |
| Settings save and persist correctly | Change settings, refresh, verify persistence | ☐ |
| Accessibility audit passes WCAG 2.1 AA | axe-core automated check on all Library routes | ☐ |

---

### Sprint L8: Testing + Launch (Weeks 35-36)

| Task | Description | Done When |
|------|-------------|-----------|
| T-L01 | Integration test suite: 14 features × acceptance criteria from MVP spec | All Gherkin scenarios pass as automated tests |
| T-L02 | Load test: 200 concurrent users, 50 simultaneous document processes | P95 response times within NFR targets |
| T-L03 | Security audit: auth on all endpoints, document access isolation | User A cannot access User B's documents, PKG, highlights |
| T-L04 | Document format stress test: 20 edge-case documents (OCR, scanned, huge) | Graceful handling; FAILED state with user notification |
| T-L05 | Cross-browser test: Chrome, Firefox, Safari, Edge | Reader and Concept Map render correctly |
| T-L06 | Beta deployment: 50 beta users, feedback collection | Feedback survey deployed; >80% completion rate |
| T-L07 | Performance regression: no Stream module degradation | Stream API P95 unchanged after Library deployment |
| T-L08 | Bug triage: fix P0/P1 bugs from beta | No P0 bugs; P1 bugs have known workarounds |

#### 🎯 Milestone L-M8: Launch (Week 36)

| Criterion | Verification | Pass/Fail |
|-----------|-------------|-----------|
| All 14 MVP features pass acceptance criteria | Automated test suite green | ☐ |
| P95 response times within NFR targets | Load test report | ☐ |
| No cross-user data leakage | Security test: 100 cross-user access attempts blocked | ☐ |
| Beta NPS > 30 | Survey results | ☐ |
| Stream performance unaffected | Before/after comparison of Stream P95 metrics | ☐ |

---

## 3. Dependency Graph

```
┌──────────────────────────────────────────────────────────────┐
│                    DEPENDENCY GRAPH                           │
│                                                               │
│  BACKEND                          FRONTEND                    │
│                                                               │
│  B-L01───┬──B-L02─────────────────F-L01──────F-L02           │
│  (schema)│  (upload API)          (shell)     (upload UI)     │
│          │                                                    │
│  B-L04──┬┴──B-L07                 F-L03──────F-L04           │
│  B-L05──┤   (format router)       (cards)    (status)         │
│  B-L06──┘                                                     │
│          │                                                    │
│  B-L11──B-L12──B-L13──B-L14      F-L06──────F-L07            │
│  (split) (embed) (chunk) (post)  (detail)    (delta badge)    │
│          │                                                    │
│  B-L16──B-L19──B-L20             F-L08                        │
│  (Qdrant) (delta) (chapters)     (progress)                   │
│          │                                                    │
│  B-L21──B-L22──B-L24──B-L25     F-L09──────F-L10             │
│  (prompt) (batch) (resolve)(PKG) (stats)    (concepts)        │
│          │                                                    │
│  B-L31──B-L33──B-L35            F-L11──F-L12──F-L15──F-L18   │
│  (state) (TOC)  (content)      (layout)(render)(TOC) (state)  │
│          │                                                    │
│  B-L36──B-L37──B-L39            F-L21──F-L22──F-L24──F-L26   │
│  (map)  (layout) (gaps)        (D3.js) (colors)(click)(split) │
│          │                                                    │
│  B-L40──B-L41──B-L44──B-L46    F-L28──F-L29──F-L31──F-L32   │
│  (JIT)  (cache) (xdoc) (budget)(overlay)(zoom)(nav)  (budget) │
│          │                                                    │
│  B-L48──B-L49──B-L52           F-L33──F-L34──F-L39           │
│  (bridge)(settings)(index)     (dash)  (save) (a11y)          │
└──────────────────────────────────────────────────────────────┘
```

### Critical Path

```
B-L01 → B-L02 → B-L04/05/06 → B-L07 → B-L11 → B-L13 → B-L16 → B-L19
→ B-L21 → B-L24 → B-L25 → B-L36 → B-L40 → B-L44 → B-L48 → T-L01

Duration: 18 weeks (no slack on backend track)
```

---

## 4. Resource Allocation

### Team Structure

| Role | Count | Sprints |
|------|-------|---------|
| Backend Engineer (Python/FastAPI) | 2 | L1-L8 |
| Frontend Engineer (React/TypeScript) | 2 | L1-L8 |
| ML/AI Engineer (LLM prompts, chunking) | 1 | L2-L6 |
| QA Engineer | 1 | L4-L8 |
| UX Designer | 1 | L1 (wireframes), L4-L5 (reader/map), L7 (polish) |

### Infrastructure Costs (Dev Environment)

| Resource | Monthly Cost | Notes |
|----------|-------------|-------|
| Qdrant Cloud (dev) | $25 | Shared with Stream dev |
| LiteLLM (dev AI budget) | $100 | Gemini Flash + embeddings |
| PostgreSQL (dev) | $0 | Supabase free tier |
| S3 Storage (dev) | $5 | Document file storage |
| **Total Dev Infra** | **$130/month** | |

---

## 5. Risk Mitigations (Sprint-Level)

| Sprint | Risk | Probability | Mitigation |
|--------|------|-------------|------------|
| L1 | PDF parsing fails on scanned docs | High | L1 scope: layout-aware PDFs only; OCR deferred to v2.5 |
| L2 | Chunking quality varies by genre | Medium | k-parameter auto-tuning per doc density; manual review gate |
| L3 | Graph extraction hallucination | High | Verifier pass (B-L23); confidence threshold 0.5; cap 50 triples/batch |
| L4 | Reader performance on large docs | Medium | Virtual scrolling; lazy-load atoms by chapter |
| L5 | D3.js graph unusable at >100 nodes | Medium | Cluster similar concepts; show top-50 by centrality; expand on click |
| L6 | JIT overlay latency >500ms | Medium | Redis caching; pre-compute for high-delta terms |
| L7 | Stream → Library bridge breaks Stream tests | Low | Run full Stream regression in CI before merge |
| L8 | Beta users find parser unusable | Medium | Include feedback form per document; fast-track parser fixes |

---

## 6. Definition of Done (Module-Level)

The Library module is **DONE** when:

1. ✅ All 14 MVP features pass acceptance criteria (`LIBRARY_MVP.md`)
2. ✅ All 8 milestones pass verification checklists
3. ✅ Integration test suite: 100% of Gherkin scenarios automated and green
4. ✅ Load test: 200 users, P95 within NFR targets
5. ✅ Security: no cross-user data access
6. ✅ Stream module: zero performance regression
7. ✅ Beta: NPS > 30, no P0 bugs
8. ✅ Documentation: API docs, user guide, admin runbook

---

*Library Implementation Plan v1.0. SSOT for tasks and dependencies. Architecture → `LIBRARY_PRD.md`. Scope → `LIBRARY_MVP.md`.*
