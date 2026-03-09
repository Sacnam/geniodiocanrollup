# Genio Knowledge OS - Final Implementation Plan
**Objective:** Reach 100% completion from current ~70%  
**Mode:** YOLO (Test-Driven, Auto-iteration)  
**Target:** Production-ready, deployable application

---

## Phase 1: Core Library Pipeline (Critical Path)

### Task 1.1: Document Processing FSM with State Tracking
**Current:** Basic processing status exists but no full FSM  
**Target:** UPLOADED→PARSING→CHUNKING→EMBEDDING→EXTRACTING→READY with retry logic

**Test Requirements:**
- FSM transitions correctly
- Sweeper retries failed states (max 3)
- State persistence in DB

**Files:**
- `backend/app/library/fsm.py` (NEW)
- `backend/app/models/document.py` (UPDATE)
- `backend/tests/test_document_fsm.py` (NEW)

---

### Task 1.2: Content-Hash Deduplication
**Current:** Documents re-process every time  
**Target:** Skip re-embedding if content hash matches

**Test Requirements:**
- Same document uploaded twice = same vectors
- Different content = new vectors

**Files:**
- `backend/app/library/dedup.py` (NEW)
- `backend/tests/test_dedup.py` (NEW)

---

### Task 1.3: Knowledge Delta for Documents (Atom-Level)
**Current:** Delta only for articles  
**Target:** Atom-level delta scoring for documents

**Test Requirements:**
- Each atom has delta_score
- Document has aggregated novelty_score
- Redundant chapters detected (mean delta < 0.15)

**Files:**
- `backend/app/library/delta.py` (UPDATE)
- `backend/tests/test_document_delta.py` (NEW)

---

### Task 1.4: Graph Extraction Pipeline (S-P-O Triples)
**Current:** Models exist but pipeline not integrated  
**Target:** Full extraction → verification → entity resolution → PKG merge

**Test Requirements:**
- Extract triples from 10-atom batch
- Verifier filters hallucinations (confidence < 0.5)
- Entity resolution merges duplicates (>0.90 similarity)
- PKG grows correctly after merge

**Files:**
- `backend/app/library/graph_extractor.py` (UPDATE - integrate pipeline)
- `backend/app/library/entity_resolution.py` (NEW)
- `backend/app/tasks/graph_tasks.py` (NEW)
- `backend/tests/test_graph_pipeline.py` (NEW)

---

## Phase 2: Advanced Reader Features

### Task 2.1: Reading State API
**Current:** Not implemented  
**Target:** Save/restore position, chapter, scroll

**Test Requirements:**
- POST/GET reading state
- Auto-save on scroll
- Restore exact position

**Files:**
- `backend/app/api/v1/reading_state.py` (NEW)
- `backend/tests/test_reading_state.py` (NEW)

---

### Task 2.2: Chapter Summary Endpoint
**Current:** Not implemented  
**Target:** Pre-computed chapter summaries via Gemini

**Test Requirements:**
- Each chapter has 1-2 paragraph summary
- Cached in PostgreSQL

**Files:**
- `backend/app/library/summarizer.py` (UPDATE)
- `backend/tests/test_chapter_summary.py` (NEW)

---

### Task 2.3: Augmented TOC with Heatmap
**Current:** Basic TOC in reader  
**Target:** Density + delta heatmap, "mostly known" indicators

**Test Requirements:**
- TOC returns per-chapter metadata
- Density color-coded
- Delta indicators for low-novelty chapters

**Files:**
- `backend/app/library/toc.py` (NEW)
- `frontend/src/components/reader/AugmentedTOC.tsx` (UPDATE)
- `backend/tests/test_toc.py` (NEW)

---

### Task 2.4: Advanced Reader UI Integration
**Current:** AugmentedReader base exists  
**Target:** Full integration of all reader features

**Test Requirements:**
- Reader renders all features
- Navigation works
- State persists

**Files:**
- `frontend/src/components/reader/Reader.tsx` (UPDATE)
- `frontend/src/components/reader/ChapterNavigation.tsx` (NEW)
- `frontend/src/components/reader/ReadingProgress.tsx` (NEW)

---

## Phase 3: Concept Map & Intelligence

### Task 3.1: Concept Map Data Endpoint
**Current:** D3.js frontend exists but backend data incomplete  
**Target:** Complete graph data with topological sort, gap detection

**Test Requirements:**
- Returns nodes + edges + gaps + known concepts
- Topological sort for DEPENDS_ON hierarchy
- 2-hop traversal <100ms

**Files:**
- `backend/app/library/concept_map_service.py` (NEW)
- `backend/app/api/v1/concept_map.py` (NEW)
- `backend/tests/test_concept_map.py` (NEW)

---

### Task 3.2: JIT Context Endpoint
**Current:** Not implemented  
**Target:** Hover → context-aware explanation

