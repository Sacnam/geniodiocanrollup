"""
Comment system with threading, likes, and mentions.
"""
import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  MessageCircle, Heart, MoreHorizontal, CornerDownRight,
  Edit2, Trash2, CheckCircle, X, AtSign
} from 'lucide-react';
import { commentApi } from '../services/api/comments';
import type { Comment } from '../types/comment';

interface CommentSystemProps {
  articleId: string;
  className?: string;
}

export function CommentSystem({ articleId, className = '' }: CommentSystemProps) {
  const queryClient = useQueryClient();
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [editingComment, setEditingComment] = useState<string | null>(null);
  
  const { data, isLoading } = useQuery({
    queryKey: ['comments', articleId],
    queryFn: () => commentApi.getArticleComments(articleId),
  });
  
  const createComment = useMutation({
    mutationFn: (data: { content: string; parentId?: string }) =>
      commentApi.create(articleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', articleId] });
      setReplyingTo(null);
    },
  });
  
  if (isLoading) {
    return <div className="animate-pulse p-4">Loading comments...</div>;
  }
  
  const comments = data?.items || [];
  const totalCount = data?.total_count || 0;
  
  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <MessageCircle className="w-5 h-5" />
          Comments
          {totalCount > 0 && (
            <span className="text-sm text-muted-foreground">
              ({totalCount})
            </span>
          )}
        </h3>
      </div>
      
      {/* New Comment Form */}
      {!replyingTo && (
        <CommentForm
          onSubmit={(content) => createComment.mutate({ content })}
          isSubmitting={createComment.isPending}
          placeholder="Add a comment... Use @ to mention users"
        />
      )}
      
      {/* Comments List */}
      <div className="space-y-4">
        {comments.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-20" />
            <p>No comments yet</p>
            <p className="text-sm">Be the first to share your thoughts</p>
          </div>
        ) : (
          comments.map((comment) => (
            <CommentThread
              key={comment.id}
              comment={comment}
              articleId={articleId}
              replyingTo={replyingTo}
              setReplyingTo={setReplyingTo}
              editingComment={editingComment}
              setEditingComment={setEditingComment}
              depth={0}
            />
          ))
        )}
      </div>
    </div>
  );
}

interface CommentThreadProps {
  comment: Comment;
  articleId: string;
  replyingTo: string | null;
  setReplyingTo: (id: string | null) => void;
  editingComment: string | null;
  setEditingComment: (id: string | null) => void;
  depth: number;
}

