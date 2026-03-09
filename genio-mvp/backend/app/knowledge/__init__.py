"""
Knowledge management package for Genio Knowledge OS.

This package provides the core knowledge processing capabilities:

Modules:
    - graph_extraction: Entity and relationship extraction from documents
    - semantic_chunking: Topic-aware document chunking
    - knowledge_delta: Novelty scoring and deduplication

Note:
    The primary implementations for these features are currently located in:
    - app.library.graph_extractor: Graph extraction from documents
    - app.library.semantic_chunker: Semantic chunking logic
    - app.library.graph_rag: GraphRAG implementation
    
    This module serves as a namespace package and will be expanded with
    dedicated implementations in future versions.

Architecture Decision:
    The knowledge processing logic was initially placed in the library/
    module for tighter integration with document processing. Future
    refactoring may move core algorithms here for better separation
    of concerns.

Example:
    >>> from app.knowledge import extract_knowledge_graph
    >>> from app.library.graph_extractor import GraphExtractor
    >>> 
    >>> # Current usage (via library module)
    >>> extractor = GraphExtractor()
    >>> graph = await extractor.extract(document_content)
"""

# Re-export key functions from library module for convenience
# This provides a stable API while allowing internal refactoring

from app.library.graph_extractor import GraphExtractor
from app.library.semantic_chunker import SemanticChunker

__all__ = [
    'GraphExtractor',
    'SemanticChunker',
]

# Version info for the knowledge module
__version__ = '0.1.0'