"""
Graph Extraction Pipeline
From LIBRARY_PRD.md §3.3

Extracts entities and relationships from Knowledge Atoms to build PKG.
"""
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple

from celery import shared_task
from sqlalchemy import text
from sqlmodel import Session, select

from app.core.ai_gateway import generate_text, embed_texts
from app.core.database import SessionLocal
from app.knowledge.vector_store import vector_store, store_chunk_embeddings
from pydantic import BaseModel
from app.library.pkg_models import (
    PKGEdge,
    PKGEdgeType,
    PKGExtraction,
    PKGNode,
    PKGNodeType,
)


class Triple(BaseModel):
    """Subject-Predicate-Object triple extracted by LLM."""
    subject: str
    predicate: str
    object: str
    confidence: float = 0.8


class GraphUpdate(BaseModel):
    """Result of graph extraction."""
    new_nodes: List[PKGNode] = []
    merged_nodes: List[Dict[str, Any]] = []  # {existing_id, merged_id, similarity}
    new_edges: List[PKGEdge] = []
    novel_concepts: List[str] = []  # IDs of concepts new to user


EXTRACTION_PROMPT = """Extract (Subject, Predicate, Object) triples from the following text.

Rules:
- Subject: A concept, idea, or entity mentioned in the text
- Predicate: The relationship type - choose from: DEPENDS_ON, SUPPORTS, CONTRADICTS, EXTENDS, EXEMPLIFIES
- Object: The target concept, idea, or entity
- Confidence: 0.0-1.0 score of extraction certainty

Return ONLY valid JSON in this exact format:
[{"subject": "string", "predicate": "DEPENDS_ON|SUPPORTS|CONTRADICTS|EXTENDS|EXEMPLIFIES", "object": "string", "confidence": 0.9}]

Text to analyze:
{text}

JSON output:"""


def extract_triples_batch(atoms: List[Dict[str, Any]], batch_size: int = 10) -> List[Dict[str, Any]]:
    """
    Extract (S, P, O) triples from Knowledge Atoms using LLM.
    
    Args:
        atoms: List of Knowledge Atoms
        batch_size: Number of atoms to process per LLM call
    
    Returns:
        List of extracted triples
    """
    all_triples = []
    
    # Process in batches
    for i in range(0, len(atoms), batch_size):
        batch = atoms[i:i + batch_size]
        batch_text = "\n\n".join([f"[{j}] {a['text']}" for j, a in enumerate(batch)])
        
        prompt = EXTRACTION_PROMPT.format(text=batch_text)
        
        try:
            response = generate_text(
                prompt=prompt,
                model="gemini-flash",  # Use flash for cost efficiency
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse JSON response
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:-3] if json_str.endswith("```") else json_str[7:]
            elif json_str.startswith("```"):
                json_str = json_str[3:-3] if json_str.endswith("```") else json_str[3:]
            
            triples = json.loads(json_str)
            
            # Validate and normalize
            for t in triples:
                if all(k in t for k in ["subject", "predicate", "object"]):
                    # Normalize predicate
                    pred = t["predicate"].upper().replace(" ", "_")
                    if pred in ["DEPENDS_ON", "SUPPORTS", "CONTRADICTS", "EXTENDS", "EXEMPLIFIES"]:
                        t["predicate"] = pred
                        t["confidence"] = float(t.get("confidence", 0.8))
                        t["source_atom_index"] = i  # Track which atom
                        all_triples.append(t)
        
        except Exception as e:
            print(f"Error extracting triples from batch {i}: {e}")
            continue
    
    return all_triples


def resolve_entity(
    entity_name: str,
    embedding: List[float],
    user_id: str,
    db: Session,
    similarity_threshold: float = 0.90
) -> Tuple[str, bool]:
    """
    Entity Resolution: Check if entity already exists in PKG.
    
    Returns:
        (node_id, is_existing)
    """
    # Search Qdrant for similar concepts
    similar = vector_store.search(
        vector=embedding,
        filter={"user_id": user_id, "node_type": "concept"},
        limit=5
    )
    
    if similar and similar[0].score > similarity_threshold:
        # Found existing node
        return similar[0].id, True
    
    # Create new node
    return str(uuid.uuid4()), False


