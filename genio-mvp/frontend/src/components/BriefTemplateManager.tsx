"""
Brief template manager for customizing Daily Briefs.
"""
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Settings, Clock, Layout, Check, MoreVertical,
  Trash2, Copy, Star, Eye
} from 'lucide-react';
import { briefTemplateApi } from '../services/api/briefTemplates';
import type { BriefTemplate, BriefLayout } from '../types/briefTemplate';

interface BriefTemplateManagerProps {
  className?: string;
}

const LAYOUTS: { id: BriefLayout; name: string; description: string }[] = [
  { id: 'compact', name: 'Compact', description: 'Minimal list for quick scanning' },
  { id: 'standard', name: 'Standard', description: 'Balanced sections with summaries' },
  { id: 'detailed', name: 'Detailed', description: 'Full content with AI analysis' },
  { id: 'executive', name: 'Executive', description: 'High-level summary only' },
  { id: 'magazine', name: 'Magazine', description: 'Visual, magazine-style' },
];

const DELIVERY_TIMES = [
  { value: '08:00', label: 'Morning (8:00 AM)' },
  { value: '12:00', label: 'Lunch (12:00 PM)' },
  { value: '18:00', label: 'Evening (6:00 PM)' },
  { value: '21:00', label: 'Night (9:00 PM)' },
];

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export function BriefTemplateManager({ className = '' }: BriefTemplateManagerProps) {
  const queryClient = useQueryClient();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<BriefTemplate | null>(null);
  
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['briefTemplates'],
    queryFn: () => briefTemplateApi.getAll(),
  });
  
  const createTemplate = useMutation({
    mutationFn: (data: Partial<BriefTemplate>) => briefTemplateApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['briefTemplates'] });
      setShowCreateForm(false);
    },
  });
  
  const updateTemplate = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<BriefTemplate> }) =>
      briefTemplateApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['briefTemplates'] });
      setEditingTemplate(null);
    },
  });
  
  const deleteTemplate = useMutation({
    mutationFn: (id: string) => briefTemplateApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['briefTemplates'] });
    },
  });
  
  const setDefault = useMutation({
    mutationFn: (id: string) => briefTemplateApi.setDefault(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['briefTemplates'] });
    },
  });
  
  if (isLoading) {
    return <div className="animate-pulse">Loading templates...</div>;
  }
  
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Brief Templates
          </h2>
          <p className="text-sm text-muted-foreground">
            Customize your Daily Brief format and schedule
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="btn btn-primary"
        >
          <Plus className="w-4 h-4 mr-1" />
          New Template
        </button>
      </div>
      
      {/* Templates List */}
      <div className="space-y-3">
        {templates.map((template) => (
          <div
            key={template.id}
            className={`card p-4 ${template.isDefault ? 'ring-2 ring-primary' : ''}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold">{template.name}</h3>
                  {template.isDefault && (
                    <span className="text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded">
                      Default
                    </span>
                  )}
                  {!template.isActive && (
                    <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded">
                      Inactive
                    </span>
                  )}
                </div>
                
                {template.description && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {template.description}
                  </p>
                )}
                
                <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Layout className="w-3 h-3" />
                    {LAYOUTS.find(l => l.id === template.layout)?.name || template.layout}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {DELIVERY_TIMES.find(t => t.value === template.deliveryTime)?.label || template.deliveryTime}
                  </span>
                  <span>
                    {template.maxArticles} articles max
                  </span>
                </div>
              </div>
              
              <div className="flex items-center gap-1">
                <button
                  onClick={() => briefTemplateApi.preview(template.id)}
                  className="p-2 hover:bg-muted rounded-lg"
                  title="Preview"
                >
                  <Eye className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setEditingTemplate(template)}
                  className="p-2 hover:bg-muted rounded-lg"
                  title="Edit"
                >
                  <Settings className="w-4 h-4" />
                </button>
                <TemplateMenu
                  template={template}
                  onSetDefault={() => setDefault.mutate(template.id)}
                  onDelete={() => {
                    if (confirm('Delete this template?')) {
                      deleteTemplate.mutate(template.id);
                    }
                  }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Create/Edit Modal */}
      {(showCreateForm || editingTemplate) && (
        <TemplateForm
          template={editingTemplate}
          onSubmit={(data) => {
            if (editingTemplate) {
              updateTemplate.mutate({ id: editingTemplate.id, data });
            } else {
              createTemplate.mutate(data);
            }
          }}
          onCancel={() => {
            setShowCreateForm(false);
            setEditingTemplate(null);
          }}
        />
      )}
    </div>
  );
}

interface TemplateMenuProps {
  template: BriefTemplate;
  onSetDefault: () => void;
  onDelete: () => void;
}

function TemplateMenu({ template, onSetDefault, onDelete }: TemplateMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 hover:bg-muted rounded-lg"
      >
        <MoreVertical className="w-4 h-4" />
      </button>
      
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 z-50 mt-1 w-48 bg-popover border rounded-lg shadow-lg py-1">
            {!template.isDefault && (
              <button
                onClick={() => {
                  onSetDefault();
                  setIsOpen(false);
                }}
                className="w-full px-4 py-2 text-left flex items-center gap-2 hover:bg-muted"
              >
                <Star className="w-4 h-4" />
                Set as Default
              </button>
            )}
            <button
              onClick={() => {
                onDelete();
                setIsOpen(false);
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
  );
}

interface TemplateFormProps {
  template: BriefTemplate | null;
  onSubmit: (data: Partial<BriefTemplate>) => void;
  onCancel: () => void;
}

function TemplateForm({ template, onSubmit, onCancel }: TemplateFormProps) {
  const [formData, setFormData] = useState<Partial<BriefTemplate>>({
    name: template?.name || '',
    description: template?.description || '',
    layout: template?.layout || 'standard',
    maxArticles: template?.maxArticles || 10,
    minDeltaScore: template?.minDeltaScore || 0,
    deliveryTime: template?.deliveryTime || '08:00',
    deliveryDays: template?.deliveryDays || [1, 2, 3, 4, 5],
    isActive: template?.isActive ?? true,
  });
  
  const toggleDay = (day: number) => {
    const days = formData.deliveryDays || [];
    if (days.includes(day)) {
      setFormData({
        ...formData,
        deliveryDays: days.filter(d => d !== day)
      });
    } else {
      setFormData({
        ...formData,
        deliveryDays: [...days, day].sort()
      });
    }
  };
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-background rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-auto">
        <div className="p-6 space-y-6">
          <h3 className="text-lg font-semibold">
            {template ? 'Edit Template' : 'Create Template'}
          </h3>
          
          {/* Name */}
          <div>
            <label className="label">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Morning Brief"
              className="input w-full"
            />
          </div>
          
          {/* Description */}
          <div>
            <label className="label">Description</label>
            <input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Brief description..."
              className="input w-full"
            />
          </div>
          
          {/* Layout */}
          <div>
            <label className="label">Layout Style</label>
            <div className="grid grid-cols-2 gap-2">
              {LAYOUTS.map((layout) => (
                <button
                  key={layout.id}
                  onClick={() => setFormData({ ...formData, layout: layout.id })}
                  className={`p-3 text-left rounded-lg border transition-all ${
                    formData.layout === layout.id
                      ? 'border-primary bg-primary/5'
                      : 'border-muted hover:border-primary/50'
                  }`}
                >
                  <div className="font-medium text-sm">{layout.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {layout.description}
                  </div>
                </button>
              ))}
            </div>
          </div>
          
          {/* Delivery Settings */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Delivery Time</label>
              <select
                value={formData.deliveryTime}
                onChange={(e) => setFormData({ ...formData, deliveryTime: e.target.value })}
                className="input w-full"
              >
                {DELIVERY_TIMES.map((time) => (
                  <option key={time.value} value={time.value}>
                    {time.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="label">Max Articles</label>
              <input
                type="number"
                min={1}
                max={50}
                value={formData.maxArticles}
                onChange={(e) => setFormData({ ...formData, maxArticles: parseInt(e.target.value) })}
                className="input w-full"
              />
            </div>
          </div>
          
          {/* Delivery Days */}
          <div>
            <label className="label">Delivery Days</label>
            <div className="flex gap-2">
              {DAYS.map((day, index) => {
                const dayNum = index + 1;
                const isSelected = formData.deliveryDays?.includes(dayNum);
                return (
                  <button
                    key={day}
                    onClick={() => toggleDay(dayNum)}
                    className={`flex-1 py-2 text-sm rounded-lg transition-all ${
                      isSelected
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground hover:bg-muted/80'
                    }`}
                  >
                    {day}
                  </button>
                );
              })}
            </div>
          </div>
          
          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <button
              onClick={onCancel}
              className="flex-1 btn btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={() => onSubmit(formData)}
              disabled={!formData.name}
              className="flex-1 btn btn-primary"
            >
              {template ? 'Save Changes' : 'Create Template'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
