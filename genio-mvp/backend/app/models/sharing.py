"""
Sharing and collaboration models for team features.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlmodel import Field, SQLModel


class SharePermission(str, Enum):
    """Permission levels for shared items."""
    VIEW = "view"  # Read-only
    COMMENT = "comment"  # Can comment
    EDIT = "edit"  # Can edit tags, notes
    ADMIN = "admin"  # Full control


class ShareType(str, Enum):
    """Types of items that can be shared."""
    ARTICLE = "article"
    DOCUMENT = "document"
    FEED = "feed"
    COLLECTION = "collection"
    SAVED_VIEW = "saved_view"
    BRIEF = "brief"


class ShareLink(SQLModel, table=True):
    """Shareable link for content."""
    __tablename__ = "share_links"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    
    # Owner
    owner_id: str = Field(foreign_key="users.id", index=True)
    
    # What is being shared
    share_type: str  # ShareType
    item_id: str  # ID of the shared item
    
    # Share configuration
    token: str = Field(index=True, unique=True)  # Public access token
    permission: str = Field(default=SharePermission.VIEW)
    
    # Access control
    password: Optional[str] = None  # Optional password protection
    expires_at: Optional[datetime] = None  # Optional expiration
    max_views: Optional[int] = None  # Optional view limit
    view_count: int = Field(default=0)
    
    # Public settings
    allow_comments: bool = Field(default=False)
    allow_download: bool = Field(default=False)
    
    # Status
    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Team(SQLModel, table=True):
    """Team/Organization for collaboration."""
    __tablename__ = "teams"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    
    # Team info
    name: str
    slug: str = Field(index=True, unique=True)
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Settings
    is_public: bool = Field(default=False)  # Discoverable in search
    allow_guest_invites: bool = Field(default=True)
    
    # Billing
    plan: str = Field(default="free")  # free, pro, enterprise
    max_members: int = Field(default=5)
    
    # Stats
    member_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TeamMember(SQLModel, table=True):
    """Membership in a team."""
    __tablename__ = "team_members"
    
    team_id: str = Field(foreign_key="teams.id", primary_key=True)
    user_id: str = Field(foreign_key="users.id", primary_key=True)
    
    # Role
    role: str = Field(default="member")  # owner, admin, member, guest
    
    # Permissions
    can_invite: bool = Field(default=False)
    can_manage_content: bool = Field(default=False)
    can_billing: bool = Field(default=False)
    
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    invited_by: Optional[str] = None


class TeamInvite(SQLModel, table=True):
    """Pending invitation to join a team."""
    __tablename__ = "team_invites"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    
    team_id: str = Field(foreign_key="teams.id", index=True)
    invited_by: str = Field(foreign_key="users.id")
    
    # Invite details
    email: str = Field(index=True)
    token: str = Field(unique=True)
    role: str = Field(default="member")
    
    # Status
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SharedCollection(SQLModel, table=True):
    """Collection of items shared within a team."""
    __tablename__ = "shared_collections"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    
    team_id: str = Field(foreign_key="teams.id", index=True)
    created_by: str = Field(foreign_key="users.id")
    
    # Collection info
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    
    # Items (JSON array of {type, id, added_by, added_at, note})
    items: str = Field(default="[]")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CommentReaction(SQLModel, table=True):
    """Reactions to comments (emoji)."""
    __tablename__ = "comment_reactions"
    
    comment_id: str = Field(foreign_key="comments.id", primary_key=True)
    user_id: str = Field(foreign_key="users.id", primary_key=True)
    reaction: str = Field(primary_key=True)  # emoji
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# API Schemas
class CreateShareLinkRequest(SQLModel):
    share_type: str
    item_id: str
    permission: str = SharePermission.VIEW
    password: Optional[str] = None
    expires_in_days: Optional[int] = None
    max_views: Optional[int] = None
    allow_comments: bool = False


class ShareLinkResponse(SQLModel):
    id: str
    token: str
    share_url: str
    permission: str
    expires_at: Optional[datetime]
    view_count: int
    is_active: bool
    created_at: datetime


class CreateTeamRequest(SQLModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False


class TeamResponse(SQLModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    avatar_url: Optional[str]
    is_public: bool
    member_count: int
    my_role: str
    created_at: datetime


class TeamMemberResponse(SQLModel):
    user_id: str
    name: str
    email: str
    avatar_url: Optional[str]
    role: str
    joined_at: datetime


class InviteToTeamRequest(SQLModel):
    email: str
    role: str = "member"


class CreateSharedCollectionRequest(SQLModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class AddToCollectionRequest(SQLModel):
    item_type: str
    item_id: str
    note: Optional[str] = None