def build_graph_from_triples(
    triples: List[Dict[str, Any]],
    atoms: List[Dict[str, Any]],
    document_id: str,
    user_id: str,
    db: Session
) -> Dict[str, Any]:
    """
    Build PKG updates from extracted triples.
    
    Returns:
        GraphUpdate stats
    """
    new_nodes = []
    merged_nodes = []
    new_edges = []
    novel_concepts = []
    
    # Track created nodes to avoid duplicates
    created_nodes: Dict[str, PKGNode] = {}
    
    for triple in triples:
        subject_name = triple["subject"]
        predicate = triple["predicate"]
        object_name = triple["object"]
        confidence = triple.get("confidence", 0.8)
        atom_index = triple.get("source_atom_index", 0)
        
        # Get or create subject node
        if subject_name not in created_nodes:
            from app.core.ai_gateway import embed_texts
            subject_embedding = embed_texts([subject_name])[0]
            
            subject_id, exists = resolve_entity(subject_name, subject_embedding, user_id, db)
            
            if not exists:
                # Check user's existing knowledge
                user_knows = check_user_knowledge(subject_id, user_id, db)
                
                node = PKGNode(
                    id=subject_id,
                    user_id=user_id,
                    node_type=PKGNodeType.CONCEPT,
                    name=subject_name,
                    source_atoms=[atoms[atom_index].get("id", str(atom_index))],
                    source_documents=[document_id],
                    confidence=confidence,
                    embedding_vector_id=subject_id,
                    knowledge_state="gap" if not user_knows else "known",
                )
                new_nodes.append(node)
                created_nodes[subject_name] = node
                
                if not user_knows:
                    novel_concepts.append(subject_id)
            else:
                merged_nodes.append({
                    "existing_id": subject_id,
                    "merged_name": subject_name,
                    "similarity": 0.95
                })
                # Load existing node
                existing = db.get(PKGNode, subject_id)
                if existing:
                    created_nodes[subject_name] = existing
        
        # Get or create object node
        if object_name not in created_nodes:
            from app.core.ai_gateway import embed_texts
            object_embedding = embed_texts([object_name])[0]
            
            object_id, exists = resolve_entity(object_name, object_embedding, user_id, db)
            
            if not exists:
                user_knows = check_user_knowledge(object_id, user_id, db)
                
                node = PKGNode(
                    id=object_id,
                    user_id=user_id,
                    node_type=PKGNodeType.CONCEPT,
                    name=object_name,
                    source_atoms=[atoms[atom_index].get("id", str(atom_index))],
                    source_documents=[document_id],
                    confidence=confidence,
                    embedding_vector_id=object_id,
                    knowledge_state="gap" if not user_knows else "known",
                )
                new_nodes.append(node)
                created_nodes[object_name] = node
                
                if not user_knows:
                    novel_concepts.append(object_id)
            else:
                merged_nodes.append({
                    "existing_id": object_id,
                    "merged_name": object_name,
                    "similarity": 0.95
                })
                existing = db.get(PKGNode, object_id)
                if existing:
                    created_nodes[object_name] = existing
        
        # Create edge
        subject_node = created_nodes.get(subject_name)
        object_node = created_nodes.get(object_name)
        
        if subject_node and object_node:
            edge = PKGEdge(
                id=str(uuid.uuid4()),
                user_id=user_id,
                source_id=subject_node.id,
                target_id=object_node.id,
                edge_type=PKGEdgeType(predicate),
                confidence=confidence,
                evidence_atoms=[atoms[atom_index].get("id", str(atom_index))],
            )
            new_edges.append(edge)
            
            # Update adjacency list in source node
            if not subject_node.relationships:
                subject_node.relationships = []
            
            subject_node.relationships.append({
                "target_id": object_node.id,
                "type": predicate,
                "confidence": confidence,
                "created_at": datetime.utcnow().isoformat(),
            })
    
    return {
        "new_nodes": new_nodes,
        "merged_nodes": merged_nodes,
        "new_edges": new_edges,
        "novel_concepts": novel_concepts,
    }


def check_user_knowledge(node_id: str, user_id: str, db: Session) -> bool:
    """Check if user already knows a concept (has KNOWS edge)."""
    edge = db.exec(
        select(PKGEdge).where(
            PKGEdge.user_id == user_id,
            PKGEdge.target_id == node_id,
            PKGEdge.edge_type == PKGEdgeType.KNOWS
        )
    ).first()
    return edge is not None


@shared_task(bind=True, max_retries=3)
def extract_graph_task(self, document_id: str, user_id: str):
    """
    Celery task to extract PKG from document.
    """
    db = SessionLocal()
    
    try:
        # Create extraction log
        extraction = PKGExtraction(
            user_id=user_id,
            document_id=document_id,
            status="running"
        )
        db.add(extraction)
        db.commit()
        db.refresh(extraction)
        
        # Get document atoms
        from app.models.document import DocumentChunk
        chunks = db.exec(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        ).all()
        
        atoms = [{"id": c.id, "text": c.content} for c in chunks]
        extraction.atoms_processed = len(atoms)
        
        # Extract triples
        triples = extract_triples_batch(atoms)
        
        # Build graph
        result = build_graph_from_triples(triples, atoms, document_id, user_id, db)
        
        # Save to database
        for node in result["new_nodes"]:
            db.add(node)
            # Store embedding
            from app.core.ai_gateway import embed_texts
            embedding = embed_texts([node.name])[0]
            vector_store.upsert_document(
                doc_id=node.id,
                content=node.name,
                metadata={
                    "type": "pkg_node",
                    "user_id": user_id,
                    "node_type": node.node_type.value,
                }
            )
        
        for edge in result["new_edges"]:
            db.add(edge)
        
        # Update extraction log
        extraction.status = "completed"
        extraction.nodes_created = len(result["new_nodes"])
        extraction.nodes_merged = len(result["merged_nodes"])
        extraction.edges_created = len(result["new_edges"])
        extraction.completed_at = datetime.utcnow()
        
        db.add(extraction)
        db.commit()
        
        return {
            "extraction_id": extraction.id,
            "nodes_created": extraction.nodes_created,
            "edges_created": extraction.edges_created,
            "novel_concepts": len(result["novel_concepts"]),
        }
        
    except Exception as exc:
        extraction.status = "failed"
        extraction.error_message = str(exc)
        db.add(extraction)
        db.commit()
        
        if self.request.retries < 3:
            raise self.retry(exc=exc, countdown=60)
        
        return {"error": str(exc)}
    
    finally:
        db.close()


from datetime import datetime
