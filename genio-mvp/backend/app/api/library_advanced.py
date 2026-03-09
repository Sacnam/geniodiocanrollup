"""
Advanced Library API endpoints.
GraphRAG, PKG queries, and cross-document reasoning.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.api.auth import get_current_user
from app.core.database import get_session
from app.library.graph_rag import (
    answer_cross_document_query,
    detect_contradictions,
    get_citation_chain,
    hybrid_search,
)
from app.library.pkg_models import PKGNode, PKGEdge
from app.models.user import User

router = APIRouter(prefix="/library/advanced", tags=["library-advanced"])


class SearchRequest(BaseModel):
    query: str
    k_vector: int = 10
    k_graph: int = 5


class SearchResult(BaseModel):
    id: str
    score: float
    type: str
    name: str


class CrossDocumentQueryRequest(BaseModel):
    query: str


class CrossDocumentQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[dict]
    context_size: int


class ContradictionResponse(BaseModel):
    source: dict
    target: dict
    confidence: float
    evidence_atoms: List[str]


class CitationChainResponse(BaseModel):
    step: str
    node: Optional[dict] = None
    document: Optional[dict] = None
    evidence_atoms: Optional[List[str]] = None
    confidence: Optional[float] = None


@router.post("/search", response_model=List[SearchResult])
def hybrid_search_endpoint(
    req: SearchRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Hybrid search combining vector similarity with graph traversal.
    """
    results = hybrid_search(
        query=req.query,
        user_id=current_user.id,
        db=db,
        k_vector=req.k_vector,
        k_graph=req.k_graph
    )
    
    # Enrich with node details
    enriched = []
    for r in results:
        node = db.get(PKGNode, r["id"])
        if node:
            enriched.append({
                "id": r["id"],
                "score": r["score"],
                "type": node.node_type.value,
                "name": node.name
            })
    
    return enriched


@router.post("/query", response_model=CrossDocumentQueryResponse)
def cross_document_query(
    req: CrossDocumentQueryRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Answer complex queries using cross-document reasoning.
    
    Example: "How does Author A's argument relate to Author B's?"
    """
    result = answer_cross_document_query(
        query=req.query,
        user_id=current_user.id,
        db=db
    )
    
    return CrossDocumentQueryResponse(**result)


@router.get("/contradictions", response_model=List[ContradictionResponse])
def get_contradictions(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get detected contradictions in user's knowledge graph.
    """
    contradictions = detect_contradictions(current_user.id, db)
    return contradictions


@router.get("/citation-chain/{node_id}", response_model=List[CitationChainResponse])
def get_citation_chain_endpoint(
    node_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get citation chain for a claim.
    Traces: Claim → Supporting Evidence → Source Document
    """
    chain = get_citation_chain(node_id, current_user.id, db)
    return chain


@router.get("/pkg/nodes", response_model=List[dict])
def get_pkg_nodes(
    node_type: Optional[str] = None,
    knowledge_state: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get PKG nodes for current user.
    """
    query = select(PKGNode).where(PKGNode.user_id == current_user.id)
    
    if node_type:
        query = query.where(PKGNode.node_type == node_type)
    if knowledge_state:
        query = query.where(PKGNode.knowledge_state == knowledge_state)
    
    nodes = db.exec(query).all()
    
    return [
        {
            "id": n.id,
            "name": n.name,
            "type": n.node_type.value,
            "definition": n.definition,
            "confidence": n.confidence,
            "knowledge_state": n.knowledge_state,
            "source_documents": n.source_documents,
            "relationships": n.relationships
        }
        for n in nodes
    ]


@router.get("/pkg/graph")
def get_pkg_subgraph(
    center_node_id: Optional[str] = None,
    hops: int = 2,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get subgraph of PKG centered on a node.
    """
    from app.library.graph_rag import traverse_graph
    
    if center_node_id:
        # Validate node belongs to user
        node = db.get(PKGNode, center_node_id)
        if not node or node.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Node not found")
        
        subgraph = traverse_graph(center_node_id, current_user.id, db, hops=hops)
    else:
        # Get full graph (limited to 100 nodes)
        nodes = db.exec(
            select(PKGNode).where(
                PKGNode.user_id == current_user.id
            ).limit(100)
        ).all()
        
        edges = db.exec(
            select(PKGEdge).where(
                PKGEdge.user_id == current_user.id
            ).limit(200)
        ).all()
        
        subgraph = {
            "nodes": [{"id": n.id, "name": n.name, "type": n.node_type.value} for n in nodes],
            "edges": [{"source": e.source_id, "target": e.target_id, "type": e.edge_type.value} for e in edges]
        }
    
    return subgraph
