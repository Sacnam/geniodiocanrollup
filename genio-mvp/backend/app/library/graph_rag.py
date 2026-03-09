"""
GraphRAG - Cross-Document Reasoning
From LIBRARY_PRD.md §3.7

Hybrid search combining vector similarity with graph traversal.
"""
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlmodel import Session, select

from app.core.ai_gateway import embed_texts, generate_text
from app.knowledge.vector_store import vector_store
from app.library.pkg_models import PKGEdge, PKGEdgeType, PKGNode


def hybrid_search(
    query: str,
    user_id: str,
    db: Session,
    k_vector: int = 10,
    k_graph: int = 5,
    graph_hops: int = 2
) -> List[Dict]:
    """
    Hybrid search: Vector + Graph traversal.
    
    Args:
        query: Search query
        user_id: User ID for PKG context
        k_vector: Number of vector search results
        k_graph: Number of graph traversal results
        graph_hops: Number of hops for graph traversal
    
    Returns:
        Fused results with scores
    """
    # Step 1: Vector search (broad recall)
    query_embedding = embed_texts([query])[0]
    
    vector_results = vector_store.search(
        vector=query_embedding,
        filter={"user_id": user_id},
        limit=k_vector
    )
    
    # Step 2: Graph traversal (structured context)
    # Find relevant nodes in PKG
    pkg_nodes = db.exec(
        select(PKGNode).where(
            PKGNode.user_id == user_id,
            PKGNode.node_type == "concept"
        )
    ).all()
    
    # Get embeddings for PKG nodes
    node_names = [node.name for node in pkg_nodes]
    if node_names:
        node_embeddings = embed_texts(node_names)
        
        # Find most similar nodes to query
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        
        similarities = cosine_similarity([query_embedding], node_embeddings)[0]
        top_nodes = [
            (pkg_nodes[i], similarities[i])
            for i in np.argsort(similarities)[-k_graph:]
        ]
        
        # Traverse graph from top nodes
        graph_results = []
        for node, sim in top_nodes:
            subgraph = traverse_graph(node.id, user_id, db, hops=graph_hops)
            graph_results.append({
                "node": node,
                "similarity": sim,
                "subgraph": subgraph
            })
    else:
        graph_results = []
    
    # Step 3: Reciprocal Rank Fusion
    fused_results = reciprocal_rank_fusion(
        vector_results=[{"id": r.id, "score": r.score} for r in vector_results],
        graph_results=[{"id": r["node"].id, "score": r["similarity"]} for r in graph_results],
        k=60  # RRF constant
    )
    
    return fused_results


def traverse_graph(
    start_node_id: str,
    user_id: str,
    db: Session,
    hops: int = 2
) -> Dict:
    """
    Traverse PKG from starting node.
    
    Uses PostgreSQL recursive CTE for graph traversal.
    """
    query = text("""
        WITH RECURSIVE graph_traversal AS (
            -- Base case: starting node
            SELECT 
                source_id as node_id,
                target_id as connected_id,
                edge_type,
                confidence,
                1 as depth
            FROM pkg_edges
            WHERE source_id = :start_id AND user_id = :user_id
            
            UNION ALL
            
            -- Recursive case: follow edges
            SELECT 
                e.source_id,
                e.target_id,
                e.edge_type,
                e.confidence,
                gt.depth + 1
            FROM pkg_edges e
            JOIN graph_traversal gt ON e.source_id = gt.connected_id
            WHERE gt.depth < :max_depth
            AND e.user_id = :user_id
        )
        SELECT * FROM graph_traversal
        ORDER BY depth, confidence DESC;
    """)
    
    result = db.execute(query, {
        "start_id": start_node_id,
        "user_id": user_id,
        "max_depth": hops
    })
    
    nodes = set()
    edges = []
    
    for row in result:
        nodes.add(row.node_id)
        nodes.add(row.connected_id)
        edges.append({
            "source": row.node_id,
            "target": row.connected_id,
            "type": row.edge_type,
            "confidence": row.confidence,
            "depth": row.depth
        })
    
    # Load node details
    node_details = db.exec(
        select(PKGNode).where(PKGNode.id.in_(nodes))
    ).all()
    
    return {
        "nodes": [{"id": n.id, "name": n.name, "type": n.node_type} for n in node_details],
        "edges": edges
    }


