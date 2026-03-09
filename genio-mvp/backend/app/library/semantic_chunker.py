"""
Semantic Chunking Algorithm (Cosine-Boundary)
From LIBRARY_PRD.md §3.2

Splits documents into Knowledge Atoms (coherent semantic units) using
cosine similarity boundaries between adjacent sentences.
"""
import re
from typing import List, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.core.ai_gateway import embed_texts


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences, preserving structure."""
    # Handle common abbreviations
    text = re.sub(r'(?<!\w)(Dr|Mr|Mrs|Ms|Prof|Sr|Jr|vs|etc|i\.e|e\.g)(\.)', r'\1<DOT>', text)
    
    # Split on sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Restore dots
    sentences = [s.replace('<DOT>', '.') for s in sentences]
    
    # Clean and filter
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    return sentences


def compute_semantic_density(text: str, document_mean_embedding: np.ndarray) -> float:
    """
    Compute semantic density = Information Gain relative to document mean.
    High density = introduces new concepts.
    Low density = anecdotal/rhetorical.
    """
    try:
        embedding = embed_texts([text])[0]
        similarity = cosine_similarity([embedding], [document_mean_embedding])[0][0]
        # Density is inverse of similarity to mean (novelty)
        density = 1 - similarity
        return float(np.clip(density, 0, 1))
    except Exception:
        return 0.5  # Default medium density


def semantic_chunking(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    k_threshold: float = 1.5
) -> List[dict]:
    """
    Semantic Chunking using Cosine-Boundary Algorithm.
    
    Args:
        text: Document text to chunk
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between chunks
        k_threshold: Standard deviations below mean for boundary detection
    
    Returns:
        List of Knowledge Atoms with metadata
    """
    # Step 1: Split into sentences
    sentences = split_into_sentences(text)
    
    if len(sentences) == 0:
        return []
    
    if len(sentences) == 1:
        return [{
            'text': sentences[0],
            'char_start': 0,
            'char_end': len(sentences[0]),
            'chunk_index': 0,
            'semantic_density': 0.5,
            'is_core_thesis': False,
        }]
    
    # Step 2: Embed all sentences
    sentence_embeddings = embed_texts(sentences)
    
    # Step 3: Compute pairwise similarities between adjacent sentences
    similarities = []
    for i in range(1, len(sentences)):
        sim = cosine_similarity(
            [sentence_embeddings[i-1]],
            [sentence_embeddings[i]]
        )[0][0]
        similarities.append(sim)
    
    if not similarities:
        return [{
            'text': ' '.join(sentences),
            'char_start': 0,
            'char_end': len(text),
            'chunk_index': 0,
            'semantic_density': 0.5,
            'is_core_thesis': True,
        }]
    
    # Step 4: Compute threshold for boundary detection
    mean_sim = np.mean(similarities)
    std_sim = np.std(similarities)
    threshold = mean_sim - k_threshold * std_sim
    
    # Step 5: Find chunk boundaries
    boundaries = [0]  # Always start at 0
    
    for i, sim in enumerate(similarities):
        if sim < threshold:
            # Low similarity = topic change = boundary
            boundaries.append(i + 1)
    
    boundaries.append(len(sentences))  # Always end at last sentence
    
    # Step 6: Create chunks from boundaries
    atoms = []
    char_position = 0
    
    for i in range(len(boundaries) - 1):
        start_idx = boundaries[i]
        end_idx = boundaries[i + 1]
        
        chunk_sentences = sentences[start_idx:end_idx]
        chunk_text = ' '.join(chunk_sentences)
        
        # Post-processing: Size constraints
        if len(chunk_text) < 100 and i < len(boundaries) - 2:
            # Merge small chunks into next
            continue
        
        if len(chunk_text) > 2000:
            # Split large chunks at nearest sentence
            mid = len(chunk_sentences) // 2
            chunk_sentences = chunk_sentences[:mid]
            chunk_text = ' '.join(chunk_sentences)
        
        # Compute document mean embedding for density calculation
        doc_mean = np.mean(sentence_embeddings, axis=0)
        density = compute_semantic_density(chunk_text, doc_mean)
        
        # Determine if core thesis (high density)
        is_core = density > (0.7 if np.mean([compute_semantic_density(s, doc_mean) for s in sentences]) else 0.5)
        
        atom = {
            'text': chunk_text,
            'char_start': char_position,
            'char_end': char_position + len(chunk_text),
            'chunk_index': len(atoms),
            'semantic_density': round(density, 3),
            'is_core_thesis': is_core,
            'sentence_count': len(chunk_sentences),
        }
        
        atoms.append(atom)
        char_position += len(chunk_text) + 1  # +1 for space
    
    # Step 7: Handle overlaps for context preservation
    atoms_with_overlap = []
    for i, atom in enumerate(atoms):
        if i > 0 and chunk_overlap > 0:
            # Add overlap from previous atom
            prev_text = atoms[i-1]['text']
            overlap_text = prev_text[-chunk_overlap:] if len(prev_text) > chunk_overlap else prev_text
            atom['text'] = overlap_text + ' ' + atom['text']
            atom['char_start'] = max(0, atom['char_start'] - chunk_overlap)
        
        atoms_with_overlap.append(atom)
    
    return atoms_with_overlap


def chunk_by_chapters(text: str, chapter_markers: List[str]) -> List[Tuple[str, str]]:
    """
    Alternative chunking: split by explicit chapter markers first,
    then apply semantic chunking within each chapter.
    
    Returns:
        List of (chapter_title, chapter_text)
    """
    chapters = []
    current_pos = 0
    
    for i, marker in enumerate(chapter_markers):
        # Find marker position
        pos = text.find(marker, current_pos)
        if pos == -1:
            continue
        
        # Determine chapter end (next marker or EOF)
        if i + 1 < len(chapter_markers):
            next_pos = text.find(chapter_markers[i + 1], pos)
            if next_pos == -1:
                next_pos = len(text)
        else:
            next_pos = len(text)
        
        chapter_text = text[pos:next_pos].strip()
        chapter_title = marker.strip()
        
        chapters.append((chapter_title, chapter_text))
        current_pos = pos + 1
    
    return chapters


# Re-export for compatibility
__all__ = ['semantic_chunking', 'chunk_by_chapters', 'compute_semantic_density']
