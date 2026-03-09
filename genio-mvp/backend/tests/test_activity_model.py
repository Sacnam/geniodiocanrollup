"""Tests for AI Activity Log model."""
import pytest
from datetime import datetime, timedelta
from sqlmodel import Session, select, func

from app.models.activity import AIActivityLog, AIActivityLogCreate


class TestAIActivityLog:
    """Test AI Activity Log functionality."""

    def test_create_activity_log(self, session: Session):
        """Should create activity log entry."""
        log = AIActivityLog(
            user_id="user-123",
            operation="embedding",
            model="text-embedding-3-small",
            input_tokens=100,
            output_tokens=0,
            total_tokens=100,
            cost=0.0001,
            resource_type="article",
            resource_id="article-456",
            latency_ms=150,
            status="success"
        )
        
        session.add(log)
        session.commit()
        session.refresh(log)
        
        assert log.id is not None
        assert log.user_id == "user-123"
        assert log.operation == "embedding"
        assert log.cost == 0.0001
        assert log.status == "success"
        assert log.created_at is not None

    def test_activity_log_with_error(self, session: Session):
        """Should log failed operations."""
        log = AIActivityLog(
            user_id="user-123",
            operation="summary",
            model="gpt-4o",
            input_tokens=500,
            output_tokens=0,
            total_tokens=500,
            cost=0.0,
            status="error",
            error_message="Rate limit exceeded"
        )
        
        session.add(log)
        session.commit()
        
        assert log.status == "error"
        assert log.error_message == "Rate limit exceeded"

    def test_cached_operation(self, session: Session):
        """Should mark cached operations."""
        log = AIActivityLog(
            user_id="user-123",
            operation="embedding",
            model="text-embedding-3-small",
            input_tokens=100,
            cost=0.0,
            cached=True
        )
        
        session.add(log)
        session.commit()
        
        assert log.cached is True

    def test_query_by_user(self, session: Session):
        """Should query logs by user."""
        # Create logs for different users
        for i in range(3):
            log = AIActivityLog(
                user_id="user-123",
                operation="embedding",
                model="text-embedding-3-small",
                cost=0.0001 * (i + 1)
            )
            session.add(log)
        
        for i in range(2):
            log = AIActivityLog(
                user_id="user-456",
                operation="summary",
                model="gpt-4o",
                cost=0.01 * (i + 1)
            )
            session.add(log)
        
        session.commit()
        
        # Query for user-123
        from sqlalchemy import select as sa_select
        result = session.exec(
            sa_select(AIActivityLog).where(AIActivityLog.user_id == "user-123")
        ).all()
        
        assert len(result) == 3
        for log in result:
            assert log.user_id == "user-123"

    def test_query_by_operation(self, session: Session):
        """Should query logs by operation type."""
        operations = ["embedding", "embedding", "summary", "brief_generation"]
        
        for op in operations:
            log = AIActivityLog(
                user_id="user-123",
                operation=op,
                model="gpt-4o",
                cost=0.001
            )
            session.add(log)
        
        session.commit()
        
        from sqlalchemy import select as sa_select, func as sa_func
        result = session.exec(
            sa_select(AIActivityLog).where(AIActivityLog.operation == "embedding")
        ).all()
        
        assert len(result) == 2

    def test_cost_aggregation(self, session: Session):
        """Should aggregate costs correctly."""
        costs = [0.001, 0.002, 0.003, 0.004]
        
        for cost in costs:
            log = AIActivityLog(
                user_id="user-123",
                operation="summary",
                model="gpt-4o",
                cost=cost
            )
            session.add(log)
        
        session.commit()
        
        from sqlalchemy import select as sa_select, func as sa_func
        total_cost = session.exec(
            sa_select(sa_func.coalesce(sa_func.sum(AIActivityLog.cost), 0))
            .where(AIActivityLog.user_id == "user-123")
        ).one()
        
        assert total_cost == sum(costs)

    def test_time_based_filtering(self, session: Session):
        """Should filter logs by time range."""
        now = datetime.utcnow()
        
        # Old log
        old_log = AIActivityLog(
            user_id="user-123",
            operation="embedding",
            model="text-embedding-3-small",
            cost=0.001,
            created_at=now - timedelta(days=10)
        )
        session.add(old_log)
        
        # Recent logs
        for i in range(3):
            log = AIActivityLog(
                user_id="user-123",
                operation="summary",
                model="gpt-4o",
                cost=0.01,
                created_at=now - timedelta(hours=i)
            )
            session.add(log)
        
        session.commit()
        
        # Query last 24 hours
        from sqlalchemy import select as sa_select, func as sa_func
        recent_count = session.exec(
            sa_select(sa_func.count(AIActivityLog.id))
            .where(AIActivityLog.user_id == "user-123")
            .where(AIActivityLog.created_at >= now - timedelta(days=1))
        ).one()
        
        assert recent_count == 3

    def test_latency_tracking(self, session: Session):
        """Should track operation latency."""
        log = AIActivityLog(
            user_id="user-123",
            operation="embedding",
            model="text-embedding-3-small",
            latency_ms=145,
            cost=0.0001
        )
        
        session.add(log)
        session.commit()
        
        assert log.latency_ms == 145

    def test_resource_tracking(self, session: Session):
        """Should track which resource triggered the operation."""
        log = AIActivityLog(
            user_id="user-123",
            operation="graph_extraction",
            model="gemini-flash",
            resource_type="document",
            resource_id="doc-789",
            cost=0.005
        )
        
        session.add(log)
        session.commit()
        
        assert log.resource_type == "document"
        assert log.resource_id == "doc-789"
