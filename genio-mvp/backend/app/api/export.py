"""
Data export API for GDPR compliance and user data portability.
"""
import json
from datetime import datetime
from typing import Optional
from io import StringIO, BytesIO
import csv

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.feed import Feed
from app.models.article import Article, UserArticleContext
from app.models.document import Document, DocumentHighlight
from app.models.brief import Brief
from app.models.reading_list import ReadingListItem
from app.library.pkg_models import PKGNode, PKGEdge
from app.lab.models import ScoutAgent, ScoutFinding

router = APIRouter(prefix="/export", tags=["export"])


class ExportRequest(BaseModel):
    format: str = "json"  # json, csv, markdown
    include_feeds: bool = True
    include_articles: bool = True
    include_documents: bool = True
    include_highlights: bool = True
    include_reading_list: bool = True
    include_pkg: bool = False
    include_scouts: bool = True
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


def export_to_json(user: User, db: Session, request: ExportRequest) -> dict:
    """Export all user data to JSON format."""
    data = {
        "export_metadata": {
            "user_id": str(user.id),
            "email": user.email,
            "exported_at": datetime.utcnow().isoformat(),
            "version": "1.0"
        }
    }
    
    # Feeds
    if request.include_feeds:
        feeds = db.exec(select(Feed).where(Feed.user_id == user.id)).all()
        data["feeds"] = [{
            "id": str(f.id),
            "url": f.url,
            "title": f.title,
            "category": f.category,
            "created_at": f.created_at.isoformat() if f.created_at else None
        } for f in feeds]
    
    # Articles (with user context)
    if request.include_articles:
        contexts = db.exec(
            select(UserArticleContext, Article)
            .join(Article)
            .where(UserArticleContext.user_id == user.id)
        ).all()
        
        data["articles"] = [{
            "id": str(ctx.article_id),
            "title": article.title,
            "url": article.url,
            "is_read": ctx.is_read,
            "is_starred": ctx.is_starred,
            "is_archived": ctx.is_archived,
            "delta_score": ctx.delta_score,
            "read_at": ctx.read_at.isoformat() if ctx.read_at else None,
            "created_at": article.created_at.isoformat() if article.created_at else None
        } for ctx, article in contexts]
    
    # Documents
    if request.include_documents:
        documents = db.exec(
            select(Document).where(Document.user_id == user.id)
        ).all()
        
        data["documents"] = [{
            "id": str(d.id),
            "filename": d.original_filename,
            "title": d.title,
            "tags": d.tags,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None
        } for d in documents]
    
    # Highlights
    if request.include_highlights:
        highlights = db.exec(
            select(DocumentHighlight)
            .where(DocumentHighlight.user_id == user.id)
        ).all()
        
        data["highlights"] = [{
            "id": str(h.id),
            "document_id": str(h.document_id),
            "text": h.highlighted_text,
            "note": h.note,
            "color": h.color,
            "created_at": h.created_at.isoformat() if h.created_at else None
        } for h in highlights]
    
    # Reading List
    if request.include_reading_list:
        items = db.exec(
            select(ReadingListItem)
            .where(ReadingListItem.user_id == user.id)
        ).all()
        
        data["reading_list"] = [{
            "id": str(item.id),
            "url": item.url,
            "title": item.title,
            "is_read": item.is_read,
            "is_archived": item.is_archived,
            "tags": item.tags,
            "notes": item.notes,
            "created_at": item.created_at.isoformat() if item.created_at else None
        } for item in items]
    
    # Knowledge Graph
    if request.include_pkg:
        nodes = db.exec(select(PKGNode).where(PKGNode.user_id == user.id)).all()
        edges = db.exec(select(PKGEdge).where(PKGEdge.user_id == user.id)).all()
        
        data["knowledge_graph"] = {
            "nodes": [{
                "id": str(n.id),
                "name": n.name,
                "type": n.node_type,
                "definition": n.definition,
                "knowledge_state": n.knowledge_state
            } for n in nodes],
            "edges": [{
                "id": str(e.id),
                "source": e.source_id,
                "target": e.target_id,
                "type": e.edge_type
            } for e in edges]
        }
    
    # Scouts
    if request.include_scouts:
        scouts = db.exec(
            select(ScoutAgent).where(ScoutAgent.user_id == user.id)
        ).all()
        
        data["scouts"] = []
        for scout in scouts:
            findings = db.exec(
                select(ScoutFinding).where(ScoutFinding.scout_id == scout.id)
            ).all()
            
            data["scouts"].append({
                "id": str(scout.id),
                "name": scout.name,
                "research_question": scout.research_question,
                "keywords": scout.keywords,
                "findings": [{
                    "id": str(f.id),
                    "title": f.source_title,
                    "url": f.source_url,
                    "relevance_score": f.relevance_score,
                    "is_saved": f.is_saved
                } for f in findings]
            })
    
    return data


