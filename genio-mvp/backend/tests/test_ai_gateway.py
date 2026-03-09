"""Tests for AI Gateway."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.core.ai_gateway import embed_texts, generate_text, generate_json, count_tokens


class TestAIGateway:
    """Test AI gateway functions."""

    @patch("app.core.ai_gateway.embedding")
    @patch("app.core.ai_gateway.track_ai_cost")
    def test_embed_texts(self, mock_track, mock_embed):
        """Should generate embeddings and track cost."""
        mock_embed.return_value = {
            "data": [
                {"embedding": [0.1] * 1536},
                {"embedding": [0.2] * 1536},
            ],
            "usage": {"total_tokens": 100}
        }
        
        result = embed_texts(
            texts=["text 1", "text 2"],
            user_id="user-123",
            model="text-embedding-3-small"
        )
        
        assert len(result) == 2
        assert len(result[0]) == 1536
        mock_embed.assert_called_once()
        mock_track.assert_called_once()

    @patch("app.core.ai_gateway.embedding")
    def test_embed_texts_no_user(self, mock_embed):
        """Should generate embeddings without tracking."""
        mock_embed.return_value = {
            "data": [{"embedding": [0.1] * 1536}],
            "usage": {"total_tokens": 50}
        }
        
        result = embed_texts(
            texts=["text"],
            user_id=None,  # No tracking
        )
        
        assert len(result) == 1

    @patch("app.core.ai_gateway.embedding")
    def test_embed_texts_empty(self, mock_embed):
        """Should handle empty input."""
        result = embed_texts(texts=[])
        
        assert result == []
        mock_embed.assert_not_called()

    @patch("app.core.ai_gateway.completion")
    @patch("app.core.ai_gateway.track_ai_cost")
    def test_generate_text(self, mock_track, mock_complete):
        """Should generate text and track cost."""
        mock_complete.return_value = {
            "choices": [{"message": {"content": "Generated text"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
        
        result = generate_text(
            prompt="Test prompt",
            user_id="user-123",
            model="gemini-flash"
        )
        
        assert result == "Generated text"
        mock_complete.assert_called_once()
        mock_track.assert_called_once()

    @patch("app.core.ai_gateway.completion")
    def test_generate_text_error(self, mock_complete):
        """Should handle generation errors."""
        mock_complete.side_effect = Exception("API Error")
        
        result = generate_text(
            prompt="Test prompt",
            user_id="user-123"
        )
        
        assert result == ""  # Returns empty on error

    @patch("app.core.ai_gateway.generate_text")
    def test_generate_json(self, mock_generate):
        """Should generate and parse JSON."""
        mock_generate.return_value = '{"key": "value", "number": 42}'
        
        result = generate_json(
            prompt="Generate JSON",
            user_id="user-123"
        )
        
        assert result == {"key": "value", "number": 42}

    @patch("app.core.ai_gateway.generate_text")
    def test_generate_json_with_code_block(self, mock_generate):
        """Should parse JSON from markdown code block."""
        mock_generate.return_value = '```json\n{"key": "value"}\n```'
        
        result = generate_json(prompt="Generate JSON")
        
        assert result == {"key": "value"}

    @patch("app.core.ai_gateway.generate_text")
    def test_generate_json_invalid(self, mock_generate):
        """Should handle invalid JSON."""
        mock_generate.return_value = "Not valid JSON"
        
        result = generate_json(prompt="Generate JSON")
        
        assert result is None

    def test_count_tokens(self):
        """Should approximate token count."""
        # This is an approximation test
        text = "Hello world"
        count = count_tokens(text)
        
        assert count > 0
        assert count >= len(text) // 4  # Rough approximation
