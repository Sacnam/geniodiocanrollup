"""
AI Gateway - Centralized AI service integration
Wraps LiteLLM with cost tracking and error handling.
"""
from typing import List, Optional, Dict, Any
import time

import litellm
from litellm import completion, embedding

from app.core.config import settings
from app.services.ai_service import track_ai_cost


def embed_texts(
    texts: List[str],
    user_id: Optional[str] = None,
    model: str = "text-embedding-3-small"
) -> List[List[float]]:
    """
    Generate embeddings for texts with cost tracking.
    
    Args:
        texts: List of texts to embed
        user_id: User ID for cost tracking
        model: Embedding model to use
        
    Returns:
        List of embedding vectors
    """
    if not texts:
        return []
    
    start_time = time.time()
    
    try:
        # Call LiteLLM embedding
        response = embedding(
            model=model,
            input=texts,
            api_key=settings.OPENAI_API_KEY if "openai" in model else None,
        )
        
        # Extract embeddings
        embeddings = [item["embedding"] for item in response["data"]]
        
        # Track cost if user_id provided
        if user_id:
            # Calculate cost based on tokens
            total_tokens = response.get("usage", {}).get("total_tokens", 0)
            
            # Pricing per 1K tokens
            pricing = {
                "text-embedding-3-small": 0.00002,
                "text-embedding-3-large": 0.00013,
                "text-embedding-ada-002": 0.00010,
            }
            
            cost = (total_tokens / 1000) * pricing.get(model, 0.00002)
            
            track_ai_cost(
                user_id=user_id,
                cost_usd=cost,
                operation="embedding",
                model=model,
                input_tokens=total_tokens,
                output_tokens=0,
            )
        
        return embeddings
        
    except Exception as e:
        # Log error but don't expose details
        import structlog
        logger = structlog.get_logger()
        logger.error("Embedding failed", error=str(e), user_id=user_id)
        
        # Return zero embeddings as fallback
        dim = 1536 if "small" in model else 3072
        return [[0.0] * dim for _ in texts]


def generate_text(
    prompt: str,
    model: str = "gemini-flash",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    user_id: Optional[str] = None,
    operation: str = "generation",
) -> str:
    """
    Generate text with LiteLLM with cost tracking.
    
    Args:
        prompt: The prompt to send
        model: Model to use (gemini-flash, gpt-4o, etc.)
        temperature: Sampling temperature
        max_tokens: Max tokens to generate
        user_id: User ID for cost tracking
        operation: Operation type for tracking
        
    Returns:
        Generated text
    """
    start_time = time.time()
    
    # Map model aliases to actual LiteLLM model names
    model_mapping = {
        "gemini-flash": "gemini/gemini-1.5-flash",
        "gemini-pro": "gemini/gemini-1.5-pro",
        "gpt-4o": "openai/gpt-4o",
        "gpt-4o-mini": "openai/gpt-4o-mini",
    }
    
    actual_model = model_mapping.get(model, model)
    
    try:
        response = completion(
            model=actual_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.GEMINI_API_KEY if "gemini" in actual_model else settings.OPENAI_API_KEY,
        )
        
        # Extract generated text
        generated = response["choices"][0]["message"]["content"]
        
        # Track cost if user_id provided
        if user_id:
            usage = response.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            
            # Pricing per 1K tokens (approximate)
            pricing = {
                "gemini-flash": {"input": 0.00035, "output": 0.00105},
                "gemini-pro": {"input": 0.0035, "output": 0.0105},
                "gpt-4o": {"input": 0.005, "output": 0.015},
                "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            }
            
            model_pricing = pricing.get(model, {"input": 0.005, "output": 0.015})
            cost = (input_tokens / 1000) * model_pricing["input"] + \
                   (output_tokens / 1000) * model_pricing["output"]
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            track_ai_cost(
                user_id=user_id,
                cost_usd=cost,
                operation=operation,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
            )
        
        return generated
        
    except Exception as e:
        import structlog
        logger = structlog.get_logger()
        logger.error("Text generation failed", error=str(e), model=model, user_id=user_id)
        
        # Return empty string on failure
        return ""


def generate_json(
    prompt: str,
    model: str = "gemini-flash",
    temperature: float = 0.1,
    user_id: Optional[str] = None,
    operation: str = "json_generation",
) -> Optional[Dict[str, Any]]:
    """
    Generate JSON response with LiteLLM.
    
    Args:
        prompt: The prompt to send
        model: Model to use
        temperature: Sampling temperature
        user_id: User ID for cost tracking
        operation: Operation type for tracking
        
    Returns:
        Parsed JSON dict or None on failure
    """
    import json
    
    text = generate_text(
        prompt=prompt + "\n\nReturn ONLY valid JSON.",
        model=model,
        temperature=temperature,
        user_id=user_id,
        operation=operation,
    )
    
    # Clean up response
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Count tokens in text.
    
    Args:
        text: Text to count
        model: Model to use for counting
        
    Returns:
        Token count
    """
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        # Fallback: approximate (1 token ≈ 4 chars)
        return len(text) // 4
