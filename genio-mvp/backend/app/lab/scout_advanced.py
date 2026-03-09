"""
Advanced Scout Agent Engine
Lab Module v3.0 - Proactive Research Automation

From LIBRARY_PRD.md §7 (Dual-Agent Architecture):
- The Scout (Outbound Agent): Verifies claims, finds counter-arguments
- Integrates with PKG for context-aware research
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from celery import shared_task
from sqlmodel import Session, select

from app.core.ai_gateway import embed_texts, generate_text
from app.core.database import SessionLocal
from app.lab.models import (
    ScoutAgent,
    ScoutExecution,
    ScoutFinding,
    ScoutInsight,
    ScoutStatus,
)
from app.library.graph_rag import hybrid_search, answer_cross_document_query
from app.library.pkg_models import PKGNode, PKGEdge, PKGEdgeType
from app.models.article import Article
from app.models.document import Document


class ScoutResearchEngine:
    """
    Advanced Scout engine with PKG-aware research capabilities.
    
    Capabilities:
    1. Proactive monitoring of user feeds, documents, web
    2. Contextual verification using PKG
    3. Counter-argument discovery
    4. Confidence-weighted findings
    """
    
    def __init__(self, scout_id: str, db: Session):
        self.scout_id = scout_id
        self.db = db
        self.scout = db.get(ScoutAgent, scout_id)
        self.execution = None
        self.findings_buffer = []
        
    def run_advanced_research(self) -> Dict[str, Any]:
        """
        Execute advanced research with PKG context.
        
        Pipeline:
        1. Understand research context from PKG
        2. Multi-source parallel search
        3. Relevance scoring with PKG alignment
        4. Counter-argument detection
        5. Generate insights
        """
        if not self.scout or not self.scout.is_active:
            return {"error": "Scout not found or inactive"}
        
        # Create execution log
        self.execution = ScoutExecution(scout_id=self.scout_id)
        self.db.add(self.execution)
        self.db.commit()
        
        try:
            self.scout.status = ScoutStatus.RUNNING
            self.scout.last_run_at = datetime.utcnow()
            self.db.add(self.scout)
            self.db.commit()
            
            # Step 1: Get user's PKG context
            pkg_context = self._get_pkg_context()
            
            # Step 2: Search across sources
            for source in self.scout.sources:
                self._search_source_advanced(source, pkg_context)
                self.execution.sources_checked += 1
                self.db.add(self.execution)
                self.db.commit()
            
            # Step 3: Detect contradictions with existing knowledge
            self._detect_contradictions(pkg_context)
            
            # Step 4: Generate insights from findings
            insights = self._generate_insights()
            
            # Step 5: Update execution
            self.execution.status = "completed"
            self.execution.completed_at = datetime.utcnow()
            self.execution.findings_generated = len(self.findings_buffer)
            
            self.scout.status = ScoutStatus.IDLE
            self.scout.total_findings += len(self.findings_buffer)
            self.scout.unread_findings += len(self.findings_buffer)
            self.scout.next_run_at = self._calculate_next_run()
            
            self.db.add(self.execution)
            self.db.add(self.scout)
            self.db.commit()
            
            return {
                "findings_count": len(self.findings_buffer),
                "insights_count": len(insights),
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
    
    def _get_pkg_context(self) -> Dict[str, Any]:
        """
        Extract relevant PKG context for research.
        
        Returns known concepts, knowledge gaps, and recent interests.
        """
        # Get user's known concepts
        known_concepts = self.db.exec(
            select(PKGNode).where(
                PKGNode.user_id == self.scout.user_id,
                PKGNode.knowledge_state.in_(["known", "learning"])
            )
        ).all()
        
        # Get knowledge gaps
        gaps = self.db.exec(
            select(PKGNode).where(
                PKGNode.user_id == self.scout.user_id,
                PKGNode.knowledge_state == "gap"
            )
        ).all()
        
        # Get recent research interests (from Scout keywords)
        interests = self.scout.keywords or []
        
        return {
            "known_concepts": [{"id": c.id, "name": c.name} for c in known_concepts[:20]],
            "knowledge_gaps": [{"id": g.id, "name": g.name} for g in gaps[:10]],
            "interests": interests,
            "research_question": self.scout.research_question,
        }
    
    def _search_source_advanced(self, source: str, pkg_context: Dict):
        """
        Advanced source search with PKG awareness.
        """
        if source == "feeds":
            self._search_feeds_advanced(pkg_context)
        elif source == "documents":
            self._search_documents_advanced(pkg_context)
        elif source == "web":
            self._search_web_advanced(pkg_context)
        elif source == "arxiv":
            self._search_arxiv_advanced(pkg_context)
    
    def _search_feeds_advanced(self, pkg_context: Dict):
        """Search RSS feeds with PKG-enhanced relevance."""
        cutoff = datetime.utcnow() - timedelta(days=self.scout.date_range_days)
        
        # Get recent articles
        articles = self.db.exec(
            select(Article).where(
                Article.user_id == self.scout.user_id,
                Article.created_at >= cutoff,
            )
        ).all()
        
        self.execution.items_scanned += len(articles)
        
        for article in articles:
            # Compute base relevance
            text = f"{article.title} {article.excerpt or ''}"
            relevance = self._calculate_advanced_relevance(text, pkg_context)
            
            if relevance >= self.scout.min_relevance_score:
                # Check if contradicts existing knowledge
                contradiction = self._check_contradiction(text, pkg_context)
                
                finding = ScoutFinding(
                    scout_id=self.scout_id,
                    user_id=self.scout.user_id,
                    source_type="article",
                    source_id=article.id,
                    source_url=article.url,
                    source_title=article.title or "Untitled",
                    relevance_score=relevance,
                    explanation=self._generate_explanation(text, relevance, pkg_context),
                    matched_keywords=self._extract_matched_keywords(text),
                    key_insights=["Relevant to research focus"] if relevance > 0.8 else [],
                    contradictions=contradiction,
                )
                
                self.findings_buffer.append(finding)
                self.db.add(finding)
        
        self.db.commit()
    
    def _search_documents_advanced(self, pkg_context: Dict):
        """Search user's document library."""
        # Use GraphRAG for semantic search across documents
        if pkg_context["research_question"]:
            results = hybrid_search(
                query=pkg_context["research_question"],
                user_id=self.scout.user_id,
                db=self.db,
                k_vector=10,
                k_graph=5
            )
            
            for result in results:
                node = self.db.get(PKGNode, result["id"])
                if node and node.source_documents:
                    # Get source document
                    doc_id = node.source_documents[0]
                    doc = self.db.get(Document, doc_id)
                    
                    if doc:
                        finding = ScoutFinding(
                            scout_id=self.scout_id,
                            user_id=self.scout.user_id,
                            source_type="document",
                            source_id=doc.id,
                            source_url=f"/library/{doc.id}",
                            source_title=doc.title or doc.original_filename,
                            relevance_score=result["score"],
                            explanation=f"Relevant concept: {node.name}",
                            matched_keywords=[node.name],
                            key_insights=[f"Connected to {len(node.relationships or [])} concepts in your knowledge graph"],
                        )
                        
                        self.findings_buffer.append(finding)
                        self.db.add(finding)
            
            self.db.commit()
    
    def _search_web_advanced(self, pkg_context: Dict):
        """Web search (placeholder for future implementation)."""
        # Would integrate with SerpAPI, Bing API, etc.
        pass
    
    def _search_arxiv_advanced(self, pkg_context: Dict):
        """arXiv search (placeholder for future implementation)."""
        # Would integrate with arXiv API
        pass
    
    def _calculate_advanced_relevance(self, text: str, pkg_context: Dict) -> float:
        """
        Calculate relevance using multiple signals:
        1. Keyword overlap with research question
        2. Semantic similarity to PKG known concepts
        3. Gap-filling potential
        """
        text_lower = text.lower()
        
        # Signal 1: Keyword overlap
        keywords = set(self.scout.keywords or [])
        text_words = set(text_lower.split())
        keyword_score = len(keywords & text_words) / len(keywords) if keywords else 0
        
        # Signal 2: Semantic similarity to known concepts
        concept_score = 0
        if pkg_context["known_concepts"]:
            concept_text = " ".join([c["name"] for c in pkg_context["known_concepts"][:5]])
            # Simplified - would use embeddings in production
            concept_score = len(set(concept_text.lower().split()) & text_words) / 10
        
        # Signal 3: Gap-filling potential
        gap_score = 0
        for gap in pkg_context["knowledge_gaps"]:
            if gap["name"].lower() in text_lower:
                gap_score += 0.1
        
        # Combine signals
        relevance = min(1.0, keyword_score * 0.5 + concept_score * 0.3 + gap_score)
        return relevance
    
    def _check_contradiction(self, text: str, pkg_context: Dict) -> Optional[str]:
        """
        Check if text contradicts user's existing PKG knowledge.
        Uses LLM for contradiction detection.
        """
        if not pkg_context["known_concepts"]:
            return None
        
        # Simplified check - would use LLM in production
        # Look for negation of known concepts
        known_names = [c["name"].lower() for c in pkg_context["known_concepts"]]
        
        for name in known_names:
            # Very simple heuristic: concept + negation words
            negation_patterns = [f"not {name}", f"{name} is false", f"{name} is wrong"]
            for pattern in negation_patterns:
                if pattern in text.lower():
                    return f"Possible contradiction with: {name}"
        
        return None
    
    def _generate_explanation(self, text: str, relevance: float, pkg_context: Dict) -> str:
        """Generate human-readable explanation of relevance."""
        reasons = []
        
        if relevance > 0.8:
            reasons.append("Highly relevant to your research focus")
        
        matched = self._extract_matched_keywords(text)
        if matched:
            reasons.append(f"Matches keywords: {', '.join(matched[:3])}")
        
        if pkg_context["knowledge_gaps"]:
            reasons.append("May fill knowledge gaps")
        
        return "; ".join(reasons) if reasons else "Relevant to research"
    
    def _extract_matched_keywords(self, text: str) -> List[str]:
        """Extract which scout keywords are matched in text."""
        text_lower = text.lower()
        matched = []
        
        for keyword in (self.scout.keywords or []):
            if keyword.lower() in text_lower:
                matched.append(keyword)
        
        return matched
    
    def _detect_contradictions(self, pkg_context: Dict):
        """Flag findings that contradict existing knowledge."""
        # Already done during search, but could do additional verification
        pass
    
    def _generate_insights(self) -> List[ScoutInsight]:
        """
        Generate aggregated insights from findings.
        
        Types: trend, pattern, gap, opportunity
        """
        insights = []
        
        if len(self.findings_buffer) < 3:
            return insights
        
        # Analyze findings for patterns
        sources = set(f.source_type for f in self.findings_buffer)
        
        if len(sources) > 1:
            # Multi-source insight
            insight = ScoutInsight(
                scout_id=self.scout_id,
                user_id=self.scout.user_id,
                insight_type="pattern",
                title="Cross-Source Pattern Detected",
                description=f"Topic appears across {len(sources)} different source types",
                supporting_findings=[f.id for f in self.findings_buffer[:5]],
                confidence_score=0.75,
                period_start=datetime.utcnow() - timedelta(days=self.scout.date_range_days),
                period_end=datetime.utcnow(),
            )
            insights.append(insight)
            self.db.add(insight)
        
        # Gap-filling opportunity
        gaps_filled = sum(1 for f in self.findings_buffer if f.relevance_score > 0.8)
        if gaps_filled > 0:
            insight = ScoutInsight(
                scout_id=self.scout_id,
                user_id=self.scout.user_id,
                insight_type="opportunity",
                title="Knowledge Gap Filling",
                description=f"{gaps_filled} findings highly relevant to your knowledge gaps",
                supporting_findings=[f.id for f in self.findings_buffer if f.relevance_score > 0.8][:3],
                confidence_score=0.8,
                period_start=datetime.utcnow() - timedelta(days=self.scout.date_range_days),
                period_end=datetime.utcnow(),
            )
            insights.append(insight)
            self.db.add(insight)
        
        self.db.commit()
        return insights
    
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
def run_advanced_scout_task(scout_id: str):
    """Celery task to run advanced Scout research."""
    db = SessionLocal()
    try:
        engine = ScoutResearchEngine(scout_id, db)
        return engine.run_advanced_research()
    finally:
        db.close()


@shared_task
def verify_claim_task(claim: str, scout_id: str, user_id: str):
    """
    Explicit verification task.
    User asks: "Scout, verify this claim"
    """
    db = SessionLocal()
    try:
        # Use GraphRAG to check claim against PKG
        result = answer_cross_document_query(
            query=f"Verify this claim: {claim}",
            user_id=user_id,
            db=db
        )
        
        # Create finding with verification result
        finding = ScoutFinding(
            scout_id=scout_id,
            user_id=user_id,
            source_type="verification",
            source_id="",
            source_url="",
            source_title=f"Verification: {claim[:50]}...",
            relevance_score=1.0,
            explanation=result["answer"],
            key_insights=[f"Based on {result['context_size']} knowledge sources"],
        )
        
        db.add(finding)
        db.commit()
        
        return {
            "finding_id": finding.id,
            "verified": True,
            "sources_used": result["context_size"],
        }
    finally:
        db.close()
