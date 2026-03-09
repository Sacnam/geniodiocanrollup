"""
TypeScript types for comments system.
"""

export interface Comment {
  id: string;
  articleId: string;
  userId: string;
  parentId: string | null;
  depth: number;
  content: string;
  contentHtml?: string;
  mentions: string[];
  likesCount: number;
  repliesCount: number;
  isEdited: boolean;
  editedAt?: string;
  isDeleted: boolean;
  isResolved: boolean;
  resolvedAt?: string;
  user?: {
    id: string;
    name: string;
    avatar?: string;
  };
  isLikedByMe: boolean;
  createdAt: string;
  updatedAt: string;
  replies?: Comment[];
}

export interface CommentThread {
  items: Comment[];
  totalCount: number;
  rootCount: number;
}

export interface CreateCommentRequest {
  content: string;
  parentId?: string;
}

export interface UpdateCommentRequest {
  content: string;
}
