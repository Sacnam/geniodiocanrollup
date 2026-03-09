"""
Scout Agent API endpoints for Lab module.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.auth import get_current_user
from app.core.database import get_session
from app.lab.engine import run_scout_task
from app.lab.models import ScoutAgent, ScoutFinding, ScoutInsight, ScoutStatus
from app.models.user import User

router = APIRouter(prefix="/scouts", tags=["scouts"])


class ScoutCreate(BaseModel):
    name: str
    description: Optional[str] = None
    research_question: str
    keywords: List[str] = []
    sources: List[str] = ["feeds"]
    schedule: str = "daily"
    min_relevance_score: float = 0.7


class ScoutUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    research_question: Optional[str] = None
    keywords: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    schedule: Optional[str] = None
    is_active: Optional[bool] = None
    min_relevance_score: Optional[float] = None


class ScoutResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    research_question: str
    keywords: List[str]
    sources: List[str]
    schedule: str
    status: str
    is_active: bool
    total_findings: int
    unread_findings: int
    last_run_at: Optional[str]
    next_run_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ScoutFindingResponse(BaseModel):
    id: str
    source_type: str
    source_title: str
    source_url: str
    relevance_score: float
    explanation: str
    matched_keywords: List[str]
    key_insights: List[str]
    is_read: bool
    is_saved: bool
    created_at: str


class ScoutInsightResponse(BaseModel):
    id: str
    insight_type: str
    title: str
    description: str
    confidence_score: float
    period_start: str
    period_end: str
    created_at: str


@router.post("", response_model=ScoutResponse, status_code=status.HTTP_201_CREATED)
def create_scout(
    scout_data: ScoutCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new Scout agent."""
    scout = ScoutAgent(
        user_id=current_user.id,
        **scout_data.dict()
    )
    
    db.add(scout)
    db.commit()
    db.refresh(scout)
    
    return _scout_to_response(scout)


