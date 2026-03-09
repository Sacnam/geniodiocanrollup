"""
Smart LLM Router for cost-optimized AI operations.

This module implements intelligent routing between LLM providers based on:
1. User's credit balance and tier
2. Operation complexity requirements
3. Cost optimization strategies
4. Fallback chains for reliability

Cost Optimization Strategy:
- Free tier: Llama 3.1 via Groq (cheapest)
- Low balance: DeepSeek V3 (good quality/price ratio)
- Premium operations: GPT-4o (best quality)
- Embeddings: text-embedding-3-small (cost optimized)

Provider Costs (per 1M tokens):
| Provider         | Input   | Output  | Quality |
|------------------|---------|---------|---------|
| Llama 3.1 (Groq) | $0.05   | $0.08   | ⭐⭐⭐⭐  |
| DeepSeek V3      | $0.27   | $1.10   | ⭐⭐⭐⭐  |
| GPT-4o           | $5.00   | $15.00  | ⭐⭐⭐⭐⭐ |
| Gemini Flash     | $0.075  | $0.30   | ⭐⭐⭐⭐  |
| Mistral Small    | $0.20   | $0.60   | ⭐⭐⭐   |
"""
import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

from app.core.config import settings
from app.core.redis import redis_client

logger = structlog.get_logger()


class LLMProvider(str, Enum):
    """Available LLM providers."""
    GROQ = "groq"           # Llama 3.1, Mixtral
    DEEPSEEK = "deepseek"   # DeepSeek V3
    OPENAI = "openai"       # GPT-4o, GPT-4o-mini
    GEMINI = "gemini"       # Gemini Flash
    MISTRAL = "mistral"     # Mistral Small
    LOCAL = "local"         # Self-hosted models


class OperationComplexity(str, Enum):
    """Operation complexity levels."""
    SIMPLE = "simple"       # Basic summarization, extraction
    MODERATE = "moderate"   # Brief generation, analysis
    COMPLEX = "complex"     # Deep reasoning, multi-step
    PREMIUM = "premium"     # User explicitly requested premium


