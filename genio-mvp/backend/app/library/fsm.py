"""
Document Processing Finite State Machine (FSM)
Manages document processing lifecycle with retry logic.
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus


class ProcessingState(str, Enum):
    """Document processing states."""
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    CHUNKING = "chunking"
    CHUNKED = "chunked"
    EMBEDDING = "embedding"
    EMBEDDED = "embedded"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    SCORING = "scoring"
    READY = "ready"
    
    # Failure states
    PARSE_FAILED = "parse_failed"
    CHUNK_FAILED = "chunk_failed"
    EMBED_FAILED = "embed_failed"
    EXTRACT_FAILED = "extract_failed"
    FAILED = "failed"


# Valid state transitions
VALID_TRANSITIONS = {
    ProcessingState.UPLOADED: [ProcessingState.PARSING],
    ProcessingState.PARSING: [ProcessingState.PARSED, ProcessingState.PARSE_FAILED],
    ProcessingState.PARSED: [ProcessingState.CHUNKING],
    ProcessingState.CHUNKING: [ProcessingState.CHUNKED, ProcessingState.CHUNK_FAILED],
    ProcessingState.CHUNKED: [ProcessingState.EMBEDDING],
    ProcessingState.EMBEDDING: [ProcessingState.EMBEDDED, ProcessingState.EMBED_FAILED],
    ProcessingState.EMBEDDED: [ProcessingState.EXTRACTING],
    ProcessingState.EXTRACTING: [ProcessingState.EXTRACTED, ProcessingState.EXTRACT_FAILED],
    ProcessingState.EXTRACTED: [ProcessingState.SCORING],
    ProcessingState.SCORING: [ProcessingState.READY],
    
    # Retry transitions from failure states
    ProcessingState.PARSE_FAILED: [ProcessingState.PARSING],
    ProcessingState.CHUNK_FAILED: [ProcessingState.CHUNKING],
    ProcessingState.EMBED_FAILED: [ProcessingState.EMBEDDING],
    ProcessingState.EXTRACT_FAILED: [ProcessingState.EXTRACTING],
}


class DocumentFSM:
    """Finite State Machine for document processing."""
    
    MAX_RETRIES = 3
    
    def __init__(self, document_id: str, db: Session):
        self.document_id = document_id
        self.db = db
        self.document = self._get_document()
    
    def _get_document(self) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == self.document_id).first()
    
    def get_state(self) -> ProcessingState:
        """Get current processing state."""
        if not self.document:
            raise ValueError(f"Document {self.document_id} not found")
        
        # Map DocumentStatus to ProcessingState
        status_map = {
            DocumentStatus.PENDING: ProcessingState.UPLOADED,
            DocumentStatus.PROCESSING: ProcessingState(self.document.processing_state or "parsing"),
            DocumentStatus.READY: ProcessingState.READY,
            DocumentStatus.ERROR: ProcessingState.FAILED,
        }
        
        return status_map.get(self.document.status, ProcessingState.UPLOADED)
    
    def transition_to(self, new_state: ProcessingState) -> bool:
        """Attempt state transition."""
        if not self.document:
            return False
        
        current_state = self.get_state()
        
        # Check if transition is valid
        valid_next = VALID_TRANSITIONS.get(current_state, [])
        if new_state not in valid_next:
            return False
        
        # Update document
        self.document.processing_state = new_state.value
        self.document.state_changed_at = datetime.utcnow()
        
        # Update status based on state
        if new_state == ProcessingState.READY:
            self.document.status = DocumentStatus.READY
            self.document.processed_at = datetime.utcnow()
        elif new_state in [ProcessingState.PARSE_FAILED, ProcessingState.CHUNK_FAILED,
                          ProcessingState.EMBED_FAILED, ProcessingState.EXTRACT_FAILED]:
            self.document.status = DocumentStatus.ERROR
        elif new_state == ProcessingState.FAILED:
            self.document.status = DocumentStatus.ERROR
        else:
            self.document.status = DocumentStatus.PROCESSING
        
        self.db.commit()
        return True
    
    def fail(self, error_message: str) -> bool:
        """Mark current state as failed."""
        if not self.document:
            return False
        
        current = self.get_state()
        
        # Map to failure state
        failure_map = {
            ProcessingState.PARSING: ProcessingState.PARSE_FAILED,
            ProcessingState.CHUNKING: ProcessingState.CHUNK_FAILED,
            ProcessingState.EMBEDDING: ProcessingState.EMBED_FAILED,
            ProcessingState.EXTRACTING: ProcessingState.EXTRACT_FAILED,
        }
        
        failure_state = failure_map.get(current)
        if not failure_state:
            failure_state = ProcessingState.FAILED
        
        self.document.processing_state = failure_state.value
        self.document.processing_error = error_message
        self.document.state_changed_at = datetime.utcnow()
        self.document.status = DocumentStatus.ERROR
        
        self.db.commit()
        return True
    
    def retry(self) -> bool:
        """Retry from failure state."""
        if not self.document:
            return False
        
        current = self.get_state()
        
        # Check if we can retry
        if current not in [ProcessingState.PARSE_FAILED, ProcessingState.CHUNK_FAILED,
                          ProcessingState.EMBED_FAILED, ProcessingState.EXTRACT_FAILED]:
            return False
        
        # Check retry count
        if self.document.retry_count >= self.MAX_RETRIES:
            self.document.processing_state = ProcessingState.FAILED.value
            self.db.commit()
            return False
        
        # Map back to processing state
        retry_map = {
            ProcessingState.PARSE_FAILED: ProcessingState.PARSING,
            ProcessingState.CHUNK_FAILED: ProcessingState.CHUNKING,
            ProcessingState.EMBED_FAILED: ProcessingState.EMBEDDING,
            ProcessingState.EXTRACT_FAILED: ProcessingState.EXTRACTING,
        }
        
        new_state = retry_map[current]
        self.document.processing_state = new_state.value
        self.document.retry_count += 1
        self.document.state_changed_at = datetime.utcnow()
        self.document.status = DocumentStatus.PROCESSING
        
        self.db.commit()
        return True


class Sweeper:
    """Sweeper task to retry stuck documents."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_stuck_documents(self, timeout_minutes: int = 5) -> List[Document]:
        """Find documents stuck in processing state."""
        cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        stuck_states = [
            ProcessingState.PARSING.value,
            ProcessingState.CHUNKING.value,
            ProcessingState.EMBEDDING.value,
            ProcessingState.EXTRACTING.value,
            ProcessingState.SCORING.value,
        ]
        
        return self.db.query(Document).filter(
            and_(
                Document.status == DocumentStatus.PROCESSING,
                Document.processing_state.in_(stuck_states),
                Document.state_changed_at < cutoff
            )
        ).all()
    
    def retry_stuck_documents(self, timeout_minutes: int = 5) -> int:
        """Retry all stuck documents. Returns count retried."""
        stuck = self.find_stuck_documents(timeout_minutes)
        retried = 0
        
        for doc in stuck:
            fsm = DocumentFSM(doc.id, self.db)
            if fsm.retry():
                retried += 1
        
        return retried
