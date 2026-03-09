"""
Knowledge Delta for Documents - Atom-level novelty detection
"""
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session

from app.library.embeddings import get_embedding, cosine_similarity
from app.models.document_atom import DocumentAtom
from app.models.user import User


# Delta thresholds
DUPLICATE_THRESHOLD = 0.90  # Hide completely
RELATED_THRESHOLD = 0.85    # Show but note as related
NOVEL_THRESHOLD = 0.85      # Below this = novel


class DocumentDeltaCalculator:
    """Calculate Knowledge Delta for document atoms."""
    
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
    
    async def calculate_atom_delta(self, atom: DocumentAtom) -> float:
        """
        Calculate delta score for a single atom.
        
        Returns 0.0-1.0 where:
        - 1.0 = completely novel (nothing similar in user's knowledge)
        - 0.0 = completely duplicate (highly similar content exists)
        """
        # Get embedding for this atom
        atom_embedding = await get_embedding(atom.content)
        
        # Search for similar atoms in user's knowledge
        similar = await self._find_similar_atoms(atom_embedding, top_k=5)
        
        if not similar:
            # Completely novel
            return 1.0
        
        # Calculate delta based on max similarity
        max_similarity = max(s['score'] for s in similar)
        
        # Delta = 1 - similarity (inverted)
        # But we want some nuance in the middle range
        if max_similarity >= DUPLICATE_THRESHOLD:
            delta = 0.0  # Duplicate
        elif max_similarity >= RELATED_THRESHOLD:
            delta = 0.5  # Related
        else:
            delta = 1.0 - max_similarity
        
        return round(delta, 2)
    
    async def _find_similar_atoms(self, embedding: List[float], top_k: int = 5) -> List[Dict]:
        """Find similar atoms in user's knowledge graph."""
        # This would query Qdrant for similar vectors
        # For now, return empty (implementation depends on vector store)
        
        # TODO: Implement Qdrant query
        # query_result = qdrant_client.search(
        #     collection_name="atoms",
        #     query_vector=embedding,
        #     query_filter={"user_id": self.user_id},
        #     limit=top_k
        # )
        
        return []
    
    async def calculate_document_delta(self, document_id: str) -> Dict:
        """
        Calculate delta for all atoms in a document.
        
        Returns:
            Dict with document-level novelty metrics
        """
        atoms = self.db.query(DocumentAtom).filter(
            DocumentAtom.document_id == document_id
        ).all()
        
        if not atoms:
            return {
                "document_id": document_id,
                "total_atoms": 0,
                "novel_atoms": 0,
                "related_atoms": 0,
                "duplicate_atoms": 0,
                "novelty_score": 0.0,
                "is_redundant": False
            }
        
        novel_count = 0
        related_count = 0
        duplicate_count = 0
        
        for atom in atoms:
            delta = await self.calculate_atom_delta(atom)
            atom.delta_score = delta
            
            if delta >= DUPLICATE_THRESHOLD:
                atom.is_redundant = True
                atom.is_novel = False
                duplicate_count += 1
            elif delta >= RELATED_THRESHOLD:
                atom.is_novel = False
                related_count += 1
            else:
                atom.is_novel = True
                novel_count += 1
        
        self.db.commit()
        
        # Calculate document-level metrics
        total = len(atoms)
        novelty_score = sum(a.delta_score for a in atoms) / total
        
        # Document is redundant if >50% atoms are duplicates
        is_redundant = duplicate_count / total > 0.5
        
        return {
            "document_id": document_id,
            "total_atoms": total,
            "novel_atoms": novel_count,
            "related_atoms": related_count,
            "duplicate_atoms": duplicate_count,
            "novelty_score": round(novelty_score, 2),
            "is_redundant": is_redundant
        }
    
    def detect_redundant_chapters(self, document_id: str) -> List[Dict]:
        """
        Detect chapters with low novelty (mostly known content).
        
        Returns:
            List of redundant chapters with their delta scores
        """
        from sqlalchemy import func
        
        chapter_stats = self.db.query(
            DocumentAtom.chapter_title,
            DocumentAtom.chapter_index,
            func.avg(DocumentAtom.delta_score).label("avg_delta"),
            func.count(DocumentAtom.id).label("atom_count")
        ).filter(
            DocumentAtom.document_id == document_id
        ).group_by(
            DocumentAtom.chapter_title,
            DocumentAtom.chapter_index
        ).all()
        
        redundant = []
        for chapter in chapter_stats:
            if chapter.avg_delta < 0.15:  # Threshold for redundant chapter
                redundant.append({
                    "title": chapter.chapter_title,
                    "index": chapter.chapter_index,
                    "avg_delta": round(chapter.avg_delta, 2),
                    "atom_count": chapter.atom_count,
                    "is_redundant": True
                })
        
        return redundant


class DeltaClassifier:
    """Classify atoms into delta categories."""
    
    @staticmethod
    def classify(delta_score: float) -> str:
        """Classify atom by delta score."""
        if delta_score >= DUPLICATE_THRESHOLD:
            return "DUPLICATE"
        elif delta_score >= RELATED_THRESHOLD:
            return "RELATED"
        else:
            return "NOVEL"
    
    @staticmethod
    def should_show(delta_score: float) -> bool:
        """Determine if atom should be shown to user."""
        return delta_score < DUPLICATE_THRESHOLD
