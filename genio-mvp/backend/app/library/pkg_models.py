"""
Personal Knowledge Graph (PKG) Models
From LIBRARY_PRD.md §3.3

Graph Schema for user-specific knowledge representation.
Stored in PostgreSQL using JSONB (no Neo4j at MVP).
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class PKGNodeType(str, Enum):
    CONCEPT = "concept"
    ATOM = "atom"
    DOCUMENT = "document"


class PKGEedgeType(str, Enum):
    DEPENDS_ON = "depends_on"      # Concept → Concept (logical dependency)
    SUPPORTS = "supports"          # Atom → Concept (evidence)
    CONTRADICTS = "contradicts"    # Concept ↔ Concept (conflict)
    EXTENDS = "extends"            # Concept → Concept (builds upon)
    EXEMPLIFIES = "exemplifies"    # Atom → Concept (example)
    CONTAINS = "contains"          # Document → Atom
    KNOWS = "knows"                # User → Concept


class PKGNode(SQLModel, table=True):
    """
    Node in the Personal Knowledge Graph.
    Stored in PostgreSQL with JSONB for relationships.
    """
    __tablename__ = "pkg_nodes"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Node identity
    node_type: PKGNodeType
    name: str  # Concept name, atom excerpt, or document title
    
    # Content (varies by type)
    definition: Optional[str] = None  # For concepts
    source_atoms: List[str] = Field(default=[], sa_column=Column(JSONB))
    source_documents: List[str] = Field(default=[], sa_column=Column(JSONB))
    
    # Metadata
    confidence: float = Field(default=0.8)  # 0-1 confidence in node validity
    embedding_vector_id: Optional[str] = Field(default=None, index=True)
    
    # User knowledge state
    knowledge_state: str = Field(default="gap")  # known, gap, learning
    last_seen: Optional[datetime] = None
    review_count: int = Field(default=0)
    
    # Graph relationships (edges stored as adjacency list)
    relationships: List[Dict[str, Any]] = Field(
        default=[],
        sa_column=Column(JSONB),
        description="List of {target_id, type, confidence, created_at}"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "node_type": "concept",
                "name": "Bayesian Priors",
                "definition": "Prior probability distribution in Bayesian inference",
                "confidence": 0.85,
                "knowledge_state": "known",
                "relationships": [
                    {"target_id": "node-xyz", "type": "depends_on", "confidence": 0.92}
                ]
            }
        }


class PKGEdge(SQLModel, table=True):
    """
    Explicit edge table for efficient graph traversal.
    Complements the adjacency list in PKGNode.
    """
    __tablename__ = "pkg_edges"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    source_id: str = Field(index=True)  # Source node ID
    target_id: str = Field(index=True)  # Target node ID
    edge_type: PKGEedgeType
    
    confidence: float = Field(default=0.8)
    evidence_atoms: List[str] = Field(default=[], sa_column=Column(JSONB))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PKGExtraction(SQLModel, table=True):
    """Log of graph extraction operations."""
    __tablename__ = "pkg_extractions"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    document_id: str = Field(foreign_key="documents.id", index=True)
    
    status: str = Field(default="running")  # running, completed, failed
    
    # Metrics
    atoms_processed: int = Field(default=0)
    nodes_created: int = Field(default=0)
    nodes_merged: int = Field(default=0)
    edges_created: int = Field(default=0)
    
    # Errors
    error_message: Optional[str] = None
    
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


from pydantic import BaseModel


# Helper types for graph operations
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
