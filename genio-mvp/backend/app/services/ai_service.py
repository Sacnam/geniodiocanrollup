import time
from typing import List, Optional

import litellm
from litellm import embedding as litellm_embedding

from app.core.config import settings
from app.core.redis import redis_client

# Configure LiteLLM
litellm.set_verbose = settings.DEBUG


class AIBudgetExceeded(Exception):
    """Raised when AI budget is exceeded."""
    pass


def get_embedding(text: str, user_id: Optional[str] = None) -> List[float]:
    """
    Get embedding vector for text.
    B01: Uses 1536-dim text-embedding-3-small.
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    response = litellm_embedding(
        model="text-embedding-3-small",
        input=text[:8000],  # Truncate if needed
        dimensions=1536,  # B01: 1536-dim optimization
        api_key=settings.OPENAI_API_KEY,
    )
    
    vector = response.data[0]["embedding"]
    
    # Track cost if user_id provided
    if user_id:
        # text-embedding-3-small: $0.02 per 1M tokens
        estimated_tokens = len(text) / 4
        cost = (estimated_tokens / 1_000_000) * 0.02
        track_ai_cost(user_id, cost)
    
    return vector


def get_embeddings_batch(texts: List[str], user_id: Optional[str] = None) -> List[List[float]]:
    """
    Get embeddings for multiple texts in one call (B13: Batch optimization).
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    # Truncate texts
    truncated = [t[:8000] for t in texts]
    
    response = litellm_embedding(
        model="text-embedding-3-small",
        input=truncated,
        dimensions=1536,
        api_key=settings.OPENAI_API_KEY,
    )
    
    vectors = [item["embedding"] for item in response.data]
    
    # Track cost
    if user_id:
        total_chars = sum(len(t) for t in texts)
        estimated_tokens = total_chars / 4
        cost = (estimated_tokens / 1_000_000) * 0.02
        track_ai_cost(user_id, cost)
    
    return vectors


def generate_summary(
    title: str,
    content: str,
    max_length: int = 200,
    user_id: Optional[str] = None,
    budget_remaining: Optional[float] = None,
) -> str:
    """
    Generate article summary using Gemini Flash (cheap & fast).
    """
    if budget_remaining is not None and budget_remaining < 0.01:
        raise AIBudgetExceeded("AI budget exceeded")
    
    if not settings.GEMINI_API_KEY:
        # Fallback: return excerpt
        return content[:max_length] + "..." if len(content) > max_length else content
    
    prompt = f"""Summarize this article in 2-3 sentences. Be factual and neutral.

Title: {title}

Content: {content[:6000]}

Summary:"""
    
    try:
        response = litellm.completion(
            model="gemini/gemini-1.5-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_length,
            temperature=0.3,
            api_key=settings.GEMINI_API_KEY,
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Track cost
        if user_id:
            # Gemini Flash: ~$0.35 per 1M tokens input, $0.70 output
            cost = 0.001  # Rough estimate per call
            track_ai_cost(user_id, cost)
        
        return summary
        
    except Exception as exc:
        # Fallback to excerpt
        return content[:max_length] + "..." if len(content) > max_length else content


def generate_brief_content(
    articles_data: List[dict],
    user_tier: str = "starter",
    budget_remaining: float = 2.0,
) -> dict:
    """
    Generate Daily Brief content using AI.
    B12: Graceful degradation based on budget.
    """
    if budget_remaining < 0.20:
        # L3: No AI - return excerpt-based brief
        return generate_fallback_brief(articles_data)
    
    if not settings.GEMINI_API_KEY:
        return generate_fallback_brief(articles_data)
    
    # Prepare articles summary
    articles_text = "\n\n".join([
        f"{i+1}. {a['title']}\n{a['summary'][:200]}"
        for i, a in enumerate(articles_data[:15])
    ])
    
    prompt = f"""Create a daily news brief from these articles.

Articles:
{articles_text}

Generate:
1. A catchy title for the brief
2. A 2-3 sentence executive summary
3. Group related articles into 3-5 key themes

Return as JSON:
{{
  "title": "...",
  "executive_summary": "...",
  "sections": [
    {{"title": "Theme name", "summary": "...", "article_indices": [0, 1, 2]}}
  ]
}}"""
    
    try:
        response = litellm.completion(
            model="gemini/gemini-1.5-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.4,
            api_key=settings.GEMINI_API_KEY,
            response_format={"type": "json_object"},
        )
        
        import json
        content = response.choices[0].message.content
        result = json.loads(content)
        
        return {
            "title": result.get("title", "Daily Brief"),
            "executive_summary": result.get("executive_summary", ""),
            "sections": result.get("sections", []),
            "ai_generated": True,
        }
        
    except Exception as exc:
        return generate_fallback_brief(articles_data)


def generate_fallback_brief(articles_data: List[dict]) -> dict:
    """Generate brief without AI (L3 degradation)."""
    sections = []
    for i, article in enumerate(articles_data[:10]):
        sections.append({
            "title": article["title"],
            "summary": article.get("summary", article.get("excerpt", ""))[:200],
            "article_indices": [i],
        })
    
    return {
        "title": "Your Daily Brief",
        "executive_summary": f"{len(articles_data)} stories from your feeds.",
        "sections": sections,
        "ai_generated": False,
    }


def track_ai_cost(user_id: str, cost_usd: float):
    """Track AI cost for user."""
    from sqlmodel import Session
    from app.core.database import SessionLocal
    from app.models.user import User
    
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if user:
            user.ai_budget_used_this_month += cost_usd
            db.add(user)
            db.commit()
    finally:
        db.close()
    
    # Also cache in Redis for quick access
    key = f"user:{user_id}:ai_cost"
    redis_client.incr(key, int(cost_usd * 1_000_000))  # Store as microdollars


def get_budget_status(user_id: str) -> dict:
    """Get user's AI budget status."""
    from sqlmodel import Session
    from app.core.database import SessionLocal
    from app.models.user import User
    
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if not user:
            return {"error": "User not found"}
        
        remaining = user.budget_remaining
        percentage = user.budget_percentage_remaining
        
        # Determine degradation level (B12)
        if percentage > 50:
            level = "L1"  # Full AI
        elif percentage > 20:
            level = "L2"  # Reduced AI
        else:
            level = "L3"  # No AI
        
        return {
            "total": user.monthly_ai_budget,
            "used": user.ai_budget_used_this_month,
            "remaining": remaining,
            "percentage_remaining": percentage,
            "level": level,
        }
    finally:
        db.close()
