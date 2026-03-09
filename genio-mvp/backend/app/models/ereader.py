"""
E-Reader models for advanced book reading with AI features.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship


class ReadingStatus(str, Enum):
    """Reading progress status."""
    NOT_STARTED = "not_started"
    READING = "reading"
    PAUSED = "paused"
    COMPLETED = "completed"
    DNF = "did_not_finish"  # Did not finish


class HighlightColor(str, Enum):
    """Highlight colors."""
    YELLOW = "#fef08a"
    GREEN = "#bbf7d0"
    BLUE = "#bfdbfe"
    PINK = "#fbcfe8"
    PURPLE = "#e9d5ff"
    ORANGE = "#fed7aa"


class AnnotationType(str, Enum):
    """Types of annotations."""
    HIGHLIGHT = "highlight"
    NOTE = "note"
    BOOKMARK = "bookmark"
    DEFINITION = "definition"
    TRANSLATION = "translation"
    FLASHCARD = "flashcard"


class UserBook(SQLModel, table=True):
    """User's library book with reading progress."""
    __tablename__ = "user_books"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    document_id: str = Field(foreign_key="documents.id")
    
    # Reading progress
    current_position: str = Field(default="0")  # CFI or page number
    current_page: int = Field(default=0)
    total_pages: int = Field(default=0)
    progress_percent: float = Field(default=0.0)
    reading_status: str = Field(default=ReadingStatus.NOT_STARTED)
    
    # Reading session tracking
    total_reading_time_minutes: int = Field(default=0)
    last_read_at: Optional[datetime] = None
    sessions_count: int = Field(default=0)
    
    # Settings
    font_family: str = Field(default="system")
    font_size: int = Field(default=16)
    line_height: float = Field(default=1.5)
    margin_size: int = Field(default=20)
    theme: str = Field(default="light")  # light, dark, sepia
    text_align: str = Field(default="justify")
    
    # AI Features settings
    tts_enabled: bool = Field(default=False)
    tts_voice: Optional[str] = None
    tts_speed: float = Field(default=1.0)
    auto_summarize: bool = Field(default=False)
    
    # Book metadata (cached)
    title: str
    author: Optional[str] = None
    cover_url: Optional[str] = None
    
    # Organization
    rating: Optional[int] = None  # 1-5 stars
    review: Optional[str] = None
    tags: str = Field(default="[]")  # JSON array
    collections: str = Field(default="[]")  # JSON array
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Highlight(SQLModel, table=True):
    """Text highlight with AI enrichment."""
    __tablename__ = "highlights"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_book_id: str = Field(foreign_key="user_books.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Location
    start_cfi: str  # EPUB Canonical Fragment Identifier
    end_cfi: str
    start_position: int  # For PDF
    end_position: int
    page_number: Optional[int] = None
    
    # Content
    selected_text: str
    surrounding_text: Optional[str] = None  # Context
    chapter_title: Optional[str] = None
    
    # Appearance
    color: str = Field(default=HighlightColor.YELLOW)
    annotation_type: str = Field(default=AnnotationType.HIGHLIGHT)
    
    # User note
    note: Optional[str] = None
    note_html: Optional[str] = None
    
    # AI Features
    ai_summary: Optional[str] = None  # Auto-generated summary
    ai_key_concepts: str = Field(default="[]")  # Extracted concepts
    ai_flashcard_front: Optional[str] = None  # Auto-generated flashcard
    ai_flashcard_back: Optional[str] = None
    ai_sentiment: Optional[str] = None  # emotional tone
    
    # Sharing
    is_public: bool = Field(default=False)
    share_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Bookmark(SQLModel, table=True):
    """Bookmark with optional note."""
    __tablename__ = "bookmarks"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_book_id: str = Field(foreign_key="user_books.id", index=True)
    
    cfi: str
    page_number: Optional[int] = None
    chapter_title: Optional[str] = None
    
    label: Optional[str] = None
    note: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReadingSession(SQLModel, table=True):
    """Track reading sessions for analytics."""
    __tablename__ = "reading_sessions"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_book_id: str = Field(foreign_key="user_books.id", index=True)
    
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: int = Field(default=0)
    
    start_position: str
    end_position: Optional[str] = None
    pages_read: int = Field(default=0)
    
    # TTS usage
    tts_duration_minutes: int = Field(default=0)
    tts_chars_read: int = Field(default=0)


class FlashcardDeck(SQLModel, table=True):
    """Flashcard deck generated from book highlights."""
    __tablename__ = "flashcard_decks"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_book_id: str = Field(foreign_key="user_books.id", index=True)
    user_id: str = Field(foreign_key="users.id")
    
    name: str
    description: Optional[str] = None
    
    # Spaced repetition settings
    algorithm: str = Field(default="sm2")  # SuperMemo-2
    daily_new_cards: int = Field(default=10)
    daily_review_cards: int = Field(default=50)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Flashcard(SQLModel, table=True):
    """Individual flashcard."""
    __tablename__ = "flashcards"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    deck_id: str = Field(foreign_key="flashcard_decks.id", index=True)
    highlight_id: Optional[str] = Field(foreign_key="highlights.id")
    
    front: str  # Question
    back: str   # Answer
    front_html: Optional[str] = None
    back_html: Optional[str] = None
    
    # Spaced repetition data
    interval: int = Field(default=0)  # Days
    repetitions: int = Field(default=0)
    ease_factor: float = Field(default=2.5)
    next_review: Optional[datetime] = None
    last_reviewed: Optional[datetime] = None
    
    # Stats
    total_reviews: int = Field(default=0)
    correct_reviews: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StudyPlan(SQLModel, table=True):
    """AI-generated study plan for book."""
    __tablename__ = "study_plans"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_book_id: str = Field(foreign_key="user_books.id", index=True)
    
    target_completion_date: Optional[datetime] = None
    daily_reading_minutes: int = Field(default=30)
    
    # Generated schedule
    schedule: str = Field(default="[]")  # JSON array of daily goals
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TTSAudioCache(SQLModel, table=True):
    """Cache for TTS audio to avoid regenerating."""
    __tablename__ = "tts_audio_cache"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    
    text_hash: str = Field(index=True, unique=True)  # SHA256 of text
    text_preview: str  # First 100 chars
    
    provider: str
    voice: str
    
    audio_url: str  # S3 or local path
    audio_size_bytes: int
    duration_seconds: float
    
    use_count: int = Field(default=0)
    last_used_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# API Schemas
class ReaderSettingsUpdate(SQLModel):
    font_family: Optional[str] = None
    font_size: Optional[int] = None
    line_height: Optional[float] = None
    margin_size: Optional[int] = None
    theme: Optional[str] = None
    text_align: Optional[str] = None
    tts_enabled: Optional[bool] = None
    tts_voice: Optional[str] = None
    tts_speed: Optional[float] = None


class CreateHighlightRequest(SQLModel):
    start_cfi: str
    end_cfi: str
    selected_text: str
    color: str = HighlightColor.YELLOW
    note: Optional[str] = None
    chapter_title: Optional[str] = None


class CreateFlashcardRequest(SQLModel):
    highlight_id: str
    front: str
    back: str


class TTSRequest(SQLModel):
    text: str
    provider: Optional[str] = None  # "elevenlabs", "openai", "coqui"
    voice: Optional[str] = None
    speed: float = 1.0
    use_cache: bool = True


class AIStudyAssistRequest(SQLModel):
    book_id: str
    action: str  # "summarize_chapter", "generate_flashcards", "explain_concept", "create_quiz"
    context: Optional[str] = None  # Selected text or chapter
    language: str = "en"


class ReaderProgressUpdate(SQLModel):
    current_position: str
    current_page: int
    progress_percent: float