function CommentThread({
  comment,
  articleId,
  replyingTo,
  setReplyingTo,
  editingComment,
  setEditingComment,
  depth
}: CommentThreadProps) {
  const queryClient = useQueryClient();
  const [showActions, setShowActions] = useState(false);
  
  const isReplying = replyingTo === comment.id;
  const isEditing = editingComment === comment.id;
  
  const createReply = useMutation({
    mutationFn: (content: string) =>
      commentApi.create(articleId, { content, parentId: comment.id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', articleId] });
      setReplyingTo(null);
    },
  });
  
  const updateComment = useMutation({
    mutationFn: (content: string) => commentApi.update(comment.id, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', articleId] });
      setEditingComment(null);
    },
  });
  
  const deleteComment = useMutation({
    mutationFn: () => commentApi.delete(comment.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', articleId] });
    },
  });
  
  const toggleLike = useMutation({
    mutationFn: () =>
      comment.isLikedByMe
        ? commentApi.unlike(comment.id)
        : commentApi.like(comment.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', articleId] });
    },
  });
  
  const maxDepth = 4;
  const canNest = depth < maxDepth;
  
  if (comment.isDeleted && !comment.replies?.length) {
    return null;
  }
  
  return (
    <div className={`${depth > 0 ? 'ml-8 pl-4 border-l-2 border-muted' : ''}`}>
      <div className="group flex gap-3">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
            {comment.user?.name?.charAt(0).toUpperCase() || '?'}
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="bg-muted/50 rounded-lg p-3">
            {/* Header */}
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-sm">
                {comment.user?.name || 'Unknown'}
              </span>
              <span className="text-xs text-muted-foreground">
                {new Date(comment.createdAt).toLocaleDateString()}
              </span>
              {comment.isEdited && (
                <span className="text-xs text-muted-foreground">(edited)</span>
              )}
              {comment.isResolved && (
                <CheckCircle className="w-3 h-3 text-green-500" />
              )}
            </div>
            
            {/* Body */}
            {isEditing ? (
              <CommentForm
                initialValue={comment.content}
                onSubmit={(content) => updateComment.mutate(content)}
                onCancel={() => setEditingComment(null)}
                isSubmitting={updateComment.isPending}
                submitLabel="Save"
              />
            ) : (
              <div className="text-sm whitespace-pre-wrap">
                {comment.isDeleted ? (
                  <span className="text-muted-foreground italic">[deleted]</span>
                ) : (
                  <HighlightedMentions text={comment.content} />
                )}
              </div>
            )}
          </div>
          
          {/* Actions */}
          {!comment.isDeleted && !isEditing && (
            <div className="flex items-center gap-4 mt-1 ml-1">
              <button
                onClick={() => toggleLike.mutate()}
                className={`flex items-center gap-1 text-xs transition-colors ${
                  comment.isLikedByMe
                    ? 'text-red-500'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Heart
                  className="w-3 h-3"
                  fill={comment.isLikedByMe ? 'currentColor' : 'none'}
                />
                {comment.likesCount > 0 && comment.likesCount}
              </button>
              
              {canNest && (
                <button
                  onClick={() => setReplyingTo(isReplying ? null : comment.id)}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Reply
                </button>
              )}
              
              {/* More actions */}
              <div className="relative">
                <button
                  onClick={() => setShowActions(!showActions)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <MoreHorizontal className="w-4 h-4 text-muted-foreground" />
                </button>
                
                {showActions && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setShowActions(false)}
                    />
                    <div className="absolute z-50 mt-1 w-32 bg-popover border rounded-lg shadow-lg py-1">
                      <button
                        onClick={() => {
                          setEditingComment(comment.id);
                          setShowActions(false);
                        }}
                        className="w-full px-3 py-1.5 text-left text-sm flex items-center gap-2 hover:bg-muted"
                      >
                        <Edit2 className="w-3 h-3" />
                        Edit
                      </button>
                      <button
                        onClick={() => {
                          if (confirm('Delete this comment?')) {
                            deleteComment.mutate();
                          }
                          setShowActions(false);
                        }}
                        className="w-full px-3 py-1.5 text-left text-sm flex items-center gap-2 text-destructive hover:bg-destructive/10"
                      >
                        <Trash2 className="w-3 h-3" />
                        Delete
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
          
          {/* Reply Form */}
          {isReplying && (
            <div className="mt-3">
              <CommentForm
                onSubmit={(content) => createReply.mutate(content)}
                onCancel={() => setReplyingTo(null)}
                isSubmitting={createReply.isPending}
                placeholder="Write a reply..."
                autoFocus
              />
            </div>
          )}
        </div>
      </div>
      
      {/* Nested Replies */}
      {comment.replies?.map((reply) => (
        <div key={reply.id} className="mt-3">
          <CommentThread
            comment={reply}
            articleId={articleId}
            replyingTo={replyingTo}
            setReplyingTo={setReplyingTo}
            editingComment={editingComment}
            setEditingComment={setEditingComment}
            depth={depth + 1}
          />
        </div>
      ))}
    </div>
  );
}

interface CommentFormProps {
  initialValue?: string;
  onSubmit: (content: string) => void;
  onCancel?: () => void;
  isSubmitting?: boolean;
  placeholder?: string;
  submitLabel?: string;
  autoFocus?: boolean;
}

function CommentForm({
  initialValue = '',
  onSubmit,
  onCancel,
  isSubmitting,
  placeholder = "Write a comment...",
  submitLabel = "Post",
  autoFocus
}: CommentFormProps) {
  const [content, setContent] = useState(initialValue);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;
    onSubmit(content.trim());
    if (!initialValue) {
      setContent('');
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="flex gap-3">
      <div className="flex-1">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          rows={Math.max(2, content.split('\n').length)}
          className="input w-full resize-none"
        />
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <AtSign className="w-3 h-3" />
            Use @ to mention
          </span>
          <div className="flex gap-2">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="btn btn-secondary btn-sm"
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              disabled={!content.trim() || isSubmitting}
              className="btn btn-primary btn-sm"
            >
              {isSubmitting ? 'Posting...' : submitLabel}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}

function HighlightedMentions({ text }: { text: string }) {
  const parts = text.split(/(@\w+(?:\.\w+)*)/g);
  
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('@')) {
          return (
            <span key={i} className="text-primary font-medium">
              {part}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}
