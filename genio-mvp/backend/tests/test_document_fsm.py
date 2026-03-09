"""
Test Document Processing FSM
"""
import pytest
from datetime import datetime, timedelta
from app.library.fsm import DocumentFSM, ProcessingState
from app.models.document import Document, DocumentStatus


class TestDocumentFSM:
    """Test document processing state machine."""

    def test_fsm_initial_state(self, db_session):
        """Document starts in UPLOADED state."""
        doc = Document(
            user_id="user-1",
            filename="test.pdf",
            title="Test Doc",
            status=DocumentStatus.PENDING
        )
        db_session.add(doc)
        db_session.commit()
        
        fsm = DocumentFSM(doc.id, db_session)
        assert fsm.get_state() == ProcessingState.UPLOADED

    def test_fsm_transition_uploaded_to_parsing(self, db_session):
        """Can transition from UPLOADED to PARSING."""
        doc = Document(user_id="user-1", filename="test.pdf", title="Test")
        db_session.add(doc)
        db_session.commit()
        
        fsm = DocumentFSM(doc.id, db_session)
        assert fsm.transition_to(ProcessingState.PARSING) == True
        assert fsm.get_state() == ProcessingState.PARSING

    def test_fsm_complete_flow(self, db_session):
        """Test complete processing flow."""
        doc = Document(user_id="user-1", filename="test.pdf", title="Test")
        db_session.add(doc)
        db_session.commit()
        
        fsm = DocumentFSM(doc.id, db_session)
        
        # Complete flow
        states = [
            ProcessingState.UPLOADED,
            ProcessingState.PARSING,
            ProcessingState.CHUNKING,
            ProcessingState.EMBEDDING,
            ProcessingState.EXTRACTING,
            ProcessingState.READY
        ]
        
        for i in range(len(states) - 1):
            current = states[i]
            next_state = states[i + 1]
            assert fsm.transition_to(next_state) == True
            assert fsm.get_state() == next_state

    def test_fsm_invalid_transition(self, db_session):
        """Invalid transitions should fail."""
        doc = Document(user_id="user-1", filename="test.pdf", title="Test")
        db_session.add(doc)
        db_session.commit()
        
        fsm = DocumentFSM(doc.id, db_session)
        
        # Cannot skip from UPLOADED to READY
        assert fsm.transition_to(ProcessingState.READY) == False
        assert fsm.get_state() == ProcessingState.UPLOADED

    def test_fsm_failure_and_retry(self, db_session):
        """Test failure state and retry mechanism."""
        doc = Document(user_id="user-1", filename="test.pdf", title="Test")
        db_session.add(doc)
        db_session.commit()
        
        fsm = DocumentFSM(doc.id, db_session)
        
        # Move to parsing
        fsm.transition_to(ProcessingState.PARSING)
        
        # Fail
        assert fsm.fail("Parse error") == True
        assert fsm.get_state() == ProcessingState.PARSE_FAILED
        assert doc.processing_error == "Parse error"
        assert doc.retry_count == 0
        
        # Retry
        assert fsm.retry() == True
        assert fsm.get_state() == ProcessingState.PARSING
        assert doc.retry_count == 1

    def test_fsm_max_retries(self, db_session):
        """Max 3 retries then permanent failure."""
        doc = Document(user_id="user-1", filename="test.pdf", title="Test")
        db_session.add(doc)
        db_session.commit()
        
        fsm = DocumentFSM(doc.id, db_session)
        
        # Exhaust retries
        for i in range(3):
            fsm.transition_to(ProcessingState.PARSING)
            fsm.fail(f"Error {i}")
            if i < 2:
                fsm.retry()
        
        # 4th retry should fail
        assert fsm.retry() == False
        assert fsm.get_state() == ProcessingState.FAILED

    def test_fsm_sweeper_detection(self, db_session):
        """Sweeper detects stuck documents."""
        from app.library.fsm import Sweeper
        
        # Create stuck document
        doc = Document(
            user_id="user-1",
            filename="test.pdf",
            title="Test",
            status=DocumentStatus.PROCESSING,
            processing_state="PARSING",
            state_changed_at=datetime.utcnow() - timedelta(minutes=10)
        )
        db_session.add(doc)
        db_session.commit()
        
        sweeper = Sweeper(db_session)
        stuck = sweeper.find_stuck_documents(timeout_minutes=5)
        
        assert len(stuck) == 1
        assert stuck[0].id == doc.id

    def test_fsm_state_timestamps(self, db_session):
        """Each state change updates timestamp."""
        doc = Document(user_id="user-1", filename="test.pdf", title="Test")
        db_session.add(doc)
        db_session.commit()
        
        fsm = DocumentFSM(doc.id, db_session)
        before = datetime.utcnow()
        
        fsm.transition_to(ProcessingState.PARSING)
        
        assert doc.state_changed_at >= before