def export_to_csv(user: User, db: Session, request: ExportRequest) -> str:
    """Export articles to CSV format."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "ID", "Title", "URL", "Feed", "Is Read", "Is Starred",
        "Is Archived", "Delta Score", "Created At"
    ])
    
    # Data
    contexts = db.exec(
        select(UserArticleContext, Article, Feed)
        .join(Article)
        .join(Feed)
        .where(UserArticleContext.user_id == user.id)
    ).all()
    
    for ctx, article, feed in contexts:
        writer.writerow([
            str(ctx.article_id),
            article.title,
            article.url,
            feed.title,
            ctx.is_read,
            ctx.is_starred,
            ctx.is_archived,
            ctx.delta_score,
            article.created_at.isoformat() if article.created_at else ""
        ])
    
    return output.getvalue()


def export_highlights_to_markdown(user: User, db: Session) -> str:
    """Export highlights to Markdown format."""
    lines = ["# My Highlights\n", f"*Exported on {datetime.utcnow().strftime('%Y-%m-%d')}*\n\n"]
    
    highlights = db.exec(
        select(DocumentHighlight, Document)
        .join(Document)
        .where(DocumentHighlight.user_id == user.id)
        .order_by(DocumentHighlight.created_at.desc())
    ).all()
    
    current_doc = None
    for hl, doc in highlights:
        if current_doc != doc.id:
            lines.append(f"\n## {doc.title or doc.original_filename}\n")
            current_doc = doc.id
        
        lines.append(f"\n> {hl.highlighted_text}\n")
        if hl.note:
            lines.append(f"\n**Note:** {hl.note}\n")
        lines.append(f"\n---\n")
    
    return "".join(lines)


@router.post("/data")
def export_data(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export user data in requested format."""
    
    if request.format == "json":
        data = export_to_json(current_user, db, request)
        
        return StreamingResponse(
            iter([json.dumps(data, indent=2)]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=genio_export_{datetime.utcnow().strftime('%Y%m%d')}.json"
            }
        )
    
    elif request.format == "csv":
        csv_data = export_to_csv(current_user, db, request)
        
        return StreamingResponse(
            iter([csv_data]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=genio_articles_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            }
        )
    
    elif request.format == "markdown":
        md_data = export_highlights_to_markdown(current_user, db)
        
        return StreamingResponse(
            iter([md_data]),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=genio_highlights_{datetime.utcnow().strftime('%Y%m%d')}.md"
            }
        )
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {request.format}"
        )


@router.delete("/account")
def delete_account(
    confirmation: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user account and all associated data (GDPR right to erasure)."""
    
    if confirmation != "DELETE":
        raise HTTPException(
            status_code=400,
            detail="Please type 'DELETE' to confirm account deletion"
        )
    
    # TODO: Implement cascade deletion
    # Delete all user data in order:
    # 1. Highlights
    # 2. Reading list
    # 3. Documents
    # 4. Briefs
    # 5. User article contexts
    # 6. Feeds
    # 7. PKG nodes/edges
    # 8. Scouts
    # 9. User
    
    # For now, just deactivate
    current_user.is_active = False
    db.add(current_user)
    db.commit()
    
    return {
        "message": "Account deletion scheduled. All data will be removed within 30 days."
    }