@router.get("", response_model=List[ScoutResponse])
def list_scouts(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List user's Scout agents."""
    scouts = db.exec(
        select(ScoutAgent)
        .where(ScoutAgent.user_id == current_user.id)
        .order_by(ScoutAgent.created_at.desc())
    ).all()
    
    return [_scout_to_response(s) for s in scouts]


@router.get("/{scout_id}", response_model=ScoutResponse)
def get_scout(
    scout_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific Scout agent."""
    scout = db.exec(
        select(ScoutAgent).where(
            ScoutAgent.id == scout_id,
            ScoutAgent.user_id == current_user.id
        )
    ).first()
    
    if not scout:
        raise HTTPException(status_code=404, detail="Scout not found")
    
    return _scout_to_response(scout)


@router.patch("/{scout_id}", response_model=ScoutResponse)
def update_scout(
    scout_id: str,
    updates: ScoutUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a Scout agent."""
    scout = db.exec(
        select(ScoutAgent).where(
            ScoutAgent.id == scout_id,
            ScoutAgent.user_id == current_user.id
        )
    ).first()
    
    if not scout:
        raise HTTPException(status_code=404, detail="Scout not found")
    
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(scout, field, value)
    
    db.add(scout)
    db.commit()
    db.refresh(scout)
    
    return _scout_to_response(scout)


@router.delete("/{scout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scout(
    scout_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a Scout agent."""
    scout = db.exec(
        select(ScoutAgent).where(
            ScoutAgent.id == scout_id,
            ScoutAgent.user_id == current_user.id
        )
    ).first()
    
    if not scout:
        raise HTTPException(status_code=404, detail="Scout not found")
    
    db.delete(scout)
    db.commit()
    
    return None


@router.post("/{scout_id}/run")
def run_scout(
    scout_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger a Scout agent run."""
    scout = db.exec(
        select(ScoutAgent).where(
            ScoutAgent.id == scout_id,
            ScoutAgent.user_id == current_user.id
        )
    ).first()
    
    if not scout:
        raise HTTPException(status_code=404, detail="Scout not found")
    
    if scout.status == ScoutStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Scout is already running")
    
    # Trigger async execution
    run_scout_task.delay(scout_id)
    
    return {"message": "Scout run queued", "scout_id": scout_id}


# Findings

@router.get("/{scout_id}/findings", response_model=List[ScoutFindingResponse])
def list_findings(
    scout_id: str,
    unread_only: bool = False,
    saved_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List findings for a Scout agent."""
    query = select(ScoutFinding).where(
        ScoutFinding.scout_id == scout_id,
        ScoutFinding.user_id == current_user.id,
        ScoutFinding.is_dismissed == False
    )
    
    if unread_only:
        query = query.where(ScoutFinding.is_read == False)
    if saved_only:
        query = query.where(ScoutFinding.is_saved == True)
    
    findings = db.exec(
        query.order_by(ScoutFinding.relevance_score.desc())
        .limit(limit)
    ).all()
    
    return [
        ScoutFindingResponse(
            id=f.id,
            source_type=f.source_type,
            source_title=f.source_title,
            source_url=f.source_url,
            relevance_score=f.relevance_score,
            explanation=f.explanation,
            matched_keywords=f.matched_keywords or [],
            key_insights=f.key_insights or [],
            is_read=f.is_read,
            is_saved=f.is_saved,
            created_at=f.created_at.isoformat(),
        )
        for f in findings
    ]


@router.post("/findings/{finding_id}/save")
def save_finding(
    finding_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Save/bookmark a finding."""
    finding = db.exec(
        select(ScoutFinding).where(
            ScoutFinding.id == finding_id,
            ScoutFinding.user_id == current_user.id
        )
    ).first()
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    finding.is_saved = True
    db.add(finding)
    db.commit()
    
    return {"message": "Finding saved"}


@router.post("/findings/{finding_id}/dismiss")
def dismiss_finding(
    finding_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Dismiss a finding."""
    finding = db.exec(
        select(ScoutFinding).where(
            ScoutFinding.id == finding_id,
            ScoutFinding.user_id == current_user.id
        )
    ).first()
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    finding.is_dismissed = True
    db.add(finding)
    db.commit()
    
    return {"message": "Finding dismissed"}


# Insights

@router.get("/{scout_id}/insights", response_model=List[ScoutInsightResponse])
def list_insights(
    scout_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List insights for a Scout agent."""
    insights = db.exec(
        select(ScoutInsight).where(
            ScoutInsight.scout_id == scout_id,
            ScoutInsight.user_id == current_user.id
        ).order_by(ScoutInsight.created_at.desc())
    ).all()
    
    return [
        ScoutInsightResponse(
            id=i.id,
            insight_type=i.insight_type,
            title=i.title,
            description=i.description,
            confidence_score=i.confidence_score,
            period_start=i.period_start.isoformat(),
            period_end=i.period_end.isoformat(),
            created_at=i.created_at.isoformat(),
        )
        for i in insights
    ]


@router.post("/{scout_id}/verify")
def verify_claim_endpoint(
    scout_id: str,
    claim: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Verify a claim using the Scout's research context.
    'Scout, verify this' functionality.
    """
    from app.lab.scout_advanced import verify_claim_task
    
    result = verify_claim_task.delay(claim, scout_id, current_user.id)
    
    return {
        "task_id": result.id,
        "message": "Verification started",
        "scout_id": scout_id,
    }


def _scout_to_response(scout: ScoutAgent) -> ScoutResponse:
    """Convert Scout to response."""
    return ScoutResponse(
        id=scout.id,
        name=scout.name,
        description=scout.description,
        research_question=scout.research_question,
        keywords=scout.keywords or [],
        sources=scout.sources or ["feeds"],
        schedule=scout.schedule,
        status=scout.status.value,
        is_active=scout.is_active,
        total_findings=scout.total_findings,
        unread_findings=scout.unread_findings,
        last_run_at=scout.last_run_at.isoformat() if scout.last_run_at else None,
        next_run_at=scout.next_run_at.isoformat() if scout.next_run_at else None,
        created_at=scout.created_at.isoformat(),
    )
