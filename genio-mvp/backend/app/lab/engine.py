"""
Scout Agent execution engine.
Runs research queries against configured sources.
"""
from datetime import datetime, timedelta
from typing import List

from celery import shared_task
from sqlmodel import Session, select

from app.core.database import SessionLocal
from app.lab.models import ScoutAgent, ScoutExecution, ScoutFinding, ScoutStatus
from app.models.article import Article
from app.models.document import Document


class ScoutEngine:
    """
    Executes Scout agent research queries.
    
    Process:
    1. Retrieve relevant content from configured sources
    2. Compute relevance scores using embeddings
    3. Generate AI explanations for matches
    4. Store findings
    """
    
    def __init__(self, scout_id: str, db: Session):
        self.scout_id = scout_id
        self.db = db
        self.scout = db.get(ScoutAgent, scout_id)
        self.execution = None
        
    def run(self) -> dict:
        """Execute the Scout agent."""
        if not self.scout or not self.scout.is_active:
            return {"error": "Scout not found or inactive"}
        
        # Create execution log
        self.execution = ScoutExecution(scout_id=self.scout_id)
        self.db.add(self.execution)
        self.db.commit()
        
        try:
            # Update scout status
            self.scout.status = ScoutStatus.RUNNING
            self.scout.last_run_at = datetime.utcnow()
            self.db.add(self.scout)
            self.db.commit()
            
            findings = []
            
            # Query each source
            for source in self.scout.sources:
                source_findings = self._query_source(source)
                findings.extend(source_findings)
                
                self.execution.sources_checked += 1
                self.db.add(self.execution)
                self.db.commit()
            
            # Update execution
            self.execution.status = "completed"
            self.execution.completed_at = datetime.utcnow()
            self.execution.findings_generated = len(findings)
            
            # Update scout stats
            self.scout.status = ScoutStatus.IDLE
            self.scout.total_findings += len(findings)
            self.scout.unread_findings += len(findings)
            self.scout.next_run_at = self._calculate_next_run()
            
            self.db.add(self.execution)
            self.db.add(self.scout)
            self.db.commit()
            
            return {
                "findings_count": len(findings),
                "sources_checked": self.execution.sources_checked,
                "execution_id": self.execution.id,
            }
            
        except Exception as e:
            self.execution.status = "failed"
            self.execution.error_message = str(e)
            self.execution.completed_at = datetime.utcnow()
            
            self.scout.status = ScoutStatus.ERROR
            
            self.db.add(self.execution)
            self.db.add(self.scout)
            self.db.commit()
            
            raise
    
    def _query_source(self, source: str) -> List[ScoutFinding]:
        """Query a specific data source."""
        if source == "feeds":
            return self._query_feeds()
        elif source == "documents":
            return self._query_documents()
        elif source == "arxiv":
            return self._query_arxiv()
        else:
            return []
    
    def _query_feeds(self) -> List[ScoutFinding]:
        """Query user's RSS feeds."""
        # Get recent articles from user's feeds
        cutoff = datetime.utcnow() - timedelta(days=self.scout.date_range_days)
        
        articles = self.db.exec(
            select(Article)
            .where(
                Article.user_id == self.scout.user_id,
                Article.created_at >= cutoff,
            )
        ).all()
        
        self.execution.items_scanned += len(articles)
        
        findings = []
        for article in articles:
            # Check relevance (simplified - would use embeddings in production)
            relevance = self._calculate_relevance(article.title + " " + (article.excerpt or ""))
            
            if relevance >= self.scout.min_relevance_score:
                finding = ScoutFinding(
                    scout_id=self.scout_id,
                    user_id=self.scout.user_id,
                    source_type="article",
                    source_id=article.id,
                    source_url=article.url,
                    source_title=article.title or "Untitled",
                    relevance_score=relevance,
                    explanation=f"Relevant to research question: {self.scout.research_question}",
                    matched_keywords=self._extract_matched_keywords(article.content or ""),
                )
                findings.append(finding)
                self.db.add(finding)
        
        self.db.commit()
        return findings
    
    def _query_documents(self) -> List[ScoutFinding]:
        """Query user's document library."""
        from app.models.document import Document
        
        documents = self.db.exec(
            select(Document)
            .where(
                Document.user_id == self.scout.user_id,
                Document.status == "ready",
            )
        ).all()
        
        self.execution.items_scanned += len(documents)
        
        findings = []
        for doc in documents:
            relevance = self._calculate_relevance(doc.title + " " + (doc.excerpt or ""))
            
            if relevance >= self.scout.min_relevance_score:
                finding = ScoutFinding(
                    scout_id=self.scout_id,
                    user_id=self.scout.user_id,
                    source_type="document",
                    source_id=doc.id,
                    source_url=f"/library/{doc.id}",
                    source_title=doc.title or doc.original_filename,
                    relevance_score=relevance,
                    explanation=f"Document relevant to research",
                    matched_keywords=[],
                )
                findings.append(finding)
                self.db.add(finding)
        
        self.db.commit()
        return findings
    
    def _query_arxiv(self) -> List[ScoutFinding]:
        """Query arXiv for academic papers."""
        # Would integrate with arXiv API
        # For now, return empty
        return []
    
    def _calculate_relevance(self, text: str) -> float:
        """
        Calculate relevance score (0-1) between text and scout query.
        Simplified - production would use embeddings.
        """
        text_lower = text.lower()
        question_lower = self.scout.research_question.lower()
        
        # Simple keyword overlap
        question_words = set(question_lower.split())
        text_words = set(text_lower.split())
        
        if not question_words:
            return 0.0
        
        overlap = len(question_words & text_words)
        score = overlap / len(question_words)
        
        # Boost for exact keyword matches
        for keyword in self.scout.keywords:
            if keyword.lower() in text_lower:
                score += 0.1
        
        return min(score, 1.0)
    
    def _extract_matched_keywords(self, text: str) -> List[str]:
        """Extract which keywords were matched in text."""
        text_lower = text.lower()
        matched = []
        
        for keyword in self.scout.keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)
        
        return matched
    
    def _calculate_next_run(self) -> datetime:
        """Calculate next run time based on schedule."""
        now = datetime.utcnow()
        
        if self.scout.schedule == "hourly":
            return now + timedelta(hours=1)
        elif self.scout.schedule == "daily":
            return now + timedelta(days=1)
        elif self.scout.schedule == "weekly":
            return now + timedelta(weeks=1)
        else:
            return now + timedelta(days=1)


@shared_task
def run_scout_task(scout_id: str):
    """Celery task to run a Scout agent."""
    db = SessionLocal()
    try:
        engine = ScoutEngine(scout_id, db)
        return engine.run()
    finally:
        db.close()


@shared_task
def schedule_scout_runs():
    """
    Periodic task to schedule Scout agents.
    Runs every hour to check which scouts need execution.
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Find scouts ready to run
        scouts = db.exec(
            select(ScoutAgent)
            .where(
                ScoutAgent.is_active == True,
                ScoutAgent.status == ScoutStatus.IDLE,
                ScoutAgent.next_run_at <= now,
            )
        ).all()
        
        for scout in scouts:
            run_scout_task.delay(scout.id)
        
        return {"scheduled": len(scouts)}
        
    finally:
        db.close()
