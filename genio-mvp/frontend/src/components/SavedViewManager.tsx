"""
Saved views management component with filter builder.
"""
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, LayoutGrid, Star, Pin, Trash2, Edit3, Share2, MoreVertical,
  Search, Tag, Filter, Calendar, ArrowUpDown, Check
} from 'lucide-react';
import { savedViewApi } from '../services/api/savedViews';
import type { SavedView, FilterConfig } from '../types/savedView';

interface SavedViewManagerProps {
  onSelectView?: (view: SavedView) => void;
  currentFilters?: FilterConfig;
  className?: string;
}

const PRESET_ICONS = ['📋', '⭐', '🔖', '📚', '🔥', '💡', '🤖', '📰', '📊', '🎯'];
const PRESET_COLORS = ['#7c3aed', '#2563eb', '#059669', '#dc2626', '#d97706', '#db2777', '#4f46e5'];

export function SavedViewManager({
  onSelectView,
  currentFilters,
  className = ''
}: SavedViewManagerProps) {
  const queryClient = useQueryClient();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingView, setEditingView] = useState<SavedView | null>(null);
  const [formData, setFormData] = useState<Partial<SavedView>>({
    name: '',
    description: '',
    icon: PRESET_ICONS[0],
    color: PRESET_COLORS[0],
    filters: currentFilters || {},
  });

  const { data: views = [], isLoading } = useQuery({
    queryKey: ['savedViews'],
    queryFn: () => savedViewApi.getAll(),
  });

  const createView = useMutation({
    mutationFn: (data: Partial<SavedView>) => savedViewApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedViews'] });
      setShowCreateForm(false);
      resetForm();
    },
  });

  const updateView = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<SavedView> }) =>
      savedViewApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedViews'] });
      setEditingView(null);
      resetForm();
    },
  });

  const deleteView = useMutation({
    mutationFn: (id: string) => savedViewApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedViews'] });
    },
  });

  const setDefaultView = useMutation({
    mutationFn: (id: string) => savedViewApi.setDefault(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedViews'] });
    },
  });

  const shareView = useMutation({
    mutationFn: (id: string) => savedViewApi.share(id),
    onSuccess: (data) => {
      // Copy share URL to clipboard
      navigator.clipboard.writeText(data.share_url);
      alert('Share link copied to clipboard!');
    },
  });

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      icon: PRESET_ICONS[0],
      color: PRESET_COLORS[0],
      filters: currentFilters || {},
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingView) {
      updateView.mutate({ id: editingView.id, data: formData });
    } else {
      createView.mutate(formData);
    }
  };

  const startEdit = (view: SavedView) => {
    setEditingView(view);
    setFormData(view);
    setShowCreateForm(true);
  };

  const pinnedViews = views.filter((v: SavedView) => v.is_pinned);
  const unpinnedViews = views.filter((v: SavedView) => !v.is_pinned);

  if (isLoading) {
    return <div className="animate-pulse">Loading views...</div>;
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <LayoutGrid className="w-5 h-5" />
          Saved Views
        </h3>
        <button
          onClick={() => {
            setEditingView(null);
            setShowCreateForm(!showCreateForm);
          }}
          className="btn btn-primary btn-sm"
        >
          <Plus className="w-4 h-4 mr-1" />
          New View
        </button>
      </div>

      {/* Create/Edit Form */}
      {showCreateForm && (
        <form onSubmit={handleSubmit} className="card p-4 space-y-4">
          <div>
            <label className="label">View Name *</label>
            <input
              type="text"
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., High Priority Articles"
              className="input"
              required
            />
          </div>

          <div>
            <label className="label">Description</label>
            <input
              type="text"
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Brief description of this view"
              className="input"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Icon</label>
              <div className="flex gap-1 flex-wrap">
                {PRESET_ICONS.map((icon) => (
                  <button
                    key={icon}
                    type="button"
                    onClick={() => setFormData({ ...formData, icon })}
                    className={`w-10 h-10 text-xl rounded-lg transition-all ${
                      formData.icon === icon
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    {icon}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label">Color</label>
              <div className="flex gap-1 flex-wrap">
                {PRESET_COLORS.map((color) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => setFormData({ ...formData, color })}
                    className={`w-8 h-8 rounded-full transition-all ${
                      formData.color === color ? 'ring-2 ring-offset-2 ring-primary' : ''
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={!formData.name?.trim()}
              className="btn btn-primary"
            >
              {editingView ? 'Update View' : 'Create View'}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowCreateForm(false);
                setEditingView(null);
                resetForm();
              }}
              className="btn btn-secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Pinned Views */}
      {pinnedViews.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground">Pinned</h4>
          {pinnedViews.map((view: SavedView) => (
            <ViewCard
              key={view.id}
              view={view}
              onSelect={onSelectView}
              onEdit={startEdit}
              onDelete={(id) => deleteView.mutate(id)}
              onSetDefault={(id) => setDefaultView.mutate(id)}
              onShare={(id) => shareView.mutate(id)}
            />
          ))}
        </div>
      )}

      {/* All Views */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-muted-foreground">All Views</h4>
        {unpinnedViews.length === 0 && pinnedViews.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <LayoutGrid className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No saved views yet</p>
            <p className="text-sm">Create a view to quickly access your favorite filters</p>
          </div>
        ) : (
          unpinnedViews.map((view: SavedView) => (
            <ViewCard
              key={view.id}
              view={view}
              onSelect={onSelectView}
              onEdit={startEdit}
              onDelete={(id) => deleteView.mutate(id)}
              onSetDefault={(id) => setDefaultView.mutate(id)}
              onShare={(id) => shareView.mutate(id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

interface ViewCardProps {
  view: SavedView;
  onSelect?: (view: SavedView) => void;
  onEdit: (view: SavedView) => void;
  onDelete: (id: string) => void;
  onSetDefault: (id: string) => void;
  onShare: (id: string) => void;
}

function ViewCard({ view, onSelect, onEdit, onDelete, onSetDefault, onShare }: ViewCardProps) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div
      className={`group flex items-center justify-between p-3 rounded-lg border transition-all cursor-pointer ${
        view.is_default
          ? 'bg-primary/5 border-primary/20'
          : 'bg-card hover:bg-muted/50'
      }`}
      onClick={() => onSelect?.(view)}
    >
      <div className="flex items-center gap-3">
        <span
          className="text-2xl"
          style={{ filter: view.color ? `drop-shadow(0 0 4px ${view.color})` : undefined }}
        >
          {view.icon || '📋'}
        </span>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium">{view.name}</span>
            {view.is_default && (
              <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
            )}
            {view.is_pinned && <Pin className="w-4 h-4 text-primary" />}
          </div>
          {view.description && (
            <p className="text-sm text-muted-foreground">{view.description}</p>
          )}
          {view.use_count > 0 && (
            <p className="text-xs text-muted-foreground">
              Used {view.use_count} times
            </p>
          )}
        </div>
      </div>

      <div className="relative">
        <button
          onClick={(e) => {
            e.stopPropagation();
            setShowMenu(!showMenu);
          }}
          className="p-2 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <MoreVertical className="w-4 h-4" />
        </button>

        {showMenu && (
          <>
            <div
              className="fixed inset-0 z-40"
              onClick={() => setShowMenu(false)}
            />
            <div className="absolute right-0 z-50 mt-1 w-48 bg-popover border rounded-lg shadow-lg py-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(view);
                  setShowMenu(false);
                }}
                className="w-full px-4 py-2 text-left flex items-center gap-2 hover:bg-muted"
              >
                <Edit3 className="w-4 h-4" />
                Edit
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onSetDefault(view.id);
                  setShowMenu(false);
                }}
                className="w-full px-4 py-2 text-left flex items-center gap-2 hover:bg-muted"
              >
                <Star className="w-4 h-4" />
                Set as Default
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onShare(view.id);
                  setShowMenu(false);
                }}
                className="w-full px-4 py-2 text-left flex items-center gap-2 hover:bg-muted"
              >
                <Share2 className="w-4 h-4" />
                Share
              </button>
              <hr className="my-1" />
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm('Are you sure you want to delete this view?')) {
                    onDelete(view.id);
                  }
                  setShowMenu(false);
                }}
                className="w-full px-4 py-2 text-left flex items-center gap-2 text-destructive hover:bg-destructive/10"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
