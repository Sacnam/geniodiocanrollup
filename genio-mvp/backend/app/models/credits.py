"""
Credit-based sustainability system for Genio Knowledge OS.

This module implements a "Genio Wallet" credit system that:
1. Tracks AI usage in credits (1 GC = $0.01 USD)
2. Enables pay-as-you-go model alongside subscriptions
3. Optimizes costs through smart LLM routing
4. Supports gamification (streaks, referrals)

Key Concepts:
- Credit (GC): 1 GC = $0.01 USD value
- Operations cost credits based on actual AI costs
- Free tier gets monthly credit allocation
- Paid users can purchase credit packs or subscribe
"""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class CreditOperationType(str, Enum):
    """Types of credit-consuming operations."""
    # LLM Operations
    BRIEF_SIMPLE = "brief_simple"           # Basic brief with Llama/Groq
    BRIEF_ADVANCED = "brief_advanced"       # Premium brief with DeepSeek
    BRIEF_PREMIUM = "brief_premium"         # Full GPT-4o brief
    SEARCH_SEMANTIC = "search_semantic"     # Semantic search query
    SUMMARIZE = "summarize"                 # Article summarization
    EXPLAIN_CONCEPT = "explain_concept"     # Concept explanation
    FLASHCARD_GENERATE = "flashcard_generate"  # Flashcard generation
    EMBEDDING_GENERATE = "embedding_generate"  # Vector embedding
    
    # TTS Operations
    TTS_PIPER = "tts_piper"                 # Self-hosted TTS
    TTS_PLAYHT = "tts_playht"               # PlayHT TTS
    TTS_ELEVENLABS = "tts_elevenlabs"       # ElevenLabs TTS
    
    # Storage Operations
    STORAGE_MB = "storage_mb"               # Per MB per month
    
    # Premium Features
    EXPORT_PDF = "export_pdf"               # PDF export with AI
    TEAM_SHARE = "team_share"               # Team sharing
    API_CALL = "api_call"                   # API usage
    
    # Document Operations
    DOCUMENT_UPLOAD = "document_upload"     # Document processing
    DOCUMENT_OCR = "document_ocr"           # OCR processing
    DOCUMENT_ANALYZE = "document_analyze"   # AI analysis
    KNOWLEDGE_GRAPH = "knowledge_graph"     # KG query


class CreditTransactionType(str, Enum):
    """Types of credit transactions."""
    # Inflows
    MONTHLY_ALLOCATION = "monthly_allocation"   # Free tier monthly credits
    PURCHASE = "purchase"                       # Credit pack purchase
    REFERRAL_BONUS = "referral_bonus"           # Referral reward
    STREAK_BONUS = "streak_bonus"               # Streak reward
    ADMIN_GRANT = "admin_grant"                 # Admin granted credits
    REFUND = "refund"                           # Refunded credits
    
    # Outflows
    OPERATION = "operation"                     # AI operation consumption
    EXPIRATION = "expiration"                   # Credits expired
    ADMIN_DEDUCT = "admin_deduct"               # Admin deducted credits


class CreditPackage(str, Enum):
    """Available credit packages for purchase."""
    MINI = "mini"           # 600 GC for $5
    STANDARD = "standard"   # 1500 GC for $10
    PRO = "pro"             # 4000 GC for $20
    POWER = "power"         # 14000 GC for $50


# Credit costs for operations (in GC = $0.01)
CREDIT_COSTS = {
    # LLM Operations (priced for sustainability with cheap models)
    CreditOperationType.BRIEF_SIMPLE: 5,        # Llama 3.1 via Groq ~$0.05
    CreditOperationType.BRIEF_ADVANCED: 15,     # DeepSeek V3 ~$0.15
    CreditOperationType.BRIEF_PREMIUM: 50,      # GPT-4o ~$0.50
    CreditOperationType.SEARCH_SEMANTIC: 1,     # Embedding lookup ~$0.01
    CreditOperationType.SUMMARIZE: 5,           # Summary ~$0.05
    CreditOperationType.EXPLAIN_CONCEPT: 10,    # Explanation ~$0.10
    CreditOperationType.FLASHCARD_GENERATE: 15, # Flashcards ~$0.15
    CreditOperationType.EMBEDDING_GENERATE: 1,  # Single embedding ~$0.01
    
    # TTS Operations (per 1000 characters)
    CreditOperationType.TTS_PIPER: 1,           # Self-hosted ~$0.01
    CreditOperationType.TTS_PLAYHT: 3,          # PlayHT ~$0.03
    CreditOperationType.TTS_ELEVENLABS: 10,     # ElevenLabs ~$0.10
    
    # Storage (per MB per month)
    CreditOperationType.STORAGE_MB: 1,          # ~$0.01/MB/month
    
    # Premium Features
    CreditOperationType.EXPORT_PDF: 25,         # PDF export ~$0.25
    CreditOperationType.TEAM_SHARE: 5,          # Team sharing ~$0.05
    CreditOperationType.API_CALL: 1,            # API call ~$0.01
    
    # Document Operations
    CreditOperationType.DOCUMENT_UPLOAD: 5,     # Basic processing ~$0.05
    CreditOperationType.DOCUMENT_OCR: 20,       # OCR processing ~$0.20
    CreditOperationType.DOCUMENT_ANALYZE: 15,   # AI analysis ~$0.15
    CreditOperationType.KNOWLEDGE_GRAPH: 10,    # KG query ~$0.10
}

