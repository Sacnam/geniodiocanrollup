"""Tests for PKG Graph Extractor."""
import pytest
from unittest.mock import Mock, patch

from app.library.graph_extractor import (
    extract_triples_batch,
    check_user_knowledge,
    EXTRACTION_PROMPT,
)


class TestGraphExtractor:
    """Test graph extraction from documents."""

    def test_extraction_prompt_format(self):
        """Prompt should include text placeholder."""
        assert "{text}" in EXTRACTION_PROMPT
        assert "subject" in EXTRACTION_PROMPT.lower()
        assert "predicate" in EXTRACTION_PROMPT.lower()
        assert "object" in EXTRACTION_PROMPT.lower()

    @patch("app.library.graph_extractor.generate_text")
    def test_extract_triples_batch(self, mock_generate):
        """Should extract triples from atoms."""
        mock_generate.return_value = '''```json
        [
            {"subject": "Machine Learning", "predicate": "DEPENDS_ON", "object": "Statistics", "confidence": 0.9},
            {"subject": "Deep Learning", "predicate": "EXTENDS", "object": "Machine Learning", "confidence": 0.85}
        ]
        ```'''
        
        atoms = [
            {"id": "atom1", "text": "Machine Learning depends on Statistics."},
            {"id": "atom2", "text": "Deep Learning extends Machine Learning concepts."},
        ]
        
        triples = extract_triples_batch(atoms, batch_size=2)
        
        assert len(triples) == 2
        assert triples[0]["subject"] == "Machine Learning"
        assert triples[0]["predicate"] == "DEPENDS_ON"
        assert triples[0]["object"] == "Statistics"

    @patch("app.library.graph_extractor.generate_text")
    def test_extract_triples_handles_invalid_json(self, mock_generate):
        """Should handle invalid JSON gracefully."""
        mock_generate.return_value = "Invalid JSON response"
        
        atoms = [{"id": "atom1", "text": "Some text."}]
        
        triples = extract_triples_batch(atoms)
        
        assert triples == []  # Should return empty list on error

    def test_check_user_knowledge(self, session):
        """Should check if user knows a concept."""
        # Initially user doesn't know anything
        result = check_user_knowledge("node-123", "user-456", session)
        assert result is False

    def test_extract_triples_validates_predicates(self):
        """Should only accept valid predicate types."""
        from unittest.mock import patch
        
        with patch("app.library.graph_extractor.generate_text") as mock_generate:
            mock_generate.return_value = '''[
                {"subject": "A", "predicate": "INVALID_PRED", "object": "B", "confidence": 0.9},
                {"subject": "C", "predicate": "SUPPORTS", "object": "D", "confidence": 0.8}
            ]'''
            
            atoms = [{"id": "atom1", "text": "Test"}]
            triples = extract_triples_batch(atoms)
            
            # Only valid predicate should be included
            assert len(triples) == 1
            assert triples[0]["predicate"] == "SUPPORTS"