**Test Requirements:**
- POST /api/library/jit-context returns explanation
- Cached in Redis (TTL: 24h)
- <500ms response

**Files:**
- `backend/app/library/jit_context.py` (NEW)
- `backend/tests/test_jit.py` (NEW)

---

### Task 3.3: Semantic Zoom Data
**Current:** Not implemented  
**Target:** 3 detail levels per chapter

**Test Requirements:**
- API returns atoms filtered by density threshold
- Toggle levels works

**Files:**
- `backend/app/library/semantic_zoom.py` (NEW)
- `frontend/src/components/reader/SemanticZoom.tsx` (NEW)
- `backend/tests/test_semantic_zoom.py` (NEW)

---

### Task 3.4: Cross-Document Synthesis
**Current:** Basic GraphRAG exists  
**Target:** Multi-document synthesis with citations

**Test Requirements:**
- Query across documents
- Response includes citations [Title, Chapter]

**Files:**
- `backend/app/library/synthesis.py` (NEW)
- `backend/tests/test_synthesis.py` (NEW)

---

## Phase 4: Extension & Integration

### Task 4.1: Extension Bridge Integration
**Current:** Bridge code exists but not integrated  
**Target:** Extension uses Genio API instead of Firebase

**Test Requirements:**
- Extension saves to Genio Library
- Auth via JWT
- Offline capability

**Files:**
- `genio_extension/src/genio-bridge.js` (UPDATE - integrate)
- `genio_extension/src/background.js` (UPDATE)
- `genio_extension/manifest.json` (UPDATE permissions)

---

### Task 4.2: Extension UI for Save
**Current:** Basic popup exists  
**Target:** Enhanced save with metadata, tags

**Test Requirements:**
- Save dialog with title extraction
- Tags input
- Category selection

**Files:**
- `genio_extension/src/popup/popup.js` (UPDATE)
- `genio_extension/src/popup/popup.html` (UPDATE)

---

## Phase 5: Desktop App (Tauri)

### Task 5.1: Tauri Project Setup
**Current:** Not exists  
**Target:** Desktop app with embedded web view

**Test Requirements:**
- Builds for Windows/Mac/Linux
- Auto-updater configured

**Files:**
- `genio-desktop/` (NEW PROJECT)
- `genio-desktop/src-tauri/Cargo.toml`
- `genio-desktop/src-tauri/tauri.conf.json`

---

### Task 5.2: Desktop Native Features
**Target:** System tray, native menus, offline sync

**Files:**
- `genio-desktop/src-tauri/src/main.rs`
- `genio-desktop/src/App.tsx`

---

## Phase 6: Testing & Quality

### Task 6.1: E2E Test Suite
**Current:** Basic structure exists  
**Target:** Full coverage of critical paths

**Test Requirements:**
- Auth flow
- Feed management
- Document upload
- Reader navigation
- GraphRAG search
- Scout creation

**Files:**
- `e2e/tests/auth.spec.ts` (UPDATE)
- `e2e/tests/feeds.spec.ts` (UPDATE)
- `e2e/tests/library.spec.ts` (NEW)
- `e2e/tests/reader.spec.ts` (NEW)
- `e2e/tests/scout.spec.ts` (NEW)

---

### Task 6.2: Integration Tests
**Target:** API integration tests

**Files:**
- `backend/tests/integration/test_library_api.py` (NEW)
- `backend/tests/integration/test_reader_api.py` (NEW)

---

### Task 6.3: Load Testing
**Target:** 200 concurrent users

**Files:**
- `backend/tests/load/locustfile.py` (UPDATE)

---

## Phase 7: Final Polish

### Task 7.1: Error Handling Audit
**Target:** Consistent error responses across all endpoints

---

### Task 7.2: Performance Optimization
**Target:** DB queries <50ms at P95

---

### Task 7.3: Documentation
**Target:** API docs, user guide, admin runbook complete

---

## Execution Order (Priority)

```
Phase 1 (Core Pipeline):
  1.1 → 1.2 → 1.3 → 1.4

Phase 2 (Reader):
  2.1 → 2.2 → 2.3 → 2.4

Phase 3 (Intelligence):
  3.1 → 3.2 → 3.3 → 3.4

Phase 4 (Extension):
  4.1 → 4.2

Phase 5 (Desktop):
  5.1 → 5.2

Phase 6 (Testing):
  6.1 → 6.2 → 6.3

Phase 7 (Polish):
  7.1 → 7.2 → 7.3
```

---

## Success Criteria (100% Definition)

- [ ] All 7 phases complete
- [ ] All tests passing (unit + integration + e2e)
- [ ] Load test: 200 users, P95 < 200ms
- [ ] Extension saves to Genio (not just Firebase)
- [ ] Desktop app builds and runs
- [ ] Mobile responsive (already done)
- [ ] Documentation complete
- [ ] No critical security issues

---

**Starting YOLO execution loop now...**