def reciprocal_rank_fusion(
    vector_results: List[Dict],
    graph_results: List[Dict],
    k: int = 60
) -> List[Dict]:
    """
    Reciprocal Rank Fusion of vector and graph results.
    
    Formula: score = sum(1 / (k + rank)) for each list
    """
    scores = {}
    
    # Add vector scores
    for rank, result in enumerate(vector_results):
        doc_id = result["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    
    # Add graph scores
    for rank, result in enumerate(graph_results):
        doc_id = result["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    
    # Sort by fused score
    fused = sorted(
        [{"id": doc_id, "score": score} for doc_id, score in scores.items()],
        key=lambda x: x["score"],
        reverse=True
    )
    
    return fused


def detect_contradictions(user_id: str, db: Session) -> List[Dict]:
    """
    Detect contradictions in user's PKG.
    
    Finds CONTRADICTS edges and flags for user attention.
    """
    contradictions = db.exec(
        select(PKGEdge, PKGNode).join(
            PKGNode, PKGEdge.source_id == PKGNode.id
        ).where(
            PKGEdge.user_id == user_id,
            PKGEdge.edge_type == PKGEdgeType.CONTRADICTS
        )
    ).all()
    
    results = []
    for edge, source_node in contradictions:
        target_node = db.get(PKGNode, edge.target_id)
        if target_node:
            results.append({
                "source": {
                    "id": source_node.id,
                    "name": source_node.name,
                    "document_ids": source_node.source_documents
                },
                "target": {
                    "id": target_node.id,
                    "name": target_node.name,
                    "document_ids": target_node.source_documents
                },
                "confidence": edge.confidence,
                "evidence_atoms": edge.evidence_atoms
            })
    
    return results


def answer_cross_document_query(
    query: str,
    user_id: str,
    db: Session
) -> Dict:
    """
    Answer a query using cross-document reasoning.
    
    Example: "How does Author A's argument relate to Author B's?"
    """
    # Step 1: Hybrid search for relevant context
    search_results = hybrid_search(query, user_id, db)
    
    # Step 2: Gather context from top results
    context_parts = []
    
    for result in search_results[:5]:
        node = db.get(PKGNode, result["id"])
        if node:
            # Get connected nodes for context
            connected = traverse_graph(node.id, user_id, db, hops=1)
            
            context_parts.append(f"""
Concept: {node.name}
Definition: {node.definition or 'N/A'}
Related concepts: {', '.join([n['name'] for n in connected['nodes'][:3]])}
Source documents: {', '.join(node.source_documents[:2])}
""")
    
    # Step 3: Generate answer
    context = "\n---\n".join(context_parts)
    
    prompt = f"""Answer the following question based on the knowledge graph context.

Question: {query}

Context from Personal Knowledge Graph:
{context}

Provide a concise answer that synthesizes information across documents. 
Cite specific concepts and their relationships."""
    
    answer = generate_text(
        prompt=prompt,
        model="gemini-flash",
        temperature=0.3,
        max_tokens=1000
    )
    
    return {
        "query": query,
        "answer": answer,
        "sources": search_results[:5],
        "context_size": len(context_parts)
    }


def get_citation_chain(
    claim_node_id: str,
    user_id: str,
    db: Session
) -> List[Dict]:
    """
    Trace evidence path: Claim → Supporting Atom → Source Document.
    """
    node = db.get(PKGNode, claim_node_id)
    if not node:
        return []
    
    chain = []
    
    # Get supporting edges
    supports = db.exec(
        select(PKGEdge).where(
            PKGEdge.target_id == claim_node_id,
            PKGEdge.edge_type == PKGEdgeType.SUPPORTS,
            PKGEdge.user_id == user_id
        )
    ).all()
    
    for edge in supports:
        source_node = db.get(PKGNode, edge.source_id)
        if source_node:
            chain.append({
                "step": "evidence",
                "node": source_node,
                "evidence_atoms": edge.evidence_atoms,
                "confidence": edge.confidence
            })
    
    # Get source documents
    for doc_id in node.source_documents:
        from app.models.document import Document
        doc = db.get(Document, doc_id)
        if doc:
            chain.append({
                "step": "source",
                "document": {
                    "id": doc.id,
                    "title": doc.title,
                    "author": doc.author
                }
            })
    
    return chain