# Credit packages for purchase
CREDIT_PACKAGES = {
    CreditPackage.MINI: {
        "credits": 600,
        "price_cents": 500,      # $5
        "bonus_credits": 100,    # +100 bonus
        "validity_days": 180,    # 6 months
        "features_unlocked": ["no_ads", "tts_base"],
    },
    CreditPackage.STANDARD: {
        "credits": 1500,
        "price_cents": 1000,     # $10
        "bonus_credits": 300,    # +300 bonus
        "validity_days": 365,    # 12 months
        "features_unlocked": ["no_ads", "tts_base", "knowledge_graph", "team_3"],
    },
    CreditPackage.PRO: {
        "credits": 4000,
        "price_cents": 2000,     # $20
        "bonus_credits": 1000,   # +1000 bonus
        "validity_days": 365,
        "features_unlocked": ["no_ads", "tts_premium", "knowledge_graph", "team_5", "ocr", "api_access"],
    },
    CreditPackage.POWER: {
        "credits": 14000,
        "price_cents": 5000,     # $50
        "bonus_credits": 4000,   # +4000 bonus
        "validity_days": 365,
        "features_unlocked": ["all_features", "priority_support", "custom_ai_params"],
    },
}

# Monthly credit allocations by tier
MONTHLY_CREDIT_ALLOCATION = {
    "free": 50,           # 50 GC/month (~$0.50 value)
    "starter": 500,       # 500 GC/month (~$5 value)
    "professional": 1500, # 1500 GC/month (~$15 value)
    "enterprise": 5000,   # 5000 GC/month (~$50 value)
}


class CreditWallet(SQLModel, table=True):
    """User's credit wallet with balance tracking."""
    __tablename__ = "credit_wallets"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", unique=True, index=True)
    
    # Current balance
    balance: int = Field(default=0)  # Current available credits
    total_earned: int = Field(default=0)  # Total credits ever earned
    total_spent: int = Field(default=0)  # Total credits ever spent
    
    # Monthly allocation tracking
    monthly_allocation: int = Field(default=50)  # Credits allocated per month
    allocation_resets_at: Optional[datetime] = None
    
    # Streak tracking
    current_streak: int = Field(default=0)
    longest_streak: int = Field(default=0)
    last_activity_date: Optional[datetime] = None
    
    # Referral tracking
    referral_code: str = Field(unique=True, index=True)
    referral_credits_earned: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    transactions: List["CreditTransaction"] = Relationship(back_populates="wallet")
    
    @property
    def has_low_balance(self) -> bool:
        """Check if balance is below 20% of monthly allocation."""
        return self.balance < (self.monthly_allocation * 0.2)
    
    @property
    def is_exhausted(self) -> bool:
        """Check if balance is exhausted."""
        return self.balance <= 0


class CreditTransaction(SQLModel, table=True):
    """Record of credit inflow/outflow."""
    __tablename__ = "credit_transactions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    wallet_id: int = Field(foreign_key="credit_wallets.id", index=True)
    
    # Transaction details
    type: CreditTransactionType = Field(index=True)
    operation: Optional[CreditOperationType] = None
    amount: int = Field()  # Positive for inflow, negative for outflow
    balance_after: int = Field()  # Balance after transaction
    
    # Context
    description: Optional[str] = None
    reference_id: Optional[str] = None  # Related entity ID (document, brief, etc.)
    metadata_json: Optional[str] = None  # JSON for additional data
    
    # For purchased credits
    stripe_payment_id: Optional[str] = None
    package: Optional[CreditPackage] = None
    expires_at: Optional[datetime] = None  # For purchased credits with expiry
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Relationships
    wallet: Optional[CreditWallet] = Relationship(back_populates="transactions")


class CreditPurchase(SQLModel, table=True):
    """Record of credit package purchases."""
    __tablename__ = "credit_purchases"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Purchase details
    package: CreditPackage = Field()
    credits_purchased: int = Field()
    bonus_credits: int = Field(default=0)
    price_cents: int = Field()
    
    # Payment
    stripe_payment_intent_id: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    payment_status: str = Field(default="pending")  # pending, completed, failed, refunded
    
    # Credit expiry
    credits_expire_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class UserStreak(SQLModel, table=True):
    """Daily activity streak for gamification."""
    __tablename__ = "user_streaks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", unique=True, index=True)
    
    # Streak tracking
    current_streak: int = Field(default=0)
    longest_streak: int = Field(default=0)
    last_activity_date: Optional[datetime] = None
    
    # Milestone rewards
    streak_7_rewarded: bool = Field(default=False)
    streak_30_rewarded: bool = Field(default=False)
    streak_90_rewarded: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_streak_bonus(self) -> int:
        """Calculate bonus credits for current streak."""
        if self.current_streak >= 90:
            return 200  # +200 GC for 90+ day streak
        elif self.current_streak >= 30:
            return 50   # +50 GC for 30+ day streak
        elif self.current_streak >= 7:
            return 10   # +10 GC for 7+ day streak
        return 0


class Referral(SQLModel, table=True):
    """User referral tracking."""
    __tablename__ = "referrals"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    referrer_id: str = Field(foreign_key="users.id", index=True)
    referred_id: str = Field(foreign_key="users.id", unique=True)
    
    # Status
    status: str = Field(default="pending")  # pending, qualified, rewarded
    qualified_at: Optional[datetime] = None  # When referred user made first purchase
    
    # Rewards
    referrer_credits: int = Field(default=100)  # Credits for referrer
    referred_credits: int = Field(default=50)   # Credits for referred user
    rewarded_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
