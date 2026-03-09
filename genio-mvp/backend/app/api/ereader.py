"""
E-Reader API with premium features and AI assistance.
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select, and_, func

from app.db.database import get_session
from app.core.security import get_current_user
from app.core.ai_providers import ai_manager, ProviderType
from app.models.user import User
from app.models.ereader import (
    UserBook, Highlight, Bookmark, ReadingSession,
    FlashcardDeck, Flashcard, StudyPlan, TTSAudioCache,
    ReaderSettingsUpdate, CreateHighlightRequest,
    CreateFlashcardRequest, TTSRequest, AIStudyAssistRequest,
    ReaderProgressUpdate
)
from app.utils.id_generator import generate_id

router = APIRouter()


@router.post("/books/{document_id}/open")
async def open_book(
    document_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Open a book (create or get UserBook)."""
    # Check if already in library
    user_book = session.exec(
        select(UserBook).where(
            and_(
                UserBook.user_id == current_user.id,
                UserBook.document_id == document_id
            )
        )
    ).first()
    
    if not user_book:
        # Get document details
        from app.models.document import Document
        doc = session.get(Document, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        user_book = UserBook(
            id=generate_id("ubook"),
            user_id=current_user.id,
            document_id=document_id,
            title=doc.title or "Untitled",
            author=doc.author,
            cover_url=doc.cover_url,
            reading_status="not_started"
        )
        session.add(user_book)
        session.commit()
        session.refresh(user_book)
    
    return {
        "user_book_id": user_book.id,
        "title": user_book.title,
        "author": user_book.author,
        "current_position": user_book.current_position,
        "progress_percent": user_book.progress_percent,
        "settings": {
            "font_family": user_book.font_family,
            "font_size": user_book.font_size,
            "line_height": user_book.line_height,
            "theme": user_book.theme,
            "tts_enabled": user_book.tts_enabled,
            "tts_voice": user_book.tts_voice,
        }
    }


@router.get("/books/{user_book_id}/content")
async def get_book_content(
    user_book_id: str,
    chapter: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get book content for rendering."""
    user_book = session.get(UserBook, user_book_id)
    if not user_book or user_book.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Get document content
    from app.models.document import Document
    doc = session.get(Document, user_book.document_id)
    
    # Parse based on format
    if doc.doc_type == "epub":
        content = await parse_epub_chapter(doc.content, chapter or 0)
    elif doc.doc_type == "pdf":
        content = await get_pdf_pages(doc.content, chapter or 0, 10)
    else:
        content = {"text": doc.content[:50000]}  # Limit for plain text
    
    # Get highlights for this chapter
    highlights = session.exec(
        select(Highlight).where(
            and_(
                Highlight.user_book_id == user_book_id,
                Highlight.page_number == chapter
            )
        )
    ).all()
    
    return {
        "content": content,
        "highlights": [h.dict() for h in highlights],
        "current_chapter": chapter or 0,
        "total_chapters": content.get("total_chapters", 1)
    }


@router.post("/books/{user_book_id}/progress")
async def update_progress(
    user_book_id: str,
    data: ReaderProgressUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update reading progress."""
    user_book = session.get(UserBook, user_book_id)
    if not user_book or user_book.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Update progress
    user_book.current_position = data.current_position
    user_book.current_page = data.current_page
    user_book.progress_percent = data.progress_percent
    user_book.last_read_at = datetime.utcnow()
    
    # Update status
    if data.progress_percent >= 100:
        user_book.reading_status = "completed"
    elif data.progress_percent > 0:
        user_book.reading_status = "reading"
    
    session.add(user_book)
    session.commit()
    
    return {"success": True}


@router.post("/books/{user_book_id}/highlights")
async def create_highlight(
    user_book_id: str,
    data: CreateHighlightRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a highlight with optional AI enrichment."""
    user_book = session.get(UserBook, user_book_id)
    if not user_book or user_book.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Book not found")
    
    highlight = Highlight(
        id=generate_id("hl"),
        user_book_id=user_book_id,
        user_id=current_user.id,
        start_cfi=data.start_cfi,
        end_cfi=data.end_cfi,
        selected_text=data.selected_text[:1000],  # Limit length
        color=data.color,
        note=data.note,
        chapter_title=data.chapter_title
    )
    
    session.add(highlight)
    session.commit()
    
    # Trigger AI enrichment in background
    if len(data.selected_text) > 50:
        background_tasks.add_task(
            enrich_highlight_ai,
            highlight.id,
            data.selected_text
        )
    
    return highlight


async def enrich_highlight_ai(highlight_id: str, text: str):
    """Generate AI summary and flashcard for highlight."""
    from app.db.database import SessionLocal
    
    with SessionLocal() as session:
        highlight = session.get(Highlight, highlight_id)
        if not highlight:
            return
        
        # Generate summary
        summary_result = await ai_manager.generate_text(
            f"Summarize this text in 2-3 sentences: {text[:500]}",
            provider_type=ProviderType.LLM
        )
        
        if summary_result.get("success"):
            highlight.ai_summary = summary_result["text"]
        
        # Generate flashcard
        flashcard_prompt = f"""Create a flashcard from this text.
        Front (Question): [Key concept or term]
        Back (Answer): [Brief explanation]
        
        Text: {text[:500]}
        
        Format:
        FRONT: [question]
        BACK: [answer]"""
        
        flashcard_result = await ai_manager.generate_text(
            flashcard_prompt,
            provider_type=ProviderType.LLM
        )
        
        if flashcard_result.get("success"):
            result_text = flashcard_result["text"]
            if "FRONT:" in result_text and "BACK:" in result_text:
                front = result_text.split("FRONT:")[1].split("BACK:")[0].strip()
                back = result_text.split("BACK:")[1].strip()
                highlight.ai_flashcard_front = front
                highlight.ai_flashcard_back = back
        
        session.add(highlight)
        session.commit()


@router.post("/tts/generate")
async def generate_tts(
    data: TTSRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Generate TTS audio with caching."""
    
    # Check cache
    text_hash = hashlib.sha256(data.text.encode()).hexdigest()
    cache_key = f"{text_hash}:{data.provider}:{data.voice}"
    
    cached = session.exec(
        select(TTSAudioCache).where(TTSAudioCache.text_hash == cache_key)
    ).first()
    
    if cached and data.use_cache:
        # Update usage
        cached.use_count += 1
        cached.last_used_at = datetime.utcnow()
        session.add(cached)
        session.commit()
        
        return {
            "audio_url": cached.audio_url,
            "duration_seconds": cached.duration_seconds,
            "provider": cached.provider,
            "cached": True
        }
    
    # Generate new audio
    from app.core.ai_providers import ProviderType
    
    # Get preferred provider
    provider = data.provider
    if not provider:
        providers = ai_manager.get_available_providers(ProviderType.TTS)
        provider = providers[0] if providers else None
    
    if not provider:
        raise HTTPException(status_code=503, detail="No TTS provider available")
    
    # Generate
    provider_instance = ai_manager.providers.get(provider)
    if not provider_instance:
        raise HTTPException(status_code=400, detail="Provider not found")
    
    async with provider_instance:
        audio_bytes = await provider_instance.generate_speech(
            data.text,
            speed=data.speed
        )
    
    # Save to storage (S3 or local)
    audio_url = await save_audio_file(audio_bytes, f"tts_{cache_key}.mp3")
    
    # Cache metadata
    duration = len(data.text) / 15  # Rough estimate: 15 chars per second
    
    cache_entry = TTSAudioCache(
        id=generate_id("tts"),
        text_hash=cache_key,
        text_preview=data.text[:100],
        provider=provider,
        voice=data.voice or "default",
        audio_url=audio_url,
        audio_size_bytes=len(audio_bytes),
        duration_seconds=duration,
        use_count=1,
        last_used_at=datetime.utcnow()
    )
    session.add(cache_entry)
    session.commit()
    
    return {
        "audio_url": audio_url,
        "duration_seconds": duration,
        "provider": provider,
        "cached": False
    }


async def save_audio_file(audio_bytes: bytes, filename: str) -> str:
    """Save audio file to S3 or local storage."""
    # TODO: Implement S3 upload
    # For now, return local path
    import os
    from app.core.config import settings
    
    upload_dir = "/tmp/tts_audio"
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        f.write(audio_bytes)
    
    return f"/audio/{filename}"


@router.post("/ai/assist")
async def ai_study_assist(
    data: AIStudyAssistRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """AI study assistant - various learning aids."""
    
    user_book = session.get(UserBook, data.book_id)
    if not user_book or user_book.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Book not found")
    
    prompts = {
        "summarize_chapter": f"""Summarize the following chapter concisely, highlighting key points:
        {data.context}""",
        
        "explain_concept": f"""Explain this concept in simple terms as if teaching a student:
        {data.context}
        
        Include:
        1. Definition
        2. Key aspects
        3. Real-world examples
        4. Connections to broader themes""",
        
        "create_quiz": f"""Create 5 quiz questions (multiple choice) based on this text:
        {data.context}
        
        Format each as:
        Q: [Question]
        A: [Correct answer]
        B: [Wrong answer]
        C: [Wrong answer]
        D: [Wrong answer]""",
        
        "generate_flashcards": f"""Extract 5 key concepts from this text and create flashcards:
        {data.context}
        
        Format:
        CONCEPT 1:
        Q: [Question]
        A: [Answer]
        
        CONCEPT 2:
        ...""",
        
        "extract_arguments": f"""Analyze this text and extract:
        1. Main arguments
        2. Supporting evidence
        3. Counter-arguments (if any)
        4. Author's conclusion
        
        Text: {data.context}""",
        
        "compare_concepts": f"""Compare and contrast the concepts discussed in this text:
        {data.context}
        
        Use a structured format showing similarities and differences."""
    }
    
    prompt = prompts.get(data.action, data.action)
    
    result = await ai_manager.generate_text(
        prompt,
        provider_type=ProviderType.LLM,
        max_tokens=2000
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=503, detail="AI service unavailable")
    
    # Parse structured responses
    response_data = {
        "text": result["text"],
        "provider": result["provider"],
        "action": data.action
    }
    
    # Special parsing for quiz
    if data.action == "create_quiz":
        questions = parse_quiz_response(result["text"])
        response_data["structured"] = questions
    
    return response_data


def parse_quiz_response(text: str) -> List[dict]:
    """Parse quiz format from AI response."""
    questions = []
    # Simple parsing logic
    lines = text.split("\n")
    current_q = None
    
    for line in lines:
        line = line.strip()
        if line.startswith("Q:"):
            if current_q:
                questions.append(current_q)
            current_q = {"question": line[2:].strip(), "options": []}
        elif line.startswith(("A:", "B:", "C:", "D:")):
            option = {"label": line[0], "text": line[2:].strip()}
            if current_q:
                current_q["options"].append(option)
                if line.startswith("A:"):
                    current_q["correct"] = "A"
    
    if current_q:
        questions.append(current_q)
    
    return questions


@router.post("/flashcards/generate-deck")
async def generate_flashcard_deck(
    user_book_id: str,
    highlight_ids: List[str],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Generate flashcard deck from highlights."""
    
    user_book = session.get(UserBook, user_book_id)
    if not user_book or user_book.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Create deck
    deck = FlashcardDeck(
        id=generate_id("deck"),
        user_book_id=user_book_id,
        user_id=current_user.id,
        name=f"{user_book.title} - Key Concepts"
    )
    session.add(deck)
    
    # Create cards from highlights
    for hl_id in highlight_ids:
        highlight = session.get(Highlight, hl_id)
        if highlight and highlight.ai_flashcard_front:
            card = Flashcard(
                id=generate_id("card"),
                deck_id=deck.id,
                highlight_id=hl_id,
                front=highlight.ai_flashcard_front,
                back=highlight.ai_flashcard_back or highlight.selected_text,
                next_review=datetime.utcnow() + timedelta(days=1)
            )
            session.add(card)
    
    session.commit()
    
    return {
        "deck_id": deck.id,
        "card_count": len(highlight_ids),
        "name": deck.name
    }


@router.get("/flashcards/study")
async def get_study_cards(
    deck_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get cards due for review (spaced repetition)."""
    
    now = datetime.utcnow()
    
    cards = session.exec(
        select(Flashcard).where(
            and_(
                Flashcard.deck_id == deck_id,
                Flashcard.next_review <= now
            )
        ).limit(limit)
    ).all()
    
    return {
        "cards": cards,
        "due_count": len(cards),
        "new_cards": len([c for c in cards if c.repetitions == 0])
    }


@router.post("/flashcards/{card_id}/review")
async def review_card(
    card_id: str,
    quality: int,  # 0-5 (0=complete blackout, 5=perfect)
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Submit flashcard review and update spaced repetition schedule."""
    
    card = session.get(Flashcard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # SuperMemo-2 algorithm
    if quality < 3:
        card.repetitions = 0
        card.interval = 1
    else:
        card.repetitions += 1
        if card.repetitions == 1:
            card.interval = 1
        elif card.repetitions == 2:
            card.interval = 6
        else:
            card.interval = int(card.interval * card.ease_factor)
    
    # Update ease factor
    card.ease_factor = max(1.3, card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    
    # Schedule next review
    card.next_review = datetime.utcnow() + timedelta(days=card.interval)
    card.last_reviewed = datetime.utcnow()
    card.total_reviews += 1
    if quality >= 3:
        card.correct_reviews += 1
    
    session.add(card)
    session.commit()
    
    return {
        "next_review": card.next_review,
        "interval": card.interval,
        "ease_factor": card.ease_factor
    }


# Helper functions
async def parse_epub_chapter(content: bytes, chapter_idx: int) -> dict:
    """Parse EPUB chapter."""
    # Implementation would use epub library
    return {
        "html": "<p>Chapter content...</p>",
        "text": "Chapter text...",
        "total_chapters": 10
    }

async def get_pdf_pages(content: bytes, start_page: int, count: int) -> dict:
    """Get PDF pages."""
    # Implementation would use PyPDF2 or similar
    return {
        "pages": [],
        "text": "PDF text...",
        "total_pages": 200
    }
