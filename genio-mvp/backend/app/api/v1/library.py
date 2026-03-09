"""
Library API Endpoints
Document management, PKG, GraphRAG, and Augmented Reader
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.services.document_service import DocumentService
from app.library.graph_rag import GraphRAG
from app.library.pkg_models import PKGNode, PKGEdge
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.services.document_service import DocumentService

router = APIRouter()


# ========== Schemas ==========

class DocumentUploadResponse(BaseModel):
    id: str
    status: str
    message: str


class HighlightCreate(BaseModel):
    document_id: str
    start_offset: int
    end_offset: int
    text: str
    color: str = "yellow"
    note: Optional[str] = None


class HighlightResponse(BaseModel):
    id: str
    document_id: str
    start_offset: int
    end_offset: int
    text: str
    color: str
    note: Optional[str]
    created_at: str


class PKGGraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class GraphRAGQuery(BaseModel):
    query: str
    max_results: int = 10
    include_documents: bool = True
    include_concepts: bool = True


class GraphRAGResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    concepts: List[str]
    citations: List[str]


class OverlayItem(BaseModel):
    id: str
    type: str
    text: str
    related_nodes: Optional[List[str]] = None


# ========== Document Endpoints ==========

@router.post("/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a new document."""
    doc_service = DocumentService(db)
    document = await doc_service.create_document(
        user_id=current_user.id,
        file=file,
    )
    
    return DocumentUploadResponse(
        id=document.id,
        status=document.status,
        message="Document uploaded and queued for processing",
    )


@router.get("/documents")
def list_documents(
    search: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's documents."""
    query = db.query(Document).filter(Document.user_id == current_user.id)
    
    if search:
        query = query.filter(
            Document.title.ilike(f"%{search}%") | 
            Document.original_filename.ilike(f"%{search}%")
        )
    
    if status:
        query = query.filter(Document.status == status)
    
    total = query.count()
    documents = query.order_by(Document.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "items": documents,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/documents/{document_id}")
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document details."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return doc


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(doc)
    db.commit()
    
    return None


# ========== Highlights ==========

@router.post("/highlights", response_model=HighlightResponse)
def create_highlight(
    highlight: HighlightCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a text highlight."""
    # Verify document ownership
    doc = db.query(Document).filter(
        Document.id == highlight.document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Create highlight (would need a Highlight model)
    # For now, return mock response
    return HighlightResponse(
        id=f"hl_{hash(highlight.text) % 10000}",
        document_id=highlight.document_id,
        start_offset=highlight.start_offset,
        end_offset=highlight.end_offset,
        text=highlight.text,
        color=highlight.color,
        note=highlight.note,
        created_at="2026-02-17T10:00:00Z",
    )


@router.get("/documents/{document_id}/highlights")
def get_highlights(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get highlights for a document."""
    # Would query from database
    return []


# ========== PKG Graph ==========

@router.get("/pkg/graph", response_model=PKGGraphResponse)
def get_pkg_graph(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's Personal Knowledge Graph."""
    nodes = db.query(PKGNode).filter(PKGNode.user_id == current_user.id).all()
    edges = db.query(PKGEdge).filter(PKGEdge.user_id == current_user.id).all()
    
    return PKGGraphResponse(
        nodes=[
            {
                "id": n.id,
                "node_type": n.node_type.value,
                "name": n.name,
                "definition": n.definition,
                "confidence": n.confidence,
                "knowledge_state": n.knowledge_state,
                "relationships": n.relationships,
            }
            for n in nodes
        ],
        edges=[
            {
                "id": e.id,
                "source_id": e.source_id,
                "target_id": e.target_id,
                "edge_type": e.edge_type.value,
                "confidence": e.confidence,
            }
            for e in edges
        ],
    )


@router.get("/pkg/nodes/{node_id}")
def get_node(
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific PKG node."""
    node = db.query(PKGNode).filter(
        PKGNode.id == node_id,
        PKGNode.user_id == current_user.id
    ).first()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return node


# ========== GraphRAG ==========

@router.post("/pkg/query", response_model=GraphRAGResponse)
def graph_rag_query(
    query: GraphRAGQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query knowledge graph using hybrid search."""
    graph_rag = GraphRAG(db)
    
    result = graph_rag.answer_query(query.query, current_user.id)
    
    # Format sources
    sources = []
    for chunk in result.get("source_chunks", []):
        doc = db.query(Document).filter(Document.id == chunk["document_id"]).first()
        sources.append({
            "document_id": chunk["document_id"],
            "title": doc.title if doc else "Unknown",
            "excerpt": chunk["text"][:200] + "...",
            "relevance_score": chunk["score"],
        })
    
    return GraphRAGResponse(
        answer=result["answer"],
        sources=sources,
        concepts=result.get("concepts_used", []),
        citations=result.get("citations", []),
    )


# ========== Augmented Reader ==========

@router.post("/documents/overlays")
def get_overlays(
    document_id: str,
    segment_text: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get contextual overlays for a document segment."""
    # Use GraphRAG to find relevant concepts
    graph_rag = GraphRAG(db)
    
    # Find related concepts
    results = graph_rag.search(segment_text, current_user.id, k=5)
    
    overlays = []
    for i, result in enumerate(results):
        if result.get("node_type") == "concept":
            overlays.append({
                "id": f"overlay_{i}",
                "type": "concept",
                "text": result.get("name", ""),
                "related_nodes": [r["id"] for r in results[:3]],
            })
    
    # Add definition overlay if concept found
    if overlays:
        overlays.insert(0, {
            "id": "overlay_def",
            "type": "definition",
            "text": f"Key concept in this section: {overlays[0]['text']}",
        })
    
    return overlays


@router.post("/documents/related-concepts")
def get_related_concepts(
    document_id: str,
    text_range: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get concepts related to a text range."""
    graph_rag = GraphRAG(db)
    results = graph_rag.search(text_range, current_user.id, k=10)
    
    return [
        {
            "id": r["id"],
            "name": r.get("name", ""),
            "node_type": r.get("node_type", "concept"),
            "confidence": r.get("confidence", 0.8),
        }
        for r in results if r.get("node_type") == "concept"
    ]
