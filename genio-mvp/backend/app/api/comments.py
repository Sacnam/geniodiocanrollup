"""
API endpoints for article comments.
"""
import json
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, and_, func

from app.db.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.comment import (
    Comment, CommentLike, CommentCreate, CommentUpdate,
    CommentResponse, CommentThreadResponse
)
from app.utils.id_generator import generate_id
from app.utils.sanitizer import sanitize_html

router = APIRouter()


def build_comment_tree(comments: List[Comment]) -> List[CommentResponse]:
    """Build threaded comment tree from flat list."""
    comment_map = {}
    roots = []
    
    # Create map
    for comment in comments:
        comment_map[comment.id] = {
            **comment.dict(),
            "replies": [],
            "mentions": json.loads(comment.mentions) if comment.mentions else []
        }
    
    # Build tree
    for comment in comments:
        node = comment_map[comment.id]
        if comment.parent_id and comment.parent_id in comment_map:
            comment_map[comment.parent_id]["replies"].append(node)
        else:
            roots.append(node)
    
    return roots


def get_user_info(session: Session, user_id: str) -> dict:
    """Get minimal user info for comment display."""
    user = session.get(User, user_id)
    if not user:
        return {"id": user_id, "name": "Unknown", "avatar": None}
    return {
        "id": user.id,
        "name": user.name or user.email.split('@')[0],
        "avatar": getattr(user, 'avatar_url', None)
    }


