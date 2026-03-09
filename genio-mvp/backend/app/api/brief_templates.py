"""
API endpoints for brief templates.
"""
import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, and_

from app.db.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.brief_template import (
    BriefTemplate, BriefTemplateCreate, BriefTemplateUpdate,
    BriefTemplateResponse, BriefSectionConfig, BriefLayout
)
from app.utils.id_generator import generate_id

router = APIRouter()


def parse_sections(sections_json: str) -> List[BriefSectionConfig]:
    """Parse sections from JSON string."""
    try:
        data = json.loads(sections_json) if sections_json else []
        return [BriefSectionConfig(**item) for item in data]
    except (json.JSONDecodeError, TypeError):
        return []


@router.post("", status_code=201, response_model=BriefTemplateResponse)
async def create_template(
    data: BriefTemplateCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new brief template."""
    # If setting as default, unset other defaults
    if data.is_default if hasattr(data, 'is_default') else False:
        existing_defaults = session.exec(
            select(BriefTemplate).where(
                and_(
                    BriefTemplate.user_id == current_user.id,
                    BriefTemplate.is_default == True
                )
            )
        ).all()
        for template in existing_defaults:
            template.is_default = False
            session.add(template)
    
    # Create default sections
    default_sections = [
        BriefSectionConfig(
            type="headlines",
            title="Top Headlines",
            position=0,
            max_items=3
        ),
        BriefSectionConfig(
            type="high_delta",
            title="High Novelty",
            position=1,
            max_items=5,
            filter_delta_min=0.7
        ),
        BriefSectionConfig(
            type="saved_searches",
            title="Your Topics",
            position=2,
            max_items=3
        )
    ]
    
    template = BriefTemplate(
        id=generate_id("brieftmpl"),
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        layout=data.layout,
        max_articles=data.max_articles,
        min_delta_score=data.min_delta_score,
        delivery_time=data.delivery_time,
        delivery_days=json.dumps(data.delivery_days),
        sections=json.dumps([s.dict() for s in default_sections]),
        is_default=getattr(data, 'is_default', False)
    )
    
    session.add(template)
    session.commit()
    session.refresh(template)
    
    return BriefTemplateResponse(
        **template.dict(),
        sections=parse_sections(template.sections),
        delivery_days=json.loads(template.delivery_days)
    )


@router.get("", response_model=List[BriefTemplateResponse])
async def get_templates(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all brief templates for the user."""
    query = select(BriefTemplate).where(
        BriefTemplate.user_id == current_user.id
    )
    
    if not include_inactive:
        query = query.where(BriefTemplate.is_active == True)
    
    templates = session.exec(query.order_by(BriefTemplate.created_at.desc())).all()
    
    return [
        BriefTemplateResponse(
            **t.dict(),
            sections=parse_sections(t.sections),
            delivery_days=json.loads(t.delivery_days)
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=BriefTemplateResponse)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific brief template."""
    template = session.exec(
        select(BriefTemplate).where(
            and_(
                BriefTemplate.id == template_id,
                BriefTemplate.user_id == current_user.id
            )
        )
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return BriefTemplateResponse(
        **template.dict(),
        sections=parse_sections(template.sections),
        delivery_days=json.loads(template.delivery_days)
    )


@router.put("/{template_id}", response_model=BriefTemplateResponse)
async def update_template(
    template_id: str,
    data: BriefTemplateUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a brief template."""
    template = session.exec(
        select(BriefTemplate).where(
            and_(
                BriefTemplate.id == template_id,
                BriefTemplate.user_id == current_user.id
            )
        )
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Handle default change
    if data.is_default and not template.is_default:
        existing_defaults = session.exec(
            select(BriefTemplate).where(
                and_(
                    BriefTemplate.user_id == current_user.id,
                    BriefTemplate.is_default == True
                )
            )
        ).all()
        for t in existing_defaults:
            t.is_default = False
            session.add(t)
    
    # Update fields
    for field, value in data.dict(exclude_unset=True).items():
        if field == "sections" and value is not None:
            setattr(template, field, json.dumps([s.dict() for s in value]))
        elif field == "delivery_days" and value is not None:
            setattr(template, field, json.dumps(value))
        else:
            setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    
    session.add(template)
    session.commit()
    session.refresh(template)
    
    return BriefTemplateResponse(
        **template.dict(),
        sections=parse_sections(template.sections),
        delivery_days=json.loads(template.delivery_days)
    )


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a brief template."""
    template = session.exec(
        select(BriefTemplate).where(
            and_(
                BriefTemplate.id == template_id,
                BriefTemplate.user_id == current_user.id
            )
        )
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    session.delete(template)
    session.commit()


@router.post("/{template_id}/preview")
async def preview_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Generate a preview of the brief."""
    template = session.exec(
        select(BriefTemplate).where(
            and_(
                BriefTemplate.id == template_id,
                BriefTemplate.user_id == current_user.id
            )
        )
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # This would call the brief generation service with preview mode
    # For now, return a placeholder
    return {
        "template_id": template_id,
        "generated_at": datetime.utcnow().isoformat(),
        "sections": [
            {
                "type": "headlines",
                "title": "Top Headlines",
                "articles": []
            }
        ],
        "total_articles": 0,
        "estimated_read_time_minutes": 5
    }


@router.post("/{template_id}/set-default")
async def set_default_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Set a template as the default."""
    # Unset current default
    existing_defaults = session.exec(
        select(BriefTemplate).where(
            and_(
                BriefTemplate.user_id == current_user.id,
                BriefTemplate.is_default == True
            )
        )
    ).all()
    for t in existing_defaults:
        t.is_default = False
        session.add(t)
    
    # Set new default
    template = session.exec(
        select(BriefTemplate).where(
            and_(
                BriefTemplate.id == template_id,
                BriefTemplate.user_id == current_user.id
            )
        )
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.is_default = True
    template.updated_at = datetime.utcnow()
    session.add(template)
    session.commit()
    
    return {"status": "ok", "template_id": template_id}


@router.get("/layouts/available")
async def get_available_layouts():
    """Get list of available brief layouts."""
    return [
        {"id": BriefLayout.COMPACT, "name": "Compact", "description": "Minimal list view for quick scanning"},
        {"id": BriefLayout.STANDARD, "name": "Standard", "description": "Balanced sections with summaries"},
        {"id": BriefLayout.DETAILED, "name": "Detailed", "description": "Full content with AI analysis"},
        {"id": BriefLayout.EXECUTIVE, "name": "Executive", "description": "High-level summary only"},
        {"id": BriefLayout.MAGAZINE, "name": "Magazine", "description": "Visual, magazine-style layout"}
    ]
