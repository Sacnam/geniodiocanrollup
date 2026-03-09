"""
Feature Flags System
LaunchDarkly-style feature flag management for gradual rollouts and A/B testing
"""
import hashlib
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.observability import MetricsManager

metrics = MetricsManager()


class FlagType(str, Enum):
    BOOLEAN = "boolean"
    STRING = "string"
    INTEGER = "integer"
    JSON = "json"


class RolloutStrategy(str, Enum):
    ALL = "all"           # Enable for everyone
    PERCENTAGE = "percentage"  # Percentage rollout
    USER_LIST = "user_list"   # Specific users
    USER_ATTRIBUTE = "user_attribute"  # Based on user attributes
    SCHEDULE = "schedule"     # Time-based


class FlagRule(BaseModel):
    """Single flag evaluation rule."""
    strategy: RolloutStrategy
    value: Any
    percentage: Optional[int] = None  # 0-100
    user_ids: Optional[List[str]] = None
    user_attribute: Optional[str] = None  # e.g., "tier==PROFESSIONAL"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class FeatureFlag(BaseModel):
    """Feature flag definition."""
    key: str
    name: str
    description: str = ""
    flag_type: FlagType = FlagType.BOOLEAN
    default_value: Any = False
    rules: List[FlagRule] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    archived: bool = False
    
    # For A/B testing
    experiment_key: Optional[str] = None
    variations: Optional[List[Any]] = None