@router.post("/articles/{article_id}/comments", status_code=201, response_model=CommentResponse)
async def create_comment(
    article_id: str,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new comment on an article."""
    # Validate parent comment
    depth = 0
    if data.parent_id:
        parent = session.get(Comment, data.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        if parent.article_id != article_id:
            raise HTTPException(status_code=400, detail="Parent comment belongs to different article")
        if parent.is_deleted:
            raise HTTPException(status_code=400, detail="Cannot reply to deleted comment")
        depth = parent.depth + 1
        # Limit nesting depth
        if depth > 5:
            raise HTTPException(status_code=400, detail="Maximum nesting depth reached")
    
    # Extract mentions
    mentions_list = []
    mention_pattern = r'@(\w+(?:\.\w+)*)'
    mentions = re.findall(mention_pattern, data.content)
    
    # Validate mentioned users exist
    for username in mentions:
        mentioned_user = session.exec(
            select(User).where(User.email.startswith(username))
        ).first()
        if mentioned_user:
            mentions_list.append(mentioned_user.id)
    
    # Create comment
    comment = Comment(
        id=generate_id("comment"),
        article_id=article_id,
        user_id=current_user.id,
        parent_id=data.parent_id,
        depth=depth,
        content=data.content.strip(),
        content_html=sanitize_html(data.content),
        mentions=json.dumps(mentions_list)
    )
    
    session.add(comment)
    
    # Update parent replies count
    if data.parent_id:
        parent.replies_count += 1
        session.add(parent)
    
    session.commit()
    session.refresh(comment)
    
    # Build response
    response = CommentResponse(
        **comment.dict(),
        mentions=mentions_list,
        user=get_user_info(session, current_user.id),
        is_liked_by_me=False
    )
    
    return response


@router.get("/articles/{article_id}/comments", response_model=CommentThreadResponse)
async def get_article_comments(
    article_id: str,
    threaded: bool = True,
    include_deleted: bool = False,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get comments for an article."""
    # Build query
    query = select(Comment).where(Comment.article_id == article_id)
    
    if not include_deleted:
        query = query.where(Comment.is_deleted == False)
    
    query = query.order_by(Comment.created_at)
    
    comments = session.exec(query).all()
    
    # Get like status for current user
    comment_ids = [c.id for c in comments]
    liked_comments = set()
    if comment_ids:
        likes = session.exec(
            select(CommentLike.comment_id).where(
                and_(
                    CommentLike.comment_id.in_(comment_ids),
                    CommentLike.user_id == current_user.id
                )
            )
        ).all()
        liked_comments = set(likes)
    
    # Build responses
    comment_responses = []
    for comment in comments:
        mentions = json.loads(comment.mentions) if comment.mentions else []
        comment_responses.append(CommentResponse(
            **comment.dict(),
            mentions=mentions,
            user=get_user_info(session, comment.user_id),
            is_liked_by_me=comment.id in liked_comments
        ))
    
    # Count root comments
    root_count = sum(1 for c in comments if c.depth == 0)
    
    if threaded:
        # Build tree structure
        tree = build_comment_tree(comment_responses)
        return CommentThreadResponse(
            items=tree,
            total_count=len(comments),
            root_count=root_count
        )
    else:
        return CommentThreadResponse(
            items=comment_responses,
            total_count=len(comments),
            root_count=root_count
        )


@router.get("/comments/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a single comment by ID."""
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check like status
    is_liked = session.exec(
        select(CommentLike).where(
            and_(
                CommentLike.comment_id == comment_id,
                CommentLike.user_id == current_user.id
            )
        )
    ).first() is not None
    
    mentions = json.loads(comment.mentions) if comment.mentions else []
    
    return CommentResponse(
        **comment.dict(),
        mentions=mentions,
        user=get_user_info(session, comment.user_id),
        is_liked_by_me=is_liked
    )


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a comment (only by author)."""
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only edit your own comments")
    
    if comment.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot edit deleted comment")
    
    # Update content
    comment.content = data.content.strip()
    comment.content_html = sanitize_html(data.content)
    comment.is_edited = True
    comment.edited_at = datetime.utcnow()
    comment.updated_at = datetime.utcnow()
    
    # Re-extract mentions
    mentions_list = []
    mention_pattern = r'@(\w+(?:\.\w+)*)'
    mentions = re.findall(mention_pattern, data.content)
    for username in mentions:
        mentioned_user = session.exec(
            select(User).where(User.email.startswith(username))
        ).first()
        if mentioned_user:
            mentions_list.append(mentioned_user.id)
    comment.mentions = json.dumps(mentions_list)
    
    session.add(comment)
    session.commit()
    session.refresh(comment)
    
    # Check like status
    is_liked = session.exec(
        select(CommentLike).where(
            and_(
                CommentLike.comment_id == comment_id,
                CommentLike.user_id == current_user.id
            )
        )
    ).first() is not None
    
    return CommentResponse(
        **comment.dict(),
        mentions=mentions_list,
        user=get_user_info(session, comment.user_id),
        is_liked_by_me=is_liked
    )


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Soft-delete a comment."""
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only delete your own comments")
    
    # Soft delete
    comment.is_deleted = True
    comment.deleted_at = datetime.utcnow()
    comment.deleted_by = current_user.id
    comment.content = "[deleted]"
    comment.content_html = "<p>[deleted]</p>"
    comment.updated_at = datetime.utcnow()
    
    session.add(comment)
    session.commit()


@router.post("/comments/{comment_id}/like")
async def like_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Like a comment."""
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if already liked
    existing = session.exec(
        select(CommentLike).where(
            and_(
                CommentLike.comment_id == comment_id,
                CommentLike.user_id == current_user.id
            )
        )
    ).first()
    
    if existing:
        # Already liked, return current state
        return {
            "likes_count": comment.likes_count,
            "is_liked_by_me": True
        }
    
    # Create like
    like = CommentLike(
        comment_id=comment_id,
        user_id=current_user.id
    )
    session.add(like)
    
    # Update count
    comment.likes_count += 1
    session.add(comment)
    session.commit()
    
    return {
        "likes_count": comment.likes_count,
        "is_liked_by_me": True
    }


@router.delete("/comments/{comment_id}/like")
async def unlike_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Remove like from a comment."""
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Find and remove like
    like = session.exec(
        select(CommentLike).where(
            and_(
                CommentLike.comment_id == comment_id,
                CommentLike.user_id == current_user.id
            )
        )
    ).first()
    
    if like:
        session.delete(like)
        comment.likes_count = max(0, comment.likes_count - 1)
        session.add(comment)
        session.commit()
    
    return {
        "likes_count": comment.likes_count,
        "is_liked_by_me": False
    }


@router.post("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mark a comment as resolved (useful for Q&A threads)."""
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Only article owner or comment author can resolve
    # This would need article ownership check in production
    
    comment.is_resolved = True
    comment.resolved_at = datetime.utcnow()
    comment.resolved_by = current_user.id
    comment.updated_at = datetime.utcnow()
    
    session.add(comment)
    session.commit()
    
    return {
        "is_resolved": True,
        "resolved_at": comment.resolved_at,
        "resolved_by": current_user.id
    }


# Import at top level
import re
