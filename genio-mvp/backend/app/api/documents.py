"""
Document API endpoints for Library module.
"""
import os
import uuid
from pathlib import Path
from typing import List, Optional, Set

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session, func, select

from app.api.auth import get_current_user
from app.core.database import get_session
from app.core.sanitizer import sanitize_filename
from app.library.extraction import extract_document_task
from app.models.document import (
    Document,
    DocumentCollection,
    DocumentHighlight,
    DocumentStatus,
    DocumentType,
)
from app.models.user import User

router = APIRouter(prefix="/documents", tags=["documents"])

# Upload settings
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/tmp/uploads")
ALLOWED_TYPES = {
    "application/pdf": DocumentType.PDF,
    "text/plain": DocumentType.TEXT,
    "text/markdown": DocumentType.MARKDOWN,
}
ALLOWED_EXTENSIONS: Set[str] = {'.pdf', '.txt', '.md', '.docx', '.epub'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILENAME_LENGTH = 255


def validate_file_extension(filename: str) -> bool:
    """Validate file extension against allowed list."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def generate_safe_filename(original_filename: str) -> str:
    """Generate a safe unique filename."""
    # Sanitize the original filename
    safe_name = sanitize_filename(original_filename, max_length=MAX_FILENAME_LENGTH)
    
    # Get extension from sanitized name
    ext = Path(safe_name).suffix.lower()
    if not ext or ext not in ALLOWED_EXTENSIONS:
        ext = ".bin"  # Default extension if none or invalid
    
    # Generate unique filename with UUID
    return f"{uuid.uuid4()}{ext}"


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str


class DocumentResponse(BaseModel):
    id: str
    title: Optional[str]
    original_filename: str
    doc_type: str
    status: str
    excerpt: Optional[str]
    author: Optional[str]
    page_count: Optional[int]
    word_count: Optional[int]
    tags: List[str]
    created_at: str

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class HighlightCreate(BaseModel):
    char_start: int
    char_end: int
    highlighted_text: str
    note: Optional[str] = None
    color: str = "yellow"
    page_number: Optional[int] = None


class HighlightResponse(HighlightCreate):
    id: str
    created_at: str


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    collection_id: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Upload a new document."""
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, TXT, MD"
        )
    
    # Check file size (read first chunk)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Validate file extension
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File extension not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate safe unique filename
    unique_filename = generate_safe_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Ensure upload directory exists and is within allowed path
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Validate the resolved path is within UPLOAD_DIR (prevent path traversal)
    resolved_path = Path(file_path).resolve()
    resolved_upload_dir = Path(UPLOAD_DIR).resolve()
    if not str(resolved_path).startswith(str(resolved_upload_dir)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )
    
    # Save file
    with open(resolved_path, "wb") as f:
        f.write(contents)
    
    # Create document record
    doc = Document(
        user_id=current_user.id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size_bytes=len(contents),
        mime_type=file.content_type,
        doc_type=ALLOWED_TYPES[file.content_type],
        status=DocumentStatus.UPLOADED,
    )
    
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Trigger extraction
    extract_document_task.delay(doc.id)
    
    return DocumentUploadResponse(
        id=doc.id,
        filename=file.filename,
        status="processing",
        message="Document uploaded and processing started",
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[DocumentStatus] = None,
    doc_type: Optional[DocumentType] = None,
    collection_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List user's documents."""
    query = select(Document).where(Document.user_id == current_user.id)
    
    if status:
        query = query.where(Document.status == status)
    if doc_type:
        query = query.where(Document.doc_type == doc_type)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Document.title.ilike(search_term)) |
            (Document.content.ilike(search_term)) |
            (Document.original_filename.ilike(search_term))
        )
    
    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total = db.exec(count_query).one()
    
    # Apply pagination
    query = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    
    docs = db.exec(query).all()
    
    return DocumentListResponse(
        items=[_doc_to_response(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document."""
    doc = db.exec(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return _doc_to_response(doc)


@router.get("/{document_id}/content")
def get_document_content(
    document_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get full document content."""
    doc = db.exec(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if doc.status != DocumentStatus.READY:
        return {"status": doc.status.value, "content": None}
    
    return {
        "status": doc.status.value,
        "content": doc.content,
        "title": doc.title,
        "word_count": doc.word_count,
    }


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a document."""
    doc = db.exec(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except OSError:
        pass  # Ignore file deletion errors
    
    db.delete(doc)
    db.commit()
    
    return None


# Highlights

@router.post("/{document_id}/highlights", response_model=HighlightResponse)
def create_highlight(
    document_id: str,
    highlight: HighlightCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a highlight/annotation."""
    # Verify document exists and belongs to user
    doc = db.exec(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    hl = DocumentHighlight(
        document_id=document_id,
        user_id=current_user.id,
        **highlight.dict()
    )
    
    db.add(hl)
    db.commit()
    db.refresh(hl)
    
    return HighlightResponse(
        id=hl.id,
        char_start=hl.char_start,
        char_end=hl.char_end,
        highlighted_text=hl.highlighted_text,
        note=hl.note,
        color=hl.color,
        page_number=hl.page_number,
        created_at=hl.created_at.isoformat(),
    )


@router.get("/{document_id}/highlights", response_model=List[HighlightResponse])
def list_highlights(
    document_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List highlights for a document."""
    highlights = db.exec(
        select(DocumentHighlight).where(
            DocumentHighlight.document_id == document_id,
            DocumentHighlight.user_id == current_user.id
        ).order_by(DocumentHighlight.char_start)
    ).all()
    
    return [
        HighlightResponse(
            id=h.id,
            char_start=h.char_start,
            char_end=h.char_end,
            highlighted_text=h.highlighted_text,
            note=h.note,
            color=h.color,
            page_number=h.page_number,
            created_at=h.created_at.isoformat(),
        )
        for h in highlights
    ]


def _doc_to_response(doc: Document) -> DocumentResponse:
    """Convert Document to response."""
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        original_filename=doc.original_filename,
        doc_type=doc.doc_type.value,
        status=doc.status.value,
        excerpt=doc.excerpt,
        author=doc.author,
        page_count=doc.page_count,
        word_count=doc.word_count,
        tags=doc.tags or [],
        created_at=doc.created_at.isoformat(),
    )
