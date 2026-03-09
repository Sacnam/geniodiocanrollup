"""
Tag management component with autocomplete, color picker, and cloud view.
"""
import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, X, Hash, Tag as TagIcon, MoreVertical, Cloud } from 'lucide-react';
import { tagApi } from '../services/api/tags';
import type { Tag, TagCloudItem, TagCreate } from '../types/tag';

interface TagManagerProps {
  articleId?: string;
  documentId?: string;
  onTagSelect?: (tag: Tag) => void;
  mode?: 'selector' | 'manager' | 'cloud';
  className?: string;
}

const PRESET_COLORS = [
  '#7c3aed', // violet
  '#2563eb', // blue
  '#059669', // green
  '#dc2626', // red
  '#d97706', // amber
  '#db2777', // pink
  '#4f46e5', // indigo
  '#0891b2', // cyan
  '#65a30d', // lime
  '#ea580c', // orange
];

const PRESET_ICONS = ['🏷️', '📌', '⭐', '🔥', '💡', '📚', '💻', '🤖', '📰', '🔬'];

export function TagManager({
  articleId,
  documentId,
  onTagSelect,
  mode = 'selector',
  className = ''
}: TagManagerProps) {
  const queryClient = useQueryClient();
  const [newTagName, setNewTagName] = useState('');
  const [selectedColor, setSelectedColor] = useState(PRESET_COLORS[0]);
  const [selectedIcon, setSelectedIcon] = useState(PRESET_ICONS[0]);
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Fetch user's tags
  const { data: tags = [], isLoading } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagApi.getAll(),
  });

  // Fetch tag cloud
  const { data: tagCloud = [] } = useQuery({
    queryKey: ['tags', 'cloud'],
    queryFn: () => tagApi.getCloud(),
    enabled: mode === 'cloud',
  });

  // Fetch article tags
  const { data: articleTags = [] } = useQuery({
    queryKey: ['articles', articleId, 'tags'],
    queryFn: () => tagApi.getArticleTags(articleId!),
    enabled: !!articleId,
  });

  // Create tag mutation
  const createTag = useMutation({
    mutationFn: (data: TagCreate) => tagApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      setNewTagName('');
      setShowCreateForm(false);
    },
  });

  // Tag article mutation
  const tagArticle = useMutation({
    mutationFn: (tagId: string) => tagApi.tagArticle(articleId!, tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles', articleId, 'tags'] });
    },
  });

  // Untag article mutation
  const untagArticle = useMutation({
    mutationFn: (tagId: string) => tagApi.untagArticle(articleId!, tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles', articleId, 'tags'] });
    },
  });

  // Delete tag mutation
  const deleteTag = useMutation({
    mutationFn: (tagId: string) => tagApi.delete(tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] });
    },
  });

  const handleCreateTag = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (!newTagName.trim()) return;
    
    createTag.mutate({
      name: newTagName.trim(),
      color: selectedColor,
      icon: selectedIcon,
    });
  }, [newTagName, selectedColor, selectedIcon, createTag]);

  const isTagApplied = (tagId: string) => {
    return articleTags.some((t: Tag) => t.id === tagId);
  };

  if (mode === 'cloud') {
    return (
      <div className={`p-4 ${className}`}>
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Cloud className="w-5 h-5" />
          Tag Cloud
        </h3>
        <div className="flex flex-wrap gap-2">
          {tagCloud.map((tag: TagCloudItem) => (
            <button
              key={tag.id}
              onClick={() => onTagSelect?.(tag as Tag)}
              className="px-3 py-1 rounded-full text-sm font-medium transition-all hover:scale-105"
              style={{
                backgroundColor: `${tag.color}20`,
                color: tag.color,
                border: `1px solid ${tag.color}40`,
                fontSize: `${Math.max(0.75, Math.min(1.25, tag.count / 5))}rem`,
              }}
            >
              {tag.icon && <span className="mr-1">{tag.icon}</span>}
              {tag.name}
              <span className="ml-1 opacity-60">({tag.count})</span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  if (mode === 'manager') {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <TagIcon className="w-5 h-5" />
            Manage Tags
          </h3>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="btn btn-primary btn-sm"
          >
            <Plus className="w-4 h-4 mr-1" />
            New Tag
          </button>
        </div>

        {showCreateForm && (
          <form onSubmit={handleCreateTag} className="card p-4 space-y-3">
            <div>
              <label className="label">Tag Name</label>
              <input
                type="text"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                placeholder="Enter tag name..."
                className="input"
                autoFocus
              />
            </div>

            <div>
              <label className="label">Color</label>
              <div className="flex gap-2 flex-wrap">
                {PRESET_COLORS.map((color) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => setSelectedColor(color)}
                    className={`w-8 h-8 rounded-full transition-all ${
                      selectedColor === color ? 'ring-2 ring-offset-2 ring-primary' : ''
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>

            <div>
              <label className="label">Icon</label>
              <div className="flex gap-2 flex-wrap">
                {PRESET_ICONS.map((icon) => (
                  <button
                    key={icon}
                    type="button"
                    onClick={() => setSelectedIcon(icon)}
                    className={`w-10 h-10 text-xl rounded-lg transition-all ${
                      selectedIcon === icon
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    {icon}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                type="submit"
                disabled={!newTagName.trim() || createTag.isPending}
                className="btn btn-primary"
              >
                {createTag.isPending ? 'Creating...' : 'Create Tag'}
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        <div className="space-y-2">
          {tags.map((tag: Tag) => (
            <div
              key={tag.id}
              className="flex items-center justify-between p-3 bg-card rounded-lg border"
            >
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: tag.color || '#666' }}
                />
                {tag.icon && <span>{tag.icon}</span>}
                <span className="font-medium">{tag.name}</span>
                {tag.usage_count > 0 && (
                  <span className="text-xs text-muted-foreground">
                    ({tag.usage_count} items)
                  </span>
                )}
              </div>
              <button
                onClick={() => deleteTag.mutate(tag.id)}
                className="p-1 text-muted-foreground hover:text-destructive transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Selector mode (for article tagging)
  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex flex-wrap gap-2">
        {articleTags.map((tag: Tag) => (
          <span
            key={tag.id}
            className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-sm"
            style={{
              backgroundColor: `${tag.color}20`,
              color: tag.color,
            }}
          >
            {tag.icon && <span>{tag.icon}</span>}
            {tag.name}
            <button
              onClick={() => untagArticle.mutate(tag.id)}
              className="ml-1 hover:opacity-70"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>

      <div className="relative">
        <input
          type="text"
          value={newTagName}
          onChange={(e) => setNewTagName(e.target.value)}
          placeholder="Add tags..."
          className="input w-full"
        />
        {newTagName && tags.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-popover border rounded-lg shadow-lg max-h-48 overflow-auto">
            {tags
              .filter((t: Tag) =>
                t.name.toLowerCase().includes(newTagName.toLowerCase())
              )
              .map((tag: Tag) => (
                <button
                  key={tag.id}
                  onClick={() => {
                    if (!isTagApplied(tag.id)) {
                      tagArticle.mutate(tag.id);
                    }
                    setNewTagName('');
                  }}
                  className="w-full px-3 py-2 text-left hover:bg-muted flex items-center gap-2"
                  disabled={isTagApplied(tag.id)}
                >
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: tag.color || '#666' }}
                  />
                  {tag.icon && <span>{tag.icon}</span>}
                  <span className={isTagApplied(tag.id) ? 'opacity-50' : ''}>
                    {tag.name}
                  </span>
                  {isTagApplied(tag.id) && (
                    <span className="text-xs text-muted-foreground ml-auto">added</span>
                  )}
                </button>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
