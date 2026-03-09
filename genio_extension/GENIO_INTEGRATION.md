# Genio Extension - Backend Integration

## Overview
This document describes how to integrate the existing Genio Chrome Extension with the new Genio Backend (FastAPI).

## Current Architecture
- Extension uses Firebase (Auth + Firestore)
- Backend uses FastAPI + PostgreSQL + Qdrant

## Integration Strategy

### Phase 1: Dual Backend Support
Keep Firebase for auth, add Genio Backend for advanced features:
- Library document storage
- Knowledge Graph queries
- GraphRAG search
- Augmented reader content

### Phase 2: Migration (Future)
Migrate completely to Genio Backend when user system is ready.

## API Endpoints to Integrate

```
POST /api/v1/library/documents          # Save article/page
GET  /api/v1/library/documents          # List documents
GET  /api/v1/library/pkg/graph          # Get knowledge graph
POST /api/v1/library/pkg/query          # GraphRAG search
POST /api/v1/library/highlights         # Save highlights
```

## Implementation Files

### New Files Added:
1. `src/genio-bridge.js` - Bridge between extension and Genio API
2. `src/content-genio.js` - Enhanced content script with Genio features
3. `src/popup-genio.html` - Popup with Genio integration UI

### Modified Files:
1. `manifest.json` - Add Genio API host permissions
2. `background.js` - Add Genio API calls

## Configuration

Add to extension storage:
```json
{
  "genioApiUrl": "https://api.genio.ai",
  "genioApiKey": "user-api-key",
  "useGenioBackend": true
}
```

## Security

- API Key stored in chrome.storage.local (encrypted)
- JWT token from Firebase used for Genio Backend auth
- CORS configured for extension origin
