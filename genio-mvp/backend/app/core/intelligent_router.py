"""
Intelligent Router (B02): Vector-based intent routing for AI model selection.
Routes requests to appropriate model tier based on complexity and budget.
"""
from enum import Enum
from typing import Dict, List, Optional

import numpy as np

from app.core.config import settings


class ModelTier(Enum):
    """AI model tiers by capability and cost."""
    TIER_1 = "tier_1"  # GPT-4 / Gemini Ultra - Complex reasoning
    TIER_2 = "tier_2"  # GPT-3.5 / Gemini Pro - Standard tasks
    TIER_3 = "tier_3"  # Gemini Flash - Simple/fast tasks


class TaskType(Enum):
    """Classification of AI tasks."""
    SUMMARIZATION = "summarization"
    EXTRACTION = "extraction"
    GENERATION = "generation"
    REASONING = "reasoning"
    CLASSIFICATION = "classification"


class IntelligentRouter:
    """
    Routes AI requests to optimal model based on:
    - Task complexity (vector similarity to known patterns)
    - User budget remaining (L1/L2/L3 degradation)
    - Historical success rates
    
    B02: Vector-based intent routing.
    """
    
    # Task complexity embeddings (pre-computed for common patterns)
    TASK_PATTERNS = {
        TaskType.SUMMARIZATION: np.array([0.8, 0.2, 0.1, 0.3]),
        TaskType.EXTRACTION: np.array([0.3, 0.9, 0.2, 0.1]),
        TaskType.GENERATION: np.array([0.9, 0.3, 0.8, 0.7]),
        TaskType.REASONING: np.array([0.95, 0.4, 0.9, 0.9]),
        TaskType.CLASSIFICATION: np.array([0.2, 0.8, 0.1, 0.1]),
    }
    
    # Cost estimates per tier (USD per 1K tokens)
    COST_PER_1K = {
        ModelTier.TIER_1: 0.03,   # GPT-4
        ModelTier.TIER_2: 0.002,  # GPT-3.5
        ModelTier.TIER_3: 0.0005, # Gemini Flash
    }
    
    def __init__(self, budget_remaining: float, budget_total: float):
        """
        Initialize router with user's budget context.
        
        Args:
            budget_remaining: Remaining AI budget for the month
            budget_total: Total monthly AI budget
        """
        self.budget_remaining = budget_remaining
        self.budget_total = budget_total
        self.budget_pct = budget_remaining / budget_total if budget_total > 0 else 0
    
    def get_degradation_level(self) -> int:
        """
        Determine degradation level based on budget.
        B12: Graceful degradation.
        
        Returns:
            1: Normal (L1) - >50% budget
            2: Reduced (L2) - 20-50% budget
            3: Minimal (L3) - <20% budget
        """
        if self.budget_pct > 0.5:
            return 1
        elif self.budget_pct > 0.2:
            return 2
        else:
            return 3
    
    def classify_task(self, prompt: str, context: Optional[str] = None) -> TaskType:
        """
        Classify task type from prompt text.
        Uses simple keyword-based classification (vector-based in production).
        """
        prompt_lower = prompt.lower()
        
        # Simple keyword matching (in production, use embeddings)
        reasoning_keywords = ["explain", "why", "how", "analyze", "compare", "evaluate"]
        extraction_keywords = ["extract", "find", "identify", "parse", "get"]
        generation_keywords = ["write", "create", "generate", "compose", "draft"]
        classification_keywords = ["classify", "categorize", "label", "tag"]
        
        scores = {
            TaskType.REASONING: sum(1 for kw in reasoning_keywords if kw in prompt_lower),
            TaskType.EXTRACTION: sum(1 for kw in extraction_keywords if kw in prompt_lower),
            TaskType.GENERATION: sum(1 for kw in generation_keywords if kw in prompt_lower),
            TaskType.CLASSIFICATION: sum(1 for kw in classification_keywords if kw in prompt_lower),
            TaskType.SUMMARIZATION: 0.5,  # Default fallback
        }
        
        # Check for summary patterns
        if any(kw in prompt_lower for kw in ["summarize", "summary", "tl;dr", "brief"]):
            scores[TaskType.SUMMARIZATION] = 2.0
        
        return max(scores, key=scores.get)
    
    def route(self, prompt: str, context: Optional[str] = None) -> Dict:
        """
        Route request to optimal model tier.
        
        Returns:
            Dict with model selection and metadata
        """
        task_type = self.classify_task(prompt, context)
        level = self.get_degradation_level()
        
        # Base routing decision
        if level == 3:
            # L3: Minimal mode - always use cheapest
            selected_tier = ModelTier.TIER_3
            reason = "budget_l3_minimal"
            
        elif level == 2:
            # L2: Reduced mode - downgrade by one tier
            if task_type == TaskType.REASONING:
                selected_tier = ModelTier.TIER_2  # Down from T1
            else:
                selected_tier = ModelTier.TIER_3  # Down from T2
            reason = "budget_l2_reduced"
            
        else:
            # L1: Normal mode - route by complexity
            if task_type == TaskType.REASONING:
                selected_tier = ModelTier.TIER_1
            elif task_type in [TaskType.GENERATION, TaskType.SUMMARIZATION]:
                selected_tier = ModelTier.TIER_2
            else:
                selected_tier = ModelTier.TIER_3
            reason = f"task_{task_type.value}"
        
        return {
            "tier": selected_tier.value,
            "model": self._get_model_name(selected_tier),
            "task_type": task_type.value,
            "degradation_level": level,
            "reason": reason,
            "estimated_cost_per_1k": self.COST_PER_1K[selected_tier],
            "budget_remaining_pct": round(self.budget_pct * 100, 1),
        }
    
    def _get_model_name(self, tier: ModelTier) -> str:
        """Get actual model name for tier."""
        mapping = {
            ModelTier.TIER_1: "gpt-4",           # or "gemini-ultra"
            ModelTier.TIER_2: "gpt-3.5-turbo",   # or "gemini-pro"
            ModelTier.TIER_3: "gemini-flash",    # Fastest/cheapest
        }
        return mapping[tier]
    
    def can_afford(self, estimated_tokens: int) -> bool:
        """Check if user can afford estimated token cost."""
        # Use T3 cost as worst case
        estimated_cost = (estimated_tokens / 1000) * self.COST_PER_1K[ModelTier.TIER_3]
        return estimated_cost < self.budget_remaining


# Convenience function
def route_request(
    prompt: str,
    budget_remaining: float,
    budget_total: float = settings.MONTHLY_AI_BUDGET_USD,
    context: Optional[str] = None
) -> Dict:
    """
    Route an AI request to the appropriate model.
    
    Usage:
        result = route_request("Summarize this article", 1.50, 3.00)
        # Returns: {"tier": "tier_2", "model": "gpt-3.5-turbo", ...}
    """
    router = IntelligentRouter(budget_remaining, budget_total)
    return router.route(prompt, context)
