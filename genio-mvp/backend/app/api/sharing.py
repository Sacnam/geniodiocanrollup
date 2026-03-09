"""
API endpoints for sharing and team collaboration.
"""
import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, and_, or_

from app.db.database import get_session
from app.core.security import get_current_user, get_optional_user
from app.models.user import User
from app.models.sharing import (
    ShareLink, Team, TeamMember, TeamInvite, SharedCollection,
    SharePermission, ShareType,
    CreateShareLinkRequest, ShareLinkResponse,
    CreateTeamRequest, TeamResponse, TeamMemberResponse,
    InviteToTeamRequest, CreateSharedCollectionRequest
)
from app.utils.id_generator import generate_id
from app.core.config import settings

router = APIRouter()


def generate_share_token(length: int = 16) -> str:
    """Generate a secure share token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_invite_token(length: int = 32) -> str:
    """Generate a secure invite token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# Share Links

@router.post("/share", response_model=ShareLinkResponse)
async def create_share_link(
    data: CreateShareLinkRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a shareable link for content."""
    # Generate token
    token = generate_share_token()
    
    # Calculate expiration
    expires_at = None
    if data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=data.expires_in_days)
    
    share = ShareLink(
        id=generate_id("share"),
        owner_id=current_user.id,
        share_type=data.share_type,
        item_id=data.item_id,
        token=token,
        permission=data.permission,
        password=data.password,
        expires_at=expires_at,
        max_views=data.max_views,
        allow_comments=data.allow_comments
    )
    
    session.add(share)
    session.commit()
    session.refresh(share)
    
    share_url = f"{settings.FRONTEND_URL}/s/{token}"
    
    return ShareLinkResponse(
        id=share.id,
        token=token,
        share_url=share_url,
        permission=share.permission,
        expires_at=share.expires_at,
        view_count=share.view_count,
        is_active=share.is_active,
        created_at=share.created_at
    )


@router.get("/share/{token}")
async def access_shared_content(
    token: str,
    password: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_user),
    session: Session = Depends(get_session)
):
    """Access content via share link."""
    share = session.exec(
        select(ShareLink).where(ShareLink.token == token)
    ).first()
    
    if not share or not share.is_active:
        raise HTTPException(status_code=404, detail="Share link not found")
    
    # Check expiration
    if share.expires_at and share.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Share link has expired")
    
    # Check view limit
    if share.max_views and share.view_count >= share.max_views:
        raise HTTPException(status_code=410, detail="View limit reached")
    
    # Check password
    if share.password and share.password != password:
        raise HTTPException(status_code=403, detail="Invalid password")
    
    # Increment view count
    share.view_count += 1
    session.add(share)
    session.commit()
    
    # Fetch the actual content based on share_type
    content = await fetch_shared_content(session, share)
    
    return {
        "share": {
            "permission": share.permission,
            "allow_comments": share.allow_comments,
            "owner_id": share.owner_id
        },
        "content": content
    }


async def fetch_shared_content(session: Session, share: ShareLink):
    """Fetch the content being shared."""
    if share.share_type == ShareType.ARTICLE:
        from app.models.article import Article, UserArticleContext
        article = session.get(Article, share.item_id)
        if article:
            return {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "url": article.url,
                "author": article.author,
                "published_at": article.published_at
            }
    
    elif share.share_type == ShareType.COLLECTION:
        collection = session.get(SharedCollection, share.item_id)
        return collection
    
    # Add more types as needed
    return {"id": share.item_id, "type": share.share_type}


@router.get("/my-shares")
async def list_my_shares(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List all share links created by the user."""
    shares = session.exec(
        select(ShareLink).where(ShareLink.owner_id == current_user.id)
        .order_by(ShareLink.created_at.desc())
    ).all()
    
    return [
        {
            "id": s.id,
            "share_type": s.share_type,
            "item_id": s.item_id,
            "token": s.token,
            "share_url": f"{settings.FRONTEND_URL}/s/{s.token}",
            "permission": s.permission,
            "view_count": s.view_count,
            "expires_at": s.expires_at,
            "is_active": s.is_active,
            "created_at": s.created_at
        }
        for s in shares
    ]


@router.delete("/share/{share_id}")
async def revoke_share_link(
    share_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Revoke a share link."""
    share = session.exec(
        select(ShareLink).where(
            and_(
                ShareLink.id == share_id,
                ShareLink.owner_id == current_user.id
            )
        )
    ).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    share.is_active = False
    session.add(share)
    session.commit()
    
    return {"status": "revoked"}


# Teams

@router.post("/teams", response_model=TeamResponse)
async def create_team(
    data: CreateTeamRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new team."""
    # Generate slug
    base_slug = data.name.lower().replace(" ", "-")
    slug = base_slug
    counter = 1
    
    # Ensure unique slug
    while session.exec(select(Team).where(Team.slug == slug)).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    team = Team(
        id=generate_id("team"),
        name=data.name,
        slug=slug,
        description=data.description,
        is_public=data.is_public,
        member_count=1
    )
    
    session.add(team)
    
    # Add creator as owner
    member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role="owner",
        can_invite=True,
        can_manage_content=True,
        can_billing=True
    )
    session.add(member)
    session.commit()
    session.refresh(team)
    
    return TeamResponse(
        **team.dict(),
        my_role="owner"
    )


@router.get("/teams", response_model=List[TeamResponse])
async def list_my_teams(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List teams the user is a member of."""
    memberships = session.exec(
        select(TeamMember, Team)
        .join(Team, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == current_user.id)
    ).all()
    
    return [
        TeamResponse(
            **team.dict(),
            my_role=member.role
        )
        for member, team in memberships
    ]


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get team details."""
    # Check membership
    member = session.exec(
        select(TeamMember).where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.user_id == current_user.id
            )
        )
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return TeamResponse(
        **team.dict(),
        my_role=member.role
    )


@router.post("/teams/{team_id}/invite")
async def invite_to_team(
    team_id: str,
    data: InviteToTeamRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Invite someone to join the team."""
    # Check permissions
    member = session.exec(
        select(TeamMember).where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.user_id == current_user.id,
                TeamMember.can_invite == True
            )
        )
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Cannot invite members")
    
    team = session.get(Team, team_id)
    
    # Check member limit
    if team.member_count >= team.max_members:
        raise HTTPException(status_code=400, detail="Team member limit reached")
    
    # Check for existing invite
    existing = session.exec(
        select(TeamInvite).where(
            and_(
                TeamInvite.team_id == team_id,
                TeamInvite.email == data.email,
                TeamInvite.accepted_at == None
            )
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Invite already pending")
    
    # Create invite
    invite = TeamInvite(
        id=generate_id("inv"),
        team_id=team_id,
        invited_by=current_user.id,
        email=data.email,
        token=generate_invite_token(),
        role=data.role,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    session.add(invite)
    session.commit()
    
    # TODO: Send email invitation
    
    return {
        "invite_id": invite.id,
        "email": data.email,
        "expires_at": invite.expires_at
    }


@router.post("/teams/join/{token}")
async def join_team(
    token: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Join a team via invite token."""
    invite = session.exec(
        select(TeamInvite).where(TeamInvite.token == token)
    ).first()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    if invite.accepted_at:
        raise HTTPException(status_code=400, detail="Invite already used")
    
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Invite expired")
    
    if invite.email != current_user.email:
        raise HTTPException(status_code=403, detail="Invite for different email")
    
    # Add to team
    member = TeamMember(
        team_id=invite.team_id,
        user_id=current_user.id,
        role=invite.role
    )
    session.add(member)
    
    # Mark invite as accepted
    invite.accepted_at = datetime.utcnow()
    session.add(invite)
    
    # Update team count
    team = session.get(Team, invite.team_id)
    team.member_count += 1
    session.add(team)
    
    session.commit()
    
    return {"status": "joined", "team_id": invite.team_id}


@router.get("/teams/{team_id}/members", response_model=List[TeamMemberResponse])
async def list_team_members(
    team_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List team members."""
    # Check membership
    is_member = session.exec(
        select(TeamMember).where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.user_id == current_user.id
            )
        )
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a team member")
    
    members = session.exec(
        select(TeamMember, User)
        .join(User, TeamMember.user_id == User.id)
        .where(TeamMember.team_id == team_id)
    ).all()
    
    return [
        TeamMemberResponse(
            user_id=user.id,
            name=user.name or user.email.split('@')[0],
            email=user.email,
            avatar_url=getattr(user, 'avatar_url', None),
            role=member.role,
            joined_at=member.joined_at
        )
        for member, user in members
    ]


# Shared Collections

@router.post("/teams/{team_id}/collections")
async def create_shared_collection(
    team_id: str,
    data: CreateSharedCollectionRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a shared collection in a team."""
    # Check membership
    member = session.exec(
        select(TeamMember).where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.user_id == current_user.id
            )
        )
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    
    collection = SharedCollection(
        id=generate_id("coll"),
        team_id=team_id,
        created_by=current_user.id,
        name=data.name,
        description=data.description,
        icon=data.icon,
        color=data.color
    )
    
    session.add(collection)
    session.commit()
    session.refresh(collection)
    
    return collection


@router.get("/teams/{team_id}/collections")
async def list_team_collections(
    team_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List shared collections in a team."""
    # Check membership
    is_member = session.exec(
        select(TeamMember).where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.user_id == current_user.id
            )
        )
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a team member")
    
    collections = session.exec(
        select(SharedCollection).where(SharedCollection.team_id == team_id)
        .order_by(SharedCollection.created_at.desc())
    ).all()
    
    return collections