@dataclass
class LLMConfig:
    """Configuration for an LLM call."""
    provider: LLMProvider
    model: str
    max_tokens: int
    temperature: float
    cost_per_1m_input: float
    cost_per_1m_output: float
    timeout_seconds: int = 30
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for given token counts."""
        input_cost = (input_tokens / 1_000_000) * self.cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * self.cost_per_1m_output
        return input_cost + output_cost


# Model configurations with pricing
MODEL_CONFIGS = {
    # Budget tier (for free users and low balance)
    "llama-3.1-70b": LLMConfig(
        provider=LLMProvider.GROQ,
        model="groq/llama-3.1-70b-versatile",
        max_tokens=4096,
        temperature=0.3,
        cost_per_1m_input=0.05,
        cost_per_1m_output=0.08,
    ),
    "llama-3.1-8b": LLMConfig(
        provider=LLMProvider.GROQ,
        model="groq/llama-3.1-8b-instant",
        max_tokens=4096,
        temperature=0.3,
        cost_per_1m_input=0.02,
        cost_per_1m_output=0.02,
    ),
    "mixtral-8x7b": LLMConfig(
        provider=LLMProvider.GROQ,
        model="groq/mixtral-8x7b-32768",
        max_tokens=4096,
        temperature=0.3,
        cost_per_1m_input=0.27,
        cost_per_1m_output=0.27,
    ),
    
    # Mid tier (good quality/price)
    "deepseek-v3": LLMConfig(
        provider=LLMProvider.DEEPSEEK,
        model="deepseek/deepseek-chat",
        max_tokens=4096,
        temperature=0.3,
        cost_per_1m_input=0.27,
        cost_per_1m_output=1.10,
    ),
    "gemini-flash": LLMConfig(
        provider=LLMProvider.GEMINI,
        model="gemini/gemini-1.5-flash",
        max_tokens=4096,
        temperature=0.3,
        cost_per_1m_input=0.075,
        cost_per_1m_output=0.30,
    ),
    "mistral-small": LLMConfig(
        provider=LLMProvider.MISTRAL,
        model="mistral/mistral-small-latest",
        max_tokens=4096,
        temperature=0.3,
        cost_per_1m_input=0.20,
        cost_per_1m_output=0.60,
    ),
    
    # Premium tier (best quality)
    "gpt-4o": LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
        max_tokens=4096,
        temperature=0.3,
        cost_per_1m_input=5.00,
        cost_per_1m_output=15.00,
    ),
    "gpt-4o-mini": LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        max_tokens=4096,
        temperature=0.3,
        cost_per_1m_input=0.15,
        cost_per_1m_output=0.60,
    ),
    "claude-sonnet": LLMConfig(
        provider=LLMProvider.MISTRAL,  # Via OpenRouter
        model="openrouter/anthropic/claude-3.5-sonnet",
        max_tokens=4096,
        temperature=0.3,
        cost_per_1m_input=3.00,
        cost_per_1m_output=15.00,
    ),
}

# Routing rules based on operation and user context
ROUTING_RULES = {
    # Simple operations -> cheapest model
    OperationComplexity.SIMPLE: {
        "default": "llama-3.1-8b",
        "fallback": ["gemini-flash", "mistral-small"],
    },
    # Moderate operations -> good balance
    OperationComplexity.MODERATE: {
        "default": "llama-3.1-70b",
        "fallback": ["deepseek-v3", "gemini-flash"],
    },
    # Complex operations -> better models
    OperationComplexity.COMPLEX: {
        "default": "deepseek-v3",
        "fallback": ["gpt-4o-mini", "gemini-flash"],
    },
    # Premium operations -> best models
    OperationComplexity.PREMIUM: {
        "default": "gpt-4o",
        "fallback": ["claude-sonnet", "deepseek-v3"],
    },
}

# Operation type to complexity mapping
OPERATION_COMPLEXITY_MAP = {
    "brief_simple": OperationComplexity.SIMPLE,
    "brief_advanced": OperationComplexity.MODERATE,
    "brief_premium": OperationComplexity.PREMIUM,
    "summarize": OperationComplexity.SIMPLE,
    "explain_concept": OperationComplexity.MODERATE,
    "flashcard_generate": OperationComplexity.MODERATE,
    "document_analyze": OperationComplexity.COMPLEX,
    "knowledge_graph": OperationComplexity.COMPLEX,
}


class SmartLLMRouter:
    """
    Intelligent LLM router that optimizes for cost while maintaining quality.
    
    Routing Strategy:
    1. Check user's credit balance
    2. Determine operation complexity
    3. Select appropriate model tier
    4. Apply fallback chain if needed
    5. Track actual costs
    """
    
    def __init__(self):
        self._cache_prefix = "llm_router:"
    
    def select_model(
        self,
        operation: str,
        user_credit_balance: int,
        user_tier: str = "free",
        force_quality: Optional[str] = None,
    ) -> Tuple[LLMConfig, str]:
        """
        Select the optimal model for an operation.
        
        Args:
            operation: Operation type (e.g., "brief_simple")
            user_credit_balance: User's current credit balance
            user_tier: User's subscription tier
            force_quality: Force specific quality level
            
        Returns:
            Tuple of (LLMConfig, reason)
        """
        # Determine complexity
        complexity = OPERATION_COMPLEXITY_MAP.get(operation, OperationComplexity.MODERATE)
        
        # Override complexity if forced
        if force_quality == "premium":
            complexity = OperationComplexity.PREMIUM
        elif force_quality == "simple":
            complexity = OperationComplexity.SIMPLE
        
        # Adjust based on credit balance
        if user_credit_balance < 20:
            # Very low balance - use cheapest
            complexity = OperationComplexity.SIMPLE
            reason = "low_balance_optimization"
        elif user_credit_balance < 100 and complexity == OperationComplexity.COMPLEX:
            # Moderate balance - downgrade complex to moderate
            complexity = OperationComplexity.MODERATE
            reason = "balance_conscious_routing"
        else:
            reason = "standard_routing"
        
        # Free tier always gets simple complexity unless they have credits
        if user_tier == "free" and user_credit_balance < 50:
            complexity = OperationComplexity.SIMPLE
            reason = "free_tier_optimization"
        
        # Get model for complexity
        rules = ROUTING_RULES[complexity]
        model_name = rules["default"]
        
        # Check if model is available (API key configured)
        model_config = MODEL_CONFIGS.get(model_name)
        if not model_config or not self._is_model_available(model_config.provider):
            # Try fallbacks
            for fallback_name in rules.get("fallback", []):
                fallback_config = MODEL_CONFIGS.get(fallback_name)
                if fallback_config and self._is_model_available(fallback_config.provider):
                    model_config = fallback_config
                    reason += f"_fallback_to_{fallback_name}"
                    break
            else:
                # Ultimate fallback to Gemini Flash (usually available)
                model_config = MODEL_CONFIGS["gemini-flash"]
                reason = "ultimate_fallback"
        
        return model_config, reason
    
    def _is_model_available(self, provider: LLMProvider) -> bool:
        """Check if provider is configured."""
        if provider == LLMProvider.OPENAI:
            return bool(settings.OPENAI_API_KEY)
        elif provider == LLMProvider.GEMINI:
            return bool(settings.GEMINI_API_KEY)
        elif provider == LLMProvider.GROQ:
            return bool(getattr(settings, 'GROQ_API_KEY', None))
        elif provider == LLMProvider.DEEPSEEK:
            return bool(getattr(settings, 'DEEPSEEK_API_KEY', None))
        elif provider == LLMProvider.MISTRAL:
            return bool(getattr(settings, 'MISTRAL_API_KEY', None))
        return False
    
    def estimate_credits(
        self,
        operation: str,
        input_text: str,
        model_config: Optional[LLMConfig] = None,
    ) -> int:
        """
        Estimate credits needed for an operation.
        
        Args:
            operation: Operation type
            input_text: Input text for token estimation
            model_config: Model configuration (if known)
            
        Returns:
            Estimated credits (1 credit = $0.01)
        """
        from app.models.credits import CREDIT_COSTS, CreditOperationType
        
        # Get base credit cost
        try:
            op_type = CreditOperationType(operation)
            base_credits = CREDIT_COSTS.get(op_type, 5)
        except ValueError:
            base_credits = 5  # Default
        
        # If we have model config, estimate based on actual tokens
        if model_config:
            estimated_input_tokens = len(input_text) / 4  # Rough estimate
            estimated_output_tokens = model_config.max_tokens * 0.3  # Assume 30% of max
            
            estimated_cost = model_config.estimate_cost(
                int(estimated_input_tokens),
                int(estimated_output_tokens)
            )
            
            # Convert to credits (1 credit = $0.01)
            estimated_credits = max(1, int(estimated_cost * 100))
            
            # Use the higher of base cost or estimated cost
            return max(base_credits, estimated_credits)
        
        return base_credits
    
    async def complete(
        self,
        operation: str,
        prompt: str,
        user_id: str,
        user_credit_balance: int,
        user_tier: str = "free",
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Execute an LLM completion with smart routing.
        
        Args:
            operation: Operation type
            prompt: User prompt
            user_id: User ID for tracking
            user_credit_balance: Current credit balance
            user_tier: User subscription tier
            system_prompt: Optional system prompt
            max_tokens: Override max tokens
            temperature: Override temperature
            response_format: Response format specification
            
        Returns:
            Tuple of (response_text, metadata)
        """
        import litellm
        
        # Select optimal model
        model_config, routing_reason = self.select_model(
            operation=operation,
            user_credit_balance=user_credit_balance,
            user_tier=user_tier,
        )
        
        # Estimate credits before call
        estimated_credits = self.estimate_credits(operation, prompt, model_config)
        
        # Check if user has enough credits
        if user_credit_balance < estimated_credits:
            raise InsufficientCreditsError(
                f"Need {estimated_credits} credits, have {user_credit_balance}"
            )
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare kwargs
        kwargs = {
            "model": model_config.model,
            "messages": messages,
            "max_tokens": max_tokens or model_config.max_tokens,
            "temperature": temperature if temperature is not None else model_config.temperature,
        }
        
        # Add response format if specified
        if response_format:
            kwargs["response_format"] = response_format
        
        # Add API keys based on provider
        if model_config.provider == LLMProvider.OPENAI:
            kwargs["api_key"] = settings.OPENAI_API_KEY
        elif model_config.provider == LLMProvider.GEMINI:
            kwargs["api_key"] = settings.GEMINI_API_KEY
        elif model_config.provider == LLMProvider.GROQ:
            kwargs["api_key"] = getattr(settings, 'GROQ_API_KEY', None)
            kwargs["api_base"] = "https://api.groq.com/openai/v1"
        elif model_config.provider == LLMProvider.DEEPSEEK:
            kwargs["api_key"] = getattr(settings, 'DEEPSEEK_API_KEY', None)
            kwargs["api_base"] = "https://api.deepseek.com/v1"
        
        # Execute with timing
        start_time = time.time()
        
        try:
            response = await litellm.acompletion(**kwargs)
            
            response_text = response.choices[0].message.content
            
            # Calculate actual cost
            usage = response.usage
            actual_cost = model_config.estimate_cost(
                usage.prompt_tokens,
                usage.completion_tokens
            )
            actual_credits = max(1, int(actual_cost * 100))
            
            # Build metadata
            metadata = {
                "model": model_config.model,
                "provider": model_config.provider.value,
                "routing_reason": routing_reason,
                "estimated_credits": estimated_credits,
                "actual_credits": actual_credits,
                "actual_cost_usd": actual_cost,
                "input_tokens": usage.prompt_tokens,
                "output_tokens": usage.completion_tokens,
                "latency_ms": int((time.time() - start_time) * 1000),
            }
            
            # Log for analytics
            logger.info(
                "llm_completion",
                user_id=user_id,
                operation=operation,
                **metadata
            )
            
            return response_text, metadata
            
        except Exception as e:
            logger.error(
                "llm_completion_failed",
                user_id=user_id,
                operation=operation,
                model=model_config.model,
                error=str(e),
            )
            raise
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with their configurations."""
        models = []
        for name, config in MODEL_CONFIGS.items():
            if self._is_model_available(config.provider):
                models.append({
                    "name": name,
                    "provider": config.provider.value,
                    "max_tokens": config.max_tokens,
                    "cost_per_1m_input": config.cost_per_1m_input,
                    "cost_per_1m_output": config.cost_per_1m_output,
                })
        return models


class InsufficientCreditsError(Exception):
    """Raised when user doesn't have enough credits."""
    pass


# Singleton instance
router = SmartLLMRouter()