class FeatureFlagManager:
    """Central feature flag management."""
    
    _instance = None
    _flags: Dict[str, FeatureFlag] = {}
    _cache: Dict[str, Any] = {}
    _cache_ttl: timedelta = timedelta(minutes=5)
    _cache_timestamp: Optional[datetime] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_default_flags()
        return cls._instance
    
    def _load_default_flags(self):
        """Load default feature flags."""
        # AI Features
        self.register_flag(FeatureFlag(
            key="ai.summarization",
            name="AI Summarization",
            description="Enable AI-powered article summarization",
            default_value=True,
            rules=[
                FlagRule(strategy=RolloutStrategy.ALL, value=True)
            ]
        ))
        
        self.register_flag(FeatureFlag(
            key="ai.graph_rag",
            name="GraphRAG",
            description="Enable GraphRAG for cross-document reasoning",
            default_value=False,
            rules=[
                FlagRule(strategy=RolloutStrategy.USER_ATTRIBUTE, 
                        value=True, user_attribute="tier in [PROFESSIONAL, ENTERPRISE]")
            ]
        ))
        
        # Scout Features
        self.register_flag(FeatureFlag(
            key="scout.advanced_mode",
            name="Advanced Scout Mode",
            description="Enable advanced scout research capabilities",
            default_value=False,
            rules=[
                FlagRule(strategy=RolloutStrategy.PERCENTAGE, value=True, percentage=10)
            ]
        ))
        
        # Library Features
        self.register_flag(FeatureFlag(
            key="library.concept_map",
            name="Concept Map Visualization",
            description="Enable D3.js concept map in library",
            default_value=True,
            rules=[
                FlagRule(strategy=RolloutStrategy.ALL, value=True)
            ]
        ))
        
        self.register_flag(FeatureFlag(
            key="library.semantic_chunking_v2",
            name="Semantic Chunking V2",
            description="Improved semantic chunking algorithm",
            default_value=False,
            rules=[
                FlagRule(strategy=RolloutStrategy.PERCENTAGE, value=True, percentage=25)
            ]
        ))
        
        # Brief Features
        self.register_flag(FeatureFlag(
            key="brief.audio_generation",
            name="Audio Brief Generation",
            description="Generate audio versions of briefs",
            default_value=False,
            rules=[
                FlagRule(strategy=RolloutStrategy.USER_LIST, value=True, user_ids=[])
            ]
        ))
        
        # Performance Features
        self.register_flag(FeatureFlag(
            key="perf.batch_embeddings",
            name="Batch Embedding Processing",
            description="Process embeddings in batches for efficiency",
            default_value=True,
            rules=[
                FlagRule(strategy=RolloutStrategy.ALL, value=True)
            ]
        ))
        
        self.register_flag(FeatureFlag(
            key="perf.intelligent_router",
            name="Intelligent Router",
            description="Route requests to best model based on complexity",
            default_value=True,
            rules=[
                FlagRule(strategy=RolloutStrategy.ALL, value=True)
            ]
        ))
    
    def register_flag(self, flag: FeatureFlag):
        """Register a new feature flag."""
        self._flags[flag.key] = flag
    
    def get_flag(self, key: str) -> Optional[FeatureFlag]:
        """Get flag by key."""
        return self._flags.get(key)
    
    def evaluate(self, key: str, user_id: Optional[str] = None, 
                 user_attributes: Optional[Dict[str, Any]] = None) -> Any:
        """
        Evaluate a feature flag for a specific user.
        
        Args:
            key: Flag key
            user_id: Optional user ID
            user_attributes: Optional user attributes (tier, etc.)
        
        Returns:
            Flag value for this user
        """
        flag = self._flags.get(key)
        if not flag or flag.archived:
            return None
        
        # Track evaluation
        metrics.increment("feature_flag.evaluation", tags={"flag": key})
        
        # Evaluate rules in order
        for rule in flag.rules:
            if self._matches_rule(rule, user_id, user_attributes):
                # Track rule match
                metrics.increment("feature_flag.rule_match", 
                                tags={"flag": key, "strategy": rule.strategy})
                return rule.value
        
        # Return default
        return flag.default_value
    
    def _matches_rule(self, rule: FlagRule, user_id: Optional[str],
                      user_attributes: Optional[Dict[str, Any]]) -> bool:
        """Check if rule matches user."""
        now = datetime.utcnow()
        
        if rule.strategy == RolloutStrategy.ALL:
            return True
        
        elif rule.strategy == RolloutStrategy.PERCENTAGE:
            if not user_id or rule.percentage is None:
                return False
            # Deterministic hash-based rollout
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            user_bucket = hash_val % 100
            return user_bucket < rule.percentage
        
        elif rule.strategy == RolloutStrategy.USER_LIST:
            return user_id in (rule.user_ids or [])
        
        elif rule.strategy == RolloutStrategy.USER_ATTRIBUTE:
            # Simple attribute matching
            if not user_attributes:
                return False
            # Parse attribute condition (simplified)
            if rule.user_attribute:
                # Example: "tier==PROFESSIONAL"
                if "==" in rule.user_attribute:
                    attr, val = rule.user_attribute.split("==")
                    return user_attributes.get(attr.strip()) == val.strip()
                elif "in" in rule.user_attribute:
                    # Example: "tier in [PROFESSIONAL, ENTERPRISE]"
                    attr_part = rule.user_attribute.split("in")[0].strip()
                    vals_part = rule.user_attribute.split("[")[1].split("]")[0]
                    allowed = [v.strip() for v in vals_part.split(",")]
                    return user_attributes.get(attr_part) in allowed
            return False
        
        elif rule.strategy == RolloutStrategy.SCHEDULE:
            if rule.start_time and now < rule.start_time:
                return False
            if rule.end_time and now > rule.end_time:
                return False
            return True
        
        return False
    
    def is_enabled(self, key: str, user_id: Optional[str] = None,
                   user_attributes: Optional[Dict[str, Any]] = None) -> bool:
        """Check if boolean flag is enabled."""
        value = self.evaluate(key, user_id, user_attributes)
        return bool(value) if value is not None else False
    
    def get_string(self, key: str, user_id: Optional[str] = None,
                   user_attributes: Optional[Dict[str, Any]] = None) -> str:
        """Get string flag value."""
        value = self.evaluate(key, user_id, user_attributes)
        return str(value) if value else ""
    
    def get_integer(self, key: str, user_id: Optional[str] = None,
                    user_attributes: Optional[Dict[str, Any]] = None) -> int:
        """Get integer flag value."""
        value = self.evaluate(key, user_id, user_attributes)
        return int(value) if value else 0
    
    def get_json(self, key: str, user_id: Optional[str] = None,
                 user_attributes: Optional[Dict[str, Any]] = None) -> Dict:
        """Get JSON flag value."""
        value = self.evaluate(key, user_id, user_attributes)
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return {}
        return {}
    
    def list_flags(self, include_archived: bool = False) -> List[FeatureFlag]:
        """List all feature flags."""
        flags = self._flags.values()
        if not include_archived:
            flags = [f for f in flags if not f.archived]
        return list(flags)
    
    def update_flag(self, key: str, **updates):
        """Update flag properties."""
        flag = self._flags.get(key)
        if flag:
            for k, v in updates.items():
                if hasattr(flag, k):
                    setattr(flag, k, v)
            flag.updated_at = datetime.utcnow()
    
    def archive_flag(self, key: str):
        """Archive a feature flag."""
        self.update_flag(key, archived=True)
    
    def unarchive_flag(self, key: str):
        """Unarchive a feature flag."""
        self.update_flag(key, archived=False)


# Global instance
_feature_flags = None

def get_feature_flags() -> FeatureFlagManager:
    """Get feature flags manager."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlagManager()
    return _feature_flags


# Decorator for feature-gated functions
def feature_enabled(flag_key: str, fallback: Optional[Callable] = None):
    """Decorator to conditionally execute based on feature flag."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            flags = get_feature_flags()
            # Try to get user_id from kwargs or first arg
            user_id = kwargs.get('user_id')
            user_attributes = kwargs.get('user_attributes', {})
            
            if flags.is_enabled(flag_key, user_id, user_attributes):
                return func(*args, **kwargs)
            elif fallback:
                return fallback(*args, **kwargs)
            else:
                raise FeatureNotEnabledException(f"Feature '{flag_key}' not enabled")
        return wrapper
    return decorator


class FeatureNotEnabledException(Exception):
    """Exception raised when feature is not enabled."""
    pass
